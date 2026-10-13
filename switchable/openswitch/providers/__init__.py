"""Provider layer package for Open-Switch."""

from openswitch.providers.base import (
    ChatProvider,
    ChatResult,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)
from openswitch.providers.fake import FakeProvider
from openswitch.providers.openai_compat import OpenAICompatProvider
from openswitch.providers.registry import ProviderRegistry, registry

__all__ = [
    "ChatProvider",
    "ChatResult",
    "ProviderError",
    "RateLimitError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "OpenAICompatProvider",
    "FakeProvider",
    "ProviderRegistry",
    "registry",
]
