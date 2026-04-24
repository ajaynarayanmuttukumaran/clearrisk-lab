# Architecture

ClearRisk Lab is organized as a modular, config-driven risk simulation package.

## Repository Structure
- `src/clearrisk/`: core simulation modules (config, market, scenarios, margin, default fund, waterfall, contagion, analytics, reporting, CLI).
- `examples/`: YAML scenario/config presets for baseline and stress experiments.
- `tests/`: invariant, behavior, and integration tests for core engines and CLI/reporting flows.
- `reports/`: output directory for generated markdown/CSV/JSON report artifacts.
- `notebooks/`: walkthrough labs for quickstart, tail-risk/margin comparisons, and Cover-2/liquidity stress.
- `app/`: Streamlit dashboard entrypoint.

## Core Module Responsibilities
- `config.py`: typed dataclasses for assumptions, resources, and result payloads.
- `market.py` + `scenarios.py`: synthetic shock/path generation and scenario families.
- `margin.py`: IM computation methods and margin add-ons.
- `default_fund.py`: Cover-1/Cover-2 and prefunded adequacy metrics.
- `waterfall.py`: deterministic waterfall allocation with explicit layer ledger.
- `contagion.py`: close-out loss add-ons and assessment-driven second-round default checks.
- `analytics.py`: probability and scenario-comparison metrics.
- `reporting.py`: practitioner tables and report bundle exports.
- `cli.py`: command interface for run, compare, report, and dashboard launch.

## CLI Flow
1. Load config (`examples/*.yaml` or user-provided file).
2. Build `SimulationConfig` from typed dataclasses.
3. Execute `run_simulation(...)`.
4. Emit structured result JSON and optional report/comparison artifacts.

## Simulation Flow
1. Scenario selection and member cloning.
2. Member-level IM and clean-loss estimation.
3. Optional liquidity close-out add-ons.
4. First-round default identification.
5. Waterfall loss allocation across ordered layers.
6. Assessment burden allocation and second-round stress check.
7. Cover metrics and summary analytics population.
8. Structured outputs for CLI, notebooks, and reporting.
