'use client';

import React, { useState, useEffect } from 'react';
import { SlothMeter } from '@/components/SlothMeter';
import { SpikeAlert } from '@/components/SpikeAlert';
import { InvoiceVault, ExpenseRecord } from '@/components/InvoiceVault';
import { SessionPlayer } from '@/components/SessionPlayer';
import { ShieldCheck, Cpu, Terminal, Zap, RefreshCw, Layers } from 'lucide-react';

export default function SlothDashboard() {
  const [data, setData] = useState<{
    summary: any;
    expenses: ExpenseRecord[];
  }>({
    summary: {
      total_expenses_count: 8,
      total_amount_usd: 2187.35,
      total_deductible_usd: 2187.35,
      hours_saved: 38.5,
      clicks_eliminated: 184,
      sloth_mode: 'Maximum Chill',
      spikes_detected: 1,
      last_sync: new Date().toISOString(),
    },
    expenses: [],
  });

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // Load ledger data on mount
  const loadLedger = async () => {
    try {
      setIsRefreshing(true);
      const res = await fetch('/api/ledger');
      if (res.ok) {
        const json = await res.json();
        if (json.expenses && json.summary) {
          setData(json);
        }
      }
    } catch (err) {
      console.error('Failed to load ledger:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadLedger();
  }, []);

  // Trigger Nap & Hunt action
  const handleTriggerHunt = async () => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/hunt', { method: 'POST' });
      if (res.ok) {
        await loadLedger();
      }
    } catch (err) {
      console.error('Failed to trigger hunt:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Tactical Status Bar */}
      <header className="border border-tactical-border bg-obsidian-900 rounded-lg p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-tactile-dark">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-xl shadow-tactile">
            🦥
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold font-mono tracking-tight text-white">
                COUCHPOTATO EXPENSES
              </h1>
              <span className="text-[10px] font-mono uppercase bg-amber-500 text-obsidian-950 font-black px-1.5 py-0.2 rounded">
                Week 3
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-mono">
              Zero-Click Autonomous Invoice & Receipt Hunter • Hacktoberfest 2026
            </p>
          </div>
        </div>

        {/* Live Partner Stack Status Indicators */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-obsidian-850 border border-tactical-border text-zinc-300">
            <span className="w-2 h-2 rounded-full bg-lime-400 animate-pulse" />
            <span>Gemma 2 (Ollama): 100% Offline</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-obsidian-850 border border-tactical-border text-zinc-300">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>TabPFN-3.5: Active</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-obsidian-850 border border-tactical-border text-zinc-300">
            <Zap className="w-3.5 h-3.5 text-orange-400" />
            <span>Browserbase / Stagehand v4</span>
          </div>

          <button
            onClick={loadLedger}
            disabled={isRefreshing}
            className="p-1.5 text-zinc-400 hover:text-white bg-obsidian-850 hover:bg-obsidian-800 border border-tactical-border rounded transition-all"
            title="Refresh Vault Ledger"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      {/* Sloth Scoreboard (Hours Saved, Deductible Dollars, 1-Click Trigger) */}
      <SlothMeter
        summary={data.summary}
        onTriggerHunt={handleTriggerHunt}
        isLoading={isLoading}
      />

      {/* TabPFN Spike Alerts */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-zinc-400 px-1">
          <span className="uppercase tracking-wider font-bold">TabPFN Anomaly Guardrails</span>
          <span>Quantile Tolerance: 15% - 85%</span>
        </div>
        <SpikeAlert expenses={data.expenses} />
      </div>

      {/* Active Statement & Invoice Vault Table */}
      <InvoiceVault expenses={data.expenses} />

      {/* Browserbase + Stagehand v4 Telemetry & Replay Viewer */}
      <SessionPlayer />

      {/* Architecture & Partner Verification Footprint */}
      <footer className="border-t border-tactical-border pt-6 pb-12 text-xs font-mono text-zinc-500 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Layers className="w-4 h-4 text-zinc-400" />
          <span>Mastra Durable Engine • TabPFN-3.5 FastMCP • Stagehand v4 • Local Gemma 2 • Sentry Tracing</span>
        </div>
        <div>
          <span>CouchPotato Expenses • Built for Open Innovation & Zero Dread</span>
        </div>
      </footer>
    </main>
  );
}
