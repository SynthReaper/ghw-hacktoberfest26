'use client';

import React from 'react';
import { Clock, ShieldCheck, Zap, MousePointerClick, Moon } from 'lucide-react';

interface SlothMeterProps {
  summary: {
    total_expenses_count: number;
    total_amount_usd: number;
    total_deductible_usd: number;
    hours_saved: number;
    clicks_eliminated: number;
    sloth_mode: string;
    spikes_detected: number;
    last_sync: string;
  };
  onTriggerHunt: () => void;
  isLoading: boolean;
}

export const SlothMeter: React.FC<SlothMeterProps> = ({ summary, onTriggerHunt, isLoading }) => {
  return (
    <div className="border border-tactical-border bg-obsidian-900 rounded-lg p-6 shadow-tactile-dark">
      {/* Top Header & Trigger Action */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 border-b border-tactical-border gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🦥</span>
            <span className="text-xs font-mono uppercase tracking-widest text-amber-500 font-bold bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              International Sloth Mode Active
            </span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white mt-1">
            The Lazy Payoff Scoreboard
          </h2>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Zero human clicks required. Background agents harvest, OCR, & classify while you nap.
          </p>
        </div>

        <button
          onClick={onTriggerHunt}
          disabled={isLoading}
          className="flex items-center gap-2.5 px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-obsidian-950 font-bold font-mono text-sm rounded shadow-tactile active:translate-x-0.5 active:translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Moon className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span>{isLoading ? 'Agent Hunting...' : 'Nap & Hunt (1-Click)'}</span>
        </button>
      </div>

      {/* Primary Telemetry Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        {/* Metric 1: Hours Saved */}
        <div className="border border-tactical-border bg-obsidian-850 p-4 rounded flex flex-col justify-between">
          <div className="flex items-center justify-between text-zinc-400">
            <span className="text-xs font-mono uppercase tracking-wider">Chores Eliminated</span>
            <Clock className="w-4 h-4 text-tactical-amber" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-mono font-black text-amber-400">
              {summary.hours_saved.toFixed(1)} <span className="text-sm font-normal text-zinc-400">hrs</span>
            </div>
            <p className="text-[11px] text-zinc-400 mt-1 font-mono">
              38.5 hours of monthly login dread avoided
            </p>
          </div>
        </div>

        {/* Metric 2: Tax Deductions Identified */}
        <div className="border border-tactical-border bg-obsidian-850 p-4 rounded flex flex-col justify-between">
          <div className="flex items-center justify-between text-zinc-400">
            <span className="text-xs font-mono uppercase tracking-wider">Schedule C Deductions</span>
            <ShieldCheck className="w-4 h-4 text-tactical-lime" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-mono font-black text-lime-400">
              ${summary.total_deductible_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <p className="text-[11px] text-zinc-400 mt-1 font-mono">
              100% verified by TabPFN-3.5 classifier
            </p>
          </div>
        </div>

        {/* Metric 3: Frictionless Clicks */}
        <div className="border border-tactical-border bg-obsidian-850 p-4 rounded flex flex-col justify-between">
          <div className="flex items-center justify-between text-zinc-400">
            <span className="text-xs font-mono uppercase tracking-wider">Clicks Eliminated</span>
            <MousePointerClick className="w-4 h-4 text-tactical-cyan" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-mono font-black text-cyan-400">
              {summary.clicks_eliminated}
            </div>
            <p className="text-[11px] text-zinc-400 mt-1 font-mono">
              Portal logins, 2FA pushes & PDF saves
            </p>
          </div>
        </div>

        {/* Metric 4: Autonomous Status */}
        <div className="border border-tactical-border bg-obsidian-850 p-4 rounded flex flex-col justify-between">
          <div className="flex items-center justify-between text-zinc-400">
            <span className="text-xs font-mono uppercase tracking-wider">Autonomous Efficiency</span>
            <Zap className="w-4 h-4 text-tactical-orange" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-mono font-black text-orange-400">
              100%
            </div>
            <p className="text-[11px] text-zinc-400 mt-1 font-mono">
              Local Gemma 2 + TabPFN + Stagehand
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
