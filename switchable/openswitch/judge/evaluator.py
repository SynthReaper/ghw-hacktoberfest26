"""Pairwise swapped-order judge execution and aggregation logic."""

from dataclasses import dataclass
from typing import Literal

from openswitch.judge.parser import parse_judge_output
from openswitch.judge.prompt import format_judge_prompt
from openswitch.pricing import PricingCatalog, load_pricing
from openswitch.providers.base import ChatProvider

FinalVerdict = Literal["win", "loss", "tie", "inconsistent", "invalid"]


@dataclass
class JudgmentResult:
    verdict_ab: str
    verdict_ba: str
    final: FinalVerdict
    rationale_ab: str
    rationale_ba: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


def resolve_swapped_verdicts(verdict_ab: str | None, verdict_ba: str | None) -> FinalVerdict:
    """Resolve two swapped calls into a unified verdict.

    Call AB: A = Candidate, B = Reference
      - 'A' means Candidate preferred
      - 'B' means Reference preferred
      - 'tie' means equal

    Call BA: A = Reference, B = Candidate
      - 'B' means Candidate preferred
      - 'A' means Reference preferred
      - 'tie' means equal
    """
    if not verdict_ab or not verdict_ba:
        return "invalid"

    v_ab = verdict_ab.strip().lower()
    v_ba = verdict_ba.strip().lower()

    if v_ab not in ("a", "b", "tie") or v_ba not in ("a", "b", "tie"):
        return "invalid"

    # Map each call to candidate score (+1 = win, -1 = loss, 0 = tie)
    score_ab = 1 if v_ab == "a" else (-1 if v_ab == "b" else 0)
    score_ba = 1 if v_ba == "b" else (-1 if v_ba == "a" else 0)

    # Resolution per PRD / Eval Methodology:
    # Win if wins both or wins one and ties one
    if (
        (score_ab == 1 and score_ba == 1)
        or (score_ab == 1 and score_ba == 0)
        or (score_ab == 0 and score_ba == 1)
    ):
        return "win"
    # Loss if loses both or loses one and ties one
    elif (
        (score_ab == -1 and score_ba == -1)
        or (score_ab == -1 and score_ba == 0)
        or (score_ab == 0 and score_ba == -1)
    ):
        return "loss"
    # Tie if both tie
    elif score_ab == 0 and score_ba == 0:
        return "tie"
    # Inconsistent (e.g., position bias where judge picked 'A' both times)
    else:
        return "inconsistent"


class PairwiseJudge:
    """Impartial judge executing pairwise comparisons twice with positions swapped."""

    def __init__(self, pricing: PricingCatalog | None = None):
        self.pricing = pricing or load_pricing()

    async def evaluate_pair(
        self,
        provider: ChatProvider,
        judge_model_id: str,
        judge_pricing_key: str,
        rubric: str,
        input_text: str,
        candidate_text: str,
        reference_text: str,
    ) -> JudgmentResult:
        """Execute Call AB and Call BA, retrying once on parse failure."""
        total_tokens_in = 0
        total_tokens_out = 0

        # Call 1: AB (A = candidate, B = reference)
        sys_ab, user_ab = format_judge_prompt(rubric, input_text, candidate_text, reference_text)
        res_ab, v_ab = await self._call_with_retry(provider, judge_model_id, sys_ab, user_ab)
        total_tokens_in += res_ab.tokens_in or 0
        total_tokens_out += res_ab.tokens_out or 0

        # Call 2: BA (A = reference, B = candidate)
        sys_ba, user_ba = format_judge_prompt(rubric, input_text, reference_text, candidate_text)
        res_ba, v_ba = await self._call_with_retry(provider, judge_model_id, sys_ba, user_ba)
        total_tokens_in += res_ba.tokens_in or 0
        total_tokens_out += res_ba.tokens_out or 0

        final = resolve_swapped_verdicts(v_ab.verdict, v_ba.verdict)

        # Cost calculation
        try:
            m_price = self.pricing.get_model_price(judge_pricing_key)
            cost = m_price.calculate_cost(total_tokens_in, total_tokens_out)
        except KeyError:
            cost = 0.0

        return JudgmentResult(
            verdict_ab=v_ab.verdict or "invalid",
            verdict_ba=v_ba.verdict or "invalid",
            final=final,
            rationale_ab=v_ab.reason,
            rationale_ba=v_ba.reason,
            tokens_in=total_tokens_in,
            tokens_out=total_tokens_out,
            cost_usd=round(cost, 6),
        )

    async def _call_with_retry(
        self,
        provider: ChatProvider,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
    ):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        res = await provider.chat(
            model=model_id,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"},
            stream=False,
        )
        verdict = parse_judge_output(res.text)
        if not verdict.is_valid:
            # One retry with explicit formatting reminder
            retry_messages = messages + [
                {"role": "assistant", "content": res.text},
                {
                    "role": "user",
                    "content": "Error: Output was not valid JSON with 'verdict' and 'reason'. Respond ONLY with JSON.",
                },
            ]
            res_retry = await provider.chat(
                model=model_id,
                messages=retry_messages,
                temperature=0.0,
                response_format={"type": "json_object"},
                stream=False,
            )
            v_retry = parse_judge_output(res_retry.text)
            if v_retry.is_valid:
                return res_retry, v_retry

        return res, verdict
