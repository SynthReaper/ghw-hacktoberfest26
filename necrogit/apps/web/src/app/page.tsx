'use client';

import React, { useState, useEffect } from 'react';
import { CryptHeader } from '@/components/CryptHeader';
import { BitrotMeter } from '@/components/BitrotMeter';
import { TombstoneCard, ResurrectedRecord } from '@/components/TombstoneCard';
import { SeancePlayer } from '@/components/SeancePlayer';
import { CodeDiffViewer } from '@/components/CodeDiffViewer';
import { Skull, Compass, RefreshCw } from 'lucide-react';

export default function SeanceCryptDashboard() {
  const [data, setData] = useState<{
    summary: any;
    records: ResurrectedRecord[];
  }>({
    summary: {
      total_resurrected_count: 2,
      total_zombies_exorcised: 9,
      average_bitrot_reduction_pct: 94.5,
      crypt_status: 'Séance Ready',
      last_seance: new Date().toISOString(),
    },
    records: [],
  });

  const [selectedRecord, setSelectedRecord] = useState<ResurrectedRecord | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadGraveyard = async () => {
    try {
      const res = await fetch('/api/graveyard');
      if (res.ok) {
        const json = await res.json();
        if (json.records && json.summary) {
          setData(json);
          if (json.records.length > 0 && !selectedRecord) {
            setSelectedRecord(json.records[0]);
          }
        }
      }
    } catch (err) {
      console.error('Failed to load graveyard data:', err);
    }
  };

  useEffect(() => {
    loadGraveyard();
  }, []);

  const handleTriggerSeance = async () => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/resurrect', { method: 'POST' });
      if (res.ok) {
        await loadGraveyard();
      }
    } catch (err) {
      console.error('Failed to trigger seance:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Crypt Status Header */}
      <CryptHeader />

      {/* Bitrot Meter Scoreboard & Exorcism Button */}
      <BitrotMeter
        summary={data.summary}
        onTriggerSeance={handleTriggerSeance}
        isLoading={isLoading}
      />

      {/* Main Crypt Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Tombstone List */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
              <Skull className="w-4 h-4 text-slate-400" />
              Resurrected Codebases ({data.records.length})
            </h3>
            <span className="text-[11px] font-mono text-slate-400">
              Select to inspect AST diff
            </span>
          </div>

          <div className="space-y-3">
            {data.records.map((rec) => (
              <TombstoneCard
                key={rec.id}
                record={rec}
                onSelect={(r) => setSelectedRecord(r)}
                isSelected={selectedRecord?.id === rec.id}
              />
            ))}
          </div>
        </div>

        {/* Right Column: Audio Séance & Code Diff */}
        <div className="lg:col-span-7 space-y-6">
          {selectedRecord ? (
            <>
              {/* ElevenLabs Séance Audio Player */}
              <SeancePlayer record={selectedRecord} />

              {/* AST Exorcism Before/After Diff */}
              <CodeDiffViewer record={selectedRecord} />
            </>
          ) : (
            <div className="border border-tactical-border/70 bg-obsidian-900 rounded-lg p-12 text-center text-slate-400 font-mono text-sm">
              <Compass className="w-8 h-8 mx-auto mb-2 text-slate-500 animate-pulse" />
              Select a resurrected repository to inspect its AST exorcism diff and audio séance.
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
