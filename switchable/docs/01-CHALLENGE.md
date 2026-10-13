# 01 — Challenge Brief: Hacktoberfest Open-Source AI Challenge, Week 2 ("Side Hustle")

Sources: challenge page https://dev.to/challenges/hacktoberfest-week2-2026-10-12 · launch post https://dev.to/devteam/join-the-hacktoberfest-open-source-ai-challenge-side-hustle-2550-in-prizes-across-18-winners-55ba · hub https://dev.to/challenges/hf26 · rules https://dev.to/page/hacktoberfest-week2-2026-10-12-contest-rules and https://dev.to/page/official-hackathon-rules. Re-read the rules pages before submitting; they override this summary.

## Dates
- Start: Oct 12, 2026. **Deadline: Oct 18, 2026, 11:59 PM PDT** (= Mon Oct 19, 12:29 PM IST). Winners announced the week of Oct 19.
- Today when this pack was written: Wed Oct 14.

## Prompt
Build something with open-source AI at its core: an open-weight model, an open-source agent harness/framework, local inference, or a mix. The open pieces must be what makes the project work. The post must explain **why open innovation matters** for what was built and **where the open approach worked better than a closed one**.

## Theme: Side Hustle
Build something with open-weight models or open-source AI **that someone would actually pay for**. Think small, specific, useful; solve a real problem for a real person. Questions the post should answer: does running your own model keep costs low enough that the business works, keep customers' data private, allow fine-tuning for a niche a general API handles poorly, avoid lock-in to someone else's pricing? **Bonus points for landing a first user** (did they pay, would they, what did they ask for next).

## Judging criteria
1. **Writing quality (weighted most heavily).** The organizers state a great project with a thin write-up will not win.
2. Relevance to the prompt and theme
3. Creativity
4. Technical execution
5. Use of partner technology (optional, only for partner categories)

Ties go to the entry with the most positive reactions on its DEV post. Reactions are not otherwise a scoring input; several Weekend winners had 1–6 reactions.

## Prizes ($2,550 across 18 winners)
- Overall: $250 + DEV++ membership + winner badge
- Featured categories, $200 each: **Render, TabPFN, Tinker, Arduino, DigitalOcean, Gemma**
- Partner categories, $100 each: **Backboard, ElevenLabs, Entire, GitHub Copilot, Mastra, MongoDB Atlas, Sentry Agent Tracing, SerpApi, .tech Domain, Temporal, Tiger Data**
- Everyone with a valid submission gets a completion badge. A submission can win **once** per challenge.

Category definitions (verbatim intent):
- Render: use Render as the AI runtime, host an agent front end, or run Hermes/OpenClaw.
- Tinker: fine-tune a model for a specific task and show a clear improvement in performance, latency or cost over a baseline.
- DigitalOcean: build or deploy on DigitalOcean: host the app, run an open-weight model on a GPU Droplet (1-Click Models), or build on the Gradient AI Platform (serverless inference).
- Gemma: use Gemma locally, fine-tuned, or served via a provider.
- Backboard: R-CLI (their open-source terminal coding agent), compare open-weight models through one Backboard API key, or give an open-source assistant memory/RAG.
- Sentry Agent Tracing: show how the agent is set up, how it performs (latency, tokens, cost), what you found, how you debugged it, with traces or screenshots in the post.
- .tech: put the project live on a .tech domain claimed via Hacktoberfest and link it in the post.
- Entire: share the agent sessions behind the project in the write-up.
- GitHub Copilot: build with the coding agent/CLI/app, automate with GitHub Actions, or review PRs with Copilot.
- ElevenLabs: give an open-source agent a voice, transcribe audio for a local model, or generate narration for the demo.

**How categories work:** you opt in by genuinely using the technology and listing each category in the "Prize Categories" section of the post. Only claim what you actually used.

## Submission mechanics
- Publish one DEV post using the template (tags `devchallenge` and `hf26challenge` are added by the template). Sections: What I Built · Demo · Code · How I Built It · Why Does Open Innovation Matter? · My Agent Session (optional) · My First User (optional, bonus) · Prize Categories.
- One submission per challenge. Teams up to 4: one member publishes and lists teammates' DEV handles; DEV does not split prizes.
- Optional: save the agent session with DevRelay (https://devrelay.com) and embed it with the `agent_session` tag or link it.

## Rules that can disqualify
- **Project must be new, started and completed within the challenge window.** Commits after the deadline must be noted in the README.
- Credit all non-trivial prior work (libraries, datasets, open-source code). Plagiarism = ineligible.
- Participants must be 18+. Non-English posts are not prize-eligible. AI assistance is allowed.
- Cash winners may need to sign an eligibility affidavit and provide tax information within 7 business days of notice. Check the official rules for country eligibility.

## Credits and docs
Credits (Tinker, Render, Backboard, free .tech domain): https://hacktoberfest.com/my/promos
Docs: Render https://render.com/docs · Tinker https://tinker-docs.thinkingmachines.ai/ · DigitalOcean https://docs.digitalocean.com/products/gradient-ai-platform/ · Gemma https://ai.google.dev/gemma · Backboard https://backboard.io/hackathons · ElevenLabs https://elevenlabs.io/docs · Entire https://docs.entire.io · GitHub Copilot https://docs.github.com/copilot · Sentry https://docs.sentry.io/product/agents/getting-started/ · .tech https://get.tech

## What the research says about winning (from the Weekend Challenge winners and early Week 2 posts)
- **The overall winner** ("Phone calls are the boss fight of living in Japan", ~13 min read) had: a sharp personal pain point, a video, a screenshot of a real friend's reaction, hard numbers (113 conversations, 1.28M input tokens, one trace costing about $0.0002), a "bugs I hit" section, honest limits ("the local version isn't as good"), a free local mode next to the hosted one, and **five** partner categories each justified with specifics.
- Category winners were specific and evidence-heavy (e.g. a 39-letter test set, a backtest on 79 race legs, a fine-tuned 4B model, Indian-context problems with real users).
- **Saturated in Week 2 already:** invoice/receipt sorters, listing writers, expense anomaly checkers, one-prompt review-reply tools. These copy the prompt's own examples. Open-Switch is deliberately outside this crowd.
- Many posts say "zero cloud fees" with no business logic. The theme asks whether someone would **pay**, so the post needs a price hypothesis, a buyer, a unit cost, and ideally one real user.
- The research on Week 2 entries was partial (search results only). Do a quick re-check of https://dev.to/t/hf26challenge on Sat Oct 17 for any new entry with the same idea, and adjust the positioning paragraph if so.
