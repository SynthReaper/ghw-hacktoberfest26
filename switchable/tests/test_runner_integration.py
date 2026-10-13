import asyncio

import pytest
from sqlalchemy import select

from openswitch.config import settings
from openswitch.db import session_context
from openswitch.models import Dataset, Example, Experiment, Generation, Run, init_db
from openswitch.providers.fake import FakeProvider
from openswitch.providers.registry import registry
from openswitch.runner import BudgetExceededError, ExperimentRunner, KillSwitchActiveError


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_budget_cap_blocks_expensive_run():
    runner = ExperimentRunner()

    # Artificially small cap
    settings.experiment_max_cost_usd = 0.05
    try:
        # Check budget with estimated cost of $0.10
        with pytest.raises(BudgetExceededError) as exc_info:
            runner.check_budget_caps(0.10)
        assert "exceeds per-experiment cap" in str(exc_info.value)
    finally:
        settings.experiment_max_cost_usd = 2.0


@pytest.mark.asyncio
async def test_kill_switch_blocks_run():
    runner = ExperimentRunner()
    settings.kill_switch = True
    try:
        with pytest.raises(KillSwitchActiveError) as exc_info:
            runner.check_budget_caps(0.01)
        assert "KILL_SWITCH" in str(exc_info.value)
    finally:
        settings.kill_switch = False


@pytest.mark.asyncio
async def test_runner_resumes_without_rerunning_completed_rows():
    # 1. Register fake provider
    fake_provider = FakeProvider(default_response="Classification: Billing")
    registry.register_provider("fake-gemma", fake_provider)

    # 2. Insert test dataset with 4 examples
    async with session_context() as session:
        ds = Dataset(name="test-resume-ds", task_json="{}", n_rows=4, sha256="hash123", seed=42)
        session.add(ds)
        await session.flush()

        examples = [
            Example(dataset_id=ds.id, idx=i, input=f"Query {i}", reference="Billing", split="test")
            for i in range(4)
        ]
        session.add_all(examples)
        await session.flush()

        exp = Experiment(
            name="resume-experiment", dataset_id=ds.id, config_json="{}", config_hash="h1"
        )
        session.add(exp)
        await session.commit()
        exp_id = exp.id

    cancel_event = asyncio.Event()
    runner = ExperimentRunner(cancel_event=cancel_event)

    # Callback that triggers cancellation after 2 examples are completed
    async def stop_after_2(prog):
        if prog.completed >= 2:
            cancel_event.set()

    # First run: should execute 2 examples and stop
    await runner.run_experiment(
        experiment_id=exp_id,
        model_keys=["fake-gemma"],
        progress_callback=stop_after_2,
    )

    # Assert 2 calls recorded in fake provider
    assert len(fake_provider.call_history) == 2

    async with session_context() as session:
        gens_res = await session.execute(
            select(Generation).join(Run).where(Run.experiment_id == exp_id)
        )
        gens = list(gens_res.scalars().all())
        assert len(gens) == 2

    # Second run: without cancellation. Must resume and only process the remaining 2 examples!
    runner_resumed = ExperimentRunner()
    res2 = await runner_resumed.run_experiment(
        experiment_id=exp_id,
        model_keys=["fake-gemma"],
    )
    assert res2["status"] == "completed"

    # Fake provider should have exactly 4 calls in total (2 original + 2 remaining)
    assert len(fake_provider.call_history) == 4

    async with session_context() as session:
        gens_res = await session.execute(
            select(Generation).join(Run).where(Run.experiment_id == exp_id)
        )
        all_gens = list(gens_res.scalars().all())
        assert len(all_gens) == 4
        # Assert each example 0..3 has exactly one generation
        ex_ids = {g.example_id for g in all_gens}
        assert len(ex_ids) == 4
