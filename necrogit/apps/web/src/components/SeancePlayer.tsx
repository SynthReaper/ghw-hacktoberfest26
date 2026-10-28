'use client';

import React, { useState } from 'react';
import { Volume2, VolumeX, Sparkles, Radio, Play, Pause } from 'lucide-react';
import { ResurrectedRecord } from './TombstoneCard';

interface SeancePlayerProps {
  record: ResurrectedRecord;
}

export const SeancePlayer: React.FC<SeancePlayerProps> = ({ record }) => {
  const [isPlaying, setIsPlaying] = useState(false);

  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
  };

  return (
    <div className="border border-tactical-border bg-obsidian-900 rounded-lg p-5 shadow-tactile-dark relative overflow-hidden">
      <div className="flex items-center justify-between border-b border-tactical-border/60 pb-3">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-marigold-400" />
          <h4 className="text-sm font-bold text-white font-mono">
            ElevenLabs Spectral Séance Audio
          </h4>
        </div>
        <span className="text-[11px] font-mono text-marigold-400 bg-marigold-500/10 px-2 py-0.5 rounded border border-marigold-500/20">
          Voice: Haunting Narrator
        </span>
      </div>

      <div className="mt-4 flex flex-col sm:flex-row items-start sm:items-center gap-4 bg-obsidian-950 p-4 rounded border border-tactical-border/50">
        <button
          onClick={togglePlayback}
          className="w-12 h-12 rounded-full bg-marigold-500 hover:bg-marigold-400 text-obsidian-950 flex items-center justify-center shrink-0 shadow-tactile-candle active:translate-x-0.5 active:translate-y-0.5 transition-all"
        >
          {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
        </button>

        <div className="space-y-1 w-full">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Séance Transcript ({record.repoName})</span>
            <span>{isPlaying ? '0:07 / 0:14' : '0:14 duration'}</span>
          </div>
          <div className="h-1.5 w-full bg-obsidian-800 rounded-full overflow-hidden">
            <div
              className={`h-full bg-marigold-400 transition-all duration-300 ${
                isPlaying ? 'w-1/2 animate-pulse' : 'w-0'
              }`}
            />
          </div>
          <p className="text-xs text-slate-300 italic pt-1 font-serif leading-relaxed">
            &ldquo;{record.seanceAudioTranscript}&rdquo;
          </p>
        </div>
      </div>
    </div>
  );
};
