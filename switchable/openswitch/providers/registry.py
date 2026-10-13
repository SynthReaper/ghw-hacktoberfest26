"""Provider registry and factory for resolving model endpoints."""

import os
from typing import Any

import yaml

from openswitch.providers.base import ChatProvider
from openswitch.providers.fake import FakeProvider
from openswitch.providers.openai_compat import OpenAICompatProvider


class ProviderRegistry:
    """Manages instantiated providers and configurations."""

    def __init__(self):
        self._providers: dict[str, ChatProvider] = {}
        self._configs: dict[str, dict[str, Any]] = {}

    def register_provider(self, name: str, provider: ChatProvider) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> ChatProvider:
        if name in self._providers:
            return self._providers[name]

        if name not in self._configs:
            raise KeyError(f"Provider '{name}' is not registered or configured.")

        # Instantiate from cached config
        cfg = self._configs[name]
        provider = self._build_provider(name, cfg)
        self._providers[name] = provider
        return provider

    def load_from_yaml(self, yaml_content: str | dict[str, Any]) -> None:
        """Load provider definitions from parsed YAML or YAML string."""
        data = yaml.safe_load(yaml_content) if isinstance(yaml_content, str) else yaml_content
        providers_dict = data.get("providers", {})
        for name, cfg in providers_dict.items():
            self._configs[name] = cfg

    def _build_provider(self, name: str, cfg: dict[str, Any]) -> ChatProvider:
        kind = cfg.get("kind", "openai_compat")
        if kind == "fake":
            return FakeProvider()

        base_url = cfg.get("base_url")
        if not base_url or base_url == "UNVERIFIED":
            raise ValueError(
                f"Provider '{name}' has unverified or missing base_url. Please verify in provider documentation."
            )

        api_key_env = cfg.get("api_key_env")
        api_key = os.getenv(api_key_env, "") if api_key_env else ""

        return OpenAICompatProvider(
            base_url=base_url,
            api_key=api_key,
            provider_name=name,
        )


registry = ProviderRegistry()
