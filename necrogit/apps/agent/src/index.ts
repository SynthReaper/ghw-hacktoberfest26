#!/usr/bin/env node
import { ResurrectionWorkflow } from './workflows/resurrection.js';
import { initSentry } from './telemetry/sentry.js';

async function main() {
  initSentry();
  const args = process.argv.slice(2);

  console.log('============================================================');
  console.log('💀 NecroGit — The Open-Source Séance & Zombie Code Necromancer');
  console.log('🎃 Hacktoberfest 2026 Week 4: "Ghost in the Machine"');
  console.log('============================================================\n');

  if (args.includes('--help') || args.length === 0) {
    console.log(`Usage:
  necrogit --seance           Execute resurrection ritual across all graveyard repos
  necrogit --repo <path>      Resurrect a specific vintage repository path
  necrogit --help             Display this help message
`);
    return;
  }

  if (args.includes('--seance')) {
    console.log('[NecroGit] Commencing automated digital séance across graveyard...\n');
    const workflow = new ResurrectionWorkflow();
    const result = await workflow.run();

    console.log('\n============================================================');
    console.log('✨ SÉANCE COMPLETE — RESURRECTION REPORT:');
    console.log(`- Repositories Resurrected: ${result.resurrectedCount}`);
    console.log(`- Zombie Dependencies Banished: ${result.totalZombiesKilled}`);
    console.log(`- Average Bitrot Reduction: ${result.averageBitrotReductionPct}%`);
    console.log('============================================================');
    for (const r of result.records) {
      console.log(`\n⚰️ ${r.repoName}:`);
      console.log(`   Author: ${r.originalAuthor} (Died ~${r.deathYear})`);
      console.log(`   Bitrot Index: ${r.bitrotScoreBefore} -> ${r.bitrotScoreAfter}`);
      console.log(`   CVE Risk: ${(r.cveRiskBefore * 100).toFixed(1)}% -> ${(r.cveRiskAfter * 100).toFixed(1)}%`);
      console.log(`   Revived Location: ${r.resurrectedPath}`);
      console.log(`   Audio Séance: "${r.seanceAudioTranscript}"`);
    }
  }
}

main().catch(err => {
  console.error('[NecroGit] Fatal error during séance:', err);
  process.exit(1);
});
