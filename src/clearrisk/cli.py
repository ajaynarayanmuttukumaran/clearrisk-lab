from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

import typer
import yaml

from . import run_simulation
from .config import MarketScenario, SimulationConfig
from .reporting import (
    build_scenario_comparison_summary,
    export_scenario_comparison_csv,
    generate_report,
    write_report_bundle,
)

app = typer.Typer(help="ClearRisk Lab CLI")


def _load_config(path: Path) -> SimulationConfig:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yml", ".yaml"}:
        payload = yaml.safe_load(raw)
    else:
        payload = json.loads(raw)
    return SimulationConfig.from_dict(payload or {})


@app.command()
def run(config: Path = typer.Option(..., "--config", help="Path to config YAML/JSON")) -> None:
    cfg = _load_config(config)
    result = run_simulation(cfg)
    typer.echo(json.dumps(result.to_dict(), indent=2))


@app.command()
def stress(scenario: str = typer.Option("fat_tail", "--scenario")) -> None:
    cfg = SimulationConfig(scenarios=[MarketScenario(scenario_name=scenario, stress_label=scenario)])
    result = run_simulation(cfg)
    typer.echo(f"Scenario '{scenario}' completed. Residual shortfall={result.residual_shortfall:.2f}")


@app.command("compare")
def compare_configs(
    config_a: Path = typer.Option(..., "--config-a"),
    config_b: Path = typer.Option(..., "--config-b"),
    comparison_csv: Optional[Path] = typer.Option(None, "--comparison-csv"),
) -> None:
    result_a = run_simulation(_load_config(config_a))
    result_b = run_simulation(_load_config(config_b))
    summary = build_scenario_comparison_summary(
        result_a,
        result_b,
        baseline_name=config_a.stem,
        stressed_name=config_b.stem,
    )
    if comparison_csv is not None:
        export_scenario_comparison_csv(summary, comparison_csv)
    typer.echo(json.dumps(summary, indent=2))
    if comparison_csv is not None:
        typer.echo(f"Comparison CSV written to {comparison_csv}")


@app.command()
def report(
    config: Path = typer.Option(..., "--config"),
    compare_config: Optional[Path] = typer.Option(None, "--compare-config"),
    output: Path = typer.Option(Path("reports/report.md"), "--output"),
    comparison_csv: Optional[Path] = typer.Option(None, "--comparison-csv"),
    bundle_dir: Optional[Path] = typer.Option(None, "--bundle-dir"),
) -> None:
    cfg = _load_config(config)
    result = run_simulation(cfg)
    comparison_summary = None
    if compare_config is not None:
        compare_result = run_simulation(_load_config(compare_config))
        comparison_summary = build_scenario_comparison_summary(
            compare_result,
            result,
            baseline_name=compare_config.stem,
            stressed_name=config.stem,
        )
        if comparison_csv is not None:
            export_scenario_comparison_csv(comparison_summary, comparison_csv)

    if bundle_dir is not None:
        if comparison_summary is None:
            raise typer.BadParameter("--bundle-dir requires --compare-config so summary artifacts can be generated.")
        bundle_paths = write_report_bundle(
            result,
            bundle_dir,
            comparison_summary=comparison_summary,
        )
        typer.echo(f"Report bundle written to {bundle_paths['bundle_dir']}")
        typer.echo(f"- Markdown: {bundle_paths['report_path']}")
        typer.echo(f"- Comparison CSV: {bundle_paths['comparison_csv_path']}")
        typer.echo(f"- Summary JSON: {bundle_paths['comparison_json_path']}")
        return

    generate_report(result, output_path=output, comparison_summary=comparison_summary)
    typer.echo(f"Report written to {output}")
    if comparison_csv is not None and comparison_summary is not None:
        typer.echo(f"Comparison CSV written to {comparison_csv}")


@app.command()
def dashboard(host: str = "localhost", port: int = 8501) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    app_path = repo_root / "app" / "streamlit_app.py"
    cmd = [
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        host,
        "--server.port",
        str(port),
    ]
    subprocess.run(cmd, check=False)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
