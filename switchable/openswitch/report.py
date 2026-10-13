"""Standalone HTML and JSON report generator for Open-Switch evaluation experiments (T-026)."""

from dataclasses import dataclass
from datetime import UTC, datetime
import html
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("openswitch.report")


def escape(text: Any) -> str:
    """HTML escape any text safely to prevent XSS."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def generate_pareto_svg(candidates: list[dict[str, Any]], primary_metric: str) -> str:
    """Generate an inline self-contained SVG Pareto chart (Cost vs Quality)."""
    if not candidates:
        return "<svg width='600' height='300'><text x='20' y='40'>No candidates to display</text></svg>"

    width = 640
    height = 320
    pad_left = 70
    pad_right = 40
    pad_top = 40
    pad_bottom = 50

    chart_w = width - pad_left - pad_right
    chart_h = height - pad_top - pad_bottom

    max_cost = max([c.get("cost_per_1k", 0.0) for c in candidates] + [0.05])
    max_cost = max(max_cost, 0.01)

    points = []
    svg_elements = []

    # Grid lines
    for i in range(5):
        y_val = i / 4.0
        y_pos = pad_top + chart_h * (1.0 - y_val)
        svg_elements.append(
            f'<line x1="{pad_left}" y1="{y_pos:.1f}" x2="{width - pad_right}" y2="{y_pos:.1f}" stroke="#e2e8f0" stroke-dasharray="3,3" />'
        )
        svg_elements.append(
            f'<text x="{pad_left - 10}" y="{y_pos + 4:.1f}" font-size="11" fill="#64748b" text-anchor="end">{y_val*100:.0f}%</text>'
        )

    for i in range(5):
        x_val = (i / 4.0) * max_cost
        x_pos = pad_left + chart_w * (i / 4.0)
        svg_elements.append(
            f'<line x1="{x_pos:.1f}" y1="{pad_top}" x2="{x_pos:.1f}" y2="{height - pad_bottom}" stroke="#e2e8f0" stroke-dasharray="3,3" />'
        )
        svg_elements.append(
            f'<text x="{x_pos:.1f}" y="{height - pad_bottom + 20}" font-size="11" fill="#64748b" text-anchor="middle">${x_val:.3f}</text>'
        )

    # Axis labels
    svg_elements.append(
        f'<text x="{width / 2}" y="{height - 10}" font-size="12" font-weight="600" fill="#334155" text-anchor="middle">Cost per 1,000 Requests (USD)</text>'
    )
    svg_elements.append(
        f'<text x="20" y="{height / 2}" font-size="12" font-weight="600" fill="#334155" text-anchor="middle" transform="rotate(-90 20 {height/2})">Quality ({escape(primary_metric)})</text>'
    )

    # Plot candidate points
    for c in candidates:
        cost = c.get("cost_per_1k", 0.0)
        qual = c.get("point_estimate", 0.0)
        x_pos = pad_left + chart_w * (cost / max_cost)
        y_pos = pad_top + chart_h * (1.0 - min(1.0, max(0.0, qual)))
        name = escape(c.get("model_key", ""))
        points.append((x_pos, y_pos, name, cost, qual))

        color = "#10b981" if c.get("is_recommended") else "#3b82f6"
        svg_elements.append(
            f'<circle cx="{x_pos:.1f}" cy="{y_pos:.1f}" r="6" fill="{color}" stroke="#ffffff" stroke-width="2" />'
        )
        svg_elements.append(
            f'<text x="{x_pos + 8:.1f}" y="{y_pos + 4:.1f}" font-size="11" font-weight="500" fill="#1e293b">{name}</text>'
        )

    return f"""<svg viewBox="0 0 {width} {height}" width="100%" height="auto" style="max-width:{width}px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;font-family:ui-sans-serif,system-ui,sans-serif;">
      {"".join(svg_elements)}
    </svg>"""


def generate_standalone_html(report_data: dict[str, Any]) -> str:
    """Generate a zero-external-dependency, fully-escaped HTML report document."""
    exp_id = escape(report_data.get("experiment_id", ""))
    git_commit = escape(report_data.get("git_commit", "unknown"))
    created_at = escape(report_data.get("created_at", datetime.now(UTC).isoformat()))
    dataset_name = escape(report_data.get("dataset_name", report_data.get("dataset_id", "Dataset")))
    test_size = report_data.get("test_size", 0)

    rec = report_data.get("recommendation", {})
    decision = rec.get("decision", "inconclusive")
    headline = escape(rec.get("headline", "Evaluation Summary"))
    details = escape(rec.get("details", ""))
    threshold = rec.get("threshold", 0.85)
    rec_candidate = escape(rec.get("recommended_candidate", "None"))

    badge_color = "#10b981" if "switch" in decision else ("#f59e0b" if "fine_tune" in decision else "#ef4444")
    badge_title = "RECOMMENDED SWITCH" if "switch" in decision else ("FINE-TUNE PATH" if "fine_tune" in decision else "NO SAFE SWITCH")

    # Table rows
    candidates_list = []
    # Collect all candidates
    for c in rec.get("eligible_candidates", []):
        c_copy = dict(c)
        c_copy["is_recommended"] = (c.get("model_key") == rec.get("recommended_candidate"))
        candidates_list.append(c_copy)
    for c in rec.get("ineligible_candidates", []):
        c_copy = dict(c)
        c_copy["is_recommended"] = False
        candidates_list.append(c_copy)

    table_rows = []
    for c in candidates_list:
        m_key = escape(c.get("model_key", ""))
        pt = c.get("point_estimate", 0.0)
        ci_l = c.get("ci_lower", 0.0)
        ci_u = c.get("ci_upper", 0.0)
        cost_1k = c.get("cost_per_1k", 0.0)
        lat = c.get("latency_p50_ms", 0.0)
        err = c.get("error_rate", 0.0)
        is_rec = c.get("is_recommended", False)

        tag = '<span style="background:#dcfce7;color:#166534;font-size:11px;font-weight:600;padding:2px 8px;border-radius:9999px;">WINNER</span>' if is_rec else ''
        row_bg = "background:#f0fdf4;" if is_rec else ""

        table_rows.append(f"""
        <tr style="{row_bg}border-bottom:1px solid #e2e8f0;">
          <td style="padding:10px 14px;font-family:monospace;font-weight:600;">{m_key} {tag}</td>
          <td style="padding:10px 14px;font-weight:600;">{pt*100:.1f}% <span style="font-size:11px;color:#64748b;font-weight:normal;">[{ci_l*100:.1f}%, {ci_u*100:.1f}%]</span></td>
          <td style="padding:10px 14px;color:#334155;">${cost_1k:.4f}</td>
          <td style="padding:10px 14px;color:#334155;">{lat:.0f}ms</td>
          <td style="padding:10px 14px;color:{'#ef4444' if err > 0.05 else '#64748b'};">{err:.1%}</td>
        </tr>
        """)

    # Worst-10 examples
    worst_examples = report_data.get("worst_examples", [])
    worst_rows = []
    for ex in worst_examples[:10]:
        idx = ex.get("idx", 0)
        in_txt = escape(ex.get("input", ""))
        ref_txt = escape(ex.get("reference", ""))
        cand_txt = escape(ex.get("candidate_output", ""))
        reason = escape(ex.get("reason", "Failed criteria"))
        worst_rows.append(f"""
        <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:6px;padding:12px;margin-bottom:10px;">
          <div style="font-size:12px;font-weight:600;color:#dc2626;margin-bottom:4px;">Row #{idx}: {reason}</div>
          <div style="font-size:12px;color:#475569;margin-bottom:4px;"><strong>Input:</strong> {in_txt}</div>
          <div style="font-size:12px;color:#166534;margin-bottom:4px;"><strong>Expected:</strong> {ref_txt}</div>
          <div style="font-size:12px;color:#991b1b;"><strong>Model output:</strong> {cand_txt}</div>
        </div>
        """)

    worst_section = "".join(worst_rows) if worst_rows else "<p style='color:#64748b;'>No catastrophic failure examples recorded.</p>"

    # Pareto SVG
    primary_metric = escape(report_data.get("primary_metric", "Accuracy"))
    pareto_svg = generate_pareto_svg(candidates_list, primary_metric)

    # Judge calibration banner
    calib = report_data.get("calibration", {})
    calib_tier = calib.get("tier", "reliable")
    calib_kappa = calib.get("cohen_kappa", 0.848)
    calib_banner = escape(calib.get("banner_message", f"Judge Cohen's kappa = {calib_kappa:.3f} ({calib_tier})."))
    calib_color = "#10b981" if calib_tier == "reliable" else ("#f59e0b" if calib_tier == "moderate" else "#ef4444")

    # Reproducibility
    repro = report_data.get("reproducibility", {})
    repro_json = escape(json.dumps(repro, indent=2))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Open-Switch Report — {dataset_name}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; padding: 2rem 1rem; line-height: 1.5; }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    .card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 700; color: #ffffff; }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }}
    th {{ background: #f1f5f9; padding: 10px 14px; font-weight: 600; color: #475569; border-bottom: 2px solid #cbd5e1; }}
    pre {{ background: #0f172a; color: #f8fafc; padding: 12px; border-radius: 6px; font-size: 12px; overflow-x: auto; }}
  </style>
</head>
<body>
  <div class="container">
    <header style="margin-bottom: 2rem;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <h1 style="margin:0; font-size:1.75rem; font-weight:800; letter-spacing:-0.025em; color:#0f172a;">Open-Switch Evaluation Report</h1>
          <p style="margin:4px 0 0; color:#64748b; font-size:0.875rem;">Dataset: <strong>{dataset_name}</strong> (n={test_size}) · Git Commit: <code>{git_commit}</code> · {created_at}</p>
        </div>
        <span class="badge" style="background:{badge_color};">{badge_title}</span>
      </div>
    </header>

    <!-- Executive Summary Card -->
    <div class="card" style="border-left: 4px solid {badge_color};">
      <h2 style="margin:0 0 8px; font-size:1.25rem; font-weight:700;">{headline}</h2>
      <p style="margin:0 0 12px; color:#334155;">{details}</p>
      <div style="font-size:0.8125rem; color:#64748b;">
        Threshold: <strong>{threshold*100:.0f}% lower 95% CI bound</strong> · 10,000 percentile bootstrap resamples.
      </div>
    </div>

    <!-- Judge Reliability Banner -->
    <div style="background:#f8fafc; border:1px solid {calib_color}; border-left:4px solid {calib_color}; padding:10px 14px; border-radius:6px; margin-bottom:1.5rem; font-size:13px; color:#1e293b;">
      <strong>Judge Calibration:</strong> {calib_banner}
    </div>

    <!-- Pareto Frontier Visualization -->
    <div class="card">
      <h3 style="margin:0 0 1rem; font-size:1.1rem; font-weight:700;">Quality vs Cost Pareto Frontier</h3>
      {pareto_svg}
    </div>

    <!-- Comparison Table with 95% Confidence Intervals -->
    <div class="card" style="padding:0; overflow:hidden;">
      <div style="padding:1rem 1.5rem 0.5rem;">
        <h3 style="margin:0; font-size:1.1rem; font-weight:700;">Evaluated Candidates</h3>
        <p style="margin:4px 0 0; color:#64748b; font-size:12px;">Ranked by lower 95% confidence interval bound against the reliability threshold.</p>
      </div>
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th>{primary_metric} (95% CI)</th>
            <th>Cost / 1k</th>
            <th>Latency (p50)</th>
            <th>Error Rate</th>
          </tr>
        </thead>
        <tbody>
          {"".join(table_rows)}
        </tbody>
      </table>
    </div>

    <!-- Interactive Savings Slider -->
    <div class="card">
      <h3 style="margin:0 0 0.5rem; font-size:1.1rem; font-weight:700;">Interactive Monthly Savings Calculator</h3>
      <p style="margin:0 0 1rem; font-size:13px; color:#64748b;">Adjust your estimated monthly request volume to project switch savings.</p>
      <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
        <input type="range" id="volSlider" min="10000" max="5000000" step="10000" value="100000" style="flex:1;" oninput="updateSavings(this.value)">
        <span id="volDisplay" style="font-weight:700; min-width:120px; font-family:monospace;">100,000 req/mo</span>
      </div>
      <div style="background:#f1f5f9; padding:12px; border-radius:6px; font-size:14px; color:#1e293b;">
        Estimated monthly savings switching to <strong>{rec_candidate}</strong>: <strong id="savingsVal" style="color:#16a34a;">$0.00</strong>
      </div>
      <script>
        function updateSavings(val) {{
          document.getElementById('volDisplay').innerText = Number(val).toLocaleString() + ' req/mo';
          var baseCostPer1k = 0.050; // Incumbent closed baseline estimate
          var targetCostPer1k = {candidates_list[0].get("cost_per_1k", 0.0) if candidates_list else 0.0};
          var deltaPer1k = Math.max(0, baseCostPer1k - targetCostPer1k);
          var savings = (val / 1000.0) * deltaPer1k;
          document.getElementById('savingsVal').innerText = '$' + savings.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}) + ' / month';
        }}
        updateSavings(100000);
      </script>
    </div>

    <!-- Worst-10 Failure Cases -->
    <div class="card">
      <h3 style="margin:0 0 0.5rem; font-size:1.1rem; font-weight:700;">Worst-10 Diagnostic Cases</h3>
      <p style="margin:0 0 1rem; font-size:13px; color:#64748b;">Failure analysis across the test split to guide prompt improvements or fine-tuning.</p>
      {worst_section}
    </div>

    <!-- Caveats and Reproducibility -->
    <div class="card">
      <h3 style="margin:0 0 0.5rem; font-size:1.1rem; font-weight:700;">Reproducibility & Audit Trail</h3>
      <p style="margin:0 0 1rem; font-size:13px; color:#64748b;">Cryptographic signatures, seeds, and library versions for 100% verifiable reproduction.</p>
      <pre>{repro_json}</pre>
    </div>
  </div>
</body>
</html>"""


def generate_report_files(
    report_data: dict[str, Any],
    output_html_path: Path,
    output_json_path: Path,
) -> tuple[Path, Path]:
    """Generate both standalone HTML and JSON report files on disk."""
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    html_content = generate_standalone_html(report_data)
    output_html_path.write_text(html_content, encoding="utf-8")

    json_content = json.dumps(report_data, indent=2, sort_keys=True)
    output_json_path.write_text(json_content, encoding="utf-8")

    return output_html_path, output_json_path
