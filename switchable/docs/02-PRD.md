# 02 — Product Requirements Document: Open-Switch v1

## 1. One-liner
Open-Switch answers one question for a team: **"Can we replace our expensive closed LLM with an open-weight model on our own task, and what would we save?"** It runs candidate open models on the team's own prompts, scores them against the team's reference outputs with honest statistics, shows the quality/cost/latency trade-off, and can fine-tune a small open model to close the gap.

## 2. Problem
- Teams pay frontier-API prices for narrow, repetitive tasks (classification, extraction, triage, rewriting) that smaller open models could often handle.
- Switching is risky. Public leaderboards do not predict performance on a specific task. Teams hand-roll scripts, eyeball a few outputs, and have no confidence interval or cost projection.
- The data is sensitive, so it cannot go to a random eval SaaS.
- Fine-tuning on a closed model's outputs may breach that provider's terms. Teams do not know which of their rows are safe to train on.

## 3. Users
| Persona | Need | Role in the side hustle |
|---|---|---|
| **P1 AI integrator / agency** | Prove savings to clients, sell migration work | Buyer of the tool and operator of paid "migration audits" |
| **P2 Startup engineer who owns the LLM bill** | Cut cost without regressions | Direct user |
| **P3 Privacy-constrained team** | Evaluate locally, nothing leaves the machine | Uses local-only mode |

## 4. Positioning and honesty about alternatives
General prompt-testing and LLM-eval tools already exist (for example open-source harnesses such as promptfoo, and commercial observability/eval platforms). **Task T-040 must verify the current landscape and write `docs/landscape.md`** before the post claims anything about alternatives. Planned differentiation, to be confirmed:
1. **Decision-first output:** a clear "switch / do not switch / switch with fine-tune" recommendation with dollars, not a score table.
2. **Statistical honesty:** confidence intervals, small-sample warnings, a human-calibrated judge, and "no safe switch found" as a valid result.
3. **Provenance guard:** tracks where each reference came from and blocks training on rows that may not be trainable.
4. **Closed loop:** evaluate, then fine-tune and re-evaluate on the same held-out set.
5. **Runs both ways:** hosted demo and fully local mode with identical code.

## 5. Goals, non-goals, release criteria
**Goals (v1, challenge scope)**
- G1. End-to-end flow from dataset upload to shareable report in under 10 minutes for 100 rows × 5 models.
- G2. Produce at least one real, reproducible result like "model X kept Y% parity [CI] at Z% of baseline cost" on two tasks.
- G3. Produce one fine-tune result (positive or negative) evaluated on the same held-out test split.
- G4. Generate enough honest evidence (numbers, traces, screenshots, logs, a real user) for a strong DEV post.

**Non-goals (v1)**: multi-tenant accounts, billing, a model marketplace, RAG/agent evaluation, multi-turn conversation evaluation, automatic prompt optimisation, production traffic shadowing.

**Release criteria (definition of done)**
- [ ] Hosted demo live on Render, on a .tech domain, with spend caps and kill switch
- [ ] Local mode (Ollama-only) works with one command, documented
- [ ] ≥ 6 distinct models evaluated on ≥ 2 tasks, incl. ≥ 1 Gemma-family and ≥ 2 other open families
- [ ] Judge calibrated on ≥ 20 human labels, agreement reported honestly
- [ ] Report shows CIs, n, assumptions, price `verified_on` dates, reproducibility block
- [ ] ≥ 1 fine-tune result evaluated on the held-out test split, or the documented fallback executed
- [ ] ≥ 80% line coverage on `metrics`, `stats`, `cost`, `provenance`; CI green
- [ ] README complete; evidence folder populated; MIT license; post-deadline commits noted if any

## 6. Scope (MoSCoW)
**Must**: dataset import/validation, provenance flags and guard, provider abstraction (OpenAI-compatible), runner with cost caps, deterministic metrics, pairwise swapped judge, bootstrap CIs, cost/latency model and savings projection, recommendation engine, standalone HTML + JSON report, CLI, web UI (upload → models → progress → report), Sentry gen_ai tracing, Render deploy, local mode, Tinker fine-tune experiment.
**Should**: blind human calibration UI, kNN few-shot baseline, teacher regeneration for trainable references, PII scan warning, savings slider in the report, per-example drilldown.
**Could**: third task (summarisation/rewrite), reversible PII masking, GitHub Action that evaluates prompt changes in PRs, DigitalOcean GPU droplet serving the fine-tuned model, ElevenLabs narration for the demo video.
**Won't (v1)**: accounts/billing, scheduled monitoring, non-text modalities.

## 7. User stories and acceptance criteria
- **US-01 Import.** As P2, I upload JSONL/CSV of prompts and reference outputs. *AC:* rows validated against `specs/dataset.schema.json`; errors reported with line numbers; 50–200 rows accepted; sha256 stored; splits assigned deterministically (60/10/30 default, seed stored).
- **US-02 Provenance.** As P2, I mark where references came from. *AC:* each row has `reference_source` ∈ {human, closed_api, open_model, unknown}; `train_allowed` defaults per source; overriding to true requires an explicit attestation checkbox and is logged in the report.
- **US-03 Pick models.** As P2, I choose candidates and enter my baseline price and monthly volume. *AC:* models come from `models.yaml`; prices show `verified_on`; stale (> 30 days) or unverified prices show a warning in the UI and report.
- **US-04 Run.** As P2, I start an experiment and see live progress. *AC:* shows per-model progress, running cost, errors; estimated cost shown before start and blocked above the cap; interrupted runs resume without re-billing completed rows.
- **US-05 Report.** As P1, I get a shareable report. *AC:* executive summary with recommendation; Pareto chart (cost vs parity); results table with CIs; worst-10 failures with judge rationale; assumptions and caveats; reproducibility block; downloadable standalone HTML and JSON.
- **US-06 Savings.** As P1, I adjust monthly volume and see savings and fine-tune break-even. *AC:* formulas from doc 05 §6; all inputs echoed.
- **US-07 Calibrate.** As P1, I blind-label 20 outputs to check the judge. *AC:* UI hides which side is the reference; report shows agreement % and Cohen's kappa; if kappa < 0.4 the report banner says the judge is unreliable and ranks by deterministic metrics only where available.
- **US-08 Fine-tune.** As P2, I fine-tune a small model on permitted rows. *AC:* only `train_allowed` rows used; if too few, teacher regeneration offered; result evaluated on the same test split; compared with the base model zero-shot, the base with k-shot, and larger open models; training cost and time reported.
- **US-09 Demo data.** As the author, I have reproducible demo tasks. *AC:* Task A (human-gold public classification subset) and Task B (synthetic support-ticket → strict JSON, references from an incumbent closed model used for **evaluation only**) with scripts, seeds and license notes in `data/README.md`.
- **US-10 Local mode.** As P3, I run everything locally. *AC:* `OPENSWITCH_MODE=local` restricts providers to localhost; a clear warning appears if a hosted provider is configured; README shows the one-command path.

## 8. Functional requirements
- FR-01 Provider abstraction: any OpenAI-compatible chat endpoint (Ollama, DigitalOcean serverless inference, Backboard if compatible) plus a Tinker adapter for the fine-tuned model. Streaming to measure time-to-first-token; capture API-reported token usage.
- FR-02 Runner: async, per-provider concurrency limits, retry with backoff and jitter on 429/5xx, timeouts, idempotent per (experiment, model, example), resumable, per-experiment and global budget caps.
- FR-03 Deterministic metrics for structured tasks: JSON validity, schema conformance, per-field accuracy, label accuracy and macro-F1.
- FR-04 Judge: pairwise candidate vs reference, run twice with swapped order, strict JSON verdict, inconsistent → tie, rubric from the task file, judge model recorded and kept out of the candidate list when possible.
- FR-05 Statistics: bootstrap 95% CIs (10,000 resamples, seed stored), parity rate and win rate, latency p50/p95, cost per 1k requests.
- FR-06 Cost model and projection per doc 05 §6, with assumptions echoed.
- FR-07 Recommendation engine: cheapest candidate whose parity **lower CI bound** ≥ threshold (default 0.85, configurable); otherwise "no safe switch found".
- FR-08 Report generator: standalone HTML (no external requests, charts vendored) + JSON.
- FR-09 Provenance guard in the fine-tune pipeline (hard block, not a warning).
- FR-10 Teacher regeneration: regenerate outputs for training prompts with a chosen open model and flag `reference_source=open_model`.
- FR-11 PII scan on import (emails, phone numbers, card-like numbers) with a warning and an option to mask before sending to hosted providers.
- FR-12 Observability: Sentry gen_ai spans per generation and judge call (model, tokens, latency, cost, prompt version) without prompt/response text.
- FR-13 CLI mirrors the web flow: `init, import, models probe, run, judge, calibrate, regen, finetune, report, serve`.
- FR-14 Demo mode: bundled sample datasets, upload caps, per-visitor and global rate limits, 24h auto-delete, kill switch.

## 9. Non-functional requirements
- Performance: 100 rows × 6 models complete in ≤ 10 min on hosted providers at default concurrency.
- Reliability: a provider outage fails that model's run cleanly without failing the experiment.
- Security: see doc 03 §10. Privacy: no prompt text in logs or Sentry; auto-delete in demo mode.
- Reproducibility: every report embeds config hash, seeds, model IDs, provider, date, price table version, git commit.
- Accessibility: report and UI use semantic HTML, sufficient contrast, keyboard operable (also a good detail for the post).
- License: MIT; dependencies must be permissive; datasets' licenses recorded.

## 10. Business model hypotheses (unvalidated; test, do not assert)
- **Free open-source tool + paid migration audit** sold by the author to agencies and startups (flat fee per audit).
- Price hypothesis to test with the first user: a flat audit fee that is a small fraction of the first-year projected savings. The post must label any price as a hypothesis and report the first user's actual reaction.
- Unit economics to report from real data: eval cost per audit (API spend for ~6 models × 150 rows + judge) versus fee.

## 11. Privacy, security and legal
- Hosted demo: warn users not to upload sensitive data; default to bundled samples; uploads capped; auto-delete after 24h; no content in logs.
- **Training-on-outputs risk:** many closed providers restrict using their outputs to train competing models. The tool does not give legal advice. It defaults to not training on closed-API-sourced rows, requires explicit attestation to override, and recommends teacher regeneration with an open model. The README and post must say "check your provider's terms".
- Model and dataset licenses are shown in the report (`license` field, `UNVERIFIED` if unknown).

## 12. Open questions (owner, due)
- Q1 Which closed model produces the incumbent baseline for Task B, and does the author have a key? (human, Wed)
- Q2 Which open base models does Tinker support, are weights exportable, and what is the serving/sampling path and price? (agent, Thu via T-019)
- Q3 Is Backboard OpenAI-compatible, and which open models does it expose? (agent, Wed via T-007)
- Q4 Which open model is the judge (largest available, different family from most candidates)? (agent, Thu)
- Q5 Who is the first user? (human, by Thu; pilot Sat)
