'use client';

import React from 'react';
import { Skull, Flame, Radio, Shield, Sparkles, Terminal } from 'lucide-react';

export const CryptHeader: React.FC = () => {
  return (
    <div className="border border-tactical-border bg-obsidian-900 rounded-lg p-6 shadow-tactile-dark relative overflow-hidden">
      <div className="absolute top-0 right-0 w-96 h-96 bg-ectoplasm-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-marigold-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative z-10">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🕯️</span>
            <span className="text-xs font-mono uppercase tracking-widest text-marigold-400 font-bold bg-marigold-500/10 px-2.5 py-0.5 rounded border border-marigold-500/20">
              Día de los Muertos Digital Séance Active
            </span>
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white mt-1.5 flex items-center gap-3">
            <Skull className="w-8 h-8 text-ectoplasm-400" />
            NecroGit
            <span className="text-xs font-mono font-normal text-slate-400 bg-obsidian-850 px-2 py-1 rounded border border-tactical-border">
              v1.0.0 (Ghost in the Machine)
            </span>
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1 max-w-2xl">
            Over 40 million GitHub repos lie abandoned. NecroGit summons the spirits of forgotten codebases,
            cleanses ancient AST bitrot with local Gemma 2, and resurrects them for modern developers.
          </p>
        </div>

        {/* Live Partner Stack Status */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-obsidian-850 rounded border border-emerald-500/30 text-emerald-300">
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            <span>Gemma 2: Offline</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-obsidian-850 rounded border border-purple-500/30 text-purple-300">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>TabPFN: Forensics</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-obsidian-850 rounded border border-amber-500/30 text-amber-300">
            <Radio className="w-3.5 h-3.5 text-amber-400" />
            <span>ElevenLabs: Voice</span>
          </div>
        </div>
      </div>
    </div>
  );
};
