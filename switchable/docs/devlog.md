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

