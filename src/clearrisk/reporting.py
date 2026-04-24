from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .analytics import compute_basic_metrics, scenario_comparison_outputs
from .config import SimulationResult

PRACTITIONER_FIELDS: List[Tuple[str, str]] = [
    ("Prob. Member Default", "prob_member_default"),
    ("Prob. DF Depletion", "prob_default_fund_depletion"),
    ("Prob. Assessment Calls", "prob_assessment_calls"),
    ("Prob. Residual Shortfall", "prob_residual_shortfall"),
    ("VaR (Residual Shortfall)", "var"),
    ("Expected Shortfall", "expected_shortfall"),
    ("Mean Margin Adequacy", "mean_margin_adequacy_ratio"),
    ("Mean Cover-2 Adequacy", "mean_cover2_adequacy_ratio"),
]


def _comparison_labels(summary: Dict[str, Any]) -> Tuple[str, str]:
    keys = [k for k in summary.keys() if k != "comparison"]
    if len(keys) >= 2:
        return keys[0], keys[1]
    return "baseline", "stressed"


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_scenario_comparison_summary(
    baseline_result: SimulationResult,
    stressed_result: SimulationResult,
    *,
    baseline_name: str = "baseline",
    stressed_name: str = "stressed",
    confidence_level: float = 0.99,
) -> Dict[str, Any]:
    return scenario_comparison_outputs(
        [baseline_result],
        [stressed_result],
        baseline_name=baseline_name,
        stressed_name=stressed_name,
        confidence_level=confidence_level,
    )


def build_practitioner_table_rows(summary: Dict[str, Any]) -> List[Dict[str, float | str]]:
    baseline_key, stressed_key = _comparison_labels(summary)
    baseline_block = summary.get(baseline_key, {})
    stressed_block = summary.get(stressed_key, {})
    rows: List[Dict[str, float | str]] = []
    for label, key in PRACTITIONER_FIELDS:
        baseline_val = _safe_float(baseline_block.get(key, 0.0))
        stressed_val = _safe_float(stressed_block.get(key, 0.0))
        rows.append(
            {
                "metric": label,
                "baseline": baseline_val,
                "stressed": stressed_val,
                "delta": stressed_val - baseline_val,
            }
        )
    return rows


def export_scenario_comparison_csv(summary: Dict[str, Any], output_path: Path) -> Path:
    rows = build_practitioner_table_rows(summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["metric", "baseline", "stressed", "delta"])
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def export_scenario_comparison_json(summary: Dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return output_path


def write_report_bundle(
    result: SimulationResult,
    bundle_dir: Path,
    *,
    comparison_summary: Dict[str, Any],
    report_filename: str = "report.md",
    comparison_csv_filename: str = "scenario_comparison.csv",
    summary_json_filename: str = "scenario_comparison_summary.json",
) -> Dict[str, Path]:
    if comparison_summary is None:
        raise ValueError("comparison_summary is required to build a complete report bundle")

    bundle_dir.mkdir(parents=True, exist_ok=True)
    report_path = bundle_dir / report_filename
    csv_path = bundle_dir / comparison_csv_filename
    json_path = bundle_dir / summary_json_filename

    generate_report(result, output_path=report_path, comparison_summary=comparison_summary)
    export_scenario_comparison_csv(comparison_summary, csv_path)
    export_scenario_comparison_json(comparison_summary, json_path)

    return {
        "bundle_dir": bundle_dir,
        "report_path": report_path,
        "comparison_csv_path": csv_path,
        "comparison_json_path": json_path,
    }


def format_scenario_comparison_summary(summary: Dict[str, Any]) -> str:
    baseline_key, stressed_key = _comparison_labels(summary)
    comparison = summary.get("comparison", {})
    rows = build_practitioner_table_rows(summary)

    lines = [
        "## Scenario Comparison",
        f"- Baseline label: {baseline_key}",
        f"- Stressed label: {stressed_key}",
        f"- Tail loss ratio (ES): {_safe_float(comparison.get('tail_loss_ratio_es', 0.0)):.4f}",
        f"- Margin adequacy delta: {_safe_float(comparison.get('margin_adequacy_delta', 0.0)):.4f}",
        f"- Cover-2 adequacy delta: {_safe_float(comparison.get('cover2_adequacy_delta', 0.0)):.4f}",
        "",
        "### Practitioner Table",
        "| Metric | Baseline | Stressed | Delta |",
        "|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['metric']} | {float(row['baseline']):.4f} | {float(row['stressed']):.4f} | {float(row['delta']):.4f} |"
        )

    lines.extend(
        [
            "",
            "```json",
            json.dumps(summary, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def generate_report(
    result: SimulationResult,
    output_path: Optional[Path] = None,
    comparison_summary: Optional[Dict[str, Any]] = None,
) -> str:
    metrics = compute_basic_metrics(result)
    lines = [
        "# ClearRisk Lab Report",
        "",
        "## Executive Summary",
        f"- Defaults observed: {int(metrics['default_count'])}",
        f"- Residual shortfall: {metrics['residual_shortfall']:.2f}",
        f"- Margin adequacy ratio: {metrics['margin_adequacy_ratio']:.4f}",
        "",
        "## Scenario",
        f"- Name: {result.scenario_metadata.get('scenario_name', 'unspecified')}",
        f"- Stress label: {result.scenario_metadata.get('stress_label', 'unspecified')}",
        "",
        "## Waterfall Outcome",
        f"- Layer usage: {result.waterfall_layer_usage}",
        "",
    ]
    if comparison_summary is not None:
        lines.append(format_scenario_comparison_summary(comparison_summary))

    lines.extend(
        [
            "## Assumptions and Limits",
            "- This project is educational and research-oriented.",
            "- It is not a production CCP model or regulatory model.",
            "",
        ]
    )
    content = "\n".join(lines)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    return content
