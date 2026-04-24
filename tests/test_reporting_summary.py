from pathlib import Path

from clearrisk.reporting import (
    build_practitioner_table_rows,
    build_scenario_comparison_summary,
    export_scenario_comparison_csv,
    export_scenario_comparison_json,
    format_scenario_comparison_summary,
    generate_report,
    write_report_bundle,
)
from clearrisk.config import SimulationResult


def _result(
    *,
    total_im: float,
    total_loss: float,
    residual_shortfall: float,
    cover2_adequacy_ratio: float = 0.0,
) -> SimulationResult:
    return SimulationResult(
        im_by_member={"M1": total_im},
        member_losses={"M1": total_loss},
        residual_shortfall=residual_shortfall,
        scenario_metadata={"scenario_name": "test", "stress_label": "test"},
        metrics={"cover2_adequacy_ratio": cover2_adequacy_ratio},
    )


def test_build_scenario_comparison_summary_contains_comparison_block() -> None:
    baseline = _result(total_im=120.0, total_loss=100.0, residual_shortfall=1.0)
    stressed = _result(total_im=90.0, total_loss=150.0, residual_shortfall=8.0)
    summary = build_scenario_comparison_summary(
        baseline,
        stressed,
        baseline_name="gaussian",
        stressed_name="fat_tail",
    )
    assert "comparison" in summary
    assert "tail_loss_ratio_es" in summary["comparison"]
    assert "margin_adequacy_delta" in summary["comparison"]


def test_generate_report_includes_formatted_comparison_section(tmp_path: Path) -> None:
    baseline = _result(total_im=120.0, total_loss=100.0, residual_shortfall=1.0, cover2_adequacy_ratio=1.1)
    stressed = _result(total_im=90.0, total_loss=150.0, residual_shortfall=8.0, cover2_adequacy_ratio=0.8)
    summary = build_scenario_comparison_summary(baseline, stressed)
    output = tmp_path / "report.md"

    content = generate_report(stressed, output_path=output, comparison_summary=summary)
    assert "## Scenario Comparison" in content
    assert "### Practitioner Table" in content
    assert "Mean Cover-2 Adequacy" in content
    assert output.read_text(encoding="utf-8") == content


def test_format_scenario_comparison_summary_has_json_block() -> None:
    summary = {
        "baseline": {"expected_shortfall": 1.0},
        "stressed": {"expected_shortfall": 2.0},
        "comparison": {
            "tail_loss_ratio_es": 2.0,
            "margin_adequacy_baseline": 1.2,
            "margin_adequacy_stressed": 0.8,
            "margin_adequacy_delta": -0.4,
            "margin_adequacy_ratio": 0.666666,
            "cover2_adequacy_delta": -0.1,
        },
    }
    text = format_scenario_comparison_summary(summary)
    assert "```json" in text
    assert "tail_loss_ratio_es" in text


def test_practitioner_rows_and_csv_export(tmp_path: Path) -> None:
    baseline = _result(total_im=120.0, total_loss=100.0, residual_shortfall=1.0, cover2_adequacy_ratio=1.3)
    stressed = _result(total_im=90.0, total_loss=150.0, residual_shortfall=8.0, cover2_adequacy_ratio=0.7)
    summary = build_scenario_comparison_summary(baseline, stressed)

    rows = build_practitioner_table_rows(summary)
    assert any(row["metric"] == "Prob. Member Default" for row in rows)
    assert any(row["metric"] == "Mean Cover-2 Adequacy" for row in rows)

    csv_path = tmp_path / "comparison.csv"
    export_scenario_comparison_csv(summary, csv_path)
    csv_text = csv_path.read_text(encoding="utf-8")
    assert "metric,baseline,stressed,delta" in csv_text
    assert "Mean Cover-2 Adequacy" in csv_text

    json_path = tmp_path / "comparison.json"
    export_scenario_comparison_json(summary, json_path)
    json_text = json_path.read_text(encoding="utf-8")
    assert '"comparison"' in json_text
    assert '"tail_loss_ratio_es"' in json_text


def test_write_report_bundle_creates_markdown_csv_and_json(tmp_path: Path) -> None:
    baseline = _result(total_im=120.0, total_loss=100.0, residual_shortfall=1.0, cover2_adequacy_ratio=1.3)
    stressed = _result(total_im=90.0, total_loss=150.0, residual_shortfall=8.0, cover2_adequacy_ratio=0.7)
    summary = build_scenario_comparison_summary(baseline, stressed)
    bundle_dir = tmp_path / "bundle"

    paths = write_report_bundle(stressed, bundle_dir, comparison_summary=summary)
    assert paths["report_path"].exists()
    assert paths["comparison_csv_path"].exists()
    assert paths["comparison_json_path"].exists()

    assert "Scenario Comparison" in paths["report_path"].read_text(encoding="utf-8")
    assert "metric,baseline,stressed,delta" in paths["comparison_csv_path"].read_text(encoding="utf-8")
    assert '"comparison"' in paths["comparison_json_path"].read_text(encoding="utf-8")
