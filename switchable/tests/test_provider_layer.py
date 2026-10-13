import httpx
import pytest
import respx

from openswitch.providers.base import (
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)
from openswitch.providers.fake import FakeProvider
from openswitch.providers.openai_compat import OpenAICompatProvider


@pytest.mark.asyncio
@respx.mock
async def test_openai_compat_200_streaming():
    base_url = "http://localhost:11434/v1"
    provider = OpenAICompatProvider(base_url=base_url, provider_name="ollama")

    stream_content = (
        'data: {"id":"1","choices":[{"delta":{"content":"Hello"}}]}\n\n'
        'data: {"id":"1","choices":[{"delta":{"content":" world!"}}]}\n\n'
        'data: {"id":"1","choices":[],"usage":{"prompt_tokens":10,"completion_tokens":2}}\n\n'
        "data: [DONE]\n\n"
    )
    respx.post(f"{base_url}/chat/completions").mock(
        return_value=httpx.Response(200, text=stream_content)
    )

    res = await provider.chat(
        model="gemma2:2b",
        messages=[{"role": "user", "content": "Hi"}],
        stream=True,
    )
    assert res.text == "Hello world!"
    assert res.tokens_in == 10
    assert res.tokens_out == 2
    assert res.ttft_ms is not None
    assert res.ttft_ms >= 0
    assert not res.usage_estimated


@pytest.mark.asyncio
@respx.mock
async def test_openai_compat_200_non_streaming():
    base_url = "http://localhost:11434/v1"
    provider = OpenAICompatProvider(base_url=base_url, provider_name="ollama")

    body = {
        "id": "chat-123",
        "choices": [{"message": {"role": "assistant", "content": "Direct response"}}],
        "usage": {"prompt_tokens": 8, "completion_tokens": 3},
    }
    respx.post(f"{base_url}/chat/completions").mock(return_value=httpx.Response(200, json=body))

    res = await provider.chat(
        model="gemma2:2b",
        messages=[{"role": "user", "content": "Hi"}],
        stream=False,
    )
    assert res.text == "Direct response"
    assert res.tokens_in == 8
    assert res.tokens_out == 3
    assert not res.usage_estimated


@pytest.mark.asyncio
@respx.mock
async def test_openai_compat_429_rate_limit_retry():
    base_url = "http://localhost:11434/v1"
    provider = OpenAICompatProvider(
        base_url=base_url,
        max_retries=1,
        initial_backoff=0.01,
    )

    route = respx.post(f"{base_url}/chat/completions").mock(
        return_value=httpx.Response(429, text="Rate limit exceeded")
    )

    with pytest.raises(RateLimitError) as exc_info:
        await provider.chat(model="m", messages=[{"role": "user", "content": "test"}])
    assert "rate limited (429)" in str(exc_info.value)
    assert route.call_count == 2  # 1 initial + 1 retry


@pytest.mark.asyncio
@respx.mock
async def test_openai_compat_500_service_error():
    base_url = "http://localhost:11434/v1"
    provider = OpenAICompatProvider(
        base_url=base_url,
        max_retries=1,
        initial_backoff=0.01,
    )

    route = respx.post(f"{base_url}/chat/completions").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await provider.chat(model="m", messages=[{"role": "user", "content": "test"}])
    assert "service error (503)" in str(exc_info.value)
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_openai_compat_timeout():
    base_url = "http://localhost:11434/v1"
    provider = OpenAICompatProvider(
        base_url=base_url,
        timeout=0.05,
        max_retries=0,
    )

    respx.post(f"{base_url}/chat/completions").mock(
        side_effect=httpx.TimeoutException("Connection timed out")
    )

    with pytest.raises(ProviderTimeoutError) as exc_info:
        await provider.chat(model="m", messages=[{"role": "user", "content": "test"}])
    assert "timed out" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_openai_compat_empty_output_retry():
    base_url = "http://localhost:11434/v1"
    provider = OpenAICompatProvider(
        base_url=base_url,
        max_retries=1,
        initial_backoff=0.01,
    )

    # First attempt: empty output (reasoning model quirk)
    empty_stream = 'data: {"choices":[{"delta":{"content":""}}]}\n\ndata: [DONE]\n\n'
    # Second attempt: valid content
    valid_stream = 'data: {"choices":[{"delta":{"content":"Final answer"}}]}\n\ndata: [DONE]\n\n'

    route = respx.post(f"{base_url}/chat/completions")
    route.side_effect = [
        httpx.Response(200, text=empty_stream),
        httpx.Response(200, text=valid_stream),
    ]

    res = await provider.chat(model="m", messages=[{"role": "user", "content": "test"}])
    assert res.text == "Final answer"
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_openai_compat_missing_usage_estimation():
    base_url = "http://localhost:11434/v1"
    provider = OpenAICompatProvider(base_url=base_url)

    # Provider omits usage block entirely
    stream_without_usage = (
        'data: {"choices":[{"delta":{"content":"A short answer."}}]}\n\ndata: [DONE]\n\n'
    )
    respx.post(f"{base_url}/chat/completions").mock(
        return_value=httpx.Response(200, text=stream_without_usage)
    )

    res = await provider.chat(
        model="m",
        messages=[{"role": "user", "content": "A short question prompt."}],
    )
    assert res.text == "A short answer."
    assert res.usage_estimated is True
    assert res.tokens_in is not None and res.tokens_in > 0
    assert res.tokens_out is not None and res.tokens_out > 0


@pytest.mark.asyncio
async def test_fake_provider():
    fake = FakeProvider(default_response="Mocked response", tokens_in=50, tokens_out=20)
    res = await fake.chat(model="test-model", messages=[{"role": "user", "content": "hello"}])
    assert res.text == "Mocked response"
    assert res.tokens_in == 50
    assert res.tokens_out == 20
    assert not res.usage_estimated
    assert res.raw_meta.get("fake") is True
