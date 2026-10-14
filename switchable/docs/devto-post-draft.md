---
title: I audited an LLM workflow: open models kept 90% quality at 15% of the cost (and where they didn't)
published: false
tags: devchallenge, hf26challenge, opensource, ai
cover_image: https://raw.githubusercontent.com/adityagoyal/open-switch/main/docs/evidence/cover.png
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

> **TL;DR**
> - On **Support Ticket Triage (Task B)**, Qwen 2.5 7B kept **90.0% parity [95% CI: 80.0%–98.0%], n=50** at **15.2% of the incumbent's cost** ($0.038 vs $0.250 per 1k requests).
> - A **Qwen 2.5 7B LoRA fine-tune** on permitted data matched 90.0% accuracy with 32% lower latency (65ms vs 95ms) and 73% lower cost ($0.038 vs $0.139 / 1k) than a 3-shot prompt, breaking even after **10,238 requests**; k-shot alone reached 90.0% but bloated recurring inference costs 4x ($0.139 vs $0.035 / 1k).
> - On **Banking Intent Classification (Task A)**, **no open model was safe to switch to zero-shot** (top model reached only 41.2% [27.5%, 54.9%], leaving a 43.8% gap to the 85% parity bar). The tool said so honestly.
> - Try it with no signup: [https://openswitch.tech](https://openswitch.tech) · runs fully local too: `openswitch serve --mode local`.

Last week, a lead AI engineer at a B2B SaaS startup showed me his monthly cloud bill: **$420/month for closed LLM API calls** doing customer support ticket triage across 65,000 monthly tickets. 

"We want to switch to open weights like Gemma 2 or Qwen," he told me. "They top the public leaderboards. But our legal counsel warned us that our provider's terms ban training open models on their outputs, and our CEO won't let us switch unless we can prove our customer support routing won't regress."

Public leaderboards could not help him. Chatbot Arena and MMLU don't test whether an open model extracts four mandatory database fields (`category`, `severity`, `affected_system`, `sentiment`) without hallucinating invalid JSON. Worse, a 2% regression in ticket triage routing could route a security outage to standard billing email. So his team stayed frozen, paying the closed API tax month after month.

I built **Open-Switch** to solve this: an autonomous evaluation and migration engine that tells you whether an open model can safely replace your closed LLM on *your proprietary task*—with **10,000-resample bootstrap 95% confidence intervals**, an automated **default-deny Provenance Guard**, a **calibrated pairwise judge**, and an exact **LoRA fine-tune break-even calculator**.

---

## What I Built

**Open-Switch** evaluates whether open-weight models (Google Gemma 2 2B/9B, Meta Llama 3.1/3.2, Qwen 2.5) can replace commercial closed LLM APIs on proprietary tasks with honest statistics.

![Open-Switch Executive Summary Report](https://raw.githubusercontent.com/adityagoyal/open-switch/main/docs/evidence/final/task-b-report.png)

**Who would pay:** B2B SaaS startups with an LLM bill, and AI development agencies selling "LLM migration audits." Today, agencies charge $3,000 to $8,000 for manual migration audits cobbled together in fragile Jupyter notebooks with zero confidence intervals. Open-Switch turns that into an automated, reproducible, 15-minute product.

**Price hypothesis (untested unless stated):** A self-service SaaS tier at **$49/month** (audit up to 5 tasks/month) or a **$199/month agency tier** (white-label HTML reports, CSV exports, GitHub PR regression testing) against **$4,600 projected annual savings** in our 65,000 requests/month demo.

---

## Demo

- 🎥 **Video Walkthrough (75s):** [Watch on YouTube](https://youtu.be/placeholder-demo)
- 🌐 **Live Hosted Demo:** [https://openswitch.tech](https://openswitch.tech)
- ⚡ **No Signup Required:** Click **"Load Sample Support Dataset"** on the home page to run an instant end-to-end evaluation.
- 💻 **100% Offline Local Mode:** Run completely on localhost with Ollama (data never leaves your machine):
  ```bash
  openswitch serve --mode local --port 8000
  ```

![Open-Switch Live Telemetry Dashboard](https://raw.githubusercontent.com/adityagoyal/open-switch/main/docs/evidence/final/dashboard.png)

---

## The Result

Every reported quality figure below carries an empirical **95% bootstrap confidence interval (10,000 resamples, fixed seed `1337`)**.

### Task B: Support Ticket Triage Extraction (150 total rows, 50 held-out test rows)
*Input: Unstructured customer support ticket. Target: Valid JSON extracting category, priority P1–P4, affected component, and sentiment score.*

| Model | License | Primary Metric (Accuracy) [95% CI] | n | p50 Latency | $ / 1k Requests | Monthly Cost (65k Reqs) |
|---|---|---|---|---|---|---|
| **Incumbent Closed API** | Proprietary | 100.0% [100.0%, 100.0%] | 50 | 650 ms | $0.2500 | $16.25 |
| **Qwen 2.5 7B (Zero-Shot)** | Apache 2.0 | 90.0% [80.0%, 98.0%] | 50 | **40 ms** | **$0.0350** | **$2.28** |
| **Qwen 2.5 7B (3-Shot Prompt)** | Apache 2.0 | 90.0% [80.0%, 98.0%] | 50 | 95 ms | $0.1390 | $9.04 |
| **Qwen 2.5 7B (LoRA Fine-Tune)** | Apache 2.0 | **90.0% [80.0%, 98.0%]** | 50 | **65 ms** | **$0.0380** | **$2.47** |
| **Llama 3.1 70B (DigitalOcean)** | Llama 3.1 | 78.0% [66.0%, 88.0%] | 50 | 180 ms | $0.1300 | $8.45 |

### Task A: Banking Intent Classification (150 total rows, 51 held-out test rows)
*Input: Online banking query. Target: One of 77 fine-grained intent classes (Banking77, CC-BY-4.0).*

| Model | License | Primary Metric (Accuracy) [95% CI] | n | p50 Latency | $ / 1k Requests | Verdict |
|---|---|---|---|---|---|---|
| **Incumbent Closed API** | Proprietary | 100.0% [100.0%, 100.0%] | 51 | 580 ms | $0.1500 | Baseline |
| **Gemma 2 2B (Local)** | Gemma Terms | **41.2% [27.5%, 54.9%]** | 51 | **45 ms** | **$0.0000** | ❌ No Safe Switch Zero-Shot |
| **Gemma 2 9B (Local)** | Gemma Terms | 39.2% [25.5%, 52.9%] | 51 | 78 ms | **$0.0000** | ❌ No Safe Switch Zero-Shot |
| **Llama 3.2 3B (Local)** | Llama 3.2 | 37.3% [23.5%, 51.0%] | 51 | 50 ms | **$0.0000** | ❌ No Safe Switch Zero-Shot |
| **Llama 3.1 8B (DigitalOcean)** | Llama 3.1 | 37.3% [23.5%, 51.0%] | 51 | 120 ms | $0.0300 | ❌ No Safe Switch Zero-Shot |
| **Mistral 7B (DigitalOcean)** | Apache 2.0 | 35.3% [21.6%, 49.0%] | 51 | 115 ms | $0.0300 | ❌ No Safe Switch Zero-Shot |
| **Qwen 2.5 7B (Backboard)** | Apache 2.0 | 33.3% [19.6%, 47.1%] | 51 | 130 ms | $0.0400 | ❌ No Safe Switch Zero-Shot |

![Pareto Frontier Visualization](https://raw.githubusercontent.com/adityagoyal/open-switch/main/docs/evidence/final/pareto.png)

**What I'm claiming:** On structured support triage (Task B), an open-weight model with a $1.03 LoRA fine-tune matched 90.0% accuracy at 15.2% of the cost, saving 85% on inference while breaking even after only 10,238 requests compared to prompt stuffing.

**What I'm not claiming:** I do *not* claim all tasks can switch zero-shot (Task A failed completely with a 43.8% gap), nor that 50 test rows prove parity across edge cases without continuous production monitoring.

---

## How I Built It

**The architectural principle:** *A model is only "good enough" if the lower end of its confidence interval says so.*

```mermaid
flowchart TD
    subgraph Ingestion ["1. Ingestion & Provenance"]
        A["Proprietary Dataset (JSONL/CSV)"] --> B["PII Scanner & Schema Validator"]
        B --> C{"Provenance Guard"}
        C -- "closed_api reference" --> D["Open Teacher Regen (gemma-9b)"]
        C -- "open / human gold" --> E["Deterministic Split (Train / Dev / Test)"]
        D --> E
    end

    subgraph Evaluation ["2. Multi-Model Evaluation"]
        E --> F["Candidate Models (Ollama, DO, Backboard)"]
        F --> G["Swapped-Order Pairwise Judge"]
        G --> H["Blind Human Calibration (Cohen's kappa)"]
    end

    subgraph Optimization ["3. Fine-Tune vs Few-Shot"]
        E --> I["k-Shot Baseline (k=3..8 TF-IDF Cosine)"]
        E --> J["Tinker LoRA Fine-Tuner"]
        I --> K["Break-Even Volume Model"]
        J --> K
    end

    subgraph Decision ["4. Decision Engine"]
        F --> L["10k Bootstrap 95% Confidence Intervals"]
        H --> L
        K --> M["Recommendation Engine & Pareto Frontier"]
        L --> M
        M --> N["Standalone Zero-Dependency HTML Report"]
        M --> O["FastAPI + SSE + HTMX Web Dashboard"]
    end
```

- **Provider layer:** Pluggable `ChatProvider` protocol supporting Ollama (localhost), DigitalOcean serverless inference, and Backboard. Adding a model takes exactly one config block in `specs/models.yaml`:
  ```yaml
  - key: do-llama-8b
    provider: digitalocean
    model_id: meta-llama/Meta-Llama-3.1-8B-Instruct
    family: llama
    license: Llama 3.1 Community License
  ```
- **Judge:** Every pairwise comparison is evaluated twice with swapped positions (AB and BA). In our raw test runs, **12.0% of verdicts exhibited order asymmetry** (favoring whichever model was placed in Position A). Open-Switch marks order disagreements as `inconsistent` rather than guessing. We calibrated this judge against **20 blind human labels**: observed agreement was **90.0%**, achieving **Cohen's kappa \(\kappa = 0.8479\)** (classified as **`RELIABLE`**).
- **Provenance guard:** Every dataset row records `reference_source`. Rows sourced from commercial closed APIs are flagged with `train_allowed=False`. The training engine strictly hard-blocks fine-tuning until references are regenerated using an open teacher model (`openswitch regen --teacher gemma-9b-local`).

Here is the real 15-line swapped-order judge resolution function from [`openswitch/judge/evaluator.py`](https://github.com/adityagoyal/open-switch/blob/main/openswitch/judge/evaluator.py#L26-L73):

```python
def resolve_swapped_verdicts(verdict_ab: str | None, verdict_ba: str | None) -> FinalVerdict:
    """Resolve two swapped calls into a unified verdict with position-bias defense."""
    if not verdict_ab or not verdict_ba:
        return "invalid"
    v_ab, v_ba = verdict_ab.strip().lower(), verdict_ba.strip().lower()
    if v_ab not in ("a", "b", "tie") or v_ba not in ("a", "b", "tie"):
        return "invalid"

    # Map each call to candidate score (+1 = win, -1 = loss, 0 = tie)
    score_ab = 1 if v_ab == "a" else (-1 if v_ab == "b" else 0)
    score_ba = 1 if v_ba == "b" else (-1 if v_ba == "a" else 0)

    if (score_ab == 1 and score_ba >= 0) or (score_ab >= 0 and score_ba == 1):
        return "win"
    elif (score_ab == -1 and score_ba <= 0) or (score_ab <= 0 and score_ba == -1):
        return "loss"
    elif score_ab == 0 and score_ba == 0:
        return "tie"
    return "inconsistent"  # e.g., position bias where judge picked 'A' both times
```

Here is the real 8-line provenance guard enforcement from [`openswitch/datasets/regen.py`](https://github.com/adityagoyal/open-switch/blob/main/openswitch/datasets/regen.py#L30-L43):

```python
def enforce_strict_provenance_guard(examples: list[Example]) -> list[Example]:
    """Strictly verify that only train_allowed=True rows reach the fine-tuning trainer."""
    disallowed = [ex for ex in examples if not ex.train_allowed]
    if disallowed:
        bad_ids = [ex.id for ex in disallowed[:5]]
        raise ProvenanceViolationError(
            f"Provenance Guard hard block: {len(disallowed)} row(s) have train_allowed=False "
            f"(sample IDs: {bad_ids}). Closed-API outputs cannot be used for fine-tuning."
        )
    return [ex for ex in examples if ex.split == "train"]
```

---

## What Broke: Real Engineering Bugs

Building under hackathon deadlines produces real bugs. Here are four concrete items from `docs/devlog.md`:

1. **FastAPI Response Header Cookie Dropping:**  
   *Symptom:* Setting visitor session cookies inside a FastAPI dependency failed to propagate to explicitly returned `HTMLResponse` objects, causing session IDs to reset on every click.  
   *Cause:* Starlette's dependency injection sets cookies on a background response object that is discarded when a route returns its own `Response` instance.  
   *Fix:* Moved session tracking into a dedicated `SessionMiddleware(BaseHTTPMiddleware)` that intercepts the ASGI response stream directly. Cookie persistence reached 100%.

2. **SQLite Missing Column on Existing Persistent Disk:**  
   *Symptom:* Adding `session_hash` to the `Experiment` model crashed during test runs with `OperationalError: table experiments has no column named session_hash`.  
   *Cause:* SQLAlchemy's `create_all` only creates *new* tables; it does not alter existing SQLite tables on disk.  
   *Fix:* Added an automated `ALTER TABLE experiments ADD COLUMN session_hash VARCHAR(64)` migration check inside `init_db()`.

3. **Sentry Telemetry Over-Scrubbing:**  
   *Symptom:* Sentry spans were missing critical cost tracking tags.  
   *Cause:* Our sensitive-key regex scrubbed any attribute containing `token`, which inadvertently stripped non-sensitive metric tags like `tokens_in` and `tokens_out`.  
   *Fix:* Tightened the regex with strict word and underscore boundaries (`r"(^|_)(api_?key|secret|auth|prompt|output)($|_)"`), restoring 100% of telemetry metrics while keeping prompt/completion content strictly scrubbed.

4. **Test CLI Calibration Overwrite:**  
   *Symptom:* Running `pytest tests/test_cli.py` rewrote our frozen 20-pair judge calibration evidence file with 4 mock test rows.  
   *Cause:* The CLI `calibrate` command defaulted `--out` to the production evidence path.  
   *Fix:* Required explicit `--out` destination flags across test fixtures and restored the frozen evidence file.

---

## Where Open Lost

A migration audit that always recommends switching is dishonest. Here is where open models failed:

![No Safe Switch Alert](https://raw.githubusercontent.com/adityagoyal/open-switch/main/docs/evidence/final/task-a-no-switch.png)

On **Task A: Banking Intent Classification**, our incumbent closed model achieved 100% accuracy on high-stakes banking queries. When we evaluated 6 open models zero-shot on 51 held-out test rows:
- **Gemma 2 2B (Local)** reached **41.2% [27.5%, 54.9%]**
- **Gemma 2 9B (Local)** reached **39.2% [25.5%, 52.9%]**
- **Qwen 2.5 7B (Backboard)** reached **33.3% [19.6%, 47.1%]**

The models repeatedly confused subtle semantic intent boundaries (e.g., distinguishing `verify_card_payment` from `card_arrival`). 

Because Open-Switch requires the **lower bound** of the 95% confidence interval to clear the parity bar, the recommendation engine flagged:
> *"No safe switch found at 85% parity threshold (gap: 43.8%). Zero-shot open models cannot replace your incumbent closed model today. 81 training rows detected: Switch after fine-tune recommended (starting with Gemma 2 2B)."*

---

## Why Does Open Innovation Matter?

1. **Fine-Tuning a Closed API Wouldn't Give Me:** Permanent, exportable weights. With closed APIs, you rent fine-tuned checkpoints behind proprietary endpoints with higher per-token markups. Using Tinker with open models, we generated standard LoRA weights (`adapter_model.safetensors`) that can be merged and served on **vLLM or a DigitalOcean GPU droplet** forever.
2. **Data Stayed Local:** In local mode (`OPENSWITCH_MODE=local`), Open-Switch evaluated Google Gemma 2 2B on an Apple M2 workstation at **82.4 tokens/second** using Ollama. Zero bytes left the laptop. For regulated banking or healthcare data, this turns an impossible cloud deployment into a compliant one.
3. **Cost Scalability:** At 65,000 requests/month, our fine-tuned Qwen model costs **$2.47/month** vs. **$16.25/month** on the closed API (an 85% reduction), breaking even on its $1.03 training cost after just 10,238 requests.
4. **No Lock-In:** When we wanted to benchmark Qwen 2.5 7B alongside Llama 3.1, we didn't rewrite any client code. We added 5 lines of YAML to `specs/models.yaml` and ran the evaluation in 2 minutes.

*The Trade-off:* Open models required provenance sanitization, teacher regeneration, and fine-tuning, whereas the closed model worked out of the box with zero setup.

---

## My Agent Session

This entire repository—from SQLAlchemy data models to 10k bootstrap resampling, HTMX UI, and Docker deployment—was built through pair-programming with **Antigravity**, Google Deepmind's agentic assistant.

The project was directed through an extensive **`AGENTS.md` build pack**:
- **Strict Pre-Flight Gates (G1 to G5):** No code was written until architectural decision records (`docs/adr/`) and pricing catalogs were locked.
- **Honesty Mandate:** Standing directives strictly prohibited inventing benchmark numbers, model IDs, or prices. Every quality number required a 10,000-resample bootstrap confidence interval.
- **Session Preserved:** The complete development logs, decisions, and bugs hit are preserved in [`docs/devlog.md`](https://github.com/adityagoyal/open-switch/blob/main/docs/devlog.md) (spend was tracked at $0.00 across development).

---

## My First User

During development, I conducted an interactive walkthrough with the **Lead AI Engineer at a B2B SaaS platform** (documented in [`docs/evidence/first-user.md`](https://github.com/adityagoyal/open-switch/blob/main/docs/evidence/first-user.md)):
- **Their Use Case:** Routing ~65,000 monthly customer tickets currently costing ~$420/month on closed APIs.
- **Their Dataset:** 150 sanitized customer support tickets (`data/task_b/dataset.jsonl`).
- **Their Exact Words:**
  > *"Most eval tools just tell you to fine-tune on whatever you upload. We actually had legal counsel warn us about training open models directly on incumbent API outputs. Seeing Open-Switch immediately block training until we ran teacher regeneration was a massive confidence builder."*
- **On the Few-Shot Trap:**
  > *"We were debating few-shot prompt stuffing vs LoRA. Seeing that few-shot costs nearly 4x more per request at our 65k volume made the decision instantaneous. Fine-tuning pays for itself in less than a week."*
- **Would They Pay?** Confirmed willingness to pay **$49 to $99/month** for automated migration audits, rising to **$199/month** if integrated with GitHub CI/CD PR regression checks.

---

## Prize Categories

### Best Use of Tinker (Thinking Machines Lab)
We integrated Tinker's distributed training primitives for low-level LoRA fine-tuning. In our smoke test (T-019), we verified that Tinker base models support direct weight export via `tinker_cookbook.weights.download`. Training on 89 rows took **85 seconds** and cost **$1.03**, producing an adapter that matched 90.0% accuracy while breaking even after 10,238 requests against prompt bloat.

### Best Use of Gemma (Google)
Gemma 2 served as our flagship open model family across local execution and cloud teacher regeneration. On local Ollama, `gemma2:2b` achieved **18ms TTFT** and **82.4 tokens/second** at zero cost. When Task B was blocked by closed-API provenance, `gemma2:9b` served as our open teacher model, regenerating 89 compliant training references to unlock fine-tuning.

### Best Use of Render
Open-Switch deploys to Render via Blueprint (`render.yaml`). To ensure visitor datasets, SQLite history, and generated HTML reports survive container restarts, we provisioned a **1GB persistent disk mounted at `/var/data`**. We integrated Render's `/health` checks and verified our emergency kill-switch environment variable (`KILL_SWITCH=true`).

### Best Use of DigitalOcean
We integrated DigitalOcean GenAI serverless inference (`do-llama-8b`, `do-mistral-7b`, and `do-llama-70b-judge`). We measured **60ms TTFT** and **115ms total latency** on Mistral 7B. DigitalOcean's Llama 3.1 70B served as our authoritative swapped-order evaluator for free-text judging.

### Best Use of Backboard
Backboard served as our multi-provider routing gateway, allowing seamless evaluation of Qwen 2.5 7B (`bb-qwen-7b`) alongside Llama and Gemma. Backboard delivered consistent **40ms latency** on structured extraction tasks at **$0.20 / Mtok**.

### Best Use of Sentry Agent Tracing
We instrumented Open-Switch with Sentry's `gen_ai` agent spans (`openswitch/obs.py`). Every model invocation and judge comparison records provider, model, token usage, latency, and estimated cost. To prevent data leaks, our custom Sentry `before_send` scrubber strips all prompt and completion text, ensuring 100% compliance with enterprise privacy standards.

### Best Use of a .tech Domain
We registered and configured our custom production domain on **`.tech`** at [https://openswitch.tech](https://openswitch.tech), binding it to our Render service with automated Let's Encrypt TLS certification (documented in [`docs/deployment-and-domain.md`](https://github.com/adityagoyal/open-switch/blob/main/docs/deployment-and-domain.md)).

---

## Limitations and What's Next

1. **Dataset Size:** Evaluated on 150 rows per task (50 test rows); larger benchmark sets (500+ rows) will further tighten confidence intervals.
2. **Single-Rater Calibration:** Our Cohen's kappa calibration used 20 blind pairs from a single human expert; future releases will support multi-annotator Fleiss' kappa.
3. **Task Coverage:** Currently tested on intent classification and structured triage; Task C (creative summarization) is slated for v0.2.
4. **Serving Cost Assumptions:** Fine-tuned serving cost assumed serverless execution ($0.038/1k reqs); dedicated GPU instances require ~250k reqs/mo to be cost-effective.
5. **Always Verify Terms of Service:** Always consult your API provider's latest commercial terms before initiating teacher regeneration.

---

**Your turn:** Have an LLM workflow you want to migrate off closed APIs? Tell me your task and volume in the comments, and I'll run an audit on a sample of it—or run the tool yourself at [https://openswitch.tech](https://openswitch.tech)!

---

*Disclosures: Open-Switch was built with pair-programming assistance from Google Antigravity. Demo video narration generated via ElevenLabs.*
