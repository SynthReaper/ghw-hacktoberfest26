"""Open-Switch LLM-as-a-judge module with pairwise swapped-order execution."""

from openswitch.judge.calibration import (
    calculate_agreement,
    calculate_cohen_kappa,
    judge_reliability_tier,
)
from openswitch.judge.evaluator import (
    FinalVerdict,
    JudgmentResult,
    PairwiseJudge,
    resolve_swapped_verdicts,
)
from openswitch.judge.parser import JudgeVerdict, parse_judge_output
from openswitch.judge.prompt import format_judge_prompt

__all__ = [
    "FinalVerdict",
    "JudgeVerdict",
    "JudgmentResult",
    "PairwiseJudge",
    "calculate_agreement",
    "calculate_cohen_kappa",
    "format_judge_prompt",
    "judge_reliability_tier",
    "parse_judge_output",
    "resolve_swapped_verdicts",
]
