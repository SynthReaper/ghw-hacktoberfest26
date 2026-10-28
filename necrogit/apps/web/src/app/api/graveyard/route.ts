import { NextResponse } from 'next/server';
import fs from 'node:fs';
import path from 'node:path';

export async function GET() {
  try {
    const candidates = [
      path.resolve(process.cwd(), 'storage', 'graveyard_ledger.json'),
      path.resolve(process.cwd(), '..', '..', 'storage', 'graveyard_ledger.json'),
    ];

    const ledgerPath = candidates.find(p => fs.existsSync(p));

    if (!ledgerPath) {
      return NextResponse.json({
        summary: {
          total_resurrected_count: 2,
          total_zombies_exorcised: 9,
          average_bitrot_reduction_pct: 94.5,
          crypt_status: 'Dormant Crypt Awaiting Ritual',
          last_seance: new Date().toISOString(),
        },
        records: [
          {
            id: 'demo_urlfetch',
            repoName: 'urlfetch-py2',
            sourceLanguage: 'Python 2.7 (Abandoned 2013)',
            targetRuntime: 'Python 3.13 (Hardened)',
            originalAuthor: 'Forgotten Dev <ghost@example.null>',
            deathYear: 2013,
            yearsInCrypt: 13.0,
            bitrotScoreBefore: 0.92,
            bitrotScoreAfter: 0.04,
            cveRiskBefore: 0.88,
            cveRiskAfter: 0.01,
            riskClassBefore: 'Critical',
            zombieDependenciesKilled: 5,
            resurrectionSummary: 'Banished urllib2 and unpinned legacy C-extensions; modernized to Python 3.13 standard library with full test coverage and typing.',
            waybackSnapshotUrl: 'https://web.archive.org/web/20130412/http://code.google.com/p/urlfetch-py',
            seanceAudioTranscript: 'Hark, traveller of the terminal. I am the ghost of urlfetch-py2, authored by Forgotten Dev and abandoned to the digital crypt in the year 2013...',
            resurrectedPath: './storage/resurrected/urlfetch-py2',
            revivedFilesCount: 3,
            timestamp: new Date().toISOString(),
          },
          {
            id: 'demo_cache_daemon',
            repoName: 'cache-daemon-v0.1',
            sourceLanguage: 'Python 2.7 (Abandoned 2014)',
            targetRuntime: 'Python 3.13 (Hardened)',
            originalAuthor: 'Spectral Hacker <spectral@ancient.org>',
            deathYear: 2014,
            yearsInCrypt: 12.0,
            bitrotScoreBefore: 0.74,
            bitrotScoreAfter: 0.03,
            cveRiskBefore: 0.69,
            cveRiskAfter: 0.01,
            riskClassBefore: 'High',
            zombieDependenciesKilled: 4,
            resurrectionSummary: 'Replaced legacy md5 and unthreadsafe storage with modern SHA-256 and re-entrant threading locks.',
            waybackSnapshotUrl: 'https://web.archive.org/web/20140810/http://github.com/abandoned/cache-daemon',
            seanceAudioTranscript: 'I am the spirit of cache-daemon-v0.1. For twelve years, my threads bitrotted in silence. Today, the exorcism is complete.',
            resurrectedPath: './storage/resurrected/cache-daemon-v0.1',
            revivedFilesCount: 3,
            timestamp: new Date().toISOString(),
          },
        ],
      });
    }

    const raw = JSON.parse(fs.readFileSync(ledgerPath, 'utf-8'));
    return NextResponse.json(raw);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
