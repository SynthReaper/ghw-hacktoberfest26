"""Integration tests for FastAPI REST endpoints, SSE streams, session cookies, and Web UI (T-024, T-025)."""

import asyncio
import json
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from openswitch.db import session_context
from openswitch.models import Dataset, Example, Session, init_db
from openswitch.web.app import app
from openswitch.web.events import broadcaster


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Verify /api/health returns 200 and mode status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "version" in data


@pytest.mark.asyncio
async def test_session_cookie_creation():
    """Verify session cookie is set on request and recorded in the database."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        cookies = res.cookies
        assert "openswitch_session" in cookies
        token = cookies["openswitch_session"]
        assert len(token) >= 32

    # Verify session persisted in SQLite
    import hashlib
    t_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    async with session_context() as session:
        db_res = await session.execute(select(Session).where(Session.token_hash == t_hash))
        assert db_res.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_models_endpoint():
    """Verify /api/models returns model catalog with pricing info."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/models")
        assert res.status_code == 200
        data = res.json()
        assert "models" in data
        assert len(data["models"]) > 0
        m = data["models"][0]
        assert "key" in m
        assert "provider" in m
        assert "price_in_per_mtok" in m


@pytest.mark.asyncio
async def test_dataset_upload_and_retrieve():
    """Verify uploading a JSONL dataset via /api/datasets and retrieving it."""
    transport = ASGITransport(app=app)
    jsonl_content = (
        '{"id": "up-1", "input": "Lost card please help", "reference": "card_lost"}\n'
        '{"id": "up-2", "input": "App won\'t open crash", "reference": "app_crash"}\n'
        '{"id": "up-3", "input": "Transfer fee unexpected", "reference": "fee_inquiry"}\n'
    )

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("test_upload.jsonl", jsonl_content.encode("utf-8"), "application/jsonlines")}
        res = await client.post("/api/datasets?name=WebUploadDataset", files=files)
        assert res.status_code == 200
        ds_data = res.json()
        assert ds_data["name"] == "WebUploadDataset"
        assert ds_data["n_rows"] == 3
        ds_id = ds_data["id"]

        # List datasets
        list_res = await client.get("/api/datasets")
        assert list_res.status_code == 200
        assert any(d["id"] == ds_id for d in list_res.json()["datasets"])

        # Get specific dataset with sample rows
        get_res = await client.get(f"/api/datasets/{ds_id}")
        assert get_res.status_code == 200
        detail = get_res.json()
        assert detail["id"] == ds_id
        assert len(detail["samples"]) == 3


@pytest.mark.asyncio
async def test_experiment_creation_and_sse_events():
    """Verify creating an experiment and streaming SSE events."""
    ds_id = f"test_ds_{uuid.uuid4().hex[:8]}"

    # Seed dataset
    async with session_context() as session:
        ds = Dataset(
            id=ds_id,
            name="SSE Test Dataset",
            task_json=json.dumps({"task": "classification"}),
            n_rows=2,
            sha256="dummy",
            seed=1337,
        )
        session.add(ds)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        exp_req = {
            "name": "Integration Test Experiment",
            "dataset_id": ds_id,
            "models": ["gemma-2b-local"],
            "judge_model": "deterministic",
            "budget_limit_usd": 1.0,
            "threshold": 0.85,
        }
        res = await client.post("/api/experiments", json=exp_req)
        assert res.status_code == 201
        exp_data = res.json()
        exp_id = exp_data["experiment_id"]
        assert exp_id is not None
        assert exp_data["status"] == "pending"

        # Check experiment details endpoint
        get_res = await client.get(f"/api/experiments/{exp_id}")
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "Integration Test Experiment"

        # Test SSE event publishing and subscription
        events = []

        async def listen_events():
            async for chunk in broadcaster.subscribe(exp_id):
                events.append(chunk)
                if len(events) >= 2:
                    break

        listener_task = asyncio.create_task(listen_events())
        await asyncio.sleep(0.01)

        # Publish test event
        await broadcaster.publish(exp_id, "progress", {"pct": 50, "msg": "Halfway done"})
        await listener_task

        assert len(events) >= 2
        assert "event: ping" in events[0]
        assert "event: progress" in events[1]
        assert "Halfway done" in events[1]


@pytest.mark.asyncio
async def test_calibration_api_flow():
    """Verify /api/calibration/label records ratings and /api/calibration/summary returns tier."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit rating
        label_req = {
            "generation_id": str(uuid.uuid4()),
            "choice": "1",
            "cand_is_a": True,
            "labeler": "integration_tester",
        }
        res = await client.post("/api/calibration/label", json=label_req)
        assert res.status_code == 200
        assert res.json()["verdict"] == "win"

        # Check summary
        summary_res = await client.get("/api/calibration/summary")
        assert summary_res.status_code == 200
        data = summary_res.json()
        assert "cohen_kappa" in data
        assert "tier" in data


@pytest.mark.asyncio
async def test_web_ui_pages_render():
    """Verify all HTML UI routes return 200 with proper Swiss Technical precision headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ["/", "/models", "/calibrate", "/finetune"]:
            res = await client.get(path)
            assert res.status_code == 200
            assert "OPEN-SWITCH" in res.text
            assert "text/html" in res.headers["content-type"]
