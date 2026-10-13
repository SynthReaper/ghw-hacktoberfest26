# ADR-0001: Unified Core Architecture with Pluggable Providers & Strict Provenance Guard

**Date**: 2026-10-14
**Status**: accepted
**Deciders**: Lead Engineer, Product Owner

## Context

Teams paying frontier-API prices for narrow tasks want to evaluate whether open-weight models can replace them without sacrificing accuracy, privacy, or compliance. Commercial eval tools focus on scoring tables without decision recommendations or confidence intervals. Crucially, training open models on closed model outputs may violate terms of service, yet developers frequently overlook provenance tracking. Additionally, the application must run identically in a hosted web demo (Render) and fully locally (Ollama) without leaking confidential data.

## Decision

We adopt a decoupled, modular architecture centered on an `openswitch` core library with three lightweight frontends (CLI via Typer, Web UI via FastAPI + HTMX, and Standalone HTML Reports). All provider interactions use an async `ChatProvider` protocol conforming to OpenAI-compatible endpoints with streaming TTFT calculation and exponential backoff. We establish a non-negotiable **Provenance Guard** in data import and fine-tuning pipelines: any row marked `closed_api` or `unknown` defaults to `train_allowed=false` and raises a hard error if included in fine-tune datasets without explicit cryptographic/attestation override.

## Alternatives Considered

### Alternative 1: Full-stack Next.js/React App with Separate Python Backend
- **Pros**: Rich component ecosystem.
- **Cons**: High build overhead, complex deployment (Node + Python runtime), slower development cycle for a 4-day sprint.
- **Why not**: Violates simplicity principles. FastAPI + Jinja2 + HTMX provides reactive UI and SSE streaming without a JavaScript build step.

### Alternative 2: Rely on External Evaluation SaaS Platforms
- **Pros**: Zero infrastructure build.
- **Cons**: Requires uploading proprietary client data to 3rd-party servers, lacks statistical rigor (bootstrap CIs), and cannot run air-gapped.
- **Why not**: Defeats Open-Switch's core value proposition of privacy, local Ollama execution, and honest decision thresholds.

## Consequences

### Positive
- Identical behavior across local and cloud environments.
- Zero risk of accidental terms violation during fine-tuning.
- Fast, verifiable SQLite state persistence with zero maintenance overhead.
- Auditable reproducibility block in every generated report.

### Negative
- Local execution depends on user's hardware capacity (RAM/VRAM for Ollama).
- HTMX requires server-side state coordination over WebSocket/SSE.

### Risks
- Provider rate limits during concurrent model runs; mitigated by per-provider concurrency limits and exponential backoff with jitter.
