import test from 'node:test';
import assert from 'node:assert/strict';
import { GemmaExtractor, InvoiceMetadataSchema } from '../src/llm/gemma.js';

test('GemmaExtractor: extracts valid metadata schema from utility statement text', async () => {
  const extractor = new GemmaExtractor();
  const sampleStatement = `
  STATEMENT / TAX INVOICE: Pacific Gas & Electric
  Account # 8821-4920
  Date: Oct 15, 2026
  Commercial Electric & Gas Service
  Total Amount Due: $268.40
  Please pay by: Nov 05, 2026
  `;

  const result = await extractor.extractInvoice(sampleStatement, 'pge_statement.pdf');

  // Verify against Zod Schema
  assert.doesNotThrow(() => InvoiceMetadataSchema.parse(result));
  assert.equal(result.vendor, 'Pacific Gas & Electric');
  assert.equal(result.amount, 268.40);
  assert.equal(result.account_last4, '4920');
  assert.equal(result.privacy_verified, true);
  assert.equal(result.is_likely_deductible, true);
});

test('GemmaExtractor: extracts cloud hosting invoice correctly', async () => {
  const extractor = new GemmaExtractor();
  const sampleAws = `
  STATEMENT / TAX INVOICE: Amazon Web Services, Inc.
  Account # 9940-1288-02
  Invoice Date: 2026-10-20
  Description: AWS Cloud Infrastructure EC2, S3, RDS
  Total Amount Due: $341.25
  `;

  const result = await extractor.extractInvoice(sampleAws, 'aws_tax_invoice.pdf');

  assert.equal(result.vendor, 'AWS Cloud Infrastructure');
  assert.equal(result.amount, 341.25);
  assert.equal(result.privacy_verified, true);
});

test('PdfExtractor & GemmaExtractor: successfully parses real binary vault statement PDF', async () => {
  const { PdfExtractor } = await import('../src/tools/pdf-extractor.js');
  const path = await import('node:path');
  const fs = await import('node:fs');

  const candidates = [
    path.resolve(process.cwd(), 'storage', 'vault', 'aws_tax_invoice_2026_10.pdf'),
    path.resolve(process.cwd(), '..', 'storage', 'vault', 'aws_tax_invoice_2026_10.pdf'),
    path.resolve(process.cwd(), '..', '..', 'storage', 'vault', 'aws_tax_invoice_2026_10.pdf'),
  ];
  const awsPdf = candidates.find(p => fs.existsSync(p));
  assert(awsPdf, 'Vault PDF must exist');

  const pdfExtractor = new PdfExtractor();
  const doc = await pdfExtractor.extractText(awsPdf);
  assert(doc.rawText.includes('AWS Cloud Infrastructure'));
  assert(doc.rawText.includes('$341.25'));

  const extractor = new GemmaExtractor();
  const metadata = await extractor.extractInvoice(doc.rawText, doc.filename);
  assert.equal(metadata.vendor, 'AWS Cloud Infrastructure');
  assert.equal(metadata.amount, 341.25);
  assert.equal(metadata.privacy_verified, true);
});
