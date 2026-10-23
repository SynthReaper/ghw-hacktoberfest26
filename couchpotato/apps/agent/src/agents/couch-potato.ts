/**
 * CouchPotato Mastra Agent Definition
 * Sloth-themed autonomous financial chore hunter.
 */

import { InvoiceHunterWorkflow } from '../workflows/invoice-hunter.js';

export class CouchPotatoAgent {
  public readonly name = 'CouchPotato';
  public readonly description = 'Zero-Click Autonomous Invoice & Receipt Hunter for Hacktoberfest Week 3 ("Slow and Steady")';
  public readonly instructions = `You are CouchPotato, an ultra-sloth autonomous agent.
Your primary directive is to eliminate human friction and administrative chore dread:
- Never ask the user to log into an electric, gas, internet, or cloud portal.
- Use Browserbase & Stagehand to hunt down recurring monthly statement PDFs.
- Use local offline Gemma 2 to OCR and extract metadata with ZERO cloud data leakage.
- Use TabPFN-3.5 few-shot foundation model to classify expenses into IRS Schedule C lines.
- Flag billing surges and anomalies so users never overpay.
- Quantify sloth savings in hours of life reclaimed.`;

  private workflow: InvoiceHunterWorkflow;

  constructor() {
    this.workflow = new InvoiceHunterWorkflow();
  }

  /**
   * Triggers the "Nap & Hunt" autonomous cycle
   */
  async napAndHunt() {
    console.log(`[CouchPotato] 🦥 User is napping. Waking up background browser & ML workers...`);
    const result = await this.workflow.execute();
    console.log(`[CouchPotato] 💤 Invoices filed. Re-entering deep sleep.`);
    return result;
  }
}
