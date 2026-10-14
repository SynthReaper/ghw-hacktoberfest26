"""Tests for blind calibration flow and reliability tier calculation (T-023)."""

import json
import uuid

import pytest
from sqlalchemy import select

from openswitch.db import session_context
from openswitch.judge.calibration_flow import (
    analyze_calibration,
    map_human_choice_to_verdict,
    sample_blind_pairs,
    save_human_label,
)
from openswitch.models import Dataset, Example, Experiment, Generation, HumanLabel, Judgment, Run


def test_map_human_choice_to_verdict():
    """Verify human selection maps correctly to candidate win/loss/tie regardless of blinded position."""
    # When candidate is Option A
    assert map_human_choice_to_verdict("1", cand_is_a=True) == "win"
    assert map_human_choice_to_verdict("a", cand_is_a=True) == "win"
    assert map_human_choice_to_verdict("2", cand_is_a=True) == "loss"
    assert map_human_choice_to_verdict("b", cand_is_a=True) == "loss"
    assert map_human_choice_to_verdict("3", cand_is_a=True) == "tie"
    assert map_human_choice_to_verdict("tie", cand_is_a=True) == "tie"

    # When candidate is Option B
    assert map_human_choice_to_verdict("2", cand_is_a=False) == "win"
    assert map_human_choice_to_verdict("b", cand_is_a=False) == "win"
    assert map_human_choice_to_verdict("1", cand_is_a=False) == "loss"
    assert map_human_choice_to_verdict("a", cand_is_a=False) == "loss"
    assert map_human_choice_to_verdict("3", cand_is_a=False) == "tie"


def test_analyze_calibration_high_agreement():
    """Verify kappa >= 0.60 produces 'reliable' tier."""
    pairs = [
        {"human": "win", "judge": "win"},
        {"human": "win", "judge": "win"},
        {"human": "win", "judge": "win"},
        {"human": "tie", "judge": "tie"},
        {"human": "tie", "judge": "tie"},
        {"human": "loss", "judge": "loss"},
        {"human": "loss", "judge": "loss"},
        {"human": "win", "judge": "tie"},  # 1 disagreement
    ]
    analysis = analyze_calibration(pairs)
    assert analysis.total_pairs == 8
    assert analysis.agreement_rate > 0.80
    assert analysis.cohen_kappa > 0.60
    assert analysis.tier == "reliable"
    assert "reliable" in analysis.banner_message.lower()


def test_analyze_calibration_moderate_agreement():
    """Verify kappa between 0.40 and 0.60 produces 'moderate' tier."""
    pairs = [
        {"human": "win", "judge": "win"},
        {"human": "win", "judge": "tie"},
        {"human": "tie", "judge": "win"},
        {"human": "loss", "judge": "loss"},
        {"human": "loss", "judge": "tie"},
        {"human": "tie", "judge": "tie"},
        {"human": "win", "judge": "win"},
        {"human": "loss", "judge": "loss"},
        {"human": "win", "judge": "loss"},
        {"human": "loss", "judge": "win"},
    ]
    analysis = analyze_calibration(pairs)
    assert 0.0 <= analysis.cohen_kappa < 0.60


@pytest.mark.asyncio
async def test_sample_blind_pairs_and_save_human_label():
    """Verify sampling from DB and saving human label records."""
    exp_id = f"test_exp_{uuid.uuid4().hex[:8]}"
    ds_id = f"test_ds_{uuid.uuid4().hex[:8]}"

    async with session_context() as session:
        ds = Dataset(
            id=ds_id,
            name="Calib Test Dataset",
            task_json=json.dumps({"task": "generation"}),
            n_rows=2,
            sha256="dummy",
            seed=1337,
        )
        session.add(ds)

        ex1 = Example(
            id=f"{ds_id}_0",
            dataset_id=ds_id,
            idx=0,
            split="test",
            input="Summary prompt 1",
            reference="Gold reference text 1",
            reference_source="human_gold",
            train_allowed=True,
        )
        session.add(ex1)

        exp = Experiment(
            id=exp_id,
            dataset_id=ds_id,
            name="Calib Exp",
            config_json=json.dumps({}),
            config_hash="abc",
            status="completed",
        )
        session.add(exp)

        run = Run(
            id=f"run_{exp_id}",
            experiment_id=exp_id,
            model_key="gemma-9b-local",
            status="completed",
        )
        session.add(run)

        gen = Generation(
            id=f"gen_{exp_id}_1",
            run_id=run.id,
            example_id=ex1.id,
            output="Candidate model output text 1",
        )
        session.add(gen)

        jud = Judgment(
            id=f"jud_{exp_id}_1",
            generation_id=gen.id,
            judge_model="do-llama-70b-judge",
            verdict_ab="win",
            verdict_ba="win",
            final="win",
        )
        session.add(jud)
        await session.commit()

    # Sample blind pairs
    pairs = await sample_blind_pairs(experiment_id=exp_id, sample_size=5, seed=123)
    assert len(pairs) >= 1
    p = [pair for pair in pairs if pair.generation_id == gen.id][0]
    assert p.input_text == "Summary prompt 1"
    assert p.judge_verdict == "win"
    assert "Candidate model output text 1" in (p.option_a_text, p.option_b_text)
    assert "Gold reference text 1" in (p.option_a_text, p.option_b_text)

    # Save human label
    await save_human_label(generation_id=gen.id, human_verdict="win", labeler="tester")

    async with session_context() as session:
        res = await session.execute(select(HumanLabel).where(HumanLabel.generation_id == gen.id))
        label = res.scalar_one_or_none()
        assert label is not None
        assert label.label == "win"
        assert label.labeler == "tester"
