"""Command-line interface for Open-Switch."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from openswitch.config import settings
from openswitch.datasets.importer import DatasetImporter
from openswitch.db import session_context
from openswitch.judge.calibration import (
    calculate_agreement,
    calculate_cohen_kappa,
    compute_confusion_matrix,
    judge_reliability_tier,
)
from openswitch.models import init_db
from openswitch.pipeline import PipelineOrchestrator
from openswitch.pricing import load_pricing
from openswitch.providers.base import ChatResult
from openswitch.providers.fake import FakeProvider
from openswitch.providers.openai_compat import OpenAICompatProvider

app = typer.Typer(
    name="openswitch",
    help="Evaluate whether open-weight models can safely replace expensive closed LLMs.",
    add_completion=False,
)
models_app = typer.Typer(help="Manage and probe model providers.")
app.add_typer(models_app, name="models")

console = Console(force_terminal=True)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            getattr(sys.stderr, "reconfigure")(encoding="utf-8")
    except Exception:
        pass


@app.command()
def init():
    """Initialize Open-Switch database and local storage."""
    console.print("[bold green]Initializing Open-Switch database and directories...[/bold green]")

    async def _init():
        await init_db()

    asyncio.run(_init())
    console.print(
        f"[green][OK] Database initialized successfully at:[/green] {settings.database_url}"
    )
    console.print(f"[green][OK] Storage directory ready at:[/green] {settings.data_dir.resolve()}")


@app.command("import")
def import_cmd(
    dataset_path: Path = typer.Argument(..., help="Path to JSONL or CSV dataset file."),
    name: str | None = typer.Option(None, "--name", "-n", help="Dataset name."),
    seed: int = typer.Option(1337, "--seed", "-s", help="Random seed for splitting."),
    attestation: bool = typer.Option(
        False,
        "--attest-closed-training",
        help="Attest that training on closed API references is legally permitted.",
    ),
):
    """Import and validate a dataset with provenance tracking and deterministic splits."""
    console.print(f"[bold cyan]Importing dataset from {dataset_path}...[/bold cyan]")
    importer = DatasetImporter(seed=seed, attestation_granted=attestation)

    try:
        imported = importer.import_from_file(dataset_path, name=name)
    except Exception as e:
        console.print(f"[bold red]Import failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[green][OK] Successfully imported:[/green] {imported.name}")
    console.print(f"  • Total rows: {len(imported.rows)}")
    console.print(f"  • SHA256: {imported.sha256}")
    console.print(
        f"  • Splits: Train={imported.split_counts['train']} | "
        f"Dev={imported.split_counts['dev']} | "
        f"Test={imported.split_counts['test']}"
    )

    if imported.pii_warnings:
        console.print(
            f"[yellow][WARN] Detected {len(imported.pii_warnings)} potential PII tokens:[/yellow]"
        )
        for w in imported.pii_warnings[:5]:
            console.print(f"   - Row {w.row_idx} ({w.example_id}): [{w.pii_type}] {w.preview}")
        if len(imported.pii_warnings) > 5:
            console.print(f"   ... and {len(imported.pii_warnings) - 5} more")

    if imported.split_warnings:
        for sw in imported.split_warnings:
            console.print(f"[yellow][WARN] {sw}[/yellow]")

    async def _save():
        async with session_context() as session:
            await importer.save_to_db(session, imported)

    asyncio.run(_save())
    console.print("[bold green][OK] Persisted to SQLite database.[/bold green]")


@app.command("run")
def run_cmd(
    dataset_id: str = typer.Option(
        ..., "--dataset", "-d", help="ID of imported dataset to evaluate."
    ),
    models: str = typer.Option(
        "digitalocean/gemma-2-9b,ollama/gemma2:2b",
        "--models",
        "-m",
        help="Comma-separated model keys to evaluate.",
    ),
    task_config_path: Path = typer.Option(
        Path("specs/task.yaml"),
        "--task",
        "-t",
        help="Path to task YAML specification.",
    ),
    name: str | None = typer.Option(None, "--name", "-n", help="Optional experiment name."),
    judge_model: str | None = typer.Option(
        None, "--judge-model", "-j", help="Judge model key (for free text/rubric tasks)."
    ),
    fake: bool = typer.Option(
        False,
        "--fake",
        help="Run evaluation using mock providers (offline verification / dry-run).",
    ),
    output_json: Path | None = typer.Option(
        None, "--output-json", "-o", help="Path to write full results JSON."
    ),
    volume: int = typer.Option(50_000, "--volume", "-v", help="Monthly request volume projection."),
    threshold: float = typer.Option(
        0.85, "--threshold", help="Primary metric lower CI threshold for migration."
    ),
    baseline_cost: float = typer.Option(
        0.015, "--baseline-cost", help="Baseline incumbent cost per request ($)."
    ),
):
    """Run an end-to-end evaluation comparing open models against incumbent references."""
    console.print(
        f"[bold cyan]Starting Open-Switch evaluation on dataset {dataset_id}...[/bold cyan]"
    )

    task_cfg: dict[str, Any] = {}
    if task_config_path.exists():
        with open(task_config_path, encoding="utf-8") as f:
            task_cfg = yaml.safe_load(f) or {}
    else:
        task_cfg = {
            "name": "default_task",
            "type": "classification",
            "primary_metric": "label_accuracy",
            "labels": ["billing", "tech", "account"],
        }

    model_keys = [m.strip() for m in models.split(",") if m.strip()]
    orchestrator = PipelineOrchestrator(fake_mode=fake)

    async def _execute():
        return await orchestrator.run_full_pipeline(
            dataset_id=dataset_id,
            model_keys=model_keys,
            task_config=task_cfg,
            experiment_name=name,
            judge_model_key=judge_model,
            monthly_volume=volume,
            baseline_cost_per_request=baseline_cost,
            threshold=threshold,
            output_json_path=output_json,
        )

    try:
        results = asyncio.run(_execute())
    except Exception as e:
        console.print(f"[bold red]Evaluation failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Display results
    rec = results["recommendation"]
    dec = rec["decision"]

    if dec == "switch_recommended":
        color = "green"
    elif dec == "switch_after_finetune":
        color = "cyan"
    elif dec == "insufficient_data":
        color = "red"
    else:
        color = "yellow"

    console.print(
        Panel(
            f"[bold]{rec['headline']}[/bold]\n\n{rec['details']}",
            title="Migration Recommendation",
            border_style=color,
        )
    )

    # Candidate table
    table = Table(title="Model Evaluation & Cost Comparison")
    table.add_column("Model Key", style="bold white")
    table.add_column("Primary Metric (95% CI)", justify="center")
    table.add_column("Error Rate", justify="right")
    table.add_column("Latency p50", justify="right")
    table.add_column("Cost / 1k", justify="right")
    table.add_column("Monthly Savings", justify="right", style="green")

    for k, m in results["models"].items():
        pm = m["primary_metric"]
        pm_str = f"{pm['point_estimate']:.1%} [{pm['ci_lower']:.1%}, {pm['ci_upper']:.1%}]"
        err_str = f"{m['error_rate']:.1%}"
        lat_str = f"{m['latency'].get('p50', 0):.0f} ms"
        c_1k = f"${m['cost_summary']['cost_per_1k']:.4f}"
        sav = f"${m['monthly_projection']['monthly_savings']:,.2f} ({m['monthly_projection']['savings_pct']:.0f}%)"
        table.add_row(k, pm_str, err_str, lat_str, c_1k, sav)

    console.print(table)

    if results.get("anomalies_detected"):
        console.print("\n[bold yellow]Telemetry Anomalies Caught:[/bold yellow]")
        for a in results["anomalies_detected"]:
            console.print(f"  • {a}")

    if output_json:
        console.print(f"\n[green][OK] Full results JSON exported to:[/green] {output_json}")


@app.command("judge")
def judge_cmd(
    rubric: str = typer.Option(..., "--rubric", "-r", help="Rubric text for the judge comparison."),
    input_text: str = typer.Option(..., "--input", "-i", help="Task input text."),
    candidate: str = typer.Option(..., "--candidate", "-c", help="Candidate model response."),
    reference: str = typer.Option(
        ..., "--reference", help="Incumbent baseline reference response."
    ),
    judge_model: str = typer.Option("gemma-2-9b", "--model", "-m", help="Judge model ID."),
    fake: bool = typer.Option(False, "--fake", help="Run with mock judge."),
):
    """Run a single swapped-order pairwise judge comparison."""
    from openswitch.judge.evaluator import PairwiseJudge
    from openswitch.providers.registry import registry

    if fake and judge_model not in registry:
        registry.register(
            judge_model,
            FakeProvider(default_response='{"verdict": "A", "reason": "Better adherence"}'),
        )

    judge = PairwiseJudge()
    provider = registry.get(judge_model)

    async def _judge():
        return await judge.evaluate_pair(
            provider=provider,
            judge_model_id=judge_model,
            judge_pricing_key=judge_model,
            rubric=rubric,
            input_text=input_text,
            candidate_text=candidate,
            reference_text=reference,
        )

    res = asyncio.run(_judge())
    console.print(f"[bold]Final Verdict:[/bold] {res.final.upper()}")
    console.print(f"  • Call AB (Candidate in A): {res.verdict_ab} ({res.rationale_ab})")
    console.print(f"  • Call BA (Candidate in B): {res.verdict_ba} ({res.rationale_ba})")
    console.print(f"  • Total Tokens: {res.tokens_in} in / {res.tokens_out} out")


@app.command("calibrate")
def calibrate_cmd(
    labels_file: Path = typer.Option(
        ...,
        "--file",
        "-f",
        help="Path to JSON file containing paired labels: [{'human': 'win', 'judge': 'win'}, ...].",
    ),
):
    """Calculate Cohen's kappa and judge reliability gating against human ground truth."""
    if not labels_file.exists():
        console.print(f"[bold red]File not found:[/bold red] {labels_file}")
        raise typer.Exit(code=1)

    with open(labels_file, encoding="utf-8") as f:
        data = json.load(f)

    human = [d["human"] for d in data]
    judge = [d["judge"] for d in data]

    agreement = calculate_agreement(human, judge)
    kappa = calculate_cohen_kappa(human, judge)
    tier, banner = judge_reliability_tier(kappa)
    cm = compute_confusion_matrix(human, judge)

    console.print(f"[bold]Annotated Pairs:[/bold] {len(human)}")
    console.print(f"[bold]Observed Agreement:[/bold] {agreement:.1%}")
    console.print(f"[bold]Cohen's Kappa:[/bold] {kappa:.3f}")

    border = "green" if tier == "reliable" else ("yellow" if tier == "moderate" else "red")
    console.print(Panel(banner, title=f"Judge Reliability: {tier.upper()}", border_style=border))

    # Confusion matrix
    categories = sorted(cm.keys())
    cm_table = Table(title="Confusion Matrix (Human vs Judge)")
    cm_table.add_column("Human \\ Judge", style="bold")
    for cat in categories:
        cm_table.add_column(cat, justify="center")

    for h_cat in categories:
        row_vals = [str(cm[h_cat].get(j_cat, 0)) for j_cat in categories]
        cm_table.add_row(h_cat, *row_vals)

    console.print(cm_table)


@app.command("report")
def report_cmd(
    json_path: Path = typer.Option(..., "--json", "-j", help="Path to experiment results JSON."),
    html_output: Path | None = typer.Option(
        None, "--output-html", "-o", help="Path to save HTML report."
    ),
    open_browser: bool = typer.Option(False, "--open", help="Open HTML report in browser."),
):
    """Generate and display summary report from an experiment results JSON."""
    if not json_path.exists():
        console.print(f"[bold red]Results file not found:[/bold red] {json_path}")
        raise typer.Exit(code=1)

    with open(json_path, encoding="utf-8") as f:
        res = json.load(f)

    rec = res.get("recommendation", {})
    console.print(
        Panel(f"[bold]{rec.get('headline')}[/bold]\n\n{rec.get('details')}", title="Report Summary")
    )

    if html_output:
        # Generate standalone HTML
        html_content = f"""<!DOCTYPE html>
<html>
<head><title>Open-Switch Report: {res.get("experiment_id")}</title></head>
<body style="font-family:sans-serif;max-width:800px;margin:2rem auto;padding:1rem;">
<h1>Open-Switch Evaluation Report</h1>
<p><strong>Commit:</strong> {res.get("git_commit")} | <strong>Date:</strong> {res.get("created_at")}</p>
<h2>{rec.get("headline")}</h2>
<p>{rec.get("details")}</p>
</body>
</html>"""
        html_output.parent.mkdir(parents=True, exist_ok=True)
        with open(html_output, "w", encoding="utf-8") as f:
            f.write(html_content)
        console.print(f"[green][OK] Standalone HTML report saved to:[/green] {html_output}")

        if open_browser:
            import webbrowser

            webbrowser.open(f"file://{html_output.resolve()}")


@app.command("regen")
def regen_cmd(
    teacher: str = typer.Option(..., "--teacher", help="Open teacher model key for regeneration."),
    dataset_id: str = typer.Option(..., "--dataset", "-d", help="Dataset ID."),
    fake: bool = typer.Option(False, "--fake", help="Run with mock teacher model."),
):
    """Run teacher regeneration on train split using an open teacher model."""
    from openswitch.datasets.regen import regenerate_teacher_references
    from openswitch.providers.fake import FakeProvider
    from openswitch.providers.registry import registry

    if fake and teacher not in registry:
        registry.register(
            teacher, FakeProvider(default_response="Teacher regenerated reference response.")
        )

    console.print(
        f"[bold cyan]Regenerating train references using open teacher {teacher}...[/bold cyan]"
    )

    async def _regen():
        return await regenerate_teacher_references(dataset_id=dataset_id, teacher_model_key=teacher)

    summary = asyncio.run(_regen())
    console.print("[green][OK] Teacher regeneration complete![/green]")
    console.print(f"  • Total train rows: {summary.total_train_rows}")
    console.print(f"  • Regenerated rows: {summary.regenerated_count}")
    console.print(f"  • Teacher model: {summary.teacher_model_key} ({summary.teacher_license})")


@app.command("finetune")
def finetune_cmd(
    base: str = typer.Option(..., "--base", help="Base model key for fine-tuning."),
    dataset_id: str = typer.Option(..., "--dataset", "-d", help="Dataset ID."),
    dry_run: bool = typer.Option(
        True, "--dry-run/--execute", help="Run dry-run simulation or real Tinker job."
    ),
    compare_kshot: bool = typer.Option(
        True, "--compare-kshot/--no-kshot", help="Compare against zero-shot and k-shot baseline."
    ),
    out: Path | None = typer.Option(
        None, "--out", "-o", help="Path to write comparison JSON evidence."
    ),
):
    """Launch LoRA fine-tuning and compare against zero-shot and k-shot baselines."""
    from rich.markdown import Markdown
    from openswitch.finetune.eval import run_finetune_vs_kshot

    console.print(
        f"[bold cyan]Evaluating fine-tuning on base {base} for dataset {dataset_id}...[/bold cyan]"
    )

    try:
        report = asyncio.run(
            run_finetune_vs_kshot(
                dataset_id=dataset_id,
                base_model=base,
                dry_run=dry_run,
            )
        )
        console.print("[green][OK] Fine-tune and baseline comparison complete![/green]\n")
        console.print(Markdown(report.to_markdown_table()))
        console.print(f"\n[bold yellow]Recommendation:[/bold yellow] {report.recommendation}")
        if report.breakeven_volume_kshot_vs_ft:
            console.print(
                f"[bold cyan]Break-even volume:[/bold cyan] {report.breakeven_volume_kshot_vs_ft:,} requests"
            )

        if out:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
            console.print(f"[dim]Saved report to {out}[/dim]")

    except Exception as e:
        console.print(f"[bold red]Fine-tune evaluation failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@models_app.command("probe")
def probe_models(
    models_config: Path = typer.Option(
        Path("specs/models.yaml"),
        "--config",
        "-c",
        help="Path to models YAML config.",
    ),
    fake: bool = typer.Option(
        False,
        "--fake",
        help="Probe using mock providers (offline verification).",
    ),
):
    """Probe configured models and providers, measuring TTFT, latency, and token reporting."""
    console.print(f"[bold cyan]Probing models from {models_config}...[/bold cyan]")

    if not models_config.exists():
        console.print(f"[bold red]Config file not found:[/bold red] {models_config}")
        raise typer.Exit(code=1)

    with open(models_config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    providers_cfg = cfg.get("providers", {})
    models_list = cfg.get("models", [])

    table = Table(title="Model Provider Telemetry Probe")
    table.add_column("Key", style="bold white")
    table.add_column("Provider", style="cyan")
    table.add_column("Model ID", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("TTFT (ms)", justify="right")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Tokens (in/out)", justify="right")
    table.add_column("Details", style="dim")

    async def _probe():
        for m in models_list:
            key = m["key"]
            provider_name = m["provider"]
            model_id = m["model_id"]

            if fake or provider_name == "fake":
                p = FakeProvider(
                    default_response=f"PONG from {key}",
                    tokens_in=12,
                    tokens_out=4,
                    latency_ms=45.0,
                    ttft_ms=18.0,
                )
            else:
                p_cfg = providers_cfg.get(provider_name, {})
                base_url = p_cfg.get("base_url")
                if not base_url or base_url == "UNVERIFIED":
                    table.add_row(
                        key,
                        provider_name,
                        model_id,
                        "[yellow]UNVERIFIED[/yellow]",
                        "-",
                        "-",
                        "-",
                        "Base URL missing",
                    )
                    continue

                import os

                api_key_env = p_cfg.get("api_key_env", "")
                api_key = os.getenv(api_key_env, "") if api_key_env else ""

                if api_key_env and not api_key:
                    table.add_row(
                        key,
                        provider_name,
                        model_id,
                        "[yellow]KEY_MISSING[/yellow]",
                        "-",
                        "-",
                        "-",
                        f"Set {api_key_env} in .env",
                    )
                    continue

                try:
                    p = OpenAICompatProvider(
                        base_url=base_url,
                        api_key=api_key,
                        provider_name=provider_name,
                        timeout=5.0,
                        max_retries=1,
                    )
                except Exception as e:
                    table.add_row(
                        key, provider_name, model_id, "[red]CONFIG_ERR[/red]", "-", "-", "-", str(e)
                    )
                    continue

            try:
                res: ChatResult = await p.chat(
                    model=model_id,
                    messages=[{"role": "user", "content": "Reply with 'PONG'"}],
                    max_tokens=10,
                    stream=True,
                )
                ttft_str = f"{res.ttft_ms:.1f}" if res.ttft_ms is not None else "N/A"
                lat_str = f"{res.latency_ms:.1f}"
                tok_str = f"{res.tokens_in}/{res.tokens_out}"
                table.add_row(
                    key,
                    provider_name,
                    model_id,
                    "[green]ONLINE[/green]",
                    ttft_str,
                    lat_str,
                    tok_str,
                    res.text.strip()[:20],
                )
            except Exception as e:
                table.add_row(
                    key, provider_name, model_id, "[red]OFFLINE[/red]", "-", "-", "-", str(e)[:30]
                )

    asyncio.run(_probe())
    console.print(table)


@app.command("pricing")
def show_pricing(
    pricing_path: Path = typer.Option(
        Path("specs/pricing.yaml"),
        "--path",
        "-p",
        help="Path to pricing YAML.",
    ),
):
    """Display verified token prices and staleness status."""
    catalog = load_pricing(pricing_path)

    table = Table(title=f"Pricing Catalog (v{catalog.version})")
    table.add_column("Model Key", style="bold white")
    table.add_column("Price In ($/Mtok)", justify="right")
    table.add_column("Price Out ($/Mtok)", justify="right")
    table.add_column("Verified On", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Source", style="dim")

    for k, p in catalog.models.items():
        status = "[red]STALE[/red]" if p.is_stale else "[green]CURRENT[/green]"
        table.add_row(
            k,
            f"${p.price_in_per_mtok:.2f}",
            f"${p.price_out_per_mtok:.2f}",
            p.verified_on or "None",
            status,
            p.source_url or "N/A",
        )

    console.print(table)
    if catalog.warnings:
        console.print(f"\n[bold yellow]Warnings ({len(catalog.warnings)}):[/bold yellow]")
        for w in catalog.warnings:
            console.print(f"  • {w}")


@app.command("serve")
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
):
    """Start Open-Switch web server."""
    import uvicorn

    console.print(f"[bold green]Starting Open-Switch server on {host}:{port}...[/bold green]")
    uvicorn.run("openswitch.web.app:app", host=host, port=port, reload=False)
