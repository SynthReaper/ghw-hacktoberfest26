'use client';

import React from 'react';
import { AlertTriangle, TrendingUp, CheckCircle2, Cpu } from 'lucide-react';

interface Expense {
  id: string;
  vendor: string;
  date: string;
  amount: number;
  tax_category: string;
  anomaly_score: number;
  is_spike: boolean;
  expected_range?: [number, number];
  spike_reason?: string | null;
}

interface SpikeAlertProps {
  expenses: Expense[];
  onSelectExpense?: (expense: Expense) => void;
}

export const SpikeAlert: React.FC<SpikeAlertProps> = ({ expenses, onSelectExpense }) => {
  const spikes = expenses.filter(e => e.is_spike);

  if (spikes.length === 0) {
    return (
      <div className="border border-tactical-border/70 bg-obsidian-900/60 rounded-lg p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-lime-500/10 border border-lime-500/20 flex items-center justify-center text-lime-400">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-zinc-200">TabPFN Baseline Clear</h4>
            <p className="text-xs text-zinc-400 font-mono">
              All recurring bills are within expected 15th-85th historical seasonal percentiles.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-400 bg-obsidian-850 px-2.5 py-1 rounded border border-tactical-border">
          <Cpu className="w-3.5 h-3.5 text-tactical-cyan" />
          <span>TabPFN Quantile Regressor: Active</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {spikes.map((spike) => (
        <div
          key={spike.id}
          className="border border-red-500/40 bg-red-950/20 rounded-lg p-5 shadow-tactile-dark"
        >
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 mt-0.5">
                <AlertTriangle className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold uppercase bg-red-500 text-obsidian-950 px-1.5 py-0.5 rounded">
                    Anomaly Surge Flagged
                  </span>
                  <span className="text-xs font-mono text-zinc-400">
                    Anomaly Score: {(spike.anomaly_score * 100).toFixed(0)}%
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white mt-1">
                  {spike.vendor}: ${spike.amount.toFixed(2)}
                </h3>
                <p className="text-xs text-zinc-300 font-mono mt-1">
                  {spike.spike_reason || 'Abnormal surge detected compared to historical seasonal median.'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 bg-obsidian-900 border border-tactical-border p-3 rounded">
              <div className="text-right">
                <div className="text-[10px] uppercase font-mono text-zinc-400">Expected Normal Range</div>
                <div className="text-sm font-mono font-bold text-zinc-200">
                  ${spike.expected_range?.[0]?.toFixed(2) ?? '140.00'} – ${spike.expected_range?.[1]?.toFixed(2) ?? '160.00'}
                </div>
              </div>
              <div className="h-8 w-px bg-tactical-border" />
              <div>
                <div className="text-[10px] uppercase font-mono text-red-400 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" /> Surge
                </div>
                <div className="text-sm font-mono font-bold text-red-400">
                  +${(spike.amount - (spike.expected_range?.[1] ?? 160)).toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
