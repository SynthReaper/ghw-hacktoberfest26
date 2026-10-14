"""Teacher regeneration: produce open-model training references from non-trainable rows."""

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select

from openswitch.datasets.provenance import ProvenanceViolationError
from openswitch.db import session_context
from openswitch.models import Example
from openswitch.providers.base import ChatProvider
from openswitch.providers.registry import registry

logger = logging.getLogger("openswitch.datasets.regen")


@dataclass
class RegenerationSummary:
    dataset_id: str
    teacher_model_key: str
    teacher_license: str
    total_train_rows: int
    regenerated_count: int
    untouched_count: int
    timestamp: str


def enforce_strict_provenance_guard(examples: list[Example]) -> list[Example]:
    """Strictly filter and verify that only train_allowed=True rows from the train split reach the trainer.

    Raises:
        ProvenanceViolationError: if any row with train_allowed=False is present.
    """
    disallowed = [ex for ex in examples if not ex.train_allowed]
    if disallowed:
        bad_ids = [ex.id for ex in disallowed[:5]]
        raise ProvenanceViolationError(
            f"Provenance Guard hard block: {len(disallowed)} row(s) have train_allowed=False "
            f"(sample IDs: {bad_ids}). Closed-API outputs cannot be used for fine-tuning."
        )

    # Verify all examples are from the train split
    non_train = [ex for ex in examples if ex.split != "train"]
    if non_train:
        raise ValueError(
            f"Split leakage guard: {len(non_train)} row(s) are from non-train splits ({[ex.split for ex in non_train[:3]]}). "
            "Only train split rows can be used for training."
        )

    return examples


async def regenerate_teacher_references(
    dataset_id: str,
    teacher_model_key: str,
    teacher_provider: ChatProvider | None = None,
    teacher_license: str = "Apache 2.0 / Open Weights",
    only_disallowed: bool = True,
) -> RegenerationSummary:
    """Regenerate train split reference answers using an open teacher model.

    Updates references, sets reference_source='open_model', and marks train_allowed=True.
    """
    provider = teacher_provider or registry.get(teacher_model_key)

    regenerated_count = 0
    untouched_count = 0
    total_train = 0

    async with session_context() as session:
        # Load train examples
        query = (
            select(Example)
            .where(
                Example.dataset_id == dataset_id,
                Example.split == "train",
            )
            .order_by(Example.idx)
        )

        res = await session.execute(query)
        train_examples = list(res.scalars().all())
        total_train = len(train_examples)

        for ex in train_examples:
            if only_disallowed and ex.train_allowed:
                untouched_count += 1
                continue

            # Format messages
            messages = []
            if ex.system_prompt:
                messages.append({"role": "system", "content": ex.system_prompt})

            try:
                parsed_in = json.loads(ex.input)
                if isinstance(parsed_in, list):
                    messages.extend(parsed_in)
                else:
                    messages.append({"role": "user", "content": str(parsed_in)})
            except (json.JSONDecodeError, TypeError):
                messages.append({"role": "user", "content": ex.input})

            # Call teacher model
            chat_res = await provider.chat(
                model=teacher_model_key,
                messages=messages,
                max_tokens=400,
                temperature=0.0,
            )

            # Update example with open-model teacher output
            ex.reference = chat_res.text
            ex.reference_source = "open_model"
            ex.train_allowed = True

            # Record provenance metadata
            meta = {}
            if ex.meta_json:
                try:
                    meta = json.loads(ex.meta_json)
                except Exception:
                    pass

            meta["teacher_model"] = teacher_model_key
            meta["teacher_license"] = teacher_license
            meta["regenerated_at"] = datetime.now(UTC).isoformat()
            ex.meta_json = json.dumps(meta)

            regenerated_count += 1

        await session.commit()

    return RegenerationSummary(
        dataset_id=dataset_id,
        teacher_model_key=teacher_model_key,
        teacher_license=teacher_license,
        total_train_rows=total_train,
        regenerated_count=regenerated_count,
        untouched_count=untouched_count,
        timestamp=datetime.now(UTC).isoformat(),
    )
