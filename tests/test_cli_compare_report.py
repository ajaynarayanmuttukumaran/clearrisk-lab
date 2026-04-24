from pathlib import Path

from typer.testing import CliRunner

from clearrisk.cli import app


def _write_config(path: Path, volatility: float) -> None:
    path.write_text(
        "\n".join(
            [
                "run_name: test_run",
                "time_horizon_days: 252",
                "scenarios:",
                "  - scenario_name: scenario",
                f"    volatility: {volatility}",
                "    liquidity_spread_multiplier: 1.0",
                "    stress_label: test",
            ]
        ),
        encoding="utf-8",
    )


def test_cli_compare_outputs_scenario_comparison_json(tmp_path: Path) -> None:
    config_a = tmp_path / "a.yaml"
    config_b = tmp_path / "b.yaml"
    _write_config(config_a, volatility=0.2)
    _write_config(config_b, volatility=0.4)

    runner = CliRunner()
    result = runner.invoke(app, ["compare", "--config-a", str(config_a), "--config-b", str(config_b)])
    assert result.exit_code == 0
    assert '"comparison"' in result.stdout
    assert '"tail_loss_ratio_es"' in result.stdout


def test_cli_compare_can_write_comparison_csv(tmp_path: Path) -> None:
    config_a = tmp_path / "a.yaml"
    config_b = tmp_path / "b.yaml"
    output_csv = tmp_path / "compare.csv"
    _write_config(config_a, volatility=0.2)
    _write_config(config_b, volatility=0.4)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "compare",
            "--config-a",
            str(config_a),
            "--config-b",
            str(config_b),
            "--comparison-csv",
            str(output_csv),
        ],
    )
    assert result.exit_code == 0
    text = output_csv.read_text(encoding="utf-8")
    assert "metric,baseline,stressed,delta" in text
    assert "Mean Cover-2 Adequacy" in text


def test_cli_report_can_include_comparison_summary(tmp_path: Path) -> None:
    config_base = tmp_path / "base.yaml"
    config_stress = tmp_path / "stress.yaml"
    output = tmp_path / "report.md"
    _write_config(config_base, volatility=0.2)
    _write_config(config_stress, volatility=0.5)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "report",
            "--config",
            str(config_stress),
            "--compare-config",
            str(config_base),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0
    text = output.read_text(encoding="utf-8")
    assert "## Scenario Comparison" in text
    assert "### Practitioner Table" in text


def test_cli_report_can_write_comparison_csv(tmp_path: Path) -> None:
    config_base = tmp_path / "base.yaml"
    config_stress = tmp_path / "stress.yaml"
    output = tmp_path / "report.md"
    output_csv = tmp_path / "report_compare.csv"
    _write_config(config_base, volatility=0.2)
    _write_config(config_stress, volatility=0.5)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "report",
            "--config",
            str(config_stress),
            "--compare-config",
            str(config_base),
            "--output",
            str(output),
            "--comparison-csv",
            str(output_csv),
        ],
    )
    assert result.exit_code == 0
    csv_text = output_csv.read_text(encoding="utf-8")
    assert "metric,baseline,stressed,delta" in csv_text


def test_cli_report_bundle_writes_markdown_csv_and_json(tmp_path: Path) -> None:
    config_base = tmp_path / "base.yaml"
    config_stress = tmp_path / "stress.yaml"
    bundle_dir = tmp_path / "reports" / "bundle_run"
    _write_config(config_base, volatility=0.2)
    _write_config(config_stress, volatility=0.5)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "report",
            "--config",
            str(config_stress),
            "--compare-config",
            str(config_base),
            "--bundle-dir",
            str(bundle_dir),
        ],
    )
    assert result.exit_code == 0
    assert (bundle_dir / "report.md").exists()
    assert (bundle_dir / "scenario_comparison.csv").exists()
    assert (bundle_dir / "scenario_comparison_summary.json").exists()


def test_cli_report_bundle_requires_compare_config(tmp_path: Path) -> None:
    config_stress = tmp_path / "stress.yaml"
    bundle_dir = tmp_path / "reports" / "bundle_run"
    _write_config(config_stress, volatility=0.5)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "report",
            "--config",
            str(config_stress),
            "--bundle-dir",
            str(bundle_dir),
        ],
    )
    assert result.exit_code != 0
    assert result.exit_code == 2
    assert not (bundle_dir / "report.md").exists()
