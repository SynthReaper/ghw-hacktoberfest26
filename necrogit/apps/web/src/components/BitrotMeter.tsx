'use client';

import React from 'react';
import { Flame, RefreshCw, AlertTriangle, ShieldCheck, Bug, Sparkles } from 'lucide-react';

interface BitrotMeterProps {
  summary: {
    total_resurrected_count: number;
    total_zombies_exorcised: number;
    average_bitrot_reduction_pct: number;
    crypt_status: string;
    last_seance: string;
  };
  onTriggerSeance: () => void;
  isLoading: boolean;
}

export const BitrotMeter: React.FC<BitrotMeterProps> = ({ summary, onTriggerSeance, isLoading }) => {
  return (
    <div className="border border-tactical-border bg-obsidian-900 rounded-lg p-6 shadow-tactile-dark">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 border-b border-tactical-border gap-4">
        <div>
          <span className="text-xs font-mono uppercase tracking-widest text-ectoplasm-400 font-bold bg-ectoplasm-500/10 px-2 py-0.5 rounded border border-ectoplasm-500/20">
            Crypt Resurrections & Bitrot Telemetry
          </span>
          <h2 className="text-2xl font-bold tracking-tight text-white mt-1">
            The Digital Séance Scoreboard
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Status: <span className="text-ectoplasm-400 font-bold">{summary.crypt_status}</span> • Last ritual: {new Date(summary.last_seance).toLocaleTimeString()}
          </p>
        </div>

        <button
          onClick={onTriggerSeance}
          disabled={isLoading}
          className="flex items-center gap-2.5 px-5 py-2.5 bg-ectoplasm-500 hover:bg-ectoplasm-400 text-obsidian-950 font-bold font-mono text-sm rounded shadow-tactile-dark active:translate-x-0.5 active:translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Flame className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span>{isLoading ? 'Summoning Spirits...' : 'Commence Digital Séance'}</span>
        </button>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        <div className="border border-tactical-border/70 bg-obsidian-850 p-4 rounded-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>Repos Resurrected</span>
            <Sparkles className="w-4 h-4 text-ectoplasm-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-2">
            {summary.total_resurrected_count} <span className="text-xs text-slate-400 font-normal">codebases</span>
          </div>
          <div className="text-[11px] font-mono text-ectoplasm-400 mt-1 flex items-center gap-1">
            <span>Revived to Python 3.13</span>
          </div>
        </div>

        <div className="border border-tactical-border/70 bg-obsidian-850 p-4 rounded-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>Zombie Deps Banished</span>
            <Bug className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-2">
            {summary.total_zombies_exorcised} <span className="text-xs text-slate-400 font-normal">packages</span>
          </div>
          <div className="text-[11px] font-mono text-red-400 mt-1 flex items-center gap-1">
            <span>Unpinned & CVEs removed</span>
          </div>
        </div>

        <div className="border border-tactical-border/70 bg-obsidian-850 p-4 rounded-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>Average Bitrot Drop</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-2">
            -{summary.average_bitrot_reduction_pct}%
          </div>
          <div className="text-[11px] font-mono text-slate-400 mt-1 flex items-center gap-1">
            <span>TabPFN Risk: 0.88 → 0.04</span>
          </div>
        </div>

        <div className="border border-tactical-border/70 bg-obsidian-850 p-4 rounded-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>Gemma 2 Privacy</span>
            <AlertTriangle className="w-4 h-4 text-marigold-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-marigold-400 mt-2">
            100% Offline
          </div>
          <div className="text-[11px] font-mono text-slate-400 mt-1 flex items-center gap-1">
            <span>Zero cloud data leakage</span>
          </div>
        </div>
      </div>
    </div>
  );
};
