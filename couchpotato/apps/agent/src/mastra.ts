/**
 * Mastra Engine & Server Configuration
 */

import { CouchPotatoAgent } from './agents/couch-potato.js';
import { InvoiceHunterWorkflow } from './workflows/invoice-hunter.js';
import { initSentry } from './telemetry/sentry.js';

initSentry();

export const couchPotatoAgent = new CouchPotatoAgent();
export const invoiceHunterWorkflow = new InvoiceHunterWorkflow();

export const mastraConfig = {
  name: 'couchpotato-engine',
  version: '1.0.0',
  agents: {
    couchPotato: couchPotatoAgent,
  },
  workflows: {
    invoiceHunter: invoiceHunterWorkflow,
  },
};
