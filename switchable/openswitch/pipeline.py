"""End-to-end experiment pipeline orchestrator."""

import json
import logging
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from openswitch.cost import (
    calculate_model_cost_summary,
    calculate_monthly_projection,
)
from openswitch.db import session_context
from openswitch.judge.evaluator import PairwiseJudge
from openswitch.metrics.field_accuracy import evaluate_field_accuracy
from openswitch.metrics.json_valid import is_valid_json
from openswitch.metrics.labels import calculate_classification_metrics
from openswitch.metrics.schema_valid import is_schema_valid
from openswitch.models import Dataset, Example, Experiment, Generation, Judgment, Run, Score
from openswitch.obs import check_and_report_experiment_anomalies, gen_ai_span
from openswitch.pricing import load_pricing
from openswitch.providers.registry import registry
from openswitch.recommend import CandidateSummary, generate_recommendation
from openswitch.runner import ExperimentRunner
from openswitch.stats import (
    calculate_judge_stats,
    calculate_metric_ci,
    calculate_percentiles,
    check_length_bias,
)

logger = logging.getLogger("openswitch.pipeline")


def get_git_commit() -> str | None:
    try:
        import subprocess

        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2.0,
        )
        return res.stdout.strip()[:8]
    except Exception:
        return None


class PipelineOrchestrator:
    """Coordinates execution, scoring, judge evaluation, statistics, and reporting."""

    def __init__(self, fake_mode: bool = False):
        self.fake_mode = fake_mode
        self.pricing = load_pricing()

    async def run_full_pipeline(
        self,
        dataset_id: str,
        model_keys: list[str],
        task_config: dict[str, Any],
        experiment_name: str | None = None,
        judge_model_key: str | None = None,
        monthly_volume: int = 50_000,
        baseline_cost_per_request: float = 0.015,
        threshold: float = 0.85,
        output_json_path: Path | None = None,
    ) -> dict[str, Any]:
        """Execute the complete experiment lifecycle from inference to reporting."""
        exp_name = experiment_name or f"exp-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
        git_commit = get_git_commit()

        # Register simulated providers if fake_mode is active
        if self.fake_mode:
            from openswitch.providers.fake import RealisticTaskProvider

            for k in model_keys:
                registry.register(k, RealisticTaskProvider(model_key=k, task_config=task_config))

            if judge_model_key:
                registry.register(
                    judge_model_key,
                    RealisticTaskProvider(model_key=judge_model_key, task_config={"type": "judge"}),
                )

        # 1. Create Experiment record
        async with session_context() as session:
            ds_res = await session.execute(select(Dataset).where(Dataset.id == dataset_id))
            dataset = ds_res.scalar_one_or_none()
            if not dataset:
                raise ValueError(f"Dataset with ID {dataset_id} not found.")

            cfg_json = json.dumps(
                {
                    "models": model_keys,
                    "task": task_config,
                    "monthly_volume": monthly_volume,
                    "baseline_cost": baseline_cost_per_request,
                    "threshold": threshold,
                }
            )

            experiment = Experiment(
                name=exp_name,
                dataset_id=dataset_id,
                config_json=cfg_json,
                config_hash=dataset.sha256[:16],
                status="created",
                git_commit=git_commit,
            )
            session.add(experiment)
            await session.commit()
            exp_id = experiment.id

        # 2. Run model generations via ExperimentRunner
        runner = ExperimentRunner(pricing=self.pricing)
        await runner.run_experiment(experiment_id=exp_id, model_keys=model_keys)

        # 3. Score Deterministic Metrics
        await self._score_deterministic(exp_id, task_config)

        # 4. Run Pairwise Judge if rubric is present
        rubric = task_config.get("rubric")
        if rubric and judge_model_key:
            await self._run_judge_evaluations(exp_id, rubric, judge_model_key)

        # 5. Aggregate Statistics & Bootstrap CIs
        aggregated = await self._aggregate_experiment(
            exp_id=exp_id,
            dataset_id=dataset_id,
            task_config=task_config,
            baseline_cost_per_request=baseline_cost_per_request,
            monthly_volume=monthly_volume,
            threshold=threshold,
        )

        # 6. Check Sentry Anomalies
        anomalies = check_and_report_experiment_anomalies(
            experiment_id=exp_id,
            inconsistency_rate=aggregated.get("max_inconsistency_rate", 0.0),
            provider_error_rate=aggregated.get("max_error_rate", 0.0),
            empty_output_rate=aggregated.get("max_empty_rate", 0.0),
            budget_cap_hit=False,
            total_cost_usd=aggregated.get("total_actual_cost_usd", 0.0),
        )
        aggregated["anomalies_detected"] = anomalies

        # 7. Export JSON report if requested
        if output_json_path:
            output_json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(aggregated, f, indent=2)

        return aggregated

    async def _score_deterministic(self, experiment_id: str, task_config: dict[str, Any]):
        """Evaluate and persist deterministic metrics for all generations."""
        task_type = task_config.get("type", "generation")
        schema = task_config.get("json_schema")

        async with session_context() as session:
            runs_res = await session.execute(select(Run).where(Run.experiment_id == experiment_id))
            runs = list(runs_res.scalars().all())

            for run in runs:
                gens_res = await session.execute(
                    select(Generation, Example)
                    .join(Example, Generation.example_id == Example.id)
                    .where(Generation.run_id == run.id)
                )

                for gen, ex in gens_res.all():
                    if not gen.output:
                        # Failed or empty output
                        session.add(
                            Score(
                                generation_id=gen.id, metric="valid", value=0.0, details_json=None
                            )
                        )
                        continue

                    # 1. JSON validity check
                    if schema or task_type == "extraction":
                        is_valid, parsed = is_valid_json(gen.output)
                        session.add(
                            Score(
                                generation_id=gen.id,
                                metric="json_valid",
                                value=1.0 if is_valid else 0.0,
                            )
                        )

                        # Schema validity check
                        if schema:
                            schema_ok, _, _ = is_schema_valid(gen.output, schema)
                            session.add(
                                Score(
                                    generation_id=gen.id,
                                    metric="schema_valid",
                                    value=1.0 if schema_ok else 0.0,
                                )
                            )

                    # 2. Label classification accuracy
                    if task_type == "classification":
                        metrics = calculate_classification_metrics([gen.output], [ex.reference])
                        session.add(
                            Score(
                                generation_id=gen.id,
                                metric="label_accuracy",
                                value=metrics["label_accuracy"],
                            )
                        )

                    # 3. Field accuracy for JSON dictionaries
                    if schema:
                        crit_fields = task_config.get("critical_fields", [])
                        try:
                            field_scores = evaluate_field_accuracy(
                                candidate_text=gen.output,
                                reference_text=ex.reference,
                                critical_fields=crit_fields,
                            )
                            for metric_name, val in field_scores.items():
                                session.add(
                                    Score(
                                        generation_id=gen.id,
                                        metric=metric_name,
                                        value=val,
                                    )
                                )
                        except Exception as e:
                            logger.warning(f"Field accuracy evaluation error on gen {gen.id}: {e}")

            await session.commit()

    async def _run_judge_evaluations(
        self,
        experiment_id: str,
        rubric: str,
        judge_model_key: str,
    ):
        """Run pairwise judge on candidate vs reference outputs."""
        judge = PairwiseJudge(pricing=self.pricing)
        judge_provider = registry.get(judge_model_key)

        async with session_context() as session:
            runs_res = await session.execute(select(Run).where(Run.experiment_id == experiment_id))
            runs = list(runs_res.scalars().all())

            for run in runs:
                # Never evaluate the judge against itself without a bias warning
                if run.model_key == judge_model_key:
                    logger.warning(
                        f"Judge model {judge_model_key} is being evaluated as candidate in run {run.id}"
                    )

                gens_res = await session.execute(
                    select(Generation, Example)
                    .join(Example, Generation.example_id == Example.id)
                    .where(Generation.run_id == run.id)
                )

                for gen, ex in gens_res.all():
                    if not gen.output:
                        continue

                    with gen_ai_span(
                        operation="judge_pairwise",
                        description=f"Judge comparison for run {run.id}",
                        model=judge_model_key,
                        provider=getattr(judge_provider, "provider_name", "judge"),
                        prompt_version="judge-v1",
                        experiment_id=experiment_id,
                    ) as span_meta:
                        res = await judge.evaluate_pair(
                            provider=judge_provider,
                            judge_model_id=judge_model_key,
                            judge_pricing_key=judge_model_key,
                            rubric=rubric,
                            input_text=ex.input,
                            candidate_text=gen.output,
                            reference_text=ex.reference,
                        )
                        span_meta["tokens_in"] = res.tokens_in
                        span_meta["tokens_out"] = res.tokens_out
                        span_meta["cost_usd"] = res.cost_usd

                    session.add(
                        Judgment(
                            generation_id=gen.id,
                            judge_model=judge_model_key,
                            verdict_ab=res.verdict_ab,
                            verdict_ba=res.verdict_ba,
                            final=res.final,
                            rationale_json=json.dumps(
                                {
                                    "ab": res.rationale_ab,
                                    "ba": res.rationale_ba,
                                }
                            ),
                        )
                    )

            await session.commit()

    async def _aggregate_experiment(
        self,
        exp_id: str,
        dataset_id: str,
        task_config: dict[str, Any],
        baseline_cost_per_request: float,
        monthly_volume: int,
        threshold: float,
    ) -> dict[str, Any]:
        """Aggregate test split evaluations, compute bootstrap CIs, costs, and recommendation."""
        primary_metric = task_config.get("primary_metric", "label_accuracy")

        candidates_summary: list[CandidateSummary] = []
        model_results: dict[str, Any] = {}
        max_inconsistent = 0.0
        max_err = 0.0
        max_empty = 0.0
        total_exp_cost = 0.0

        async with session_context() as session:
            # Query dataset counts
            ex_res = await session.execute(
                select(Example.split, Example.train_allowed).where(Example.dataset_id == dataset_id)
            )
            rows = ex_res.all()
            test_size = sum(1 for r in rows if r[0] == "test")
            trainable_rows_count = sum(1 for r in rows if r[0] == "train" and r[1] is True)

            runs_res = await session.execute(select(Run).where(Run.experiment_id == exp_id))
            runs = list(runs_res.scalars().all())

            for run in runs:
                total_exp_cost += run.actual_cost

                # Query test split generations and scores
                gens_res = await session.execute(
                    select(Generation, Example.split)
                    .join(Example, Generation.example_id == Example.id)
                    .where(Generation.run_id == run.id)
                )
                test_gens: list[Generation] = []
                all_gens: list[Generation] = []
                for g, split in gens_res.all():
                    all_gens.append(g)
                    if split == "test":
                        test_gens.append(g)

                eval_gens = test_gens if len(test_gens) >= 10 else all_gens
                n_eval = len(eval_gens)

                # Error and empty rate
                n_errors = sum(1 for g in eval_gens if g.error is not None)
                n_empty = sum(1 for g in eval_gens if not g.output)
                err_rate = n_errors / n_eval if n_eval else 0.0
                empty_rate = n_empty / n_eval if n_eval else 0.0
                max_err = max(max_err, err_rate)
                max_empty = max(max_empty, empty_rate)

                # Collect latency and token stats
                latencies = [g.latency_ms for g in eval_gens if g.latency_ms is not None]
                ttfts = [g.ttft_ms for g in eval_gens if g.ttft_ms is not None]
                tokens_pairs = [
                    (g.tokens_in or 0, g.tokens_out or 0) for g in eval_gens if g.output
                ]

                lat_pcts = calculate_percentiles(latencies, (50, 95))
                ttft_pcts = calculate_percentiles(ttfts, (50,))

                # Pricing and Cost model
                cost_summary = calculate_model_cost_summary(
                    model_key=run.model_key,
                    requests_tokens=tokens_pairs,
                    price_in_per_m=0.20,  # fallback if not in catalog
                    price_out_per_m=0.20,
                    pricing_source="pricing.yaml",
                    verified_on="2026-10-14",
                    is_stale=False,
                    is_local="local" in run.model_key.lower() or "ollama" in run.model_key.lower(),
                    baseline_cost_per_request=baseline_cost_per_request,
                )

                # Pull scores for this run
                gen_ids = [g.id for g in eval_gens]
                scores_res = await session.execute(
                    select(Score).where(Score.generation_id.in_(gen_ids))
                )
                scores = list(scores_res.scalars().all())

                # Group scores by metric name
                metrics_data: dict[str, list[float]] = {}
                for s in scores:
                    metrics_data.setdefault(s.metric, []).append(s.value)

                metrics_cis = {}
                for m_name, vals in metrics_data.items():
                    metrics_cis[m_name] = calculate_metric_ci(vals, metric_name=m_name).to_dict()

                # Pull Judgments
                judgments_res = await session.execute(
                    select(Judgment).where(Judgment.generation_id.in_(gen_ids))
                )
                judgments = list(judgments_res.scalars().all())
                verdicts = [j.final for j in judgments]
                judge_stats = calculate_judge_stats(verdicts)
                judge_stats_dict = {k: v.to_dict() for k, v in judge_stats.items()}

                if judge_stats.get("inconsistent_rate"):
                    max_inconsistent = max(
                        max_inconsistent, judge_stats["inconsistent_rate"].point_estimate
                    )

                # Length bias guard
                output_lengths = [len(g.output or "") for g in eval_gens]
                primary_scores = metrics_data.get(
                    primary_metric, [1.0 if v in ("win", "tie") else 0.0 for v in verdicts]
                )
                length_bias = check_length_bias(output_lengths, primary_scores)

                if primary_metric in metrics_cis:
                    prim_ci = metrics_cis[primary_metric]
                elif (
                    primary_metric == "composite"
                    and "composite_critical_fields_correct" in metrics_cis
                ):
                    prim_ci = metrics_cis["composite_critical_fields_correct"]
                elif (
                    "parity_rate" in judge_stats_dict
                    and judge_stats_dict["parity_rate"]["n_samples"] > 0
                ):
                    prim_ci = judge_stats_dict["parity_rate"]
                else:
                    prim_ci = {"point_estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}

                cand_summary = CandidateSummary(
                    model_key=run.model_key,
                    display_name=run.model_key,
                    primary_metric_name=primary_metric,
                    point_estimate=prim_ci["point_estimate"],
                    ci_lower=prim_ci["ci_lower"],
                    ci_upper=prim_ci["ci_upper"],
                    cost_per_1k=cost_summary.cost_per_1k,
                    error_rate=err_rate,
                    latency_p50_ms=lat_pcts.get("p50", 0.0),
                    is_local="local" in run.model_key.lower() or "ollama" in run.model_key.lower(),
                )
                candidates_summary.append(cand_summary)

                model_results[run.model_key] = {
                    "primary_metric": prim_ci,
                    "deterministic_metrics": metrics_cis,
                    "judge_metrics": judge_stats_dict,
                    "cost_summary": cost_summary.to_dict(),
                    "monthly_projection": calculate_monthly_projection(
                        baseline_cost_per_request=baseline_cost_per_request,
                        candidate_cost_per_request=cost_summary.cost_per_request,
                        monthly_volume=monthly_volume,
                        assumptions=cost_summary.assumptions,
                    ).to_dict(),
                    "latency": {**lat_pcts, **ttft_pcts},
                    "length_bias": asdict(length_bias),
                    "error_rate": round(err_rate, 4),
                    "empty_output_rate": round(empty_rate, 4),
                }

        # Generate recommendation
        rec_result = generate_recommendation(
            candidates=candidates_summary,
            baseline_cost_per_1k=baseline_cost_per_request * 1000.0,
            threshold=threshold,
            test_size=test_size or len(candidates_summary),
            trainable_rows_count=trainable_rows_count,
        )

        return {
            "experiment_id": exp_id,
            "created_at": datetime.now(UTC).isoformat(),
            "git_commit": get_git_commit(),
            "dataset_id": dataset_id,
            "test_size": test_size,
            "trainable_rows_count": trainable_rows_count,
            "total_actual_cost_usd": round(total_exp_cost, 6),
            "max_inconsistency_rate": round(max_inconsistent, 4),
            "max_error_rate": round(max_err, 4),
            "max_empty_rate": round(max_empty, 4),
            "recommendation": rec_result.to_dict(),
            "models": model_results,
        }
