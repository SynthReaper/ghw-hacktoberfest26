# CouchPotato Expenses 🦥
### *Zero-Click Invoice & Receipt Hunter for Hacktoberfest Week 3 ("Slow and Steady")*

[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-Week%203%20Slow%20%26%20Steady-orange.svg)](https://hacktoberfest.com)
[![TabPFN](https://img.shields.io/badge/PriorLabs-TabPFN--3.5-blue.svg)](https://priorlabs.ai)
[![Gemma 2](https://img.shields.io/badge/Google-Gemma%202%20Offline-green.svg)](https://ai.google.dev/gemma)
[![Stagehand](https://img.shields.io/badge/Browserbase-Stagehand%20v4-purple.svg)](https://browserbase.com)
[![Mastra](https://img.shields.io/badge/Mastra-Workflow%20Engine-black.svg)](https://mastra.ai)
[![Sentry](https://img.shields.io/badge/Sentry-Agent%20Tracing-red.svg)](https://sentry.io)

> **CouchPotato Expenses** is an autonomous, privacy-first personal finance and utility invoice hunter designed around the Hacktoberfest Week 3 theme: **"Slow and Steady" / International Sloth Day**. 

Instead of dreading recurring monthly administrative chores—logging into electric, gas, internet, cloud, and SaaS portals, searching for PDFs, calculating tax write-offs, and filing receipts—the user does literally **nothing**. The background agent wakes up on a schedule, drives a real headless browser via **Browserbase (Stagehand v4)** to retrieve invoices, uses local **Gemma 2** (via Ollama) to extract financial line items with **zero cloud data leakage**, feeds tabular history into **TabPFN-3.5** to classify tax categories and flag abnormal billing spikes, and visualizes the sloth savings in a bespoke Next.js 15 **Sloth Command Center**.

---

## 🏗️ Monorepo Topology

```
couchpotato-expenses/
├── apps/
│   ├── agent/                      # Mastra Agent & Durable Multi-Step Workflow
│   │   ├── src/
│   │   │   ├── workflows/          # InvoiceHunterWorkflow
│   │   │   ├── agents/             # CouchPotatoAgent
│   │   │   ├── tools/              # Browserbase, TabPFN MCP client, PDF Extractor
│   │   │   ├── llm/                # Local Gemma 2 Ollama Provider
│   │   │   └── telemetry/          # Sentry Agent Tracing
│   │   └── tests/                  # Gemma & Workflow test suites
│   └── web/                        # Next.js 15 Sloth Command Center Dashboard
│       └── src/
│           ├── app/                # Pages & API routes (/api/ledger, /api/hunt)
│           └── components/         # SlothMeter, InvoiceVault, SpikeAlert, SessionPlayer
├── services/
│   └── tabpfn-service/             # Python TabPFN-3.5 FastMCP Server
│       ├── server.py               # classify_expense, detect_bill_spike, audit_schedule_c
│       ├── test_tabpfn.py          # Pytest suite (8/8 passing)
│       └── data/sample_expenses.csv# Historical benchmark ledger
├── storage/
│   ├── vault/                      # Local encrypted statement storage (.pdf)
│   ├── ledger.json                 # Auto-filed expenses & sloth telemetry
│   └── sample_expenses.csv         # Benchmark ledger
├── devpost_devto/
│   ├── submission_draft.md         # Dev.to Hacktoberfest submission article
│   └── demo_guide.md               # 3-Minute video script & judging rubric
└── README.md
```

---

## ⚡ Quick Start

### 1. Run TabPFN Intelligence Service
```bash
# In one terminal
python services/tabpfn-service/server.py
```

### 2. Run the TabPFN Test Suite
```bash
pytest services/tabpfn-service/test_tabpfn.py -v
```

### 3. Run the Next.js Sloth Command Center
```bash
pnpm install
pnpm web:dev
# Or run both agent and web dashboard concurrently:
# pnpm dev
```
Open [http://localhost:3000](http://localhost:3000) to view the Sloth Command Center!

---

## 🏆 Partner Prize Implementations

- **Google Gemma 2**: 100% offline OCR extraction (`apps/agent/src/llm/gemma.ts`) guaranteeing zero cloud leakage for private statements.
- **Prior Labs TabPFN-3.5**: FastMCP Python server (`services/tabpfn-service/server.py`) for few-shot IRS Schedule C classification and quantile spike alerts.
- **Browserbase + Stagehand v4**: Intent-driven browser statement hunting (`apps/agent/src/tools/browserbase.ts`).
- **Mastra Engine**: Durable multi-step workflow (`apps/agent/src/workflows/invoice-hunter.ts`).
- **Sentry Agent Tracing**: Distributed OpenTelemetry spans across model & browser actions (`apps/agent/src/telemetry/sentry.ts`).
- **.tech Domain**: Configured for `couchpotato.tech`.

---

## 📄 License
MIT © 2026 CouchPotato Team
