"""Async evaluation runner with concurrency controls, cost estimation, budget caps, and resume support."""

import asyncio
import json
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from openswitch.config import settings
from openswitch.db import session_context
from openswitch.models import Example, Experiment, Generation, Run
from openswitch.pricing import PricingCatalog, load_pricing
from openswitch.providers.base import ChatResult, ProviderError
from openswitch.providers.registry import registry

logger = logging.getLogger("openswitch.runner")


class BudgetExceededError(ValueError):
    """Raised when an experiment exceeds configured spend caps."""

    pass


class KillSwitchActiveError(RuntimeError):
    """Raised when an experiment is prevented or stopped by the kill switch."""

    pass


@dataclass
class RunnerProgress:
    experiment_id: str
    model_key: str
    completed: int
    total: int
    current_cost_usd: float
    error_count: int = 0
    is_done: bool = False


class ExperimentRunner:
    """Orchestrates concurrent model inference across dataset examples with resume safety."""

    def __init__(
        self,
        pricing: PricingCatalog | None = None,
        max_concurrency_per_provider: int = 3,
        cancel_event: asyncio.Event | None = None,
    ):
        self.pricing = pricing or load_pricing()
        self.max_concurrency_per_provider = max_concurrency_per_provider
        self.cancel_event = cancel_event or asyncio.Event()
        self._provider_semaphores: dict[str, asyncio.Semaphore] = {}

    def _get_semaphore(self, provider_name: str) -> asyncio.Semaphore:
        if provider_name not in self._provider_semaphores:
            # Local models default to 1 concurrent to protect VRAM; cloud default is configurable
            limit = (
                1
                if "local" in provider_name.lower() or "ollama" in provider_name.lower()
                else self.max_concurrency_per_provider
            )
            self._provider_semaphores[provider_name] = asyncio.Semaphore(limit)
        return self._provider_semaphores[provider_name]

    def estimate_cost(
        self,
        model_keys: list[str],
        examples: list[Example],
        max_tokens: int = 400,
    ) -> dict[str, float]:
        """Estimate the USD cost for evaluating specified models on examples."""
        estimates: dict[str, float] = {}
        total_chars_in = sum(len(ex.input) + len(ex.system_prompt or "") for ex in examples)
        avg_tokens_in = max(1, total_chars_in // (4 * len(examples))) if examples else 0
        est_tokens_out = max_tokens // 2  # conservative average completion length

        for key in model_keys:
            try:
                m_price = self.pricing.get_model_price(key)
                cost_per_req = m_price.calculate_cost(avg_tokens_in, est_tokens_out)
                estimates[key] = round(cost_per_req * len(examples), 6)
            except KeyError:
                estimates[key] = 0.0

        return estimates

    def check_budget_caps(self, estimated_total_cost: float) -> None:
        """Enforce per-experiment and global spend ceilings."""
        if settings.kill_switch:
            raise KillSwitchActiveError(
                "KILL_SWITCH=1: All evaluation runs are halted by administrative emergency stop."
            )

        if estimated_total_cost > settings.experiment_max_cost_usd:
            raise BudgetExceededError(
                f"Estimated experiment cost ${estimated_total_cost:.4f} exceeds per-experiment cap "
                f"EXPERIMENT_MAX_COST_USD (${settings.experiment_max_cost_usd:.2f}). "
                f"Please reduce models/examples or obtain human authorization to raise the cap."
            )

        if estimated_total_cost > settings.global_daily_budget_usd:
            raise BudgetExceededError(
                f"Estimated experiment cost ${estimated_total_cost:.4f} exceeds daily budget "
                f"GLOBAL_DAILY_BUDGET_USD (${settings.global_daily_budget_usd:.2f})."
            )

    async def run_experiment(
        self,
        experiment_id: str,
        model_keys: list[str],
        progress_callback: Callable[[RunnerProgress], Coroutine[Any, Any, None]] | None = None,
        max_tokens: int = 400,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Execute full experiment with resume capability."""
        if settings.kill_switch:
            raise KillSwitchActiveError("KILL_SWITCH is enabled.")

        async with session_context() as session:
            # Load experiment and examples
            exp_res = await session.execute(
                select(Experiment).where(Experiment.id == experiment_id)
            )
            experiment = exp_res.scalar_one_or_none()
            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found.")

            ex_res = await session.execute(
                select(Example)
                .where(Example.dataset_id == experiment.dataset_id)
                .order_by(Example.idx)
            )
            examples = list(ex_res.scalars().all())

            # Cost estimation & cap check
            cost_estimates = self.estimate_cost(model_keys, examples, max_tokens)
            total_est = sum(cost_estimates.values())
            self.check_budget_caps(total_est)

            experiment.status = "running"
            await session.commit()

        # Run models concurrently
        tasks = [
            self._run_model_for_experiment(
                experiment_id=experiment_id,
                model_key=key,
                examples=examples,
                est_cost=cost_estimates.get(key, 0.0),
                max_tokens=max_tokens,
                temperature=temperature,
                progress_callback=progress_callback,
            )
            for key in model_keys
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update experiment state
        async with session_context() as session:
            exp_res = await session.execute(
                select(Experiment).where(Experiment.id == experiment_id)
            )
            experiment = exp_res.scalar_one()

            has_errors = any(isinstance(r, Exception) for r in results)
            experiment.status = (
                "failed"
                if has_errors and all(isinstance(r, Exception) for r in results)
                else "completed"
            )
            experiment.finished_at = datetime.now(UTC)
            await session.commit()

        return {
            "experiment_id": experiment_id,
            "total_estimated_cost": total_est,
            "models": model_keys,
            "status": experiment.status,
        }

    async def _run_model_for_experiment(
        self,
        experiment_id: str,
        model_key: str,
        examples: list[Example],
        est_cost: float,
        max_tokens: int,
        temperature: float,
        progress_callback: Callable[[RunnerProgress], Coroutine[Any, Any, None]] | None = None,
    ) -> Run:
        """Run single model across examples, resuming existing generations if present."""
        async with session_context() as session:
            # Find or create Run record
            run_res = await session.execute(
                select(Run).where(Run.experiment_id == experiment_id, Run.model_key == model_key)
            )
            run = run_res.scalar_one_or_none()
            if not run:
                run = Run(
                    experiment_id=experiment_id,
                    model_key=model_key,
                    status="running",
                    est_cost=est_cost,
                    started_at=datetime.now(UTC),
                )
                session.add(run)
                await session.flush()
            else:
                run.status = "running"
            await session.commit()
            run_id = run.id

        # Query already completed example IDs for idempotency / resume
        async with session_context() as session:
            completed_res = await session.execute(
                select(Generation.example_id).where(
                    Generation.run_id == run_id, Generation.error.is_(None)
                )
            )
            completed_example_ids = set(completed_res.scalars().all())

        pending_examples = [ex for ex in examples if ex.id not in completed_example_ids]
        completed_count = len(completed_example_ids)
        total_count = len(examples)
        running_cost = 0.0

        provider = registry.get(model_key)
        sem = self._get_semaphore(getattr(provider, "provider_name", "default"))

        for ex in pending_examples:
            if self.cancel_event.is_set():
                break

            messages = []
            if ex.system_prompt:
                messages.append({"role": "system", "content": ex.system_prompt})

            # Check if input is serialized JSON chat list or plain string
            try:
                parsed_in = json.loads(ex.input)
                if isinstance(parsed_in, list):
                    messages.extend(parsed_in)
                else:
                    messages.append({"role": "user", "content": str(parsed_in)})
            except (json.JSONDecodeError, TypeError):
                messages.append({"role": "user", "content": ex.input})

            gen_error: str | None = None
            chat_res: ChatResult | None = None

            async with sem:
                try:
                    chat_res = await provider.chat(
                        model=model_key,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stream=True,
                    )
                except ProviderError as e:
                    gen_error = str(e)
                    logger.warning(f"Error on model {model_key} example {ex.id}: {e}")
                except Exception as e:
                    gen_error = f"Unexpected failure: {e}"
                    logger.error(
                        f"Unexpected error on model {model_key} example {ex.id}: {e}", exc_info=True
                    )

            # Cost calculation
            item_cost = 0.0
            if chat_res:
                try:
                    m_price = self.pricing.get_model_price(model_key)
                    item_cost = m_price.calculate_cost(
                        chat_res.tokens_in or 0, chat_res.tokens_out or 0
                    )
                except KeyError:
                    item_cost = 0.0
                running_cost += item_cost

            # Persist generation row
            async with session_context() as session:
                gen = Generation(
                    run_id=run_id,
                    example_id=ex.id,
                    output=chat_res.text if chat_res else None,
                    tokens_in=chat_res.tokens_in if chat_res else None,
                    tokens_out=chat_res.tokens_out if chat_res else None,
                    ttft_ms=chat_res.ttft_ms if chat_res else None,
                    latency_ms=chat_res.latency_ms if chat_res else None,
                    cost_usd=item_cost,
                    error=gen_error,
                    usage_estimated=chat_res.usage_estimated if chat_res else False,
                )
                session.add(gen)
                await session.commit()

            completed_count += 1
            if progress_callback:
                progress = RunnerProgress(
                    experiment_id=experiment_id,
                    model_key=model_key,
                    completed=completed_count,
                    total=total_count,
                    current_cost_usd=round(running_cost, 6),
                    error_count=1 if gen_error else 0,
                    is_done=(completed_count == total_count),
                )
                await progress_callback(progress)

        async with session_context() as session:
            run_res = await session.execute(select(Run).where(Run.id == run_id))
            final_run = run_res.scalar_one()
            final_run.actual_cost = running_cost
            final_run.status = "cancelled" if self.cancel_event.is_set() else "completed"
            final_run.finished_at = datetime.now(UTC)
            await session.commit()
            return final_run
