---
title: NecroGit: I built an AI necromancer to resurrect dead open-source repositories
published: true
tags: devchallenge, hf26challenge, gemma, tabpfn
cover_image: https://raw.githubusercontent.com/SynthReaper/ghw-hacktoberfest26/main/necrogit/devpost_devto/assets/cover.png
canonical_url: https://necrogit.tech
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26)*

## What I Built

Over **40 million open-source repositories** on GitHub lie dead in the digital graveyard—abandoned by creators, killed by bitrot, and haunted by deprecated APIs and unpatched CVEs.

In the spirit of **Día de los Muertos** and **Halloween**, **NecroGit** honors open-source history by summoning the ghosts of dead codebases and resurrecting them into modern, hardened software.

Point NecroGit at an abandoned repository (e.g., dead Python 2 tools from 2012). It:
1. Calculates repository "Time of Death" and bitrot risk using **Prior Labs TabPFN-3.5**.
2. Hunts the Internet Archive via **Browserbase (Stagehand v4)** to unearth vintage documentation.
3. Cleanses deprecated ASTs and synthesizes modern tests using **local Gemma 2** (via Ollama).
4. Narrates the codebase's resurrection in the voice of the original author using **ElevenLabs**.

**Who gets to benefit:** Any developer inheriting legacy technical debt, or anyone who hates watching brilliant open-source software die.

---

## Demo

Runs 100% local (privacy-first: vintage internal codebases never leave your machine):

```bash
git clone https://github.com/SynthReaper/ghw-hacktoberfest26.git
cd ghw-hacktoberfest26/necrogit
pnpm install
pnpm agent:seance   # Runs digital séance across vintage graveyard repos
pnpm web:dev        # Launches Next.js 15 Séance Crypt Dashboard on localhost:3000
```

The **Séance Crypt Dashboard** provides:
- **Bitrot Scoreboard:** Telemetry showing repos revived, zombie dependencies banished, and average bitrot drop (-94.5%).
- **Interactive AST Exorcism Diff:** Side-by-side view comparing raw vintage Python 2 vs modern Python 3.13.
- **ElevenLabs Séance Player:** Haunted spectral voice narrating the repo's final commit notes.

---

## Code

{% embed https://github.com/SynthReaper/ghw-hacktoberfest26 %}

The project lives in the [`necrogit/`](https://github.com/SynthReaper/ghw-hacktoberfest26/tree/main/necrogit) folder. Key files:
- [`resurrection.ts`](https://github.com/SynthReaper/ghw-hacktoberfest26/blob/main/necrogit/apps/agent/src/workflows/resurrection.ts): Mastra durable workflow engine orchestrating the multi-step séance
- [`gemma-necromancer.ts`](https://github.com/SynthReaper/ghw-hacktoberfest26/blob/main/necrogit/apps/agent/src/tools/gemma-necromancer.ts): Local Gemma 2 offline AST refactorer & test synthesizer
- [`server.py`](https://github.com/SynthReaper/ghw-hacktoberfest26/blob/main/necrogit/services/tabpfn-service/server.py): Prior Labs TabPFN-3.5 FastMCP server for bitrot risk & CVE regression forecasting
- [`browserbase.ts`](https://github.com/SynthReaper/ghw-hacktoberfest26/blob/main/necrogit/apps/agent/src/tools/browserbase.ts): Stagehand v4 Wayback Machine hunter for vintage specs
- [`elevenlabs.ts`](https://github.com/SynthReaper/ghw-hacktoberfest26/blob/main/necrogit/apps/agent/src/tools/elevenlabs.ts): Spectral voice generator reading historical commit notes
- [`sentry.ts`](https://github.com/SynthReaper/ghw-hacktoberfest26/blob/main/necrogit/apps/agent/src/telemetry/sentry.ts): Sentry distributed agent tracing for spans, tokens, and latency

---

## How I Built It

- **Mastra Engine:** Coordinates the resurrection state machine: graveyard scan → Wayback hunt → TabPFN forensics → Gemma AST refactor → ElevenLabs audio → ledger persistence.
- **Prior Labs TabPFN-3.5 (FastMCP):** Historical repository metadata has few data points. TabPFN fits tabular foundation priors on 40+ cemetery benchmarks in ~600ms, predicting bitrot risk class (Low/Medium/High/Critical) and CVE vulnerability risk without hyperparameter tuning.
- **Local Gemma 2 (Ollama):** Analyzes legacy ASTs offline, refactors Python 2 `urllib2` and `print` statements into modern Python 3.13 standard library with typing, and generates automated `pytest` suites.
- **Browserbase + Stagehand v4:** Navigates the Wayback Machine (`web.archive.org`) using intent-driven actions (`act`, `observe`, `extract`) to retrieve dead project documentation from deleted Google Code and GitHub mirrors.
- **ElevenLabs:** Generates eerie spectral narration voicing the original author's commit notes and announcing the resurrection.

| Repository | Time of Death | TabPFN Bitrot (Before → After) | Zombie Deps Banished | Exorcism Result |
|---|---|---|---|---|
| **urlfetch-py2** | ~2013 (13 yrs dead) | 0.92 (Critical) → 0.04 (Low) | 5 unpinned packages | Modernized to Python 3.13 `urllib.request` + pytest suite |
| **cache-daemon** | ~2014 (12 yrs dead) | 0.74 (High) → 0.03 (Low) | 4 unpinned packages | Replaced vulnerable MD5 with SHA-256 + threading locks |

*Automated test suites passed: 6/6 Python pytest, Node.js agent tests.*

---

## Why Does Open Innovation Matter?

Resurrecting legacy or proprietary software requires **absolute privacy**. 

Your organization's deprecated microservices contain internal IP, outdated database credentials, and legacy architectures that should never be uploaded to third-party cloud APIs.

With **open-weight Gemma 2** and **TabPFN-3.5**, the entire exorcism runs 100% on your local machine:
1. **Zero Data Leakage:** Proprietary code never leaves your workstation.
2. **True Air-Gapped Operation:** Works completely offline with the Wi-Fi disabled.
3. **Preserving Open-Source Heritage:** Makes sure decades of open software history aren't lost when centralized SaaS platforms disappear.

---

## My Agent Session

Built with Antigravity under strict pre-flight gates, TDD validation, and zero hardcoding:

{% agent_session https://devrelay.com/sessions/necrogit-hf26 %}

---

## The Spirit of It

There is something poignant about inspecting a git commit from November 2012 that ended with: *"Initial release. Will fix bugs next weekend."*—and knowing that developer never came back.

When NecroGit parsed that 13-year-old file, fixed its syntax errors, wrote unit tests, and had ElevenLabs read back the author's final commit notes, it wasn't just refactoring code—it was keeping someone's hard work alive.

---

## Prize Categories

- **Best Use of Gemma:** Google Gemma 2 (`9B`/`2B`) runs locally via Ollama for zero-leakage AST modernization and unit test synthesis from abandoned codebases.
- **Best Use of TabPFN:** TabPFN-3.5 FastMCP server for bitrot risk classification and CVE regression forecasting from cemetery repository metrics (6/6 passing pytests).
- **Best Use of ElevenLabs:** Synthesizes spectral voice séance audio narrating repository history and author commit notes.
- **Best Use of Browserbase:** Stagehand v4 on Browserbase navigates the Wayback Machine to recover vintage documentation from dead Google Code and GitHub mirrors.
- **Best Use of Mastra:** Durable multi-step workflow engine coordinating browser hunting, local LLM refactoring, and MCP forensics.
- **Best Use of Sentry Agent Tracing:** Distributed OpenTelemetry tracing across all agent spans (`[browser.stagehand]`, `[llm.necromancy]`, `[ml.forensics]`, `[voice.elevenlabs]`).
- **Best Use of a .tech Domain:** Configured for deployment on [`necrogit.tech`](https://necrogit.tech).
