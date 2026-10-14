"""Tests for provenance guard hard-block and teacher regeneration pipeline (T-020)."""

import json
import uuid

import pytest
from sqlalchemy import select

from openswitch.datasets.provenance import ProvenanceViolationError
from openswitch.datasets.regen import enforce_strict_provenance_guard, regenerate_teacher_references
from openswitch.db import session_context
from openswitch.finetune.tinker import TinkerFineTuner
from openswitch.models import Dataset, Example
from openswitch.providers.fake import FakeProvider


@pytest.mark.asyncio
async def test_enforce_strict_provenance_guard_blocks_closed_api():
    """Verify that rows with train_allowed=False raise ProvenanceViolationError."""
    ex_valid = Example(
        id=str(uuid.uuid4()),
        dataset_id="test_ds",
        idx=0,
        split="train",
        input="hello",
        reference="world",
        reference_source="human_gold",
        train_allowed=True,
    )
    ex_blocked = Example(
        id=str(uuid.uuid4()),
        dataset_id="test_ds",
        idx=1,
        split="train",
        input="secret task",
        reference="closed model answer",
        reference_source="closed_api",
        train_allowed=False,
    )

    # Valid alone passes
    assert enforce_strict_provenance_guard([ex_valid]) == [ex_valid]

    # Mixed or blocked fails hard
    with pytest.raises(ProvenanceViolationError) as exc_info:
        enforce_strict_provenance_guard([ex_valid, ex_blocked])
    assert "Provenance Guard hard block" in str(exc_info.value)
    assert ex_blocked.id in str(exc_info.value)


@pytest.mark.asyncio
async def test_enforce_strict_provenance_guard_blocks_leakage_from_other_splits():
    """Verify that test or dev rows are rejected by the split leakage guard."""
    ex_test = Example(
        id=str(uuid.uuid4()),
        dataset_id="test_ds",
        idx=0,
        split="test",
        input="hello",
        reference="world",
        reference_source="open_model",
        train_allowed=True,
    )
    with pytest.raises(ValueError) as exc_info:
        enforce_strict_provenance_guard([ex_test])
    assert "Split leakage guard" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tinker_fine_tuner_hard_blocks_disallowed_rows():
    """TinkerFineTuner must reject training if any example violates provenance."""
    tuner = TinkerFineTuner()
    ex_blocked = Example(
        id=str(uuid.uuid4()),
        dataset_id="test_ds",
        idx=0,
        split="train",
        input="ticket",
        reference="gpt-4 completion",
        reference_source="closed_api",
        train_allowed=False,
    )
    with pytest.raises(ProvenanceViolationError):
        await tuner.run_training(
            base_model="qwen-2.5-7b", train_examples=[ex_blocked], dry_run=True
        )


@pytest.mark.asyncio
async def test_teacher_regeneration_converts_closed_api_to_open_model():
    """Regeneration using an open teacher updates rows to reference_source='open_model' and train_allowed=True."""
    ds_id = f"test_regen_{uuid.uuid4().hex[:8]}"

    # Seed test dataset in database
    async with session_context() as session:
        ds = Dataset(
            id=ds_id,
            name="Test Regen Dataset",
            task_json=json.dumps({"task": "classification"}),
            n_rows=3,
            sha256="dummy_sha256",
            seed=1337,
        )
        session.add(ds)

        # 2 train rows (1 closed_api/blocked, 1 human_gold/allowed)
        ex1 = Example(
            id=f"{ds_id}_0",
            dataset_id=ds_id,
            idx=0,
            split="train",
            input=json.dumps({"text": "Urgent password reset needed"}),
            reference="closed model reference",
            reference_source="closed_api",
            train_allowed=False,
        )
        ex2 = Example(
            id=f"{ds_id}_1",
            dataset_id=ds_id,
            idx=1,
            split="train",
            input=json.dumps({"text": "Billing issue refund"}),
            reference="human reference",
            reference_source="human_gold",
            train_allowed=True,
        )
        # 1 test row that should never be touched
        ex3 = Example(
            id=f"{ds_id}_2",
            dataset_id=ds_id,
            idx=2,
            split="test",
            input=json.dumps({"text": "Test split ticket"}),
            reference="eval only closed ref",
            reference_source="closed_api",
            train_allowed=False,
        )
        session.add_all([ex1, ex2, ex3])
        await session.commit()

    teacher_provider = FakeProvider(
        default_response=json.dumps({"category": "account", "priority": "high"})
    )

    summary = await regenerate_teacher_references(
        dataset_id=ds_id,
        teacher_model_key="qwen-2.5-72b",
        teacher_provider=teacher_provider,
        teacher_license="Apache-2.0",
        only_disallowed=True,
    )

    assert summary.total_train_rows == 2
    assert summary.regenerated_count == 1
    assert summary.untouched_count == 1

    # Verify DB state
    async with session_context() as session:
        res = await session.execute(
            select(Example).where(Example.dataset_id == ds_id).order_by(Example.idx)
        )
        rows = list(res.scalars().all())

    # ex1 was regenerated
    assert rows[0].reference == json.dumps({"category": "account", "priority": "high"})
    assert rows[0].reference_source == "open_model"
    assert rows[0].train_allowed is True
    meta = json.loads(rows[0].meta_json)
    assert meta["teacher_model"] == "qwen-2.5-72b"
    assert meta["teacher_license"] == "Apache-2.0"

    # ex2 was untouched
    assert rows[1].reference == "human reference"
    assert rows[1].reference_source == "human_gold"
    assert rows[1].train_allowed is True

    # ex3 (test split) was untouched and remains train_allowed=False
    assert rows[2].reference_source == "closed_api"
    assert rows[2].train_allowed is False

    # Now all train rows can safely pass the provenance guard!
    train_rows = [r for r in rows if r.split == "train"]
    assert len(train_rows) == 2
    verified = enforce_strict_provenance_guard(train_rows)
    assert len(verified) == 2
