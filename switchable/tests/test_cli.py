import json
from pathlib import Path

from typer.testing import CliRunner

from openswitch.cli import app

runner = CliRunner()


def test_cli_init_and_pricing():
    res_init = runner.invoke(app, ["init"])
    assert res_init.exit_code == 0
    assert "Database initialized" in res_init.output

    res_pricing = runner.invoke(app, ["pricing"])
    assert res_pricing.exit_code == 0
    assert "Pricing Catalog" in res_pricing.output


def test_cli_import_and_run_end_to_end(tmp_path: Path):
    # 1. Create small sample dataset JSONL
    dataset_file = tmp_path / "sample_task.jsonl"
    rows = []
    for i in range(25):
        rows.append(
            {
                "id": f"ex-{i}",
                "input": f"Sample ticket text {i}",
                "reference": "billing" if i % 2 == 0 else "tech",
                "reference_source": "human",
                "train_allowed": True,
            }
        )
    with open(dataset_file, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    import uuid

    unique_ds_name = f"test-banking-{uuid.uuid4().hex[:8]}"

    # 2. Import dataset
    import_res = runner.invoke(app, ["import", str(dataset_file), "--name", unique_ds_name])
    assert import_res.exit_code == 0
    assert "Successfully imported" in import_res.output

    # Get dataset ID from DB or query
    import asyncio

    from sqlalchemy import select

    from openswitch.db import session_context
    from openswitch.models import Dataset

    async def _get_ds_id():
        async with session_context() as session:
            res = await session.execute(select(Dataset).where(Dataset.name == unique_ds_name))
            return res.scalar_one().id

    ds_id = asyncio.run(_get_ds_id())

    # 3. Run evaluation in fake mode
    output_json = tmp_path / "eval_results.json"
    run_res = runner.invoke(
        app,
        [
            "run",
            "--dataset",
            ds_id,
            "--models",
            "digitalocean/gemma-2-9b,ollama/gemma2:2b",
            "--fake",
            "--output-json",
            str(output_json),
        ],
    )

    assert run_res.exit_code == 0
    assert "Migration Recommendation" in run_res.output
    assert "Model Evaluation & Cost Comparison" in run_res.output
    assert output_json.exists()

    # Verify JSON content
    with open(output_json, encoding="utf-8") as f:
        data = json.load(f)

    assert "experiment_id" in data
    assert "recommendation" in data
    assert "models" in data
    assert "digitalocean/gemma-2-9b" in data["models"]
    assert "ollama/gemma2:2b" in data["models"]
    assert "primary_metric" in data["models"]["digitalocean/gemma-2-9b"]


def test_cli_judge_and_calibrate(tmp_path: Path):
    # Test judge command
    judge_res = runner.invoke(
        app,
        [
            "judge",
            "--rubric",
            "Correctness and brevity",
            "--input",
            "How do I reset my password?",
            "--candidate",
            "Click forgot password on the login screen.",
            "--reference",
            "Use the password reset link.",
            "--fake",
        ],
    )
    assert judge_res.exit_code == 0
    assert "Final Verdict" in judge_res.output

    # Test calibrate command
    labels_file = tmp_path / "calibration_labels.json"
    labels_data = [
        {"human": "win", "judge": "win"},
        {"human": "loss", "judge": "loss"},
        {"human": "tie", "judge": "tie"},
        {"human": "win", "judge": "win"},
    ]
    with open(labels_file, "w", encoding="utf-8") as f:
        json.dump(labels_data, f)

    out_calib = tmp_path / "calib_out.json"
    calib_res = runner.invoke(
        app, ["calibrate", "--file", str(labels_file), "--out", str(out_calib)]
    )
    assert calib_res.exit_code == 0
    assert "Cohen's Kappa" in calib_res.output
    assert "Confusion Matrix" in calib_res.output


def test_cli_report_generation(tmp_path: Path):
    sample_json = tmp_path / "sample_results.json"
    html_out = tmp_path / "report.html"

    with open(sample_json, "w", encoding="utf-8") as f:
        json.dump(
            {
                "experiment_id": "exp-test-123",
                "git_commit": "abcdef",
                "created_at": "2026-10-14T04:00:00Z",
                "recommendation": {
                    "headline": "Safe switch recommended: Gemma 2 9B",
                    "details": "Meets 85% threshold with 95% CI.",
                },
            },
            f,
        )

    rep_res = runner.invoke(
        app,
        [
            "report",
            "--json",
            str(sample_json),
            "--output-html",
            str(html_out),
        ],
    )
    assert rep_res.exit_code == 0
    assert html_out.exists()
    assert "Report Summary" in rep_res.output
