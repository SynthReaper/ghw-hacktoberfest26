# 05 — Evaluation Methodology

The credibility of the post depends on this document. Implement it exactly. If something cannot be done, say so in the report rather than quietly weakening it.

## 1. Definitions
- **Incumbent / baseline:** the user's current expensive model. Its stored outputs are the **reference** (or human gold labels where available).
- **Candidate:** an open-weight model under test. A **fine-tuned candidate** is a candidate produced by this tool.
- **Test split:** held-out rows never used for training, few-shot selection, prompt tuning or threshold choice. Headline numbers use only this split so all models are compared on identical rows.

## 2. Splits and leakage control
- Deterministic split by `sha256(seed || example_id)`: default 60% train, 10% dev, 30% test. Minimum test size 30 (warn below; refuse headline claims below 20).
- Train and dev are used only for fine-tuning, k-shot example selection, and judge/rubric debugging. **The test split is never inspected during development.** Log any exception in the devlog.
- Zero-shot candidate evaluation is also reported on all rows as a secondary table, clearly labelled.
- Check for duplicate or near-duplicate inputs across splits (exact normalised match at minimum) and report the count.

## 3. Metrics
**Deterministic (preferred where the task allows)**
- `json_valid_rate`: output parses as JSON (after stripping code fences only; no repair).
- `schema_valid_rate`: validates against the task's JSON schema.
- `field_accuracy[f]`: exact match per field against the reference/gold (case-insensitive for enums).
- `label_accuracy` and `macro_f1` for classification.
- Optional `rouge_l` for free text, labelled a weak sanity metric.

**Judge-based (for free text or semantic fields)**
- Pairwise candidate vs reference, rubric from `task.yaml` (see `specs/judge_prompt.md`).
- Run each pair **twice with positions swapped**. Final verdict: candidate wins if it wins both or wins one and ties one; loses symmetrically; otherwise tie. Disagreement counts as `inconsistent` and is reported as a rate.
- **Parity rate** = (wins + ties) / valid verdicts. **Win rate** = wins / valid verdicts.
- Judge model: the strongest available open model, preferably a different family from most candidates to limit self-preference bias. Temperature 0. Judge model and prompt version are recorded. The judge is never evaluated as a candidate in the same table (or is marked with a bias warning).
- Length-bias guard: report mean output length per model; flag if parity correlates strongly with length (Spearman > 0.5).

**Primary metric per task (declared in `task.yaml` before running):** structured tasks use a deterministic composite (e.g. schema validity AND all critical fields correct); free-text tasks use judge parity. Declaring the primary metric up front prevents metric shopping.

## 4. Statistics
- Bootstrap 95% CI, percentile method, 10,000 resamples, seed stored, resampling over test examples (paired across models by example id when comparing two models).
- Report `n`, point estimate and CI for every quality number. Where CIs of two models overlap heavily, say "not distinguishable at this sample size".
- Latency: p50 and p95 end-to-end, TTFT p50 where streaming is available. Note region and time, run sequence, and concurrency used. Latency on a shared hosted API is noisy; say so.
- Multiple comparisons: do not claim a winner among models whose CIs overlap; the recommendation uses the **lower CI bound** against the threshold.

## 5. Judge calibration
- Sample 20+ test outputs (stratified across models), blind-label them in the UI (A/B hidden, order randomised): better / worse / tie versus the reference.
- Report percent agreement and **Cohen's kappa** between human and judge, plus a confusion table.
- Gating: kappa ≥ 0.6 → judge "reliable"; 0.4–0.6 → "moderate, interpret with caution" banner; < 0.4 → "unreliable": the report ranks by deterministic metrics only and shows judge results as informational.
- One human labelling 20 items is a small, single-rater calibration. State that limitation.

## 6. Cost, latency and savings model
- Per-request cost = `tokens_in * price_in/1e6 + tokens_out * price_out/1e6` using API-reported usage; if estimated, flag.
- Prices come from `pricing.yaml` with `source_url` and `verified_on`. **The agent must read the provider pricing pages and record them; never assume.** Any price older than 30 days or missing is flagged in the UI and report.
- Baseline cost per request: user-supplied baseline prices and tokens measured/estimated from the stored baseline outputs and inputs, or a user-supplied flat `baseline_cost_per_request`. Show which was used.
- `cost_per_1k = 1000 * mean(per-request cost)` over test rows.
- Monthly projection: `monthly_cost = volume * mean_cost`; `savings = (baseline_mean_cost - candidate_mean_cost) * volume`.
- Local models: report API cost as $0 and add an optional user-entered hardware/electricity amortisation line; do not claim "free" without that caveat.
- **Fine-tune break-even:** `one_time_cost / per_request_savings` requests, including training cost and any serving cost difference. If serving cost is unknown, state it as an assumption.

## 7. Recommendation logic
1. Eligible = candidates with primary-metric **lower CI bound ≥ threshold** (default 0.85 parity, configurable) and error rate ≤ 5%.
2. If any eligible: recommend the one with the lowest cost per 1k; show runner-ups and the savings range from the CI.
3. If none eligible but a fine-tune is feasible (enough trainable rows): recommend "switch after fine-tune" and show the best base candidate.
4. Otherwise: "No safe switch found at this threshold", with the closest candidate and the gap. This outcome is valid and must be displayed with the same prominence.

## 8. Fine-tune protocol (Tinker or fallback)
1. Provenance guard: select rows with `train_allowed=true` from the **train** split only.
2. If fewer than 50 trainable rows remain, run **teacher regeneration**: generate outputs for train prompts with an open teacher model (largest available), mark `reference_source=open_model`. Teacher choice and its license are recorded.
3. Base model: a small open model supported by Tinker (list supported models first; choose one that is also available as a zero-shot candidate so the comparison is clean).
4. Hyperparameters: choose conservative defaults from the Tinker docs; one or two settings at most, selected using the **dev** split, never the test split. Record all hyperparameters, steps, wall time and cost.
5. Evaluate on the test split with the same prompts, metrics and judge as every other candidate.
6. Compare against: (a) base zero-shot, (b) base with k-shot (k=3..8 nearest train examples by TF-IDF cosine), (c) larger open models zero-shot, (d) the incumbent.
7. Report training cost, training time, quality delta with CI, latency/cost per 1k, and the serving path assumption. **A negative or null result is a valid outcome and must be reported.**
8. Prompt-vs-finetune honesty: if k-shot achieves similar quality, say so. That is useful information for the buyer and for the post.

## 9. Reproducibility block (in every report)
Git commit, config hash, dataset sha256, seeds, split sizes, model IDs and providers, price table version and verified dates, judge model and prompt version, run dates and times (UTC), library versions.

## 10. Planned experiments (for the post)
- **E1** Task A (human-gold classification subset): 6+ open models zero-shot, test split. Deterministic metrics.
- **E2** Task B (synthetic ticket → strict JSON, incumbent references): 6+ open models zero-shot; deterministic field accuracy plus judge for the summary field.
- **E3** Task B fine-tune of a small open model vs base, k-shot, larger models.
- **E4** Judge calibration (20 labels).
- **E5** First-user dataset (if obtained and permitted): same pipeline; report anonymised outcome with the user's consent.
- **E6 (optional)** Sensitivity: change the parity threshold and show how the recommendation changes.
