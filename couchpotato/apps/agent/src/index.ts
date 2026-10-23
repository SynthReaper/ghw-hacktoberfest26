/**
 * CouchPotato Agent Service Entrypoint & CLI Runner
 */

import http from 'node:http';
import dotenv from 'dotenv';
import { CouchPotatoAgent } from './agents/couch-potato.js';
import { invoiceHunterWorkflow } from './mastra.js';

dotenv.config();

const agent = new CouchPotatoAgent();

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--hunt') || args.includes('hunt')) {
    console.log('------------------------------------------------------------');
    console.log('🦥 CouchPotato Autonomous Invoice Hunter — CLI Mode');
    console.log('------------------------------------------------------------');
    const result = await agent.napAndHunt();
    console.log('\n[Result] Workflow completed successfully:');
    console.log(JSON.stringify(result, null, 2));
    process.exit(0);
  }

  // Start lightweight HTTP daemon for Next.js Web UI trigger
  const port = parseInt(process.env.PORT || '4111', 10);
  const server = http.createServer(async (req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    if (req.url === '/health' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', agent: agent.name, mode: 'Sloth Ready' }));
      return;
    }

    if (req.url === '/api/hunt' && req.method === 'POST') {
      try {
        console.log('[API] Received /api/hunt trigger from Command Center');
        const result = await invoiceHunterWorkflow.execute();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
      } catch (err: any) {
        console.error('[API] Hunt error:', err);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
      return;
    }

    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Endpoint not found' }));
  });

  server.listen(port, () => {
    console.log(`🦥 CouchPotato Agent daemon running at http://localhost:${port}`);
    console.log(`Endpoint: POST http://localhost:${port}/api/hunt`);
  });
}

main().catch((err) => {
  console.error('[Fatal]', err);
  process.exit(1);
});
