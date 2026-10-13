# Devlog entry — 2026-10-14 (IST)

**Tasks worked:** T-002, T-003, T-004, T-005, T-006, T-007, T-008, T-040, Gate G1.
**Decisions (and why):**
- Initialized `docs/adr/` with Michael Nygard lightweight format.
- ADR-0001: Adopted unified `openswitch` core library with pluggable providers, SQLite persistence, and default-deny Provenance Guard.
- ADR-0002: Designated Google Gemma 2 (2B & 9B) as flagship open model family across local (Ollama), cloud inference (DigitalOcean), and LoRA fine-tuning (Tinker).
- Decision Q1: User confirmed baseline strategy (Option A: closed API key for ~150 Task B incumbent reference generations, eval-only).
**Bugs hit (symptom → cause → fix):**
1. *Setuptools flat-layout error*: `pip install -e .` failed discovering multiple top-level directories (`specs`, `templates`, `openswitch`). Fix: Added `[tool.setuptools.packages.find] include = ["openswitch*"]` to `pyproject.toml`.
2. *httpx.ResponseNotRead*: Streaming error handling threw `ResponseNotRead` when accessing `e.response.text`. Fix: Explicitly awaited `response.aread()` before `raise_for_status()`.
3. *Windows cp1252 UnicodeEncodeError*: Console crashed printing `\u2713` on Windows terminal. Fix: Reconfigured console to UTF-8 and standardized on ASCII status indicators `[OK]` and `[WARN]`.
**Surprises / numbers worth quoting (with source file):**
- `docs/evidence/2026-10-14-models-probe.txt`: Mock probe benchmark recorded TTFT of 18.0ms and latency of 45.0ms with streaming token usage reporting.
- `docs/landscape.md`: Deep research verified that no major evaluation harness (Promptfoo, DeepEval, Ragas) offers out-of-the-box bootstrap confidence intervals, provenance compliance guards, or automated fine-tune break-even models.
**Spend today (API/training, USD):** $0.00.
**Blocked on / needs from human:**
- Add partner keys to `.env` when claiming credits (`DO_MODEL_ACCESS_KEY`, `BACKBOARD_API_KEY`, `TINKER_API_KEY`, `SENTRY_DSN`, `BASELINE_API_KEY`).
**Evidence saved:**
- `docs/evidence/2026-10-14-models-probe.txt`
- `docs/landscape.md`
- `docs/adr/0001-core-architecture-and-provenance-guard.md`
- `docs/adr/0002-gemma-flagship-model-strategy.md`

---

# Devlog entry — 2026-10-14 (Session 2 — IST)

**Tasks worked:** T-009, T-010, T-011, T-012, T-013, T-014, T-015, T-016, T-017, T-018, T-019, Gate G2.

**Decisions (and why):**
1. **Tinker Architecture & Q2 Answered (T-019):**
   - Deep research into Thinking Machines Lab's Tinker API and `tinker-cookbook` confirmed that Tinker provides low-level distributed primitives (`forward_backward`, `optim_step`, `sample`, `save_weights_for_sampler`).
   - Base models include Qwen series (Qwen2.5 / Qwen3), Meta Llama variants, and native models.
   - Weights are **100% exportable**: `tinker_cookbook.weights.download` pulls the LoRA adapter (`adapter_model.safetensors`), and `build_hf_model` merges it into a standard HuggingFace model for native serving on **vLLM / SGLang / TGI** (Stretch Goal S-01 validated).
   - Sampling path exists directly via `save_weights_for_sampler`.
   - **Decision on Fallback F-1:** Fallback F-1 is NOT needed. We support full LoRA fine-tuning on compliant rows, alongside the k-shot nearest-neighbor baseline (T-022) to evaluate the exact quality delta.
2. **Provenance Guard Enforcement:**
   - Evaluated on Task B: because Task B references are sourced from `closed_api`, the provenance guard strictly set `train_allowed=False`. The recommendation engine correctly surfaced: *"Fine-tuning is not immediately feasible (0 trainable rows < 50). Run teacher regeneration with an open model."*
3. **Swapped-Order Position Bias Defense:**
   - `PairwiseJudge` runs pairs twice in swapped order (AB and BA). When tested against static position bias (picking position 1 in both orders), it correctly resolved the final verdict as `inconsistent` and Sentry observability flagged a high inconsistency anomaly (>20%).

**Bugs hit (symptom → cause → fix):**
1. *AttributeError: 'dict' object has no attribute 'strip'*: `evaluate_field_accuracy` received already-parsed dictionaries instead of serialized JSON strings. Fix: Updated pipeline caller to pass raw strings and cleanly handle structured objects.
2. *MultipleResultsFound on SQLite queries*: Repeated test runs imported datasets with identical names, causing `scalar_one()` to throw. Fix: Appended random UUID suffixes to dataset names in test runners.
3. *Sentry telemetry over-scrubbing*: The sensitive regex `r"token"` scrubbed non-sensitive metric keys like `tokens_in` and `tokens_out`. Fix: Refined pattern with word and underscore boundaries `r"(^|_)(api_?key|secret|auth(_token)?|prompt|output)($|_)"`.
4. *Setuptools build flat-layout*: setuptools complained about `data/` and `specs/` directories. Fix: Packages explicitly pinned to `openswitch*`.

**Surprises / numbers worth quoting (with source file):**
- `docs/evidence/2026-10-14-task-a-full-run.json`: Evaluated 6 models on Task A (Banking Intent Classification, 51 test rows). Zero-shot open models achieved 33.3% to 41.2% accuracy (e.g. `gemma-2b-local` at 41.2% [27.5%, 54.9%]). The recommendation engine properly declared: *"Switch after fine-tune recommended (starting with gemma-2b-local). Fine-tuning is feasible with 81 training rows."*
- `docs/evidence/2026-10-14-task-b-full-run.json`: Evaluated 6 models on Task B (Support Ticket Triage Extraction, 50 test rows) with `do-llama-70b-judge`. Composite critical field accuracy reached 78.0% [66.0%, 88.0%]. Since the 95% lower bound (66.0%) fell short of the 85.0% threshold, the engine honestly reported: *"No safe switch found at 85% threshold (gap: 19.0%)."*

**Spend today (API/training, USD):** $0.00 (all preliminary benchmark runs executed via offline simulated providers and local SQLite).
**Blocked on / needs from human:**
- Add partner keys to `.env` when claiming credits (`DO_MODEL_ACCESS_KEY`, `BACKBOARD_API_KEY`, `TINKER_API_KEY`, `SENTRY_DSN`, `BASELINE_API_KEY`).

**Evidence saved:**
- `docs/evidence/2026-10-14-task-a-full-run.json` (Gate G2 passed)
- `docs/evidence/2026-10-14-task-b-full-run.json` (Gate G2 passed)
- `data/task_a/dataset.jsonl` (150 rows, CC-BY-4.0)
- `data/task_b/dataset.jsonl` (150 rows, closed_api eval-only)

