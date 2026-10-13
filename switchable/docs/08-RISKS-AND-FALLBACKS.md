# 08 — Risks and Fallbacks

Format: risk → trigger (when to act) → fallback. Log every activation in `docs/devlog.md`.

| ID | Risk | Likelihood / impact | Trigger | Fallback |
|---|---|---|---|---|
| R1 | **Tinker API, serving path or queue blocks the fine-tune** | Med / High | T-019 can't train or sample by Thu night, or the Fri run hasn't finished by Fri 8 PM | **F-1:** drop to the k-shot (kNN) baseline plus a clearly labelled "fine-tuning attempted, here is what blocked it" section. Keep the Tinker category claim only if a real training run was executed. Else drop the claim |
| R2 | **No closed-API key for incumbent baseline outputs** | Med / High | Not resolved by Wed night | **F-2:** use human-gold public data only (Task A + a second human-gold task). Reposition: "baseline = human labels". The "vs closed" cost comparison uses the user-entered baseline price on a stated token volume |
| R3 | **Judge unreliable (kappa < 0.4)** | Med / Med | Calibration result | Switch the primary metric to deterministic composites; show judge as informational; say so in the post |
| R4 | **Backboard not OpenAI-compatible or lacks open models** | Low–Med / Low | T-007 | Write a thin adapter (≤ 2 h) or drop the Backboard claim |
| R5 | **Provider rate limits or outages during final runs** | Med / Med | 429 rates > 10% | Lower concurrency; spread runs across providers; run final frozen experiment Sat morning, not Sat night |
| R6 | **Credits/spend overrun** | Med / Med | Spend > $15 or > 70% of any credit | Reduce rows or models; use cached generations; keep the kill switch on; ask the human before more spend |
| R7 | **Render disk/instance limits or cold starts** | Low / Med | Deploy issues Sat | Fall back to SQLite in the container filesystem with demo auto-reset; document; keep local mode as the guaranteed path |
| R8 | **Hosted demo abused or drained** | Med / High | Spend near cap | Kill switch, per-visitor/IP limits, bundled-samples-only mode via env var |
| R9 | **Duplicate idea appears in Week 2 entries** | Low–Med / Med | Sat re-check of `hf26challenge` | Sharpen the differentiators (provenance guard, fine-tune loop, CIs, local mode) in the positioning paragraph. Do not change the project |
| R10 | **No first user** | Med / Med | None by Sat noon | Run the pilot on a friend's or a public-real dataset and label it honestly; or remove the section. Never invent |
| R11 | **Results are unimpressive (open models fail)** | Med / Low | E1/E2 | This is publishable: "No safe switch found" plus the fine-tune delta is an honest, useful finding. Lead with it |
| R12 | **ToS/legal ambiguity about training on outputs** | Med / Med | Any doubt | Keep the guard default-deny, regenerate with an open teacher, add the "check your provider's terms" caution. Not legal advice |
| R13 | **Scope creep** | High / High | Any new feature after G2 | Only if it is on the MVP list. Everything else goes to "what's next" |
| R14 | **Late writing** | High / High | Post not drafted by Sun noon | Cut features, not writing time. Freeze at Sat night (G5) |
| R15 | **Prompt injection or XSS via dataset or model output** | Low / High | Security tests | Escaping, delimiters in judge prompts, strict JSON, tests in CI |
| R16 | **Small-n results over-interpreted** | Med / High | Test n < 30 | Refuse headline claims below n=20; widen CIs visibly; recommend more data |
| R17 | **Eligibility/prize paperwork** | Unknown | Before submitting | Re-read the official rules for country eligibility and cash-prize tax steps. Enter anyway for the badge and exposure if prize eligibility is unclear |
| R18 | **Model/pricing facts go stale or are wrong** | Med / Med | Any price older than 30 days or unverified | Show `UNVERIFIED`/stale warnings; verify on provider pages on Sat; record `verified_on` |

## Kill criteria
- If by **G2 (Thu night)** there is no end-to-end result on ≥ 3 models, cut to: CLI + report only, skip the web UI beyond a minimal upload page, and put the hours into evidence and writing.
- If by **G4 (Sat noon)** the hosted demo is not up, ship the local mode + recorded demo video + a static sample report page hosted on Render as a static site, and say so.
