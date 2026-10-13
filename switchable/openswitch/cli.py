"""Command-line interface for Open-Switch."""

import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
import yaml

from openswitch.config import settings
from openswitch.datasets.importer import DatasetImporter
from openswitch.db import session_context
from openswitch.models import init_db
from openswitch.pricing import load_pricing
from openswitch.providers.base import ChatResult, ProviderError
from openswitch.providers.fake import FakeProvider
from openswitch.providers.openai_compat import OpenAICompatProvider

app = typer.Typer(
    name="openswitch",
    help="Evaluate whether open-weight models can safely replace expensive closed LLMs.",
    add_completion=False,
)
models_app = typer.Typer(help="Manage and probe model providers.")
app.add_typer(models_app, name="models")

import sys
console = Console(force_terminal=True)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


@app.command()
def init():
    """Initialize Open-Switch database and local storage."""
    console.print("[bold green]Initializing Open-Switch database and directories...[/bold green]")

    async def _init():
        await init_db()

    asyncio.run(_init())
    console.print(f"[green][OK] Database initialized successfully at:[/green] {settings.database_url}")
    console.print(f"[green][OK] Storage directory ready at:[/green] {settings.data_dir.resolve()}")


@app.command("import")
def import_cmd(
    dataset_path: Path = typer.Argument(..., help="Path to JSONL or CSV dataset file."),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Dataset name."),
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
        console.print(f"[yellow][WARN] Detected {len(imported.pii_warnings)} potential PII tokens:[/yellow]")
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
            role = m.get("role", "candidate")

            # Check if fake mode requested or fake provider
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
                    table.add_row(key, provider_name, model_id, "[yellow]UNVERIFIED[/yellow]", "-", "-", "-", "Base URL missing")
                    continue

                import os
                api_key_env = p_cfg.get("api_key_env", "")
                api_key = os.getenv(api_key_env, "") if api_key_env else ""

                if api_key_env and not api_key:
                    table.add_row(key, provider_name, model_id, "[yellow]KEY_MISSING[/yellow]", "-", "-", "-", f"Set {api_key_env} in .env")
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
                    table.add_row(key, provider_name, model_id, "[red]CONFIG_ERR[/red]", "-", "-", "-", str(e))
                    continue

            # Send tiny probe message
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
                table.add_row(key, provider_name, model_id, "[red]OFFLINE[/red]", "-", "-", "-", str(e)[:30])

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
