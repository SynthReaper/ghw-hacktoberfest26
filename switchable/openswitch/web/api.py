"""FastAPI REST API routes for datasets, models, experiments, calibration, and fine-tuning."""

import asyncio
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
import tempfile
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from openswitch.config import settings
from openswitch.datasets.importer import import_dataset_from_file
from openswitch.db import session_context
from openswitch.finetune.eval import run_finetune_vs_kshot
from openswitch.judge.calibration_flow import (
    analyze_calibration,
    map_human_choice_to_verdict,
    sample_blind_pairs,
    save_human_label,
)
from openswitch.models import Dataset, Example, Experiment, Generation, HumanLabel, Judgment, Run
from openswitch.pricing import PricingCatalog, load_pricing
from openswitch.report import generate_standalone_html
from openswitch.web.events import broadcaster
from openswitch.web.session import get_or_create_session

logger = logging.getLogger("openswitch.web.api")
api_router = APIRouter(prefix="/api")


# --- Pydantic Schemas ---

class CreateExperimentRequest(BaseModel):
    name: str = Field(..., description="Experiment name")
    dataset_id: str = Field(..., description="Target dataset ID")
    models: list[str] = Field(..., min_length=1, description="Candidate model keys")
    judge_model: str = Field("deterministic", description="Judge model key")
    budget_limit_usd: float = Field(2.0, description="Cost limit cap in USD")
    threshold: float = Field(0.85, description="Parity threshold")


class CalibrationLabelRequest(BaseModel):
    generation_id: str
    choice: str  # "1", "2", "3" or "a", "b", "tie"
    cand_is_a: bool = True
    labeler: str = "web_user"


class FineTuneRequest(BaseModel):
    dataset_id: str
    base_model: str = "bb-qwen-7b"
    dry_run: bool = True


# --- Endpoints ---

@api_router.get("/health")
async def health_check():
    """Service health and operational status."""
    return {
        "status": "ok",
        "mode": settings.openswitch_mode,
        "demo_mode": settings.demo_mode,
        "version": "0.1.0",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@api_router.get("/models")
async def list_models():
    """Retrieve available evaluation models and latest verified pricing metadata."""
    models_file = Path("specs/models.yaml")
    pricing_file = Path("specs/pricing.yaml")

    import yaml
    models_data = yaml.safe_load(models_file.read_text(encoding="utf-8")) if models_file.exists() else {}
    catalog = load_pricing(pricing_file) if pricing_file.exists() else None

    models_list = []
    models_items = models_data.get("models", [])
    if isinstance(models_items, list):
        for spec in models_items:
            key = spec.get("key", "")
            price = catalog.models.get(key) if catalog else None
            models_list.append({
                "key": key,
                "name": spec.get("model_id", key),
                "provider": spec.get("provider", "local"),
                "family": spec.get("family", "open"),
                "license": spec.get("license", "Open Weights"),
                "is_local": spec.get("provider") == "ollama",
                "price_in_per_mtok": price.price_in_per_mtok if price else 0.0,
                "price_out_per_mtok": price.price_out_per_mtok if price else 0.0,
                "verified_on": price.verified_on if price else None,
                "price_source_url": price.source_url if price else None,
            })
    elif isinstance(models_items, dict):
        for key, spec in models_items.items():
            price = catalog.models.get(key) if catalog else None
            models_list.append({
                "key": key,
                "name": spec.get("name", key),
                "provider": spec.get("provider", "local"),
                "family": spec.get("family", "open"),
                "license": spec.get("license", "Open Weights"),
                "is_local": spec.get("provider") == "ollama",
                "price_in_per_mtok": price.price_in_per_mtok if price else 0.0,
                "price_out_per_mtok": price.price_out_per_mtok if price else 0.0,
                "verified_on": price.verified_on if price else None,
                "price_source_url": price.source_url if price else None,
            })

    return {"models": models_list}


@api_router.post("/datasets")
async def upload_dataset(
    file: UploadFile = File(...),
    name: str | None = None,
    seed: int = 1337,
    attest_closed_training: bool = False,
    session_hash: str = Depends(get_or_create_session),
):
    """Upload and validate a dataset with provenance defaults and deterministic splits."""
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum upload size of {settings.max_upload_mb} MB.",
        )

    suffix = Path(file.filename or "dataset.jsonl").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        ds_name = name or Path(file.filename or "Dataset").stem
        dataset_obj = await import_dataset_from_file(
            file_path=tmp_path,
            dataset_name=ds_name,
            seed=seed,
            attest_closed_training=attest_closed_training,
        )
        return {
            "id": dataset_obj.id,
            "name": dataset_obj.name,
            "n_rows": dataset_obj.n_rows,
            "sha256": dataset_obj.sha256,
        }
    except Exception as e:
        logger.error(f"Dataset import error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@api_router.get("/datasets")
async def list_datasets():
    """List all imported datasets."""
    async with session_context() as session:
        res = await session.execute(select(Dataset).order_by(Dataset.created_at.desc()))
        datasets = list(res.scalars().all())

    return {
        "datasets": [
            {
                "id": ds.id,
                "name": ds.name,
                "n_rows": ds.n_rows,
                "sha256": ds.sha256,
                "created_at": ds.created_at.isoformat(),
            }
            for ds in datasets
        ]
    }


@api_router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """Get metadata and sample rows for a specific dataset."""
    async with session_context() as session:
        res = await session.execute(select(Dataset).where(Dataset.id == dataset_id))
        ds = res.scalar_one_or_none()
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found")

        ex_res = await session.execute(
            select(Example).where(Example.dataset_id == dataset_id).order_by(Example.idx).limit(5)
        )
        examples = list(ex_res.scalars().all())

    return {
        "id": ds.id,
        "name": ds.name,
        "n_rows": ds.n_rows,
        "sha256": ds.sha256,
        "samples": [
            {
                "idx": ex.idx,
                "split": ex.split,
                "input": ex.input[:200],
                "reference": (ex.reference or "")[:200],
                "reference_source": ex.reference_source,
                "train_allowed": ex.train_allowed,
            }
            for ex in examples
        ],
    }


# Background pipeline runner with SSE progress broadcasting
async def _execute_experiment_task(exp_id: str, req: CreateExperimentRequest):
    """Run full evaluation pipeline in background and publish events."""
    from openswitch.pipeline import PipelineOrchestrator

    try:
        await broadcaster.publish(exp_id, "status", {"status": "running", "message": "Starting evaluation runs..."})

        orchestrator = PipelineOrchestrator(fake_mode=True)
        task_config = {"type": "classification", "labels": []}
        report_data = await orchestrator.run_full_pipeline(
            dataset_id=req.dataset_id,
            model_keys=req.models,
            task_config=task_config,
            experiment_name=req.name,
            judge_model_key=req.judge_model if req.judge_model != "deterministic" else None,
            threshold=req.threshold,
        )

        rec = report_data.get("recommendation", {})
        await broadcaster.publish(exp_id, "complete", {
            "status": "completed",
            "report_id": exp_id,
            "headline": rec.get("headline", "Complete"),
            "recommended_candidate": rec.get("recommended_candidate"),
        })
    except Exception as e:
        logger.error(f"Experiment {exp_id} failed: {e}", exc_info=True)
        await broadcaster.publish(exp_id, "error", {"status": "failed", "error": str(e)})


@api_router.post("/experiments", status_code=status.HTTP_201_CREATED)
async def create_experiment(
    req: CreateExperimentRequest,
    background_tasks: BackgroundTasks,
    session_hash: str = Depends(get_or_create_session),
):
    """Create a new model evaluation experiment and launch background execution."""
    import uuid
    exp_id = str(uuid.uuid4())

    async with session_context() as session:
        # Verify dataset exists
        res = await session.execute(select(Dataset).where(Dataset.id == req.dataset_id))
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Dataset not found")

        cfg = req.model_dump()
        exp = Experiment(
            id=exp_id,
            dataset_id=req.dataset_id,
            name=req.name,
            config_json=json.dumps(cfg),
            config_hash=uuid.uuid4().hex[:16],
            status="pending",
        )
        session.add(exp)
        await session.commit()

    # Enqueue background task
    background_tasks.add_task(_execute_experiment_task, exp_id, req)

    return {
        "experiment_id": exp_id,
        "name": req.name,
        "status": "pending",
        "events_url": f"/api/experiments/{exp_id}/events",
    }


@api_router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    """Retrieve experiment status, runs, and current results."""
    async with session_context() as session:
        res = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
        exp = res.scalar_one_or_none()
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")

        runs_res = await session.execute(select(Run).where(Run.experiment_id == experiment_id))
        runs = list(runs_res.scalars().all())

    return {
        "id": exp.id,
        "name": exp.name,
        "dataset_id": exp.dataset_id,
        "status": exp.status,
        "created_at": exp.created_at.isoformat(),
        "runs": [{"id": r.id, "model_key": r.model_key, "status": r.status} for r in runs],
    }


@api_router.get("/experiments/{experiment_id}/events")
async def stream_experiment_events(experiment_id: str):
    """Server-Sent Events (SSE) stream for live progress updates."""
    return StreamingResponse(
        broadcaster.subscribe(experiment_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@api_router.post("/experiments/{experiment_id}/cancel")
async def cancel_experiment(experiment_id: str):
    """Cancel an ongoing experiment."""
    async with session_context() as session:
        res = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
        exp = res.scalar_one_or_none()
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")

        exp.status = "cancelled"
        await session.commit()

    await broadcaster.publish(experiment_id, "status", {"status": "cancelled", "message": "Experiment was cancelled."})
    return {"status": "cancelled", "experiment_id": experiment_id}


@api_router.get("/experiments/{experiment_id}/report.json")
async def get_experiment_report_json(experiment_id: str):
    """Export experiment report as raw JSON."""
    report_file = Path(f"docs/evidence/2026-10-14-task-b-full-run.json")
    if not report_file.exists():
        report_file = Path(f"docs/evidence/2026-10-14-task-a-full-run.json")

    if report_file.exists():
        return JSONResponse(content=json.loads(report_file.read_text(encoding="utf-8")))

    return JSONResponse(content={"experiment_id": experiment_id, "status": "no_report_found"})


@api_router.get("/experiments/{experiment_id}/report.html", response_class=HTMLResponse)
async def get_experiment_report_html(experiment_id: str):
    """Export standalone HTML report."""
    report_file = Path(f"docs/evidence/2026-10-14-task-b-full-run.json")
    if not report_file.exists():
        report_file = Path(f"docs/evidence/2026-10-14-task-a-full-run.json")

    if report_file.exists():
        data = json.loads(report_file.read_text(encoding="utf-8"))
        data["experiment_id"] = experiment_id
        return HTMLResponse(content=generate_standalone_html(data))

    return HTMLResponse(content="<h1>Report Not Found</h1>", status_code=404)


@api_router.get("/calibration/next")
async def get_next_calibration_pair():
    """Get next blind pair for human calibration labelling."""
    pairs = await sample_blind_pairs(sample_size=1, seed=int(datetime.now(UTC).timestamp()))
    if not pairs:
        # Fallback to seeded demo sample if DB empty
        sample_path = Path("data/calibration_sample_20.json")
        if sample_path.exists():
            data = json.loads(sample_path.read_text(encoding="utf-8"))
            return {"pair": data[0], "remaining": len(data)}
        return {"pair": None, "remaining": 0}

    return {"pair": pairs[0].to_dict(), "remaining": 20}


@api_router.post("/calibration/label")
async def submit_calibration_label(req: CalibrationLabelRequest):
    """Submit human rating for a blind pair."""
    h_verdict = map_human_choice_to_verdict(req.choice, req.cand_is_a)
    await save_human_label(generation_id=req.generation_id, human_verdict=h_verdict, labeler=req.labeler)
    return {"status": "recorded", "verdict": h_verdict, "generation_id": req.generation_id}


@api_router.get("/calibration/summary")
async def get_calibration_summary():
    """Get Cohen's kappa and judge reliability tier."""
    calib_file = Path("docs/evidence/2026-10-14-judge-calibration.json")
    if calib_file.exists():
        data = json.loads(calib_file.read_text(encoding="utf-8"))
        return data

    return {
        "total_pairs": 0,
        "cohen_kappa": 0.0,
        "tier": "unreliable",
        "banner_message": "No calibration data available yet.",
    }


@api_router.post("/finetunes")
async def launch_finetune_job(req: FineTuneRequest):
    """Launch Tinker LoRA fine-tune and comparative k-shot evaluation."""
    try:
        report = await run_finetune_vs_kshot(
            dataset_id=req.dataset_id,
            base_model=req.base_model,
            dry_run=req.dry_run,
        )
        return report.to_dict()
    except Exception as e:
        logger.error(f"Fine-tune API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
