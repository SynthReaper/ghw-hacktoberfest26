# NecroGit 💀
### *The Open-Source Séance & Zombie Code Necromancer for Hacktoberfest Week 4 ("Ghost in the Machine")*

[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-Week%204%20Ghost%20in%20the%20Machine-purple.svg)](https://hacktoberfest.com)
[![TabPFN](https://img.shields.io/badge/PriorLabs-TabPFN--3.5-blue.svg)](https://priorlabs.ai)
[![Gemma 2](https://img.shields.io/badge/Google-Gemma%202%20Offline-green.svg)](https://ai.google.dev/gemma)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Spectral%20Voice-orange.svg)](https://elevenlabs.io)
[![Stagehand](https://img.shields.io/badge/Browserbase-Stagehand%20v4-purple.svg)](https://browserbase.com)
[![Mastra](https://img.shields.io/badge/Mastra-Workflow%20Engine-black.svg)](https://mastra.ai)
[![Sentry](https://img.shields.io/badge/Sentry-Agent%20Tracing-red.svg)](https://sentry.io)

> **NecroGit** honors open-source history in the spirit of **Día de los Muertos** and **Halloween**. It summons the "ghosts" of abandoned, bitrotted repositories on GitHub, analyzes their "Time of Death" using Prior Labs' **TabPFN-3.5**, refactors legacy ASTs into hardened modern Python 3.13 using local **Gemma 2**, recovers forgotten specs via **Browserbase Stagehand**, and narrates the resurrection in the voice of the original author using **ElevenLabs**.

---

## 🏗️ Monorepo Topology

```
necrogit/
├── apps/
│   ├── agent/                      # Mastra Agent Backend (TypeScript)
│   │   ├── src/
│   │   │   ├── workflows/          # ResurrectionWorkflow (Mastra state machine)
│   │   │   ├── tools/              # Browserbase, TabPFN MCP client, Gemma refactorer, ElevenLabs
│   │   │   └── telemetry/          # Sentry distributed agent tracing
│   │   └── tests/                  # Node.js test suite
│   └── web/                        # Next.js 15 Séance Crypt Dashboard
│       ├── src/app/                # App router (Dashboard & API routes)
│       └── src/components/         # CryptHeader, BitrotMeter, TombstoneCard, SeancePlayer
├── services/
│   └── tabpfn-service/             # Python TabPFN-3.5 FastMCP Server
│       ├── server.py               # FastMCP bitrot risk & CVE regression forecaster
│       ├── test_tabpfn.py          # Pytest suite (6/6 passing)
│       └── data/                   # Historical graveyard benchmark dataset
├── graveyard/                      # Sample dead/abandoned codebases to resurrect
│   ├── dead_urlfetch/              # Vintage Python 2 HTTP library (2012)
│   └── dead_cache_daemon/          # Vintage thread-unsafe cache daemon (2014)
├── storage/                        # Encrypted local vault & graveyard_ledger.json
└── devpost_devto/                  # Dev.to submission draft & 3-minute video pitch script
```

---

## ⚡ Quickstart

### 1. Install Dependencies
```bash
pnpm install
```

### 2. Run TabPFN Unit Tests (Python)
```bash
pytest services/tabpfn-service/test_tabpfn.py -v
```

### 3. Run Agent Tests (Node.js)
```bash
pnpm test
```

### 4. Execute the Autonomous Séance CLI
```bash
pnpm agent:seance
```

### 5. Launch Next.js Séance Crypt Dashboard
```bash
pnpm web:dev
```
Open [http://localhost:3000](http://localhost:3000) to view the Graveyard Ledger, Before/After AST Code Diff viewer, and listen to the ElevenLabs audio séance.
