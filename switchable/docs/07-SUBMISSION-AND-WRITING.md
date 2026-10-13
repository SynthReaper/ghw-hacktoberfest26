# 07 — Submission and Writing Plan

Writing quality is the heaviest criterion. The post is a deliverable, not an afterthought. **Reserve Sunday morning and midday for it.** Facts come from `docs/devlog.md` and `docs/evidence/`.

## 1. Thesis
"I tried to replace a closed model with open ones on real tasks. Here is the invoice: what held up, what didn't, what it would cost, and whether anyone would pay for the answer."
The post wins by being **specific, numerate, and honest about where open lost**, which is exactly the question the prompt asks.

## 2. Title options (use real numbers only after they exist)
- "I audited an LLM bill: open models kept X% of quality at Y% of the cost (and where they didn't)"
- "Can you fire your closed LLM? I built the tool that tells you, with confidence intervals"
- Avoid hype claims you cannot back with a table.

## 3. Structure (matches the DEV template headings)
1. **Hook (3–5 sentences):** a concrete scene. A team staring at an API bill; the fear of switching; the question nobody can answer with a leaderboard.
2. **What I Built:** one paragraph, one screenshot of the report's executive summary, who pays and why (agencies selling migration audits; startups with a bill). State the price hypothesis as a hypothesis.
3. **Demo:** live link on the .tech domain, a 60–90 s video, a "no signup, try the sample dataset" instruction, and the local-mode command.
4. **Code:** embed the GitHub repo; MIT; one line on how to run locally.
5. **The result (put it early, before architecture):** the headline table (model, license, parity or primary metric with CI, p50 latency, $/1k requests, vs baseline). One chart (Pareto). One sentence on what is and is not claimed.
6. **How I Built It:** short architecture diagram; provider layer; swapped-order judge; bootstrap CIs; provenance guard; fine-tune loop. Keep code snippets small and purposeful.
7. **What broke (bugs section):** real items from the devlog (e.g. empty outputs from reasoning models, judge position bias numbers, a price that had changed, rate limits). This section is where credibility comes from.
8. **Where open lost:** state plainly which tasks or models fell short and by how much.
9. **Why Does Open Innovation Matter?** Tie to evidence: a fine-tune that a closed API would not allow for this task; data that never left the laptop in local mode (with the measured latency and quality gap); cost per 1k; switching models with a config line; no lock-in to pricing.
10. **My Agent Session:** embed/link DevRelay/Entire sessions; one paragraph on how the agent was directed (this pack).
11. **My First User:** who, what dataset, what the report said, their reaction, whether they would pay and how much, what they asked for next. If no user was obtained, delete this section rather than inventing one.
12. **Prize Categories:** one specific paragraph per category actually used (template in doc 06).
13. **Limitations and what's next (5 lines):** small samples, single-rater calibration, tasks tested, serving-cost assumptions, ToS caution (check your provider's terms).

Length: ~2,000–2,800 words plus images. Short paragraphs. No filler. Every claim either has a number, a screenshot, or is labelled opinion/hypothesis.

## 4. Style rules
- Lead sections with the finding, then the evidence.
- Numbers always with CI and n. Say "not distinguishable" when CIs overlap.
- No unverifiable superlatives. No "revolutionary", "game-changing".
- Name trade-offs (hosted demo uses paid APIs; local is slower and weaker).
- Disclose AI assistance in building and any generated narration.
- Read the draft aloud once; cut anything you would skip as a reader.

## 5. Evidence checklist (capture as you build; save to `docs/evidence/`)
- [ ] `models probe` output across providers (G1)
- [ ] First end-to-end JSON result (G2)
- [ ] Pareto chart and results table, final frozen run
- [ ] Judge calibration table (agreement, kappa) and the position-bias rate
- [ ] Tinker run: config, time, cost, before/after table; the k-shot comparison
- [ ] Sentry: trace screenshot, one real issue, dashboard of latency/tokens/cost
- [ ] Render: Blueprint, logs, disk, cap-hit screenshot
- [ ] DigitalOcean: usage/token analytics screenshot
- [ ] Backboard: usage showing multi-model comparison
- [ ] Local-mode run: hardware, tokens/s, quality gap
- [ ] Provenance guard blocking a closed-API row (screenshot)
- [ ] The "no safe switch found" example (screenshot) to show honesty
- [ ] First-user message thread (with permission, anonymised) and their dataset result
- [ ] Spend log: total API/training cost of the whole project
- [ ] Domain screenshot (.tech) and a clean-browser load test

## 6. Demo video (60–90 s) script
1. (0–10s) Problem: "This team pays for a closed model. Can they switch?"
2. (10–25s) Upload sample dataset, see provenance flags and the PII warning.
3. (25–40s) Pick models, set baseline price and volume, estimated cost shown.
4. (40–60s) Live progress, then the report: recommendation, Pareto chart, CIs.
5. (60–75s) Fine-tune result vs base and k-shot; the honest "no safe switch" case.
6. (75–90s) Local mode one-liner. End on the link.
Optional narration with ElevenLabs (disclose). Subtitles on. Host on YouTube and embed.

## 7. First-user protocol (bonus points)
- Pick 3–5 candidates (agencies, startups, a friend who owns an LLM bill). Send `templates/outreach-message.md` Wed/Thu; aim for one live session on Sat.
- Use their data only with explicit permission; prefer local mode; anonymise anything shown in the post.
- Ask exactly: Did the result surprise you? Would you act on it? Would you pay, and roughly how much for an audit like this? What would you need next?
- Record answers verbatim in `docs/evidence/first-user.md`. Report what happened even if the answer is "no".

## 8. README requirements
Quickstart (hosted, local, CLI), architecture diagram, results table, methodology link, limitations, licenses and credits (libraries, datasets, models), the "built during Oct 12–18, 2026" statement, a section "Commits after the deadline" if any are made, security notes, and the ToS caution.

## 9. Pre-submission checklist (Sunday)
- [ ] Repo public, MIT license, no secrets (run a secret scan), `.env.example` present
- [ ] First commit dated within Oct 12–18; no pre-existing project code reused without credit
- [ ] README complete, including post-deadline commit note if applicable
- [ ] Demo link loads from a clean browser/incognito and from mobile; sample dataset runs
- [ ] Caps and kill switch tested; GLOBAL_DAILY_BUDGET_USD set
- [ ] All numbers in the post match the final frozen report JSON
- [ ] Post uses the official template headings; tags `devchallenge` and `hf26challenge` present
- [ ] Each claimed partner category has a specific paragraph and evidence
- [ ] Agent session(s) embedded or linked; AI-assistance disclosed
- [ ] English language; 18+ eligibility confirmed; official rules re-read for country/prize/tax terms
- [ ] First-user section is real or removed
- [ ] Published before 8 PM IST Sun; screenshot of the live post; check it appears at https://dev.to/t/hf26challenge
