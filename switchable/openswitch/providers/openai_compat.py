"""OpenAI-compatible chat provider with streaming, TTFT calculation, and backoff retries."""

import asyncio
import json
import random
import time
from typing import Any

import httpx

from openswitch.config import settings
from openswitch.providers.base import (
    ChatProvider,
    ChatResult,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)


class OpenAICompatProvider(ChatProvider):
    """Client for any OpenAI-compatible chat completions endpoint."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        provider_name: str = "openai_compat",
        timeout: float = 60.0,
        max_retries: int = 3,
        initial_backoff: float = 0.5,
    ):
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.timeout = timeout
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff

        # Enforce security constraints (e.g. OPENSWITCH_MODE=local limits to localhost)
        settings.validate_provider_url(self.base_url, self.provider_name)

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
        """Call chat completions with retries and timing telemetry."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }
        if response_format:
            payload["response_format"] = response_format

        # Add stream_options to capture usage in the final chunk if supported
        if stream:
            payload["stream_options"] = {"include_usage": True}

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/chat/completions"

        last_exception: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.perf_counter()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if stream:
                        result = await self._chat_stream(
                            client, url, headers, payload, start_time, messages
                        )
                    else:
                        result = await self._chat_non_stream(
                            client, url, headers, payload, start_time, messages
                        )

                    # Empty output guard (reasoning model quirk where thoughts consume tokens)
                    if not result.text.strip() and attempt < self.max_retries:
                        await asyncio.sleep(0.5)
                        continue

                    return result

            except httpx.TimeoutException as e:
                last_exception = ProviderTimeoutError(
                    f"Provider '{self.provider_name}' timed out after {self.timeout}s: {e}"
                )
                if attempt == self.max_retries:
                    raise last_exception from e
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                retry_after_hdr = e.response.headers.get("Retry-After")
                retry_after = (
                    float(retry_after_hdr)
                    if retry_after_hdr and retry_after_hdr.isdigit()
                    else None
                )
                resp_text = (
                    e.response.text if hasattr(e.response, "_content") else f"HTTP {status_code}"
                )

                if status_code == 429:
                    last_exception = RateLimitError(
                        f"Provider '{self.provider_name}' rate limited (429): {resp_text}"
                    )
                elif 500 <= status_code < 600:
                    last_exception = ProviderUnavailableError(
                        f"Provider '{self.provider_name}' service error ({status_code}): {resp_text}"
                    )
                else:
                    raise ProviderError(
                        f"Provider '{self.provider_name}' error ({status_code}): {resp_text}"
                    ) from e

                if attempt == self.max_retries:
                    raise last_exception from e

                sleep_time = (
                    retry_after
                    if retry_after is not None
                    else (self.initial_backoff * (2**attempt) + random.uniform(0.1, 0.4))
                )
                await asyncio.sleep(min(60.0, sleep_time))

            except httpx.RequestError as e:
                last_exception = ProviderUnavailableError(
                    f"Network error communicating with '{self.provider_name}': {e}"
                )
                if attempt == self.max_retries:
                    raise last_exception from e
                await asyncio.sleep(self.initial_backoff * (2**attempt) + random.uniform(0.1, 0.3))

        raise last_exception or ProviderError(
            f"Provider '{self.provider_name}' failed unexpectedly."
        )

    async def _chat_stream(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        start_time: float,
        messages: list[dict[str, str]],
    ) -> ChatResult:
        """Handle streaming response, capturing TTFT and tokens."""
        text_chunks: list[str] = []
        ttft_ms: float | None = None
        tokens_in: int | None = None
        tokens_out: int | None = None
        raw_meta: dict[str, Any] = {}

        async with client.stream("POST", url, headers=headers, json=payload) as response:
            if response.is_error:
                await response.aread()
            response.raise_for_status()

            async for line in response.aiter_lines():
                line_str = line.strip()
                if not line_str or not line_str.startswith("data:"):
                    continue

                data_str = line_str[len("data:") :].strip()
                if data_str == "[DONE]":
                    break

                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if "id" in chunk and "id" not in raw_meta:
                    raw_meta["id"] = chunk["id"]

                # Usage object can appear in the final chunk
                if "usage" in chunk and chunk["usage"]:
                    u = chunk["usage"]
                    tokens_in = u.get("prompt_tokens")
                    tokens_out = u.get("completion_tokens")

                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content_piece = delta.get("content")
                    if content_piece:
                        if ttft_ms is None:
                            ttft_ms = (time.perf_counter() - start_time) * 1000.0
                        text_chunks.append(content_piece)

        full_text = "".join(text_chunks)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Token estimation fallback if provider omitted usage
        usage_estimated = False
        if tokens_in is None or tokens_out is None:
            tokens_in, tokens_out = self._estimate_tokens(messages, full_text)
            usage_estimated = True

        return ChatResult(
            text=full_text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            ttft_ms=ttft_ms,
            latency_ms=latency_ms,
            usage_estimated=usage_estimated,
            raw_meta=raw_meta,
        )

    async def _chat_non_stream(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        start_time: float,
        messages: list[dict[str, str]],
    ) -> ChatResult:
        """Handle non-streaming response."""
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        data = response.json()
        choices = data.get("choices", [])
        text = choices[0].get("message", {}).get("content", "") if choices else ""

        usage = data.get("usage", {})
        tokens_in = usage.get("prompt_tokens")
        tokens_out = usage.get("completion_tokens")

        usage_estimated = False
        if tokens_in is None or tokens_out is None:
            tokens_in, tokens_out = self._estimate_tokens(messages, text)
            usage_estimated = True

        return ChatResult(
            text=text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            ttft_ms=None,
            latency_ms=latency_ms,
            usage_estimated=usage_estimated,
            raw_meta={"id": data.get("id")},
        )

    def _estimate_tokens(self, messages: list[dict[str, str]], completion: str) -> tuple[int, int]:
        """Estimate token count when usage is omitted by the provider (~4 chars / token)."""
        prompt_text = " ".join(m.get("content", "") for m in messages)
        est_in = max(1, len(prompt_text) // 4)
        est_out = max(1, len(completion) // 4)
        return est_in, est_out
