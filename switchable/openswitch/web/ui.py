"""HTMX Web UI views: Swiss technical precision, zero JS build, keyboard accessible (T-025)."""

import html

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from openswitch.config import settings
from openswitch.db import session_context
from openswitch.models import Dataset
from openswitch.web.session import get_or_create_session

ui_router = APIRouter()


def layout(title: str, content: str, active_tab: str = "home") -> str:
    """Master Swiss layout with high-contrast monochrome typography and clean navigation."""
    nav_items = [
        ("home", "/", "Evaluate"),
        ("models", "/models", "Models & Pricing"),
        ("calibrate", "/calibrate", "Judge Calibration"),
        ("finetune", "/finetune", "LoRA Fine-Tune"),
    ]

    nav_links = "".join(
        [
            f'<a href="{url}" class="nav-link {"active" if tab == active_tab else ""}">{name}</a>'
            for tab, url, name in nav_items
        ]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Open-Switch — {html.escape(title)}</title>
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  <script src="https://unpkg.com/htmx.org@1.9.10/dist/ext/sse.js"></script>
  <style>
    :root {{
      --bg: #090a0f;
      --surface: #11131a;
      --surface-border: #1e2230;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #2563eb;
      --accent-hover: #1d4ed8;
      --green: #10b981;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      background: var(--bg);
      color: var(--text-main);
      font-family: var(--font-sans);
      margin: 0;
      padding: 0;
      line-height: 1.5;
    }}
    header {{
      background: rgba(17, 19, 26, 0.85);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--surface-border);
      position: sticky;
      top: 0;
      z-index: 50;
    }}
    .header-inner {{
      max-width: 1040px;
      margin: 0 auto;
      padding: 0.75rem 1.25rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .logo {{
      font-weight: 800;
      font-size: 1.1rem;
      letter-spacing: -0.03em;
      color: #fff;
      text-decoration: none;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .logo-badge {{
      background: var(--surface-border);
      color: #60a5fa;
      font-size: 0.75rem;
      font-family: var(--font-mono);
      padding: 2px 6px;
      border-radius: 4px;
    }}
    nav {{ display: flex; gap: 0.5rem; }}
    .nav-link {{
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.875rem;
      font-weight: 500;
      padding: 0.4rem 0.75rem;
      border-radius: 6px;
      transition: all 0.15s ease;
    }}
    .nav-link:hover {{ color: #fff; background: rgba(255,255,255,0.05); }}
    .nav-link.active {{ color: #fff; background: var(--surface-border); }}
    main {{
      max-width: 1040px;
      margin: 2rem auto;
      padding: 0 1.25rem 4rem;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }}
    h1, h2, h3 {{ letter-spacing: -0.02em; font-weight: 700; }}
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: var(--accent);
      color: #fff;
      font-weight: 600;
      font-size: 0.875rem;
      padding: 0.6rem 1.25rem;
      border-radius: 6px;
      border: none;
      cursor: pointer;
      text-decoration: none;
      transition: background 0.15s ease;
    }}
    .btn:hover {{ background: var(--accent-hover); }}
    .btn-secondary {{
      background: #1e293b;
      color: #cbd5e1;
    }}
    .btn-secondary:hover {{ background: #334155; }}
    input[type="text"], input[type="number"], select {{
      background: #090a0f;
      border: 1px solid var(--surface-border);
      color: #fff;
      padding: 0.6rem 0.75rem;
      border-radius: 6px;
      font-size: 0.875rem;
      width: 100%;
    }}
    input:focus, select:focus {{
      outline: 2px solid var(--accent);
      border-color: transparent;
    }}
    .badge-pill {{
      display: inline-block;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 9999px;
      font-family: var(--font-mono);
    }}
    .badge-green {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-blue {{ background: rgba(37, 99, 235, 0.15); color: #60a5fa; border: 1px solid rgba(37, 99, 235, 0.3); }}
    .badge-yellow {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
  </style>
</head>
<body>
  <header>
    <div class="header-inner">
      <a href="/" class="logo">
        <span>OPEN-SWITCH</span>
        <span class="logo-badge">v0.1.0</span>
      </a>
      <nav>
        {nav_links}
      </nav>
    </div>
  </header>
  {'<div style="background: rgba(239, 68, 68, 0.2); border-bottom: 1px solid #ef4444; color: #fca5a5; padding: 0.75rem 1.25rem; text-align: center; font-size: 0.875rem; font-weight: 600;">[EMERGENCY PAUSE] Open-Switch kill switch is active. Evaluation runs and fine-tuning are suspended.</div>' if settings.kill_switch else ""}
  <main>
    {content}
  </main>
</body>
</html>"""


@ui_router.get("/", response_class=HTMLResponse)
async def home_page(session_hash: str = Depends(get_or_create_session)):
    """Main dashboard: upload or pick sample dataset, select models, start evaluation."""
    async with session_context() as session:
        res = await session.execute(select(Dataset).order_by(Dataset.created_at.desc()))
        datasets = list(res.scalars().all())

    dataset_options = "".join(
        [
            f'<option value="{ds.id}">{html.escape(ds.name)} ({ds.n_rows} rows)</option>'
            for ds in datasets
        ]
    )

    models = [
        ("gemma-2b-local", "Gemma 2 2B (Local)", "Ollama", "$0.00 / Local"),
        ("gemma-9b-local", "Gemma 2 9B (Local)", "Ollama", "$0.00 / Local"),
        ("llama-3b-local", "Llama 3.2 3B (Local)", "Ollama", "$0.00 / Local"),
        ("do-llama-8b", "Llama 3.1 8B", "DigitalOcean", "$0.20 in / $0.60 out"),
        ("do-mistral-7b", "Mistral 7B Instruct", "DigitalOcean", "$0.15 in / $0.45 out"),
        ("bb-qwen-7b", "Qwen 2.5 7B", "Backboard", "$0.20 in / $0.60 out"),
    ]

    model_checkboxes = "".join(
        [
            f'''<label style="display:flex; align-items:center; gap:0.75rem; background:#0d0e14; border:1px solid var(--surface-border); padding:0.75rem 1rem; border-radius:6px; cursor:pointer;">
          <input type="checkbox" name="models" value="{key}" checked style="width:18px; height:18px;">
          <div style="flex:1;">
            <div style="font-weight:600; font-size:0.875rem;">{name}</div>
            <div style="font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">{provider} · {price}</div>
          </div>
        </label>'''
            for key, name, provider, price in models
        ]
    )

    body = f"""
    <div style="margin-bottom: 2rem;">
      <h1 style="font-size: 2rem; margin:0 0 0.5rem;">Can Open Models Replace Your Closed LLM?</h1>
      <p style="color: var(--text-muted); font-size: 1rem; margin:0;">
        Evaluate open-weight models against your proprietary tasks with honest statistics (10k bootstrap 95% CIs), default-deny provenance tracking, and automated Tinker LoRA fine-tuning.
      </p>
    </div>

    <!-- 1-Click Demo Datasets -->
    <div class="card" style="border-left: 4px solid var(--accent);">
      <h3 style="margin:0 0 0.5rem; font-size:1.1rem;">Quick Test with Verified Demo Datasets</h3>
      <p style="font-size:0.875rem; color:var(--text-muted); margin:0 0 1rem;">
        Click either dataset to evaluate open models immediately:
      </p>
      <div style="display:flex; gap:1rem; flex-wrap:wrap;">
        <form hx-post="/api/experiments" hx-target="#exp-result" hx-swap="innerHTML" style="margin:0;">
          <input type="hidden" name="name" value="Quick Banking Intent Benchmark">
          <input type="hidden" name="dataset_id" value="task_a_banking">
          <input type="hidden" name="models" value="gemma-2b-local">
          <input type="hidden" name="models" value="gemma-9b-local">
          <input type="hidden" name="models" value="do-llama-8b">
          <button type="submit" class="btn">
            Task A: Banking Intent Classification (150 Gold Rows)
          </button>
        </form>

        <form hx-post="/api/experiments" hx-target="#exp-result" hx-swap="innerHTML" style="margin:0;">
          <input type="hidden" name="name" value="Quick Support Ticket Triage Benchmark">
          <input type="hidden" name="dataset_id" value="task_b_tickets">
          <input type="hidden" name="models" value="bb-qwen-7b">
          <input type="hidden" name="models" value="gemma-9b-local">
          <input type="hidden" name="models" value="do-llama-8b">
          <button type="submit" class="btn btn-secondary">
            Task B: Support Ticket Triage (150 Rows Strict JSON)
          </button>
        </form>
      </div>
      <div id="exp-result" style="margin-top:1rem;"></div>
    </div>

    <!-- Custom Evaluation Form -->
    <div class="card">
      <h3 style="margin:0 0 1.25rem; font-size:1.1rem;">Configure New Evaluation Run</h3>
      <form hx-post="/api/experiments" hx-target="#exp-result" hx-swap="innerHTML">
        <div style="margin-bottom: 1.25rem;">
          <label style="display:block; font-size:0.8125rem; font-weight:600; margin-bottom:0.4rem; color:var(--text-muted);">
            EXPERIMENT NAME
          </label>
          <input type="text" name="name" value="Production Model Migration Benchmark" required>
        </div>

        <div style="margin-bottom: 1.25rem;">
          <label style="display:block; font-size:0.8125rem; font-weight:600; margin-bottom:0.4rem; color:var(--text-muted);">
            TARGET DATASET
          </label>
          <select name="dataset_id" required>
            {dataset_options or '<option value="">No datasets uploaded yet (use quick test above)</option>'}
          </select>
        </div>

        <div style="margin-bottom: 1.5rem;">
          <label style="display:block; font-size:0.8125rem; font-weight:600; margin-bottom:0.6rem; color:var(--text-muted);">
            SELECT CANDIDATE OPEN MODELS
          </label>
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:0.75rem;">
            {model_checkboxes}
          </div>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div style="font-size:0.8125rem; color:var(--text-muted);">
            Reliability Threshold: <strong>85% lower 95% CI bound</strong> · Max Budget: <strong>$2.00</strong>
          </div>
          <button type="submit" class="btn">
            Launch Evaluation Run →
          </button>
        </div>
      </form>
    </div>
    """
    return HTMLResponse(layout("Model Migration Evaluation", body, "home"))


@ui_router.get("/models", response_class=HTMLResponse)
async def models_page():
    """Model matrix with pricing and volume calculator."""
    body = """
    <div style="margin-bottom: 2rem;">
      <h1 style="font-size: 2rem; margin:0 0 0.5rem;">Verified Models & Pricing</h1>
      <p style="color: var(--text-muted); font-size: 1rem; margin:0;">
        All API pricing verified from provider documentation pages. Zero fabricated rates.
      </p>
    </div>

    <div class="card">
      <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.875rem;">
        <thead>
          <tr style="border-bottom:2px solid var(--surface-border); color:var(--text-muted);">
            <th style="padding:10px 14px;">Model Key</th>
            <th style="padding:10px 14px;">Provider</th>
            <th style="padding:10px 14px;">License</th>
            <th style="padding:10px 14px;">Input / MTok</th>
            <th style="padding:10px 14px;">Output / MTok</th>
            <th style="padding:10px 14px;">Verified On</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom:1px solid var(--surface-border);">
            <td style="padding:12px 14px; font-family:var(--font-mono); font-weight:600;">gemma-2b-local</td>
            <td style="padding:12px 14px;"><span class="badge-pill badge-green">Ollama Local</span></td>
            <td style="padding:12px 14px;">Gemma Terms</td>
            <td style="padding:12px 14px; color:#34d399;">$0.00</td>
            <td style="padding:12px 14px; color:#34d399;">$0.00</td>
            <td style="padding:12px 14px; color:var(--text-muted);">2026-10-14</td>
          </tr>
          <tr style="border-bottom:1px solid var(--surface-border);">
            <td style="padding:12px 14px; font-family:var(--font-mono); font-weight:600;">gemma-9b-local</td>
            <td style="padding:12px 14px;"><span class="badge-pill badge-green">Ollama Local</span></td>
            <td style="padding:12px 14px;">Gemma Terms</td>
            <td style="padding:12px 14px; color:#34d399;">$0.00</td>
            <td style="padding:12px 14px; color:#34d399;">$0.00</td>
            <td style="padding:12px 14px; color:var(--text-muted);">2026-10-14</td>
          </tr>
          <tr style="border-bottom:1px solid var(--surface-border);">
            <td style="padding:12px 14px; font-family:var(--font-mono); font-weight:600;">do-llama-8b</td>
            <td style="padding:12px 14px;"><span class="badge-pill badge-blue">DigitalOcean</span></td>
            <td style="padding:12px 14px;">Llama 3.1 Community</td>
            <td style="padding:12px 14px;">$0.20</td>
            <td style="padding:12px 14px;">$0.60</td>
            <td style="padding:12px 14px; color:var(--text-muted);">2026-10-14</td>
          </tr>
          <tr style="border-bottom:1px solid var(--surface-border);">
            <td style="padding:12px 14px; font-family:var(--font-mono); font-weight:600;">bb-qwen-7b</td>
            <td style="padding:12px 14px;"><span class="badge-pill badge-yellow">Backboard</span></td>
            <td style="padding:12px 14px;">Apache 2.0</td>
            <td style="padding:12px 14px;">$0.20</td>
            <td style="padding:12px 14px;">$0.60</td>
            <td style="padding:12px 14px; color:var(--text-muted);">2026-10-14</td>
          </tr>
        </tbody>
      </table>
    </div>
    """
    return HTMLResponse(layout("Models & Pricing", body, "models"))


@ui_router.get("/calibrate", response_class=HTMLResponse)
async def calibrate_page():
    """Interactive blind judge calibration session."""
    body = """
    <div style="margin-bottom: 2rem;">
      <h1 style="font-size: 2rem; margin:0 0 0.5rem;">Judge Calibration (Blind A/B Audit)</h1>
      <p style="color: var(--text-muted); font-size: 1rem; margin:0;">
        Label randomized paired responses to compute Cohen's kappa and determine judge reliability tier.
      </p>
    </div>

    <div class="card" id="calib-container" hx-get="/api/calibration/next" hx-trigger="load" hx-swap="innerHTML">
      <div style="text-align:center; padding:2rem; color:var(--text-muted);">
        Loading next evaluation pair...
      </div>
    </div>
    """
    return HTMLResponse(layout("Judge Calibration", body, "calibrate"))


@ui_router.get("/finetune", response_class=HTMLResponse)
async def finetune_page():
    """Tinker fine-tune vs k-shot comparative evaluation."""
    body = """
    <div style="margin-bottom: 2rem;">
      <h1 style="font-size: 2rem; margin:0 0 0.5rem;">Tinker LoRA Fine-Tuning & k-Shot Baseline</h1>
      <p style="color: var(--text-muted); font-size: 1rem; margin:0;">
        Compare zero-shot vs TF-IDF nearest-neighbor k-shot vs Tinker LoRA fine-tuning on provenance-compliant rows.
      </p>
    </div>

    <div class="card">
      <h3 style="margin:0 0 1rem; font-size:1.1rem;">Launch Fine-Tune vs k-Shot Evaluation</h3>
      <form hx-post="/api/finetunes" hx-target="#ft-result" hx-swap="innerHTML">
        <div style="margin-bottom: 1.25rem;">
          <label style="display:block; font-size:0.8125rem; font-weight:600; margin-bottom:0.4rem; color:var(--text-muted);">
            BASE MODEL FOR FINE-TUNING
          </label>
          <select name="base_model">
            <option value="bb-qwen-7b">Qwen 2.5 7B (Backboard / Tinker LoRA)</option>
            <option value="gemma-2b-local">Gemma 2 2B (Local / Tinker LoRA)</option>
          </select>
        </div>

        <div style="margin-bottom: 1.5rem;">
          <label style="display:block; font-size:0.8125rem; font-weight:600; margin-bottom:0.4rem; color:var(--text-muted);">
            TARGET DATASET ID
          </label>
          <input type="text" name="dataset_id" value="task_b_tickets" required>
        </div>

        <button type="submit" class="btn">
          Run LoRA vs k-Shot Comparison →
        </button>
      </form>
      <div id="ft-result" style="margin-top:1.5rem;"></div>
    </div>
    """
    return HTMLResponse(layout("LoRA Fine-Tune", body, "finetune"))
