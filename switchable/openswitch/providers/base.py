"""Base protocol and types for Open-Switch chat providers."""

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class ChatResult:
    """Standardized result returned by any chat provider."""

    text: str
    tokens_in: int | None
    tokens_out: int | None
    ttft_ms: float | None
    latency_ms: float
    usage_estimated: bool = False
    raw_meta: dict[str, Any] = field(default_factory=dict)


class ProviderError(Exception):
    """Base exception for provider failures."""

    pass


class RateLimitError(ProviderError):
    """Raised when a 429 rate limit is encountered and retries exhausted."""

    pass


class ProviderTimeoutError(ProviderError):
    """Raised when request times out."""

    pass


class ProviderUnavailableError(ProviderError):
    """Raised on 5xx or connection failures."""

    pass


@runtime_checkable
class ChatProvider(Protocol):
    """Protocol for model inference providers."""

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
        """Send chat messages and return a ChatResult."""
        ...
