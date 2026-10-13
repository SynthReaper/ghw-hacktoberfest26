"""Mock and scripted provider for offline testing and golden evaluations."""

import asyncio
from typing import Any

from openswitch.providers.base import (
    ChatProvider,
    ChatResult,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)


class FakeProvider(ChatProvider):
    """Simulated provider that yields preconfigured results or deterministic scripts."""

    def __init__(
        self,
        default_response: str = "Scripted output",
        model_responses: dict[str, str] | None = None,
        latency_ms: float = 50.0,
        ttft_ms: float = 20.0,
        tokens_in: int = 25,
        tokens_out: int = 10,
        error_to_raise: str | None = None,
    ):
        self.default_response = default_response
        self.model_responses = model_responses or {}
        self.latency_ms = latency_ms
        self.ttft_ms = ttft_ms
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.error_to_raise = error_to_raise
        self.call_history: list[dict[str, Any]] = []

    async def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int = 400,
        temperature: float = 0.0,
        response_format: dict[str, Any] | None = None,
        stream: bool = True,
    ) -> ChatResult:
        self.call_history.append(
            {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        )

        if self.error_to_raise == "timeout":
            raise ProviderTimeoutError("FakeProvider simulated timeout")
        elif self.error_to_raise == "rate_limit":
            raise RateLimitError("FakeProvider simulated 429 rate limit")
        elif self.error_to_raise == "unavailable":
            raise ProviderUnavailableError("FakeProvider simulated 503 unavailable")

        # Simulate small sleep
        await asyncio.sleep(self.latency_ms / 1000.0)

        response_text = self.model_responses.get(model, self.default_response)
        return ChatResult(
            text=response_text,
            tokens_in=self.tokens_in,
            tokens_out=self.tokens_out,
            ttft_ms=self.ttft_ms if stream else None,
            latency_ms=self.latency_ms,
            usage_estimated=False,
            raw_meta={"fake": True, "call_index": len(self.call_history)},
        )
