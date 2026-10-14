"""Interactive and programmatic blind judge calibration flow (T-023)."""

import logging
import random
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from openswitch.db import session_context
from openswitch.judge.calibration import (
    ReliabilityTier,
    calculate_agreement,
    calculate_cohen_kappa,
    compute_confusion_matrix,
    judge_reliability_tier,
)
from openswitch.models import Example, Generation, HumanLabel, Judgment, Run

logger = logging.getLogger("openswitch.judge.calibration_flow")


@dataclass
class BlindPair:
    generation_id: str
    example_id: str
    input_text: str
    option_a_text: str
    option_b_text: str
    # Blinded mappings
    option_a_is_candidate: bool
    candidate_model: str
    judge_verdict: str  # "win", "loss", "tie", "inconsistent"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CalibrationAnalysis:
    total_pairs: int
    agreement_rate: float
    cohen_kappa: float
    tier: ReliabilityTier
    banner_message: str
    confusion_matrix: dict[str, dict[str, int]]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


async def sample_blind_pairs(
    experiment_id: str | None = None,
    sample_size: int = 20,
    seed: int = 42,
) -> list[BlindPair]:
    """Sample outputs with judgments, randomizing option positions for blind human review."""
    rng = random.Random(seed)

    async with session_context() as session:
        query = (
            select(Generation, Judgment, Example, Run)
            .join(Judgment, Generation.id == Judgment.generation_id)
            .join(Example, Generation.example_id == Example.id)
            .join(Run, Generation.run_id == Run.id)
        )
        if experiment_id:
            query = query.where(Run.experiment_id == experiment_id)

        res = await session.execute(query)
        rows = list(res.all())

    if not rows:
        return []

    # Sample rows
    selected_rows = rng.sample(rows, min(sample_size, len(rows)))
    pairs: list[BlindPair] = []

    for gen, jud, ex, run in selected_rows:
        cand_text = gen.output or ""
        ref_text = ex.reference or ""
        # Randomize whether Candidate is Option A or Option B
        cand_is_a = rng.choice([True, False])

        opt_a = cand_text if cand_is_a else ref_text
        opt_b = ref_text if cand_is_a else cand_text

        pairs.append(
            BlindPair(
                generation_id=gen.id,
                example_id=ex.id,
                input_text=ex.input,
                option_a_text=opt_a,
                option_b_text=opt_b,
                option_a_is_candidate=cand_is_a,
                candidate_model=run.model_key,
                judge_verdict=jud.final,
            )
        )

    return pairs


def map_human_choice_to_verdict(
    choice: str,
    cand_is_a: bool,
) -> str:
    """Map human choice (option A, option B, or tie) to candidate verdict ('win', 'loss', 'tie')."""
    ch = choice.strip().lower()
    if ch in ["tie", "3", "t", "equal"]:
        return "tie"

    if cand_is_a:
        if ch in ["a", "1", "opt_a"]:
            return "win"
        elif ch in ["b", "2", "opt_b"]:
            return "loss"
    else:
        if ch in ["b", "2", "opt_b"]:
            return "win"
        elif ch in ["a", "1", "opt_a"]:
            return "loss"

    return "tie"


async def save_human_label(
    generation_id: str,
    human_verdict: str,
    labeler: str = "human",
) -> None:
    """Persist human judgment label into the database."""
    async with session_context() as session:
        label = HumanLabel(
            generation_id=generation_id,
            label=human_verdict,
            labeler=labeler,
        )
        session.add(label)
        await session.commit()


def analyze_calibration(
    paired_labels: list[dict[str, str]],
) -> CalibrationAnalysis:
    """Compute complete calibration metrics from a list of {'human': ..., 'judge': ...} records."""
    human = [p["human"] for p in paired_labels if p.get("human") and p.get("judge")]
    judge = [p["judge"] for p in paired_labels if p.get("human") and p.get("judge")]

    if not human:
        raise ValueError("No valid label pairs provided for calibration analysis.")

    agreement = calculate_agreement(human, judge)
    kappa = calculate_cohen_kappa(human, judge)
    tier, banner = judge_reliability_tier(kappa)
    cm = compute_confusion_matrix(human, judge)

    return CalibrationAnalysis(
        total_pairs=len(human),
        agreement_rate=round(agreement, 4),
        cohen_kappa=round(kappa, 4),
        tier=tier,
        banner_message=banner,
        confusion_matrix=cm,
        created_at=datetime.now(UTC).isoformat(),
    )
