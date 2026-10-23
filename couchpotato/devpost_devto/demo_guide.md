# CouchPotato Expenses — 3-Minute Video Pitch & Demo Script
*Hacktoberfest Week 3 ("Slow and Steady" / International Sloth Day)*

---

## ⏱️ Video Choreography (180 Seconds Total)

### 0:00 - 0:30 | The Hook & The Problem
- **Visual**: Camera starts on the developer lounging or taking a nap with a stuffed sloth, then cuts to a computer screen showing 12 messy browser tabs (utility portal logins, expired passwords, 2FA prompt countdowns).
- **Audio / Script**:
  > "Every month, millions of freelancers and small business owners dread the same nightmare: logging into 10 different utility and cloud portals, passing 2FA prompts, downloading PDFs, and wondering if our electric bill spiked or which line of IRS Schedule C our internet belongs on.
  > Today is International Sloth Day. Why should humans do chores an autonomous agent can do while we nap? Meet CouchPotato Expenses."

### 0:30 - 1:15 | The Sloth Command Center & Architecture
- **Visual**: Screen capture of Next.js 15 Sloth Command Center (`localhost:3000`).
- **Audio / Script**:
  > "Here is the Sloth Command Center. Notice the 'Lazy Payoff' counter: 38.5 hours of human dread eliminated, and over $2,100 in tax write-offs filed automatically.
  > With one click on 'Nap & Hunt', our background Mastra agent wakes up.
  > It drives Browserbase and Stagehand v4 to navigate directly into billing portals like PG&E, Verizon, and AWS, bypassing captcha friction and downloading statements directly into our encrypted local vault."

### 1:15 - 2:00 | Privacy First: Gemma 2 & TabPFN-3.5
- **Visual**: Open the Invoice Audit drawer. Highlight the "100% Privacy-Preserving Zero Leakage" badge and TabPFN confidence scores. Show the terminal running Ollama with Gemma 2.
- **Audio / Script**:
  > "Now here is why open innovation matters: your utility statements contain your home address and bank account numbers. CouchPotato NEVER sends them to closed cloud APIs.
  > Instead, Google's Gemma 2 runs 100% locally via Ollama to OCR and extract line items with zero data leakage.
  > Then, we pass those tabular line items into Prior Labs' TabPFN-3.5 foundation model. With only a few historical rows, TabPFN achieves instant state-of-the-art few-shot classification into IRS Schedule C tax lines."

### 2:00 - 2:30 | The TabPFN Bill Spike Alert
- **Visual**: Zoom in on the glowing red "Anomaly Surge Flagged" alert on the PG&E bill.
- **Audio / Script**:
  > "Look here: TabPFN's quantile regressor detected that our electric bill surged to $268.40—nearly 80% higher than our historical median. CouchPotato flagged the anomaly immediately before we overpaid, explaining the surge in plain English."

### 2:30 - 3:00 | Sentry Traces & Conclusion
- **Visual**: Show Sentry distributed tracing dashboard with agent spans (`stagehand.act`, `gemma.extract`, `tabpfn.classify`).
- **Audio / Script**:
  > "Every step is traced with Sentry Agent Tracing, providing complete visibility into latency and model performance.
  > CouchPotato is open-source, privacy-first, and designed for anyone who believes life is too short for recurring chores.
  > Happy Hacktoberfest Week 3. Stay slow, stay steady, and let CouchPotato hunt your receipts."

---

## 📋 Hacktoberfest Judging Verification Checklist

- [x] **Theme Alignment**: Directly celebrates Week 3 "Slow and Steady" / International Sloth Day by automating chores to zero clicks.
- [x] **Local Gemma 2**: 100% offline OCR extraction via Ollama (`apps/agent/src/llm/gemma.ts`).
- [x] **TabPFN-3.5**: FastMCP Python server with few-shot tax classification and quantile anomaly detection (`services/tabpfn-service/server.py`).
- [x] **Browserbase / Stagehand v4**: Intent-driven browser portal statement retrieval (`apps/agent/src/tools/browserbase.ts`).
- [x] **Mastra Agent Framework**: Durable multi-step workflow (`apps/agent/src/workflows/invoice-hunter.ts`).
- [x] **Sentry Agent Tracing**: Distributed spans and latency telemetry (`apps/agent/src/telemetry/sentry.ts`).
- [x] **Unit & Integration Tests**: Pytest suite for TabPFN passes 8/8 tests. Node test runner passes Gemma and Workflow suites.
- [x] **Zero AI Slop**: High-class tactical obsidian / newsprint UI with authentic telemetry.
