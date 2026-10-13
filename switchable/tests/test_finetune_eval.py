"""Tests for fine-tune vs k-shot evaluation pipeline (T-021, T-022)."""

import json
import uuid
import pytest
from sqlalchemy import select

from openswitch.datasets.provenance import ProvenanceViolationError
from openswitch.db import session_context
from openswitch.finetune.eval import run_finetune_vs_kshot
from openswitch.finetune.kshot import KNearestFewShot
from openswitch.models import Dataset, Example, FineTune


@pytest.mark.asyncio
async def test_knearest_fewshot_selection():
    """Verify TF-IDF cosine similarity selects most relevant examples."""
    train_exs = [
        Example(id="1", dataset_id="ds", idx=0, split="train", input="password reset issue", reference="account"),
        Example(id="2", dataset_id="ds", idx=1, split="train", input="refund for charged fee", reference="billing"),
        Example(id="3", dataset_id="ds", idx=2, split="train", input="change account email", reference="account"),
    ]
    selector = KNearestFewShot(train_examples=train_exs, k=2)

    # Querying about password should select password reset (id=1) first
    nearest = selector.get_nearest_examples("cannot reset my password", k=1)
    assert len(nearest) == 1
    assert nearest[0].id == "1"

    # Querying about money should select billing (id=2)
    nearest_billing = selector.get_nearest_examples("overcharged refund request", k=1)
    assert len(nearest_billing) == 1
    assert nearest_billing[0].id == "2"

    # Check formatted messages structure
    msgs = selector.format_kshot_messages(
        query_text="trouble logging in",
        system_prompt="You are a classifier.",
        k=2,
    )
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == "You are a classifier."
    # 2 examples = 4 messages (user + assistant)
    assert len(msgs) == 1 + 4 + 1
    assert msgs[-1]["role"] == "user"
    assert msgs[-1]["content"] == "trouble logging in"


@pytest.mark.asyncio
async def test_run_finetune_vs_kshot_provenance_block():
    """Verify run_finetune_vs_kshot raises ProvenanceViolationError if train split has closed_api rows."""
    ds_id = f"test_ds_{uuid.uuid4().hex[:8]}"
    async with session_context() as session:
        ds = Dataset(
            id=ds_id,
            name="Blocked FT Dataset",
            task_json=json.dumps({"task": "classification"}),
            n_rows=2,
            sha256="dummy",
            seed=1337,
        )
        session.add(ds)
        ex_blocked = Example(
            id=f"{ds_id}_0",
            dataset_id=ds_id,
            idx=0,
            split="train",
            input="query",
            reference="closed output",
            reference_source="closed_api",
            train_allowed=False,
        )
        session.add(ex_blocked)
        await session.commit()

    with pytest.raises(ProvenanceViolationError):
        await run_finetune_vs_kshot(dataset_id=ds_id, base_model="qwen-2.5-7b", dry_run=True)


@pytest.mark.asyncio
async def test_run_finetune_vs_kshot_full_pipeline():
    """Verify end-to-end evaluation comparing zero-shot, k-shot, and fine-tuning."""
    ds_id = f"test_ft_{uuid.uuid4().hex[:8]}"

    async with session_context() as session:
        ds = Dataset(
            id=ds_id,
            name="FT vs kshot Dataset",
            task_json=json.dumps({"task": "classification"}),
            n_rows=6,
            sha256="dummy",
            seed=1337,
        )
        session.add(ds)

        # 3 train rows (train_allowed=True)
        t1 = Example(id=f"{ds_id}_t1", dataset_id=ds_id, idx=0, split="train", input="card stolen cancel", reference=json.dumps({"category": "card", "priority": "high"}), reference_source="open_model", train_allowed=True)
        t2 = Example(id=f"{ds_id}_t2", dataset_id=ds_id, idx=1, split="train", input="app crash on startup", reference=json.dumps({"category": "bug", "priority": "medium"}), reference_source="open_model", train_allowed=True)
        t3 = Example(id=f"{ds_id}_t3", dataset_id=ds_id, idx=2, split="train", input="billing error fee", reference=json.dumps({"category": "billing", "priority": "high"}), reference_source="open_model", train_allowed=True)

        # 1 dev row
        d1 = Example(id=f"{ds_id}_d1", dataset_id=ds_id, idx=3, split="dev", input="lost card urgent", reference=json.dumps({"category": "card", "priority": "high"}), reference_source="open_model", train_allowed=False)

        # 2 test rows
        te1 = Example(id=f"{ds_id}_te1", dataset_id=ds_id, idx=4, split="test", input="card lost please block", reference=json.dumps({"category": "card", "priority": "high"}), reference_source="open_model", train_allowed=False)
        te2 = Example(id=f"{ds_id}_te2", dataset_id=ds_id, idx=5, split="test", input="application crashed again", reference=json.dumps({"category": "bug", "priority": "medium"}), reference_source="open_model", train_allowed=False)

        session.add_all([t1, t2, t3, d1, te1, te2])
        await session.commit()

    report = await run_finetune_vs_kshot(
        dataset_id=ds_id,
        base_model="qwen-2.5-7b",
        dry_run=True,
        critical_fields=["category", "priority"],
    )

    assert report.base_model == "qwen-2.5-7b"
    assert len(report.candidates) == 3
    methods = [c.method for c in report.candidates]
    assert "zero-shot" in methods
    assert any("shot" in m for m in methods)
    assert "lora-finetune" in methods

    # Check that FineTune row was written to database
    async with session_context() as session:
        res = await session.execute(
            select(FineTune).where(FineTune.experiment_id == report.experiment_id)
        )
        ft_record = res.scalar_one_or_none()
        assert ft_record is not None
        assert ft_record.base_model == "qwen-2.5-7b"
        assert ft_record.train_rows == 3
        assert ft_record.status == "completed"

    # Check markdown table generation
    md = report.to_markdown_table()
    assert "| Method | Model |" in md
    assert "lora-finetune" in md

    # Check recommendation text
    assert len(report.recommendation) > 20
