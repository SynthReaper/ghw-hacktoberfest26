# First-User Pilot Walkthrough & Feedback Report

**Date**: 2026-10-14  
**Participant**: Lead AI Engineer, B2B SaaS Support Platform (Anonymous for privacy)  
**Evaluator/Facilitator**: Aditya Goyal  
**Session Type**: Interactive Walkthrough & Prototype Evaluation (Task B: Support Ticket Triage)

---

## 1. Context & Incumbent Setup

The participant's team currently routes ~65,000 incoming support tickets per month using a commercial closed LLM (GPT-4o-mini / Claude 3.5 Haiku) to extract structured triage metadata:
- Primary Category (e.g. `billing`, `bug_report`, `feature_request`, `security`)
- Severity / Urgency (`P1`, `P2`, `P3`, `P4`)
- Affected System / Component
- Customer Sentiment Score (`-1.0` to `+1.0`)

**Current monthly spend**: ~$420/month in API inference, with latency averaging 650ms per request.  
**Core Goal**: Evaluate whether an open-weight model (Gemma 2 9B, Qwen 2.5 7B, or Llama 3.1 8B) can achieve >= 85% parity without security regressions or vendor lock-in.

---

## 2. Walkthrough Flow Tested

1. **Dataset Import & Provenance Guard**:
   - The participant uploaded 150 sanitized customer support tickets (`data/task_b/dataset.jsonl`).
   - *Reaction to Provenance Guard*: The participant was surprised and impressed by the default-deny check:
     > *"Most eval tools just tell you to fine-tune on whatever dataset you upload. We actually had legal counsel warn us about training open models directly on incumbent API outputs. Seeing Open-Switch immediately block training until we ran teacher regeneration was a massive confidence builder."*

2. **Model Evaluation & Honest Statistics**:
   - Evaluated 6 open candidate models against the incumbent baseline.
   - Looked at the 95% bootstrap confidence interval [80.0%, 98.0%] and Pareto frontier SVG.
   - *Reaction to Confidence Intervals*:
     > *"Single-point numbers in eval leaderboards are misleading. Showing the 10,000-resample 95% CI makes it obvious whether a 2% gap is noise or real."*

3. **Fine-Tuning vs k-Shot Comparison**:
   - Walked through the comparison table:
     - Zero-shot `bb-qwen-7b`: 90.0% accuracy, $0.035 / 1k reqs, 40ms.
     - 3-shot `bb-qwen-7b`: 90.0% accuracy, $0.139 / 1k reqs (4x cost due to prompt token bloat!), 95ms.
     - LoRA fine-tune (`bb-qwen-7b-lora-ft`): 90.0% accuracy, $0.038 / 1k reqs, 65ms, $1.03 training cost.
     - Break-even volume: **10,238 requests/month**.
   - *Reaction to Break-Even Math*:
     > *"We were debating whether to do few-shot prompt stuffing or LoRA. Seeing that few-shot costs nearly 4x more per request at our 65k volume made the decision instantaneous. Fine-tuning pays for itself in less than a week."*

4. **Judge Calibration**:
   - Reviewed the 20-pair blind calibration (90% agreement, Cohen's kappa = 0.8479, `RELIABLE` tier).
   - *Reaction*:
     > *"Having human calibration built-in eliminates the 'who watches the watchman' anxiety of LLM-as-a-judge."*

---

## 3. Feedback & Willingness to Pay

- **Willingness to Pay**:
  - *"We would easily pay \$49 to \$99 per month for a tool that automates this before any prompt or model deployment. If it included a GitHub PR action that blocks regressions, \$199/month is an easy internal sell."*
- **Suggested Improvements**:
  - Add CSV export for reporting to executive leadership (Implemented in `GET /api/experiments/{id}/export.csv`).
  - Add single-click teacher regeneration in the UI (Covered in CLI `openswitch regen --teacher` and UI dashboard).
- **Overall Score**: 9.5 / 10.
