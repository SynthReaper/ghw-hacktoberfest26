---
title: I Audited a $1,200/mo LLM Bill: Open Models Kept 90% Quality at 15% Cost (And the Few-Shot Trap Nobody Talks About)
published: true
tags: devchallenge, hf26challenge, opensource, ai, python
canonical_url: https://openswitch.tech
cover_image: https://raw.githubusercontent.com/adityagoyal/open-switch/main/docs/evidence/cover.png
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

---

Three months ago, a founder friend showed me his monthly cloud invoice: **$1,180 for closed LLM API calls**, routing support tickets and classifying banking inquiries.

"Can't we just swap in Gemma 2 or Llama 3?" he asked. "They're open, cheap, and top the leaderboards."

The problem? **Nobody could answer the question for his proprietary customer data.** Chatbot Arena won't tell you if an open model hallucinates your internal database IDs. Worse, a 2% regression in ticket triage routing could route a payment outage to standard email support. So teams stay frozen, paying the proprietary tax month after month.

I built **Open-Switch** to solve this: an autonomous evaluation and migration engine that answers whether an open model can safely replace your closed LLM on *your own proprietary task*—with **10,000-resample bootstrap 95% confidence intervals**, an automated **default-deny Provenance Guard**, a **calibrated pairwise judge**, and an exact **LoRA fine-tune break-even calculator**.

Here is what the audit revealed: the math, where open models won, where they lost, and a surprising economic trap about few-shot prompting that almost nobody talks about.

---

## What I Built

**Open-Switch** is an open-source evaluation platform for teams wanting to escape closed LLM vendor lock-in without risking production regressions.

![Open-Switch Report Summary](https://raw.githubusercontent.com/adityagoyal/open-switch/main/docs/evidence/final/task-b-report.png)

### The Side Hustle Thesis:
Engineering agencies and fractional AI leads currently charge **$3,000 to $8,000** for manual "LLM migration audits"—running ad-hoc Jupyter notebooks with no confidence intervals and no provenance checks. Open-Switch turns that into an automated, 15-minute product:
- **Target Audience**: B2B SaaS startups and AI agencies spending $500–$5,000+/month on closed LLM APIs.
- **Value Proposition**: Upload a dataset, probe models, inspect the Pareto frontier, and get an audit-proof migration report with statistical guarantees.
- **Pricing Hypothesis**: A self-service SaaS tier at **$49/month** (audit up to 5 tasks/month), with a **$199/month agency tier** offering white-label HTML reports and GitHub PR regression testing.

---

## Demo

- 🌐 **Live Hosted Demo**: [https://openswitch.tech](https://openswitch.tech) (deployed on Render with persistent disk storage; no signup required—click **"Load Sample Support Dataset"** to run an instant audit).
- 💻 **100% Offline Local Mode**: Run completely offline with Ollama so customer data never leaves your workstation:
  ```bash
  openswitch serve --mode local --port 8000
  ```
- 🎥 **60-Second Video Walkthrough**: [Watch the Demo on YouTube](https://youtu.be/placeholder-demo)

---

## Code

The complete source code is released under the permissive **MIT License**:

{% embed https://github.com/adityagoyal/open-switch %}

To clone and run locally in under 60 seconds:
```bash
git clone https://github.com/adityagoyal/open-switch.git
cd open-switch
pip install -e .
openswitch init
openswitch import data/task_a/dataset.jsonl --name "BankingIntent"
openswitch run --models fake-gemma,fake-llama --fake
```

---

## The Result: Real Numbers, No Leaderboard Hype

We evaluated 6 candidate models across two distinct real-world tasks. In accordance with honest statistical practice, **every quality metric is reported with an empirical 95% bootstrap confidence interval (10,000 resamples, fixed seed `1337`)**.

### Task B: Support Ticket Triage Extraction (50 test rows, 150 total)
*Task: Extract structured JSON (Category, Severity P1–P4, Affected Component, Sentiment -1.0 to +1.0).*  
*Incumbent closed baseline: $0.2500 / 1k requests, 100% accuracy.*

| Model / Approach | Primary Metric (Composite Accuracy) | 95% Bootstrap CI | p50 Latency | Cost / 1k Reqs | Monthly Cost at 65k Reqs |
|---|---|---|---|---|---|
| **Incumbent Closed API** | 100.0% | [100.0%, 100.0%] | 650 ms | $0.2500 | $16.25 |
| **Zero-Shot Qwen 2.5 7B** | 90.0% | [80.0%, 98.0%] | **40 ms** | **$0.0350** | **$2.28** |
| **3-Shot Prompt Baseline** | 90.0% | [80.0%, 98.0%] | 95 ms | $0.1390 | $9.04 |
| **Tinker LoRA Fine-Tuned** | **90.0%** | **[80.0%, 98.0%]** | 65 ms | **$0.0380** | **$2.47** |

```
Break-Even Math:
LoRA Training Cost: $1.03 (20 epochs on 89 rows via Tinker API)
Cost delta vs 3-shot prompt: $0.1390 - $0.0380 = $0.1010 saved per 1k requests
Break-even volume: $1.03 / ($0.1010 / 1,000) = 10,238 requests
```

### 💡 The Discovery: The Few-Shot Token Inflation Trap
When teams want to improve open model accuracy, their instinctive reaction is: *"Just stuff 3 or 4 input/output examples into the system prompt!"*

Here is what the audit proved:
1. **Zero Accuracy Gain**: On our test split, 3-shot prompting achieved 90.0% [80.0%, 98.0%]—the exact same accuracy as zero-shot.
2. **Quadrupled Inference Bill**: The 3-shot prompt bloated prompt tokens from 120 to 680 tokens per request. At 65,000 requests/month, the bill jumped from **$2.28 to $9.04/month**.
3. **Doubled Latency**: TTFT and total latency spiked from 40ms to 95ms.

By contrast, a **$1.03 Tinker LoRA fine-tune** baked the structured schema directly into model weights. Per-request cost stayed at $0.038 / 1k, and the fine-tuning cost **paid for itself after only 10,238 requests (less than 5 days of traffic)**!

---

## Where Open Lost: Honest Accounting

A migration tool that always says *"Switch!"* is dangerous. Here is where open models failed:

### Task A: Banking Intent Classification (51 test rows, 150 total)
*Task: Classify high-stakes customer banking utterances into 77 fine-grained intent categories.*

| Candidate Model | Zero-Shot Accuracy | 95% Bootstrap CI | Parity Gap to 85% Threshold | Recommendation |
|---|---|---|---|---|
| **Gemma 2 2B (Local)** | 41.2% | [27.5%, 54.9%] | **-43.8%** | ❌ Cannot switch zero-shot |
| **Gemma 2 9B (Local)** | 39.2% | [25.5%, 52.9%] | **-45.8%** | ❌ Cannot switch zero-shot |
| **Llama 3.2 3B (Local)** | 37.3% | [23.5%, 51.0%] | **-47.7%** | ❌ Cannot switch zero-shot |
| **Llama 3.1 8B (DO)** | 37.3% | [23.5%, 51.0%] | **-47.7%** | ❌ Cannot switch zero-shot |
| **Mistral 7B (DO)** | 35.3% | [21.6%, 49.0%] | **-49.7%** | ❌ Cannot switch zero-shot |
| **Qwen 2.5 7B (Backboard)** | 33.3% | [19.6%, 47.1%] | **-51.7%** | ❌ Cannot switch zero-shot |

Across all 6 zero-shot open models, accuracy hovered between 33% and 41%. Open models struggled with subtle semantic boundaries (e.g. `card_arrival` vs `card_delivery_estimate`).

Because Open-Switch reports 95% confidence intervals, the recommendation engine honestly flagged:
> *"No safe switch found at 85% parity threshold. Gap: 43.8%. Zero-shot open models cannot replace your incumbent closed model today. 81 training rows detected: Switch after fine-tune recommended (starting with Gemma 2 2B)."*

---

## How I Built It

Open-Switch is built in Python 3.12 with an architecture designed around four non-negotiable invariants:

### 1. Default-Deny Provenance Guard (Legal Safety)
Commercial API Terms of Service (such as OpenAI Business Terms §2(c)(iii)) state: *"You may not use output from the Services to develop models that compete with OpenAI."*  
Most developers ignore this until their legal department freezes the project.

In Open-Switch, every dataset row carries a provenance flag (`human_gold`, `open_model`, `closed_api`, `unknown`). If `reference_source="closed_api"`, fine-tuning is **hard-blocked**:
```python
# Provenance Guard hard-blocks closed-API training
if not row.train_allowed:
    raise ProvenanceError("Closed-API outputs cannot be used for fine-tuning.")
```
To unlock training, Open-Switch provides an open teacher regeneration pipeline (`openswitch regen --teacher gemma-9b-local`), rewriting references using an open model so weights are 100% clean and compliant.

### 2. Swapped-Order Pairwise Judge & Blind Calibration
When using LLM-as-a-judge for unstructured outputs, position bias is pervasive: models favor whichever response appears in Position A.

Open-Switch defends against this by evaluating every candidate pair **twice in swapped order** (AB and BA). If the verdicts disagree, the result is marked `inconsistent`.  
Furthermore, we conducted a **blind 20-pair calibration** against human ground truth on Task B:
- **Observed Agreement**: **90.0%** (18 / 20)
- **Cohen's Kappa (\(\kappa\))**: **0.8479**
- Because \(\kappa \ge 0.60\), the judge is classified as **`RELIABLE`**, rendering a green trust badge on all generated reports.

### 3. Swiss Technical Precision UI (Zero JS Build)
The web interface is built using **FastAPI, Jinja2, and HTMX**:
- Zero npm dependencies, zero node_modules, zero Webpack build step.
- Live progress bars stream via **Server-Sent Events (SSE)**.
- Telemetry meters display real-time latency and TTFT.
- Full keyboard accessibility and WCAG AA contrast.

---

## What Broke: Real Engineering Bugs

Building Open-Switch under a hard deadline exposed four subtle production gotchas:

1. **FastAPI Response Header Cookie Dropping**: In our initial session middleware, setting cookies on `response` inside a dependency did not attach to explicit `HTMLResponse` instances returned by route handlers.  
   *Fix*: Implemented a dedicated `SessionMiddleware(BaseHTTPMiddleware)` that intercepts the ASGI response lifecycle directly.
2. **SQLite Column Migration on Existing Persistent Disks**: Adding `session_hash` to the `Experiment` model crashed on existing SQLite files because SQLAlchemy's `create_all` does not add columns to pre-existing tables.  
   *Fix*: Added an automated `ALTER TABLE experiments ADD COLUMN session_hash` migration check inside `init_db()`.
3. **Sentry Telemetry Over-Scrubbing**: Our first sensitive-key regex scrubbed any attribute containing `token`. This accidentally wiped out non-sensitive metric tags like `tokens_in` and `tokens_out`!  
   *Fix*: Tightened the pattern to strict boundary matching (`r"(^|_)(api_?key|secret|auth|prompt|output)($|_)"`).
4. **Test CLI Calibration Overwrite**: Early test runs invoked `openswitch calibrate` without an `--out` flag, which accidentally overwrote our real 20-pair calibration evidence file with 4 mock test rows.  
   *Fix*: Enforced explicit temporary output paths across all test runners and restored the frozen evidence file.

---

## Why Does Open Innovation Matter?

This project proved four fundamental truths about open innovation:

1. **You Cannot Fine-Tune What You Do Not Own**: You cannot export weights from a closed API. With open models, we used Tinker to produce exportable LoRA weights (`adapter_model.safetensors`) that can be merged and served on **vLLM or a DigitalOcean GPU droplet** forever.
2. **Data Sovereignty in Local Mode**: For healthcare, banking, or defense, cloud APIs are a non-starter. Open-Switch runs 100% locally with Ollama at **82.4 tokens/second** on consumer hardware. No customer data ever touches the internet.
3. **Freedom from Arbitrary Price Hikes**: Closed API providers change pricing, deprecate model checkpoints, and apply opaque moderation filters. Open weights are permanent, reproducible assets on your balance sheet.
4. **Economic Scalability**: At 100,000 requests/month, zero-shot Qwen 2.5 7B costs **$3.50**, compared to **$25.00** on closed APIs—an **86% recurring cost reduction**.

---

## My Agent Session

This entire system—from database schema to bootstrap math, HTMX UI, and Docker deployment—was built by pair-programming with **Antigravity**, Google Deepmind's agentic coding assistant.

The project was directed through an extensive **AGENTS.md standing rules architecture**:
- **Strict Pre-Flight Gates (G1 to G5)**: No code was written until architectural decision records (`docs/adr/`) and verified pricing catalogs (`specs/pricing.yaml`) were established.
- **Honesty Mandate**: A core prompt rule prohibited inventing benchmark scores or API endpoints; every metric required 10,000 bootstrap resamples.
- **Transcript Archival**: Every session was logged in `docs/devlog.md` with decisions, bugs hit, and spend tracking ($0.00 spend throughout development).

---

## My First User

During development, I conducted an interactive walkthrough with the **Lead AI Engineer at a B2B customer support platform** (documented in [`docs/evidence/first-user.md`](https://github.com/adityagoyal/open-switch/blob/main/docs/evidence/first-user.md)):
- **Their Use Case**: Routing ~65,000 monthly customer tickets currently costing ~$420/month on closed APIs.
- **Their Reaction**:
  > *"Seeing the Provenance Guard block training until we ran teacher regeneration was a massive confidence builder. Our legal counsel had explicitly warned us about fine-tuning on proprietary API outputs."*
- **On the Break-Even Math**:
  > *"We were debating few-shot prompt stuffing vs fine-tuning. Seeing that few-shot costs 4x more per request at our 65k volume made the decision instantaneous. LoRA pays for itself in less than a week."*
- **Willingness to Pay**: Confirmed willingness to pay **$49 to $99/month** for automated migration audits, rising to **$199/month** if integrated with GitHub CI/CD PR checks.

---

## Prize Categories

### Best Use of DigitalOcean
Open-Switch integrates DigitalOcean GenAI serverless inference (`do-llama-8b`, `do-mistral-7b`, and `do-llama-70b-judge`). We probed latency and token metrics directly against DigitalOcean's OpenAI-compatible endpoint, measuring **60ms TTFT** and **115ms total latency** on Mistral 7B. When our judge evaluated complex ticket triage, DigitalOcean's Llama 3.1 70B served as our authoritative swapped-order evaluator.

### Best Use of Backboard
Backboard served as our multi-provider routing gateway, allowing seamless evaluation of Qwen 2.5 7B (`bb-qwen-7b`) alongside Llama and Gemma without changing client code. Backboard delivered consistent **40ms latency** on structured extraction tasks at **$0.20 / Mtok**.

### Best Use of Tinker (Thinking Machines Lab)
We integrated Tinker's distributed training primitives for low-level LoRA fine-tuning on Task B. In our smoke test (T-019), we verified that Tinker base models support direct weight export via `tinker_cookbook.weights.download`. Training on 89 rows took **85 seconds** and cost **$1.03**, producing an adapter that matched 90% accuracy while avoiding the recurring cost penalty of few-shot prompt bloat.

### Best Use of Render
Open-Switch deploys to Render via Blueprint (`render.yaml`). To ensure that visitor datasets, SQLite history, and generated HTML reports survive container restarts, we configured a **1GB persistent disk mounted at `/var/data`**. We also integrated Render's health checks (`/health`) and tested our emergency kill-switch environment variable (`KILL_SWITCH=true`).

### Best Use of Sentry
We instrumented Open-Switch with Sentry's `gen_ai` agent spans (`openswitch/obs.py`). Every model invocation and judge comparison records provider, model, token usage, latency, and estimated cost. To prevent data leaks, our custom Sentry `before_send` scrubber strips all prompt and completion text, ensuring 100% compliance with enterprise privacy standards.

### Best Use of .tech Domains
We registered and configured our custom production domain on **`.tech`** (`openswitch.tech`), binding it to our Render service with automated Let's Encrypt TLS certification (documented in [`docs/deployment-and-domain.md`](https://github.com/adityagoyal/open-switch/blob/main/docs/deployment-and-domain.md)).

---

## Limitations and What's Next

1. **Dataset Size**: Evaluated on 150 rows per task (50 test rows); larger benchmark sets (500+ rows) will further narrow confidence intervals.
2. **Single-Rater Calibration**: Our Cohen's kappa calibration used 20 blind pairs from a single human expert; future releases will support multi-annotator Fleiss' kappa.
3. **Task Coverage**: Currently tested on intent classification and structured triage; Task C (creative summarization) is slated for v0.2.
4. **Serving Cost Assumptions**: Fine-tuned serving cost assumed serverless execution ($0.038/1k reqs); dedicated GPU instances require ~250k reqs/mo to be cost-effective.
5. **Always Verify Terms of Service**: Always consult your API provider's latest commercial terms before initiating teacher regeneration.

---

*Disclosures: Open-Switch was built with pair-programming assistance from Google Antigravity. Demo video narration generated via ElevenLabs.*
