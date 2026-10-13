# 04 — Implementation Plan (Wed Oct 14 → Sun Oct 18, all times IST)

Task IDs refer to `09-TASK-BACKLOG.md`. Hard deadline: Mon Oct 19, 12:29 PM IST. **Target publish: Sun Oct 18 by 8 PM IST.** Mon morning is buffer only.

## Critical path and the two riskiest items
1. **Tinker fine-tune** (unknown API, serving path, run time). Smoke-test it on Thu night, not Fri.
2. **Baseline data** (needs the human: a closed-API key for ~150 incumbent answers, or a human-gold-only fallback). Resolve Wed.

## Day 0 — Wed Oct 14: foundations
- Human: T-001 (credits, accounts, keys), decide baseline-data route (Q1), pick candidate first-user names (Q5).
- Agent: T-002 repo + CI skeleton, T-003 config, T-004 data model, T-005 dataset import/splits/provenance/PII, T-006 provider layer + FakeProvider, T-007 provider configs and `models probe` (resolve Q3), T-008 pricing loader.
- Landscape check T-040 (30 min) in a spare slot.
- **Gate G1 (Wed night):** `openswitch models probe` returns a working chat response and token usage from at least 3 different open models on at least 2 providers; import/validation tests pass.

## Day 1 — Thu Oct 15: the core engine
- Agent: T-009 runner, T-010 deterministic metrics, T-011 judge, T-012 stats, T-013 cost model, T-014 recommendation, T-015 Sentry spans, T-016 CLI, T-017 demo datasets (Task A, Task B), T-018 first full run.
- Night: **T-019 Tinker smoke test** (list supported base models, train a few steps on 20 rows, sample once, record price/time, answer Q2).
- **Gate G2 (Thu night):** one command produces a JSON result for ≥ 6 models on Task A with CIs and cost per 1k. Save to `docs/evidence/`.

## Day 2 — Fri Oct 16: fine-tune, calibration, product surface
- Morning: T-020 teacher regen + provenance guard, T-021 Tinker fine-tune on Task B, T-022 k-shot baseline. Start the training run early; build UI while it runs.
- Agent: T-024 API + SSE, T-025 UI pages, T-026 report generator, T-023 calibration UI.
- Human: 20 blind labels (30 min).
- **Gate G3 (Fri night):** fine-tune result exists (positive or negative) evaluated on the test split, **or** fallback F-1 in doc 08 is activated and logged. Report renders end to end from a real experiment.

## Day 3 — Sat Oct 17: ship it and test it on a human
- Morning: T-027 Docker + Render + caps + kill switch + auto-delete, T-030 .tech domain, T-028 security hardening, T-029 tests/CI green, T-031 local mode check.
- **Gate G4 (Sat noon):** hosted demo reachable on the .tech domain from a clean browser, caps verified (simulate cap hit).
- Afternoon: **T-032 first-user pilot** (human), T-033 final frozen runs and evidence export, re-check Week 2 entries for duplicates.
- **Gate G5 (Sat night): FEATURE FREEZE.** After this, only bug fixes, docs, video and post.

## Day 4 — Sun Oct 18: story and submission
- Morning: T-034 README, T-035 demo video (script in doc 07; optional ElevenLabs narration), T-037 export agent sessions.
- Midday: T-036 post draft complete with real numbers; read it aloud once; trim.
- Afternoon: T-038 pre-submission checklist (doc 07 §9), clean-browser test of the demo link, repo public, license present.
- **Gate G6 (Sun 6 PM):** post complete. **Publish by 8 PM IST** (T-039). Screenshot the published post and confirm it appears under the `hf26challenge` tag.

## Daily rhythm
- Start: agent reads `docs/devlog.md` and backlog status, states today's tasks.
- During: commit per task; capture evidence at each milestone.
- End: agent writes the devlog entry (decisions, bugs, numbers, surprises) and the human reviews spend so far.

## If time is short, cut in this order
S-items (stretch) → T-031 polish → calibration UI polish (keep labelling) → Task B judge component (keep deterministic) → extra partner categories. **Never cut:** provenance guard, CIs, the one fine-tune result or its fallback, the hosted demo, the first-user attempt, the writing time on Sunday.
