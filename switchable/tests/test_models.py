import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from openswitch.models import (
    Dataset,
    Example,
    Experiment,
    Generation,
    HumanLabel,
    Judgment,
    Run,
    Score,
    init_db,
)


@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    await init_db(engine)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_and_read_entities(test_db: AsyncSession):
    # 1. Create dataset
    ds = Dataset(
        name="test-intent",
        task_json='{"type": "classification"}',
        n_rows=1,
        sha256="abc123sha",
        seed=42,
    )
    test_db.add(ds)
    await test_db.flush()

    # 2. Create example
    ex = Example(
        dataset_id=ds.id,
        idx=0,
        input="How do I change my pin?",
        reference="change_pin",
        reference_source="human",
        train_allowed=True,
        split="test",
    )
    test_db.add(ex)
    await test_db.flush()

    # 3. Create experiment & run
    exp = Experiment(
        name="test-run-1",
        dataset_id=ds.id,
        config_json='{"models": ["gemma-2b"]}',
        config_hash="cfghash123",
        status="running",
    )
    test_db.add(exp)
    await test_db.flush()

    run = Run(
        experiment_id=exp.id,
        model_key="gemma-2b",
        status="completed",
        est_cost=0.01,
        actual_cost=0.008,
    )
    test_db.add(run)
    await test_db.flush()

    # 4. Create generation
    gen = Generation(
        run_id=run.id,
        example_id=ex.id,
        output="change_pin",
        tokens_in=15,
        tokens_out=3,
        latency_ms=250.0,
        cost_usd=0.0001,
    )
    test_db.add(gen)
    await test_db.flush()

    # 5. Create score & judgment
    sc = Score(generation_id=gen.id, metric="label_accuracy", value=1.0)
    jdg = Judgment(
        generation_id=gen.id,
        judge_model="open-judge",
        verdict_ab="A",
        verdict_ba="B",
        final="win",
    )
    hl = HumanLabel(generation_id=gen.id, label="better", labeler="tester")
    test_db.add_all([sc, jdg, hl])
    await test_db.commit()

    # Verify querying
    result = await test_db.execute(select(Generation).where(Generation.id == gen.id))
    fetched_gen = result.scalar_one()
    assert fetched_gen.output == "change_pin"
    assert fetched_gen.tokens_in == 15


@pytest.mark.asyncio
async def test_generation_uniqueness_constraint(test_db: AsyncSession):
    ds = Dataset(name="ds", task_json="{}", n_rows=1, sha256="s", seed=1)
    test_db.add(ds)
    await test_db.flush()

    ex = Example(dataset_id=ds.id, idx=0, input="in", reference="ref", split="test")
    test_db.add(ex)
    await test_db.flush()

    exp = Experiment(name="e", dataset_id=ds.id, config_json="{}", config_hash="h")
    test_db.add(exp)
    await test_db.flush()

    run = Run(experiment_id=exp.id, model_key="m1")
    test_db.add(run)
    await test_db.flush()

    gen1 = Generation(run_id=run.id, example_id=ex.id, output="first")
    test_db.add(gen1)
    await test_db.flush()

    # Second generation with same (run_id, example_id) must trigger IntegrityError
    gen2 = Generation(run_id=run.id, example_id=ex.id, output="duplicate")
    test_db.add(gen2)
    with pytest.raises(IntegrityError):
        await test_db.flush()
    await test_db.rollback()
