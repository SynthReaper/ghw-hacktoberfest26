# Open-Switch — Build Pack

> **Project Timeline**: Started on October 14, 2026 for the Hacktoberfest Open-Source AI Challenge: Week 2 ("Side Hustle").
> All original code in this repository was created within the challenge window (October 12–18, 2026).

Hand this whole folder to a coding agent. It contains the product spec, architecture, evaluation method, day-by-day plan, task backlog, partner integrations, and the writing plan for the DEV post.

**Project:** Open-Switch tells a team whether it can safely replace an expensive closed LLM with an open-weight model on *its own* task. It reports quality, cost and latency with honest statistics, then optionally fine-tunes a small open model to close the gap.

**Target:** Hacktoberfest Open-Source AI Challenge: Week 2 — "Side Hustle" (DEV). Submissions close **Oct 18, 2026, 11:59 PM PDT = Mon Oct 19, 12:29 PM IST**. Plan to publish by the evening of Sun Oct 18 IST.

## Folder map

| Path | Purpose |
|---|---|
| `AGENTS.md` | Standing rules for the coding agent. Read first. |
| `docs/01-CHALLENGE.md` | Everything about the challenge: dates, rules, judging, categories, what past winners did |
| `docs/02-PRD.md` | Product requirements, scope, user stories, acceptance criteria |
| `docs/03-ARCHITECTURE.md` | System design, data model, APIs, repo layout, deployment, security |
| `docs/04-IMPLEMENTATION-PLAN.md` | Day-by-day plan with decision gates |
| `docs/05-EVALUATION-METHODOLOGY.md` | Metrics, judge protocol, statistics, fine-tune protocol, cost model |
| `docs/06-PARTNER-INTEGRATIONS.md` | How to genuinely use each partner and what evidence to capture |
| `docs/07-SUBMISSION-AND-WRITING.md` | Post structure, evidence checklist, demo video, first-user protocol |
| `docs/08-RISKS-AND-FALLBACKS.md` | Risk register with triggers and fallbacks |
| `docs/09-TASK-BACKLOG.md` | Numbered tasks with acceptance criteria. The agent works from this |
| `docs/evidence/` | Screenshots, logs, result files collected during the build |
| `specs/` | Config and schema starting points (dataset, task, models, pricing, judge prompt, `.env`) |
| `templates/` | DEV post skeleton, outreach message, devlog |

## Master prompt (paste into the agent)

```
You are the lead engineer for "Open-Switch", a hackathon project with a hard deadline.
Everything you need is in this folder.
1. Read AGENTS.md fully and follow it as standing rules.
2. Read docs/01 through docs/08 in order, then docs/09-TASK-BACKLOG.md.
3. Reply in at most 15 lines: the MVP scope, the top 3 risks, and exactly what you need from me (keys, credits, data).
4. Then execute the backlog in order. Stop at each gate (G1-G6 in docs/04) and show evidence before continuing.
Never invent API shapes, model names, prices or results. Verify against the docs and record the date.
```

## First three human actions (do today, Wed Oct 14)

1. Claim partner credits at https://hacktoberfest.com/my/promos (Tinker, Render, Backboard, free .tech domain). Create accounts for DigitalOcean, Sentry, and optionally ElevenLabs.
2. Put keys in `.env` (see `specs/.env.example`). Never commit it.
3. Decide how the "incumbent" baseline outputs will be produced for the demo task (see PRD §7, US-09). You need either a closed-API key to generate about 150 baseline answers, or a human-labelled public dataset only.

## Timeline snapshot (IST)

| Day | Focus |
|---|---|
| Wed Oct 14 | Setup, scaffold, provider layer, data import |
| Thu Oct 15 | Runner, metrics, judge, stats, first end-to-end run. Tinker smoke test tonight |
| Fri Oct 16 | Fine-tune, calibration, web UI, report |
| Sat Oct 17 | Deploy, harden, first-user pilot, final runs. **Feature freeze tonight** |
| Sun Oct 18 | Video, README, post, submit by evening |
| Mon Oct 19 | Buffer only. Deadline 12:29 PM IST |
