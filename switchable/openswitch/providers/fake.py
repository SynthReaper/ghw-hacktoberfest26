"""Mock and scripted provider for offline testing and golden evaluations."""

import asyncio
import json
import random
import re
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
        await asyncio.sleep(min(self.latency_ms, 10.0) / 1000.0)

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


class RealisticTaskProvider(ChatProvider):
    """Generates realistic, reproducible outputs based on model capability and task domain."""

    ACCURACY_PROFILES = {
        "gemma-9b-local": {"acc": 0.92, "lat": 65.0, "ttft": 20.0},
        "do-llama-8b": {"acc": 0.90, "lat": 85.0, "ttft": 28.0},
        "bb-qwen-7b": {"acc": 0.88, "lat": 95.0, "ttft": 30.0},
        "do-mistral-7b": {"acc": 0.86, "lat": 80.0, "ttft": 25.0},
        "llama-3b-local": {"acc": 0.84, "lat": 40.0, "ttft": 14.0},
        "gemma-2b-local": {"acc": 0.81, "lat": 30.0, "ttft": 12.0},
        "default": {"acc": 0.85, "lat": 60.0, "ttft": 20.0},
    }

    def __init__(self, model_key: str, task_config: dict[str, Any]):
        self.model_key = model_key
        self.task_config = task_config
        profile = self.ACCURACY_PROFILES.get(model_key, self.ACCURACY_PROFILES["default"])
        self.target_acc = profile["acc"]
        self.base_latency = profile["lat"]
        self.base_ttft = profile["ttft"]
        self.rng = random.Random(hash(model_key))

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
        user_msg = ""
        for m in messages:
            if m.get("role") == "user":
                user_msg = m.get("content", "")

        task_type = self.task_config.get("type", "generation")
        input_len = len(user_msg)
        tokens_in = max(10, input_len // 4)

        if task_type == "classification":
            resp_text = self._classify(user_msg)
            tokens_out = 4
        elif task_type == "extraction":
            resp_text = self._extract(user_msg)
            tokens_out = max(20, len(resp_text) // 4)
        elif "judge" in self.model_key.lower():
            resp_text = self._judge(user_msg)
            tokens_out = 25
        else:
            resp_text = "Standard response text"
            tokens_out = 15

        # Tiny sleep for realism
        await asyncio.sleep(0.001)

        return ChatResult(
            text=resp_text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            ttft_ms=self.base_ttft,
            latency_ms=self.base_latency,
            usage_estimated=False,
            raw_meta={"model": self.model_key, "simulated": True},
        )

    def _classify(self, user_msg: str) -> str:
        labels = self.task_config.get("labels", [])
        if not labels:
            return "billing"

        low_input = user_msg.lower()
        matched = None
        for l in labels:
            clean_l = l.replace("_", " ")
            if any(w in low_input for w in clean_l.split()):
                matched = l
                break

        if not matched:
            matched = labels[0]

        # Simulate model accuracy profile
        if self.rng.random() <= self.target_acc:
            return matched
        else:
            # Mistake: return alternative label
            alternatives = [lbl for lbl in labels if lbl != matched]
            return self.rng.choice(alternatives) if alternatives else matched

    def _extract(self, user_msg: str) -> str:
        # Detect category
        low = user_msg.lower()
        cat = "tech"
        if "charge" in low or "invoice" in low or "bill" in low or "refund" in low:
            cat = "billing"
        elif "account" in low or "password" in low or "surname" in low or "sso" in low:
            cat = "account"
        elif "printer" in low or "hardware" in low or "scanner" in low or "terminal" in low:
            cat = "hardware"

        # Detect urgency
        urg = "medium"
        if "critical" in low or "outage" in low or "compromise" in low or "breach" in low:
            urg = "critical"
        elif "immediately" in low or "urgent" in low or "waiting" in low or "overdraft" in low:
            urg = "high"
        elif "cosmetic" in low or "convenient" in low or "annual" in low:
            urg = "low"

        # Match ticket ID if present
        tck_match = re.search(r"TCK-\d+", user_msg)
        tck_id = tck_match.group(0) if tck_match else "TCK-GENERAL"

        summary = f"[{tck_id}] Automated triage summary of customer issue in {cat} department."

        payload = {
            "category": cat,
            "urgency": urg,
            "summary": summary,
        }
        return json.dumps(payload)

    def _judge(self, user_msg: str) -> str:
        # Extract answer_a and answer_b to simulate a content-aware judge
        a_match = re.search(r"<answer_a>\s*(.*?)\s*</answer_a>", user_msg, re.DOTALL)
        b_match = re.search(r"<answer_b>\s*(.*?)\s*</answer_b>", user_msg, re.DOTALL)
        a_text = a_match.group(1) if a_match else ""
        b_text = b_match.group(1) if b_match else ""

        # Content-aware evaluation
        len_a = len(a_text)
        len_b = len(b_text)

        if abs(len_a - len_b) < 15:
            return json.dumps(
                {"verdict": "tie", "reason": "Both answers satisfy the rubric with equal precision."}
            )
        elif len_a > len_b:
            return json.dumps(
                {"verdict": "A", "reason": "Answer A is more comprehensive and adheres strictly to the required rubric."}
            )
        else:
            return json.dumps(
                {"verdict": "B", "reason": "Answer B is more comprehensive and adheres strictly to the required rubric."}
            )
