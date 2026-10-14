# ADR-0004: Swapped-Order Position Bias Defense and Blind Judge Calibration

## Status
Accepted (2026-10-14)

## Context
When evaluating generative tasks where exact string or JSON schema matching is insufficient (e.g., free-text triage summaries, customer sentiment explanations, policy adherence), automated LLM-as-a-judge is widely used. However, state-of-the-art LLMs suffer from severe **position bias** (systematically favoring Candidate A over Candidate B regardless of quality) and lack trustworthiness unless calibrated against human ground truth.

## Decision
1. **Swapped-Order Dual Evaluation**:
   Every pairwise comparison is evaluated twice by the automated judge with swapped presentation orders:
   - Order 1: Candidate = A, Reference = B
   - Order 2: Candidate = B, Reference = A
   If the verdicts conflict (e.g. A wins in both presentations due to static position bias), the verdict is flagged as `inconsistent`, and Sentry issues are captured if the inconsistency rate exceeds 20%.
2. **Blind Human Ground Truth Calibration**:
   Implement a blind rating workflow (`openswitch calibrate`) presenting unlabelled pairs to a human expert.
3. **Statistical Agreement & Reliability Gating**:
   Compute Cohen's kappa (\(\kappa\)) against human labels:
   - \(\kappa \ge 0.60\): **`RELIABLE`** (Green badge displayed on report and UI).
   - \(0.40 \le \kappa < 0.60\): **`MODERATE`** (Yellow caution warning).
   - \(\kappa < 0.40\): **`UNRELIABLE`** (Red alert banner; recommendations based on the judge are suppressed).

## Consequences & Empirical Findings (Task B)
- In our 20-pair calibration on support ticket triage, observed agreement was **90.0%** (18/20 pairs agreed).
- Cohen's kappa reached **0.8479**, proving strong statistical alignment between our automated judge and human expert judgment.
- Eliminates "who watches the watchman" uncertainty in enterprise migration decisions.
