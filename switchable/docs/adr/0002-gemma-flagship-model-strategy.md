# ADR-0002: Gemma 2 as Flagship Open Model Family Across Local, Hosted, and Fine-Tuning

**Date**: 2026-10-14
**Status**: accepted
**Deciders**: Lead Engineer, Product Owner

## Context

Open-Switch requires evaluating multiple open-weight models across tasks of varying complexity, including classification and structured ticket triage. In the Hacktoberfest AI Challenge, specific partner categories offer prize incentives (Gemma category \$200, Tinker category \$200). Choosing a consistent model family that works locally on modest hardware (laptop VRAM) and scales to cloud servers provides a coherent narrative for the writeup and demo video.

## Decision

We designate **Google's Gemma 2 family (Gemma 2 2B and Gemma 2 9B)** as the flagship candidate across:
1. **Local Mode (Ollama)**: Gemma 2 2B / 9B as default local models.
2. **Hosted Inference**: DigitalOcean Serverless Inference and Backboard.
3. **Fine-Tuning Loop**: Gemma 2 2B as the target model for LoRA fine-tuning on Tinker.
Other candidate models (e.g. Llama 3.2 3B, Qwen 2.5 7B, Mistral 7B) will be evaluated alongside Gemma to demonstrate multi-family comparison.

## Alternatives Considered

### Alternative 1: Llama 3.1 / 3.2 Exclusively
- **Pros**: Highly popular, broad provider support.
- **Cons**: Misses the specific \$200 Gemma prize category.
- **Why not**: Gemma 2 offers top-tier performance at 2B and 9B sizes while unlocking both Gemma and Tinker challenge categories.

### Alternative 2: Large Dense Models (70B+)
- **Pros**: Higher zero-shot parity on complex tasks.
- **Cons**: Cannot run locally on user laptops without enterprise GPU hardware, high inference costs, slow fine-tuning.
- **Why not**: Contrary to the "Side Hustle" theme of keeping costs low and enabling local evaluation.

## Consequences

### Positive
- Direct eligibility for both Gemma and Tinker prize categories.
- Gemma 2 2B runs comfortably on modern developer laptops under Ollama.
- Clear comparative benchmarks between base Gemma 2 2B, k-shot Gemma 2 2B, and fine-tuned Gemma 2 2B.

### Negative
- Gemma is licensed under Google's Gemma Terms of Use rather than a permissive OSI license (e.g. Apache 2.0 / MIT); this nuance must be honestly disclosed in the documentation and report.

### Risks
- Provider availability on serverless inference platforms; mitigated by fallback to alternative providers (DigitalOcean, Backboard, Ollama).
