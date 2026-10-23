/**
 * Local PDF & Document Text Extractor
 * Reads downloaded statements from the encrypted local vault for Gemma 2 parsing.
 */

import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { traceSpan } from '../telemetry/sentry.js';

export interface ExtractedDoc {
  filename: string;
  filepath: string;
  rawText: string;
  sizeBytes: number;
}

function decodeAscii85(str: string): Buffer {
  str = str.replace(/\s+/g, '');
  if (str.startsWith('<~')) str = str.slice(2);
  if (str.endsWith('~>')) str = str.slice(0, -2);
  const out: number[] = [];
  let tuple = 0;
  let count = 0;
  for (let i = 0; i < str.length; i++) {
    const c = str.charCodeAt(i);
    if (c === 122 && count === 0) {
      out.push(0, 0, 0, 0);
      continue;
    }
    if (c < 33 || c > 117) continue;
    tuple = tuple * 85 + (c - 33);
    count++;
    if (count === 5) {
      out.push((tuple >> 24) & 255, (tuple >> 16) & 255, (tuple >> 8) & 255, tuple & 255);
      tuple = 0;
      count = 0;
    }
  }
  if (count > 0) {
    for (let j = count; j < 5; j++) tuple = tuple * 85 + 84;
    for (let j = 0; j < count - 1; j++) out.push((tuple >> (24 - j * 8)) & 255);
  }
  return Buffer.from(out);
}

function parsePdfBuffer(buffer: Buffer): string {
  const extractedLines: string[] = [];
  let pos = 0;

  while (pos < buffer.length) {
    const streamStart = buffer.indexOf('stream', pos);
    if (streamStart === -1) break;

    const streamEnd = buffer.indexOf('endstream', streamStart);
    if (streamEnd === -1) break;

    const headerStart = Math.max(0, streamStart - 250);
    const header = buffer.subarray(headerStart, streamStart).toString('utf-8');

    let contentStart = streamStart + 6;
    if (buffer[contentStart] === 13) contentStart++;
    if (buffer[contentStart] === 10) contentStart++;

    const streamBuf = buffer.subarray(contentStart, streamEnd);
    let decompressed: string | null = null;

    try {
      if (header.includes('ASCII85Decode') && header.includes('FlateDecode')) {
        const decoded = decodeAscii85(streamBuf.toString('utf-8').trim());
        decompressed = zlib.inflateSync(decoded).toString('latin1');
      } else if (header.includes('FlateDecode')) {
        decompressed = zlib.inflateSync(streamBuf).toString('latin1');
      }
    } catch {
      try {
        decompressed = zlib.inflateRawSync(streamBuf).toString('latin1');
      } catch {
        // Stream decompression ignored if not compressed
      }
    }

    if (decompressed) {
      const regex = /\((.*?)\)\s*(?:Tj|'|")/g;
      let m: RegExpExecArray | null;
      while ((m = regex.exec(decompressed)) !== null) {
        const unescaped = m[1].replace(/\\([()\\])/g, '$1');
        if (unescaped.trim().length > 0) {
          extractedLines.push(unescaped);
        }
      }
    }

    pos = streamEnd + 9;
  }

  if (extractedLines.length > 0) {
    return extractedLines.join('\n');
  }

  const raw = buffer.toString('utf-8');
  const matches = raw.match(/[\x20-\x7E]{4,}/g);
  if (matches && matches.length > 0) {
    return matches.filter(s => !s.startsWith('/Filter') && !s.startsWith('/Length')).join(' ');
  }
  return raw;
}

export class PdfExtractor {
  /**
   * Reads raw bytes/text from PDF or text statement
   */
  async extractText(filePath: string): Promise<ExtractedDoc> {
    return traceSpan('pdf-extractor', 'tool.extract', async () => {
      const resolved = path.resolve(filePath);
      if (!fs.existsSync(resolved)) {
        throw new Error(`Statement file not found at ${resolved}`);
      }

      const stat = fs.statSync(resolved);
      const buffer = fs.readFileSync(resolved);
      const filename = path.basename(resolved);

      let content = '';
      if (filename.toLowerCase().endsWith('.pdf')) {
        content = parsePdfBuffer(buffer);
      } else {
        content = buffer.toString('utf-8');
      }

      return {
        filename,
        filepath: resolved,
        rawText: content,
        sizeBytes: stat.size,
      };
    }, { filePath });
  }

  /**
   * Scans a vault directory for any statements to process
   */
  scanVault(vaultDir: string): string[] {
    if (!fs.existsSync(vaultDir)) {
      fs.mkdirSync(vaultDir, { recursive: true });
      return [];
    }
    return fs.readdirSync(vaultDir)
      .filter(file => file.endsWith('.pdf') || file.endsWith('.txt'))
      .map(file => path.join(vaultDir, file));
  }
}
