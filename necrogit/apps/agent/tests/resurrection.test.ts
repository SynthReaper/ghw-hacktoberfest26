import { test } from 'node:test';
import assert from 'node:assert';
import path from 'node:path';
import fs from 'node:fs';
import { ResurrectionWorkflow, GraveyardRepoTarget } from '../src/workflows/resurrection.js';

test('ResurrectionWorkflow: runs durable multi-step séance and revives target', async () => {
  const workflow = new ResurrectionWorkflow();

  const tempGraveyard = path.resolve(__dirname, 'test_graveyard');
  const tempRepo = path.join(tempGraveyard, 'vintage_tool');
  if (!fs.existsSync(tempRepo)) {
    fs.mkdirSync(tempRepo, { recursive: true });
  }

  fs.writeFileSync(
    path.join(tempRepo, 'tool.py'),
    `import urllib2\nprint "vintage tool running"\n`
  );

  const targets: GraveyardRepoTarget[] = [
    {
      id: 'test_vintage_tool',
      name: 'vintage-tool-2012',
      path: tempRepo,
      historicalUrl: 'http://example.com/vintage-tool',
      daysInactive: 4800,
      dependencyCount: 5,
      unpinnedRatio: 0.8,
      cyclomaticEntropy: 35.0,
    },
  ];

  const result = await workflow.run(targets);

  assert.strictEqual(result.status, 'completed');
  assert.strictEqual(result.resurrectedCount, 1);
  assert.ok(result.totalZombiesKilled >= 1);
  assert.ok(result.records.length === 1);

  const rec = result.records[0];
  assert.strictEqual(rec.repoName, 'vintage-tool-2012');
  assert.ok(rec.bitrotScoreBefore > rec.bitrotScoreAfter);
  assert.ok(rec.cveRiskBefore > rec.cveRiskAfter);
  assert.ok(fs.existsSync(rec.resurrectedPath));

  // Clean up temp
  fs.rmSync(tempGraveyard, { recursive: true, force: true });
});
