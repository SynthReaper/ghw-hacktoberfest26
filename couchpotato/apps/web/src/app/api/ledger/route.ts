import { NextResponse } from 'next/server';
import fs from 'node:fs';
import path from 'node:path';

export async function GET() {
  try {
    const candidates = [
      path.resolve(process.cwd(), 'storage', 'ledger.json'),
      path.resolve(process.cwd(), '..', '..', 'storage', 'ledger.json'),
    ];

    let ledgerPath = candidates.find(p => fs.existsSync(p));

    if (!ledgerPath) {
      return NextResponse.json({
        summary: {
          total_expenses_count: 0,
          total_amount_usd: 0,
          total_deductible_usd: 0,
          hours_saved: 0,
          clicks_eliminated: 0,
          sloth_mode: 'Initial Sleep',
          spikes_detected: 0,
          last_sync: new Date().toISOString(),
        },
        expenses: [],
      });
    }

    const data = JSON.parse(fs.readFileSync(ledgerPath, 'utf-8'));
    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
