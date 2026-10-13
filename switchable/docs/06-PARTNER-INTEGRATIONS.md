# 06 — Partner Integrations (genuine use only)

Rule: claim a category only if the technology does real work in the project. Each category needs a specific paragraph in the post. Depth beats breadth: **target 7 categories**, listed in priority order. Verify every API detail in the partner's docs; do not rely on this file for shapes.

| Priority | Category | Prize | Effort | Genuine role in Open-Switch |
|---|---|---|---|---|
| 1 | Tinker | $200 | High | Fine-tune a small open model on permitted rows; compare against baseline, k-shot and larger models |
| 2 | Gemma | $200 | Low | Gemma-family models as candidates, as the local-mode default, and as the fine-tune base if Tinker supports it |
| 3 | Render | $200 | Med | Hosts the app and API from a Blueprint, persistent disk, caps as env vars, health check, auto-delete job |
| 4 | DigitalOcean | $200 | Low–Med | Serverless inference serves hosted candidates; optional GPU Droplet serving the fine-tuned model (S-01) |
| 5 | Backboard | $100 | Low | One key to compare multiple open-weight models (verify compatibility in T-007) |
| 6 | Sentry Agent Tracing | $100 | Low–Med | gen_ai traces per generation/judge call with latency, tokens, cost; real issues caught |
| 7 | .tech Domain | $100 | Low | Hosted demo on a claimed .tech domain |
| Optional | GitHub Copilot | $100 | Low | Only if Copilot coding agent/CLI/PR review is actually used and CI via GitHub Actions |
| Optional | Entire | $100 | Low | Share agent sessions in the post (also DevRelay for the optional session embed) |
| Optional | ElevenLabs | $100 | Low | Narration for the demo video |
| Skip | TabPFN, Arduino, Mastra, MongoDB, SerpApi, Temporal, Tiger Data | — | — | No natural fit. Do not force them |

You can only win once per challenge, so extra honest categories raise the odds of being picked in one of them; they do not stack prizes.

## Per-partner plan

### Tinker (https://tinker-docs.thinkingmachines.ai/)
- T-019 smoke test: list supported base models, methods, whether weights can be downloaded, how the tuned model is sampled/served, and prices. Record in `docs/evidence/` and the devlog.
- Evidence for the post: training config, run time, cost, before/after table with CIs on the same test split, the comparison with k-shot and larger open models, and the honest serving-cost assumption.
- Risk: API changes, slow queues, tiny data. Fallback F-1 in doc 08.

### Gemma (https://ai.google.dev/gemma)
- Include at least one Gemma model among candidates and one in the Ollama local default. Say that Gemma is open-weight under Google's own terms (not an OSI license) in the post.
- Evidence: per-task scores and latency; local-mode run on a laptop (hardware, tokens/s).

### Render (https://render.com/docs)
- `render.yaml` Blueprint, Docker service, health check, persistent disk, env-var caps, deploy-on-push, custom domain.
- Evidence: Blueprint screenshot, logs showing runs, a screenshot of the disk, the cap-hit behaviour.

### DigitalOcean (https://docs.digitalocean.com/products/gradient-ai-platform/)
- Use serverless inference for hosted open models. Verify the base URL and model IDs in the docs.
- Evidence: usage/analyze tab screenshot with token counts; cost table.
- Stretch S-01: vLLM on a GPU Droplet serving the fine-tuned model if weights are exportable.

### Backboard (https://backboard.io/hackathons)
- Read the hackathon page for credits and how to access multiple open models with one key. If OpenAI-compatible, register as a provider; otherwise write a small adapter.
- Evidence: models compared through Backboard, request counts, any difference in latency or cost versus calling providers directly.
- Optional: R-CLI (their open-source terminal coding agent) for part of the build only if genuinely used.

### Sentry (https://docs.sentry.io/product/agents/getting-started/)
- gen_ai spans for every generation and judge call. Scrub content. Keep the dashboard of latency/tokens/cost.
- Evidence: a trace screenshot, an issue the tool actually caught (e.g. empty outputs from a reasoning model, judge inconsistency spike), and what you changed because of it.

### .tech (https://get.tech)
- Claim via https://hacktoberfest.com/my/promos; point DNS at Render; link in the post. It renews at $29.99/yr after year one (per the challenge page).

### Optional trio
- **GitHub Copilot:** if used, show Copilot-reviewed PRs or agent sessions and the Actions workflow. If not used, do not claim.
- **Entire / DevRelay:** export the real agent sessions that built the project and embed/link them. Cheap and aligned with the judges' wish to see process.
- **ElevenLabs:** narrate the demo video with it (the category explicitly allows this). Disclose that narration is generated.

## Claim text template for the post (fill with facts)
> **Best Use of <Partner>:** <what it does in the product, in one sentence>. <one number or screenshot reference>. <one thing that went wrong or surprised me and what I did>.
