'use client';

import React, { useState } from 'react';
import { Globe, Play, ExternalLink, Terminal, CheckCircle2 } from 'lucide-react';

export const SessionPlayer: React.FC = () => {
  const [selectedSession, setSelectedSession] = useState<'pge' | 'aws' | 'verizon'>('pge');

  const sessionDetails = {
    pge: {
      portal: 'Pacific Gas & Electric (PG&E)',
      url: 'https://www.pge.com/myaccount',
      sessionId: 'bb_sess_90218_pge',
      duration: '4.2s',
      actions: [
        'Browserbase cloud instance launched in US-West (Silicon Valley)',
        'Stagehand act: "Log in with encrypted credentials from local vault"',
        'Stagehand observe: "Detect billing history table & locate latest monthly PDF"',
        'Stagehand act: "Click download statement and pipe buffer to local vault"',
        'Session finished cleanly. Zero captcha friction encountered.',
      ],
    },
    aws: {
      portal: 'AWS Cloud Billing Console',
      url: 'https://aws.amazon.com/console/billing',
      sessionId: 'bb_sess_81092_aws',
      duration: '3.8s',
      actions: [
        'Browserbase persistent authenticated context loaded',
        'Stagehand act: "Navigate to Payment and Tax Invoices tab"',
        'Stagehand observe: "Find latest October 2026 invoice link"',
        'Stagehand act: "Stream PDF binary to CouchPotato encrypted storage"',
        'Session complete. Zero manual clicks performed.',
      ],
    },
    verizon: {
      portal: 'Verizon Fios Business',
      url: 'https://www.verizon.com/business',
      sessionId: 'bb_sess_74211_vz',
      duration: '3.1s',
      actions: [
        'Browserbase headless Chromium container provisioned',
        'Stagehand act: "Access business portal statements"',
        'Stagehand observe: "Verify due date and download current e-statement"',
        'Stagehand act: "Saved statement to vault/verizon_fios_2026_10.pdf"',
        'Session complete.',
      ],
    },
  };

  const active = sessionDetails[selectedSession];

  return (
    <div className="border border-tactical-border bg-obsidian-900 rounded-lg shadow-tactile-dark overflow-hidden">
      <div className="p-5 border-b border-tactical-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-tactical-cyan" />
            <h3 className="text-lg font-bold text-white">Browserbase + Stagehand v4 Telemetry</h3>
          </div>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Autonomous headless browser agent driving web portals with human intent.
          </p>
        </div>

        {/* Portal Selector */}
        <div className="flex items-center gap-1.5 bg-obsidian-850 p-1 rounded border border-tactical-border font-mono text-xs">
          {(['pge', 'aws', 'verizon'] as const).map((key) => (
            <button
              key={key}
              onClick={() => setSelectedSession(key)}
              className={`px-3 py-1 rounded transition-colors uppercase ${
                selectedSession === key
                  ? 'bg-amber-500 text-obsidian-950 font-bold'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              {key}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 divide-y lg:divide-y-0 lg:divide-x divide-tactical-border">
        {/* Left: Simulated Browser Replay Viewport */}
        <div className="lg:col-span-7 p-6 bg-obsidian-950 flex flex-col justify-between min-h-[300px]">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800 text-xs font-mono text-zinc-400">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-lime-500 animate-ping" />
                <span>Replay Viewport [Recorded]</span>
              </span>
              <span>Session: {active.sessionId}</span>
            </div>

            <div className="mt-6 border border-tactical-border bg-obsidian-900 rounded p-6 text-center space-y-3">
              <div className="w-12 h-12 mx-auto rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-tactical-cyan">
                <Play className="w-6 h-6 ml-0.5" />
              </div>
              <h4 className="text-white font-bold text-base">{active.portal}</h4>
              <p className="text-xs font-mono text-zinc-400 max-w-sm mx-auto">
                Headless autonomous session recorded via Browserbase SDK.
                Total duration: <span className="text-amber-400 font-bold">{active.duration}</span>
              </p>
              <div className="pt-2">
                <a
                  href={`https://browserbase.com/sessions/${active.sessionId}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-tactical-cyan/10 hover:bg-tactical-cyan/20 text-cyan-400 border border-cyan-500/30 rounded transition-all"
                >
                  <span>Open Full Session Replay in Browserbase</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between text-[11px] font-mono text-zinc-500">
            <span>Stagehand v4 Intent Engine</span>
            <span>DOM Execution: 0 Errors</span>
          </div>
        </div>

        {/* Right: Live Action Log Stream */}
        <div className="lg:col-span-5 p-5 bg-obsidian-900 space-y-3 font-mono text-xs">
          <div className="flex items-center gap-1.5 text-zinc-400 font-bold uppercase tracking-wider text-[11px] pb-2 border-b border-tactical-border">
            <Terminal className="w-3.5 h-3.5 text-tactical-amber" />
            <span>Stagehand Action Execution Log</span>
          </div>

          <div className="space-y-2.5 pt-1 text-zinc-300">
            {active.actions.map((act, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-lime-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{act}</span>
              </div>
            ))}
          </div>

          <div className="pt-3 border-t border-tactical-border/70 text-[11px] text-zinc-500">
            Target URL: <span className="text-zinc-400">{active.url}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
