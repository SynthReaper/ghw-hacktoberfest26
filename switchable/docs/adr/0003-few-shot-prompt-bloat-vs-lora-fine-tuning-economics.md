# ADR-0003: Few-Shot Token Bloat vs. LoRA Fine-Tuning Economics

## Status
Accepted (2026-10-14)

## Context
When engineering teams seek to close the accuracy gap between an open-weight model and a proprietary closed LLM, the default instinct is few-shot prompt stuffing (e.g., prepending 3–8 input/output demonstrations to the system prompt). However, in high-volume production systems, adding demonstrations significantly inflates input token counts on every single invocation.

Before recommending a LoRA fine-tuning run (which incurs one-time compute cost and operational complexity), Open-Switch must provide a rigorous, empirical baseline comparison answering:
1. Does few-shot prompting actually improve accuracy on the specific proprietary task?
2. At what monthly request volume does LoRA fine-tuning break even compared to the recurring token tax of few-shot prompting?

## Decision
1. **Mandatory k-Shot Baseline**: Implement `KNearestFewShot` using TF-IDF cosine similarity nearest-neighbor selection from the training split. Evaluate \(k \in \{3, 4, 5, 6, 7, 8\}\) on the dev split to select the optimal \(k\) before benchmarking test split performance.
2. **LoRA Fine-Tuning via Tinker API**: Execute distributed LoRA fine-tuning on compliant training rows (`train_allowed=True`), producing exportable adapter weights (`adapter_model.safetensors`).
3. **Break-Even Volume Model**: Compute the exact break-even request volume:
   \[
   V_{\text{breakeven}} = \left\lceil \frac{C_{\text{training}}}{c_{\text{kshot}} - c_{\text{lora}}} \right\rceil
   \]
   where \(C_{\text{training}}\) is the one-time fine-tuning cost, \(c_{\text{kshot}}\) is the per-request few-shot inference cost, and \(c_{\text{lora}}\) is the per-request LoRA inference cost.

## Consequences & Empirical Findings (Task B)
- **Zero Accuracy Delta**: 3-shot prompting achieved 90.0% [80.0%, 98.0%]—identical to zero-shot accuracy.
- **Economic Trap**: 3-shot prompting bloated prompt length from 120 to 680 tokens, nearly quadrupling inference cost from $0.035 to $0.139 per 1,000 requests and doubling latency (40ms to 95ms).
- **Clear Break-Even**: The \$1.03 Tinker LoRA fine-tune maintained low latency (65ms) and minimal per-request cost ($0.038 / 1k), paying for itself after **10,238 requests/month** (less than 5 days of typical startup traffic).
