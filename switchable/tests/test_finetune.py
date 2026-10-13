import pytest

from openswitch.datasets.provenance import ProvenanceViolationError
from openswitch.finetune.kshot import KNearestFewShot
from openswitch.finetune.tinker import Hyperparameters, TinkerFineTuner
from openswitch.models import Example


def make_example(idx: int, input_text: str, reference: str, train_allowed: bool) -> Example:
    return Example(
        id=f"ex-{idx}",
        dataset_id="ds-test",
        idx=idx,
        input=input_text,
        reference=reference,
        reference_source="human" if train_allowed else "closed_api",
        train_allowed=train_allowed,
        split="train",
    )


def test_tinker_provenance_guard_blocks_disallowed_rows():
    tuner = TinkerFineTuner()

    allowed = [make_example(1, "Text 1", "Ref 1", train_allowed=True)]
    tuner.validate_provenance_guard(allowed)  # Should pass

    disallowed = [
        make_example(1, "Text 1", "Ref 1", train_allowed=True),
        make_example(2, "Text 2", "Ref 2", train_allowed=False),  # Closed API!
    ]

    with pytest.raises(ProvenanceViolationError) as exc_info:
        tuner.validate_provenance_guard(disallowed)

    assert "Provenance Guard violation" in str(exc_info.value)
    assert "ex-2" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tinker_run_training_dry_run():
    tuner = TinkerFineTuner()
    examples = [
        make_example(i, f"Input prompt {i}", f"Target response {i}", train_allowed=True)
        for i in range(20)
    ]

    hp = Hyperparameters(lora_r=16, lora_alpha=32, epochs=2)
    result = await tuner.run_training(
        base_model="Qwen/Qwen2.5-7B-Instruct",
        train_examples=examples,
        hyperparams=hp,
        dry_run=True,
    )

    assert result.status == "completed"
    assert result.train_rows_count == 20
    assert result.cost_usd > 0
    assert result.time_seconds > 0
    assert "tinker-lora-" in result.job_id
    assert result.sampler_endpoint is not None
    assert result.exportable_hf_path is not None


def test_knearest_few_shot():
    examples = [
        make_example(1, "I need to reset my debit card PIN code.", "change_pin", True),
        make_example(2, "When will my replacement card arrive in the mail?", "card_arrival", True),
        make_example(3, "Can I cancel an outgoing bank transfer?", "cancel_transfer", True),
        make_example(4, "My PIN is blocked after three failed tries.", "change_pin", True),
    ]

    selector = KNearestFewShot(examples, k=2)

    # Query about PIN
    nearest = selector.get_nearest_examples("Help me change my card PIN number")
    assert len(nearest) == 2
    # Both nearest should be PIN examples
    assert nearest[0].reference == "change_pin"
    assert nearest[1].reference == "change_pin"

    # Message formatting
    msgs = selector.format_kshot_messages(
        query_text="Forgot my PIN",
        system_prompt="You are a banking assistant.",
        k=2,
    )
    assert len(msgs) == 1 + (2 * 2) + 1  # 1 system + 2 demo pairs (4) + 1 query = 6
    assert msgs[0]["role"] == "system"
    assert msgs[-1]["role"] == "user"
    assert msgs[-1]["content"] == "Forgot my PIN"
