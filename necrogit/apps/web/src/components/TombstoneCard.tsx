'use client';

import React from 'react';
import { Skull, Shield, ArrowRight, ExternalLink, Calendar, Code } from 'lucide-react';

export interface ResurrectedRecord {
  id: string;
  repoName: string;
  sourceLanguage: string;
  targetRuntime: string;
  originalAuthor: string;
  deathYear: number;
  yearsInCrypt: number;
  bitrotScoreBefore: number;
  bitrotScoreAfter: number;
  cveRiskBefore: number;
  cveRiskAfter: number;
  riskClassBefore: string;
  zombieDependenciesKilled: number;
  resurrectionSummary: string;
  waybackSnapshotUrl: string;
  seanceAudioTranscript: string;
  resurrectedPath: string;
  revivedFilesCount: number;
  timestamp: string;
}

interface TombstoneCardProps {
  record: ResurrectedRecord;
  onSelect: (record: ResurrectedRecord) => void;
  isSelected: boolean;
}

export const TombstoneCard: React.FC<TombstoneCardProps> = ({ record, onSelect, isSelected }) => {
  return (
    <div
      onClick={() => onSelect(record)}
      className={`border rounded-lg p-5 cursor-pointer transition-all shadow-tactile-dark relative overflow-hidden ${
        isSelected
          ? 'border-ectoplasm-400/80 bg-obsidian-850 shadow-tactile-glow'
          : 'border-tactical-border/70 bg-obsidian-900 hover:border-slate-600'
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Skull className="w-4 h-4 text-slate-400" />
            <h3 className="font-bold text-base text-white font-mono">{record.repoName}</h3>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Authored by {record.originalAuthor} • Died ~{record.deathYear} ({record.yearsInCrypt} years in crypt)
          </p>
        </div>

        <span
          className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
            record.riskClassBefore === 'Critical'
              ? 'bg-red-500/10 text-red-400 border border-red-500/20'
              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
          }`}
        >
          {record.riskClassBefore} Bitrot
        </span>
      </div>

      <p className="text-xs text-slate-300 mt-3 line-clamp-2 leading-relaxed">
        {record.resurrectionSummary}
      </p>

      {/* Before / After Stats Bar */}
      <div className="mt-4 pt-4 border-t border-tactical-border/50 grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="bg-obsidian-950/60 p-2.5 rounded border border-tactical-border/40">
          <div className="text-[10px] text-slate-500 uppercase">Bitrot Score</div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-red-400 font-bold">{record.bitrotScoreBefore}</span>
            <ArrowRight className="w-3 h-3 text-slate-500" />
            <span className="text-emerald-400 font-bold">{record.bitrotScoreAfter}</span>
          </div>
        </div>

        <div className="bg-obsidian-950/60 p-2.5 rounded border border-tactical-border/40">
          <div className="text-[10px] text-slate-500 uppercase">CVE Vulnerability</div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-red-400 font-bold">{(record.cveRiskBefore * 100).toFixed(0)}%</span>
            <ArrowRight className="w-3 h-3 text-slate-500" />
            <span className="text-emerald-400 font-bold">{(record.cveRiskAfter * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between mt-4 text-[11px] font-mono text-slate-400">
        <div className="flex items-center gap-1">
          <Code className="w-3 h-3 text-ectoplasm-400" />
          <span>{record.targetRuntime}</span>
        </div>
        <span className="text-ectoplasm-400 font-bold hover:underline">
          View Exorcism Diff →
        </span>
      </div>
    </div>
  );
};
