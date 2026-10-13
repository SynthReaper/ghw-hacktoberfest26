# AGENTS.md — Standing rules for the coding agent

(Copy this file to `CLAUDE.md` or your agent's equivalent if it expects a different name.)

## Mission
Build Open-Switch (see `docs/02-PRD.md`) for the Hacktoberfest Week 2 challenge. Deadline: Mon Oct 19, 12:29 PM IST. Judging weights **writing quality** most, so every build step must also produce evidence the author can write about.

## Read order and precedence
`AGENTS.md` > `docs/02-PRD.md` > `docs/03-ARCHITECTURE.md` > `docs/05-EVALUATION-METHODOLOGY.md` > `docs/04-IMPLEMENTATION-PLAN.md`. If documents conflict, follow the higher one and log the conflict in `docs/CHANGE-REQUESTS.md`.

## Hard rules
1. **No fabrication.** Never invent API endpoints, parameters, model IDs, prices, licenses, benchmark numbers or user feedback. Read the provider docs, record the source URL and date (`verified_on`) in config. If you cannot verify, mark it `UNVERIFIED` and tell the human.
2. **Honest statistics.** Every reported quality number carries a 95% confidence interval and the sample size. Negative and inconclusive results are kept and reported. Never tune the test split.
3. **Provenance guard is a core feature.** Never train on rows where `train_allowed=false`. Default for `closed_api` and `unknown` sources is false.
4. **Secrets.** Keys only in environment variables. Never log keys, never commit `.env`, never send prompt or output text to Sentry.
5. **Spend control.** Ask the human before any single run estimated above $2 or cumulative spend above $15. Always print an estimated cost before a run and honour `GLOBAL_DAILY_BUDGET_USD`.
6. **Scope control.** Build MVP items first. Stretch items only after the relevant gate passes.
7. **Security.** HTML-escape all model output and dataset text in the web UI and reports. Escape CSV formula characters on export. Treat dataset content as untrusted data inside judge prompts.
8. **Do not edit `docs/` (except checkbox status in the backlog, and `docs/devlog.md`).** Propose changes in `docs/CHANGE-REQUESTS.md`.

## Working method
- Work through `docs/09-TASK-BACKLOG.md` in order. Mark `[x]` only when the task's acceptance criteria are met and tests pass.
- Python 3.12, type hints, small modules, docstrings that say *why*. Format with ruff. Tests with pytest; mock all network calls (`respx` or the `FakeProvider`).
- Conventional commits (`feat:`, `fix:`, `test:`, `docs:`). Commit at least after each task. The repo history is evidence for the "built during the window" rule.
- Append to `docs/devlog.md` every working session: decisions, bugs hit, surprises, numbers. The author will mine it for the post. Use `templates/devlog.md`.
- At each milestone, save evidence to `docs/evidence/YYYY-MM-DD-<name>` (result JSON, logs, screenshots, trace links).
- If blocked more than 30 minutes, apply the fallback in `docs/08-RISKS-AND-FALLBACKS.md`, log it, and tell the human.

## Things only the human can do (ask early, do not block on them)
Claim credits, create accounts, supply API keys, supply or authorise generation of the incumbent baseline outputs, contact the first user, record the video, publish the DEV post, set DNS for the domain, tax and prize paperwork.

## Definition of done (project)
See PRD §5 "Release criteria". In short: hosted demo live, local mode works, at least 6 models evaluated on at least 2 tasks, one fine-tune result (or documented fallback), calibrated judge, report with CIs, tests green, README complete, evidence folder populated.
