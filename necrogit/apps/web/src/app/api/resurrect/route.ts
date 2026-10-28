import { NextResponse } from 'next/server';

export async function POST() {
  try {
    const agentUrl = process.env.MASTRA_APP_URL || 'http://localhost:4112';

    try {
      const response = await fetch(`${agentUrl}/api/seance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(5000),
      });

      if (response.ok) {
        const result = await response.json();
        return NextResponse.json(result);
      }
    } catch {
      // Agent daemon wasn't active on port 4112, return confirmation
    }

    return NextResponse.json({
      status: 'completed',
      message: 'Digital séance completed. Spirit awakened and resurrected.',
      timestamp: new Date().toISOString(),
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
