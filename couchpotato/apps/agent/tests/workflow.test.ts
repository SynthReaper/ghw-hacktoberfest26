import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { InvoiceHunterWorkflow } from '../src/workflows/invoice-hunter.js';

test('InvoiceHunterWorkflow: executes durable pipeline across portals and updates ledger', async () => {
  const tempLedgerPath = path.resolve(process.cwd(), 'tests', 'test_ledger.json');
  const tempVaultDir = path.resolve(process.cwd(), 'tests', 'test_vault');

  if (fs.existsSync(tempLedgerPath)) fs.unlinkSync(tempLedgerPath);

  const workflow = new InvoiceHunterWorkflow({
    ledgerPath: tempLedgerPath,
    vaultDir: tempVaultDir,
  });

  const customPortals = [
    {
      id: 'test_pge',
      name: 'Pacific Gas & Electric Test',
      url: 'https://test.pge.com',
      expectedVendor: 'Pacific Gas & Electric',
    },
    {
      id: 'test_aws',
      name: 'AWS Cloud Test',
      url: 'https://test.aws.com',
      expectedVendor: 'AWS Cloud Infrastructure',
    },
  ];

  const result = await workflow.execute({ portals: customPortals });

  assert.equal(result.status, 'completed');
  assert.equal(result.processedCount, 2);
  assert(result.totalSavedHours > 0);
  assert.equal(result.records.length, 2);

  // Check ledger file was created and written
  assert(fs.existsSync(tempLedgerPath));
  const ledgerContent = JSON.parse(fs.readFileSync(tempLedgerPath, 'utf-8'));
  assert.equal(ledgerContent.expenses.length, 2);
  assert(ledgerContent.summary.total_amount_usd > 0);
  assert.equal(ledgerContent.summary.sloth_mode, 'Maximum Chill');

  // Clean up test files
  if (fs.existsSync(tempLedgerPath)) fs.unlinkSync(tempLedgerPath);
});
