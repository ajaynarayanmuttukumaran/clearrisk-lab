# ClearRisk Lab: CCP Margin Procyclicality, Tail-Risk, and Default Waterfall Stress Engine

ClearRisk Lab is an educational CCP stress-testing simulator that studies how margin models, tail-risk assumptions, liquidity close-out costs, default fund sizing, and assessment calls affect the resilience of a simplified central counterparty default waterfall.

## Core Risk Question
When does a CCP margin and default waterfall system appear safe under standard assumptions but become fragile under tail risk, wrong-way risk, margin procyclicality, liquidity close-out costs, concentration, and assessment-driven contagion?

## Why This Matters
Clearing risk is about tradeoffs, not single metrics. Higher margin can reduce CCP shortfall risk but increase member liquidity stress. Cover-2 can appear adequate in clean assumptions yet weaken under close-out frictions and concentrated stress. This project is designed to make those tensions explicit and testable.

## What the Simulator Does
- Simulates synthetic stress regimes (Gaussian baseline, Student-t tail stress, jump stress, high-volatility stress).
- Computes margin under multiple methods (Gaussian VaR, Expected Shortfall, stressed VaR) with MPOR scaling, volatility floor, anti-procyclicality buffer, and simple add-ons.
- Sizes default fund resources with fixed, percent-IM, Cover-1, Cover-2, and stress-Cover-2 logic.
- Applies deterministic waterfall allocation with full layer logging.
- Adds liquidity close-out cost effects and assessment-driven second-round default checks.
- Produces scenario comparison summaries, practitioner tables, CSV artifacts, and report bundles.

## What Makes It Different
- Thesis-driven design: every component maps to a risk question.
- Auditability-first implementation: explicit layer logs, no hidden loss leakage.
- Practitioner framing: Cover-2 adequacy, liquidity burden, contagion stress, and margin adequacy deltas.
- Reproducible outputs: markdown report + comparison CSV + raw JSON summary bundles.

## Architecture Overview
- `src/clearrisk/config.py`: dataclasses for scenarios, margin, waterfall, close-out, contagion, results.
- `src/clearrisk/market.py` and `src/clearrisk/scenarios.py`: synthetic path generation and scenario sets.
- `src/clearrisk/margin.py`: modular margin engine.
- `src/clearrisk/default_fund.py`: Cover-1/Cover-2 sizing and adequacy metrics.
- `src/clearrisk/waterfall.py`: deterministic waterfall ledger.
- `src/clearrisk/contagion.py`: close-out and assessment contagion logic.
- `src/clearrisk/analytics.py` and `src/clearrisk/reporting.py`: metrics, comparisons, tables, reports, bundles.
- `src/clearrisk/cli.py`: run/stress/compare/report/dashboard commands.

## Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt
```

## Quickstart
```bash
python3 -m clearrisk.cli run --config examples/baseline_config.yaml
python3 -m clearrisk.cli compare \
  --config-a examples/gaussian_var_config.yaml \
  --config-b examples/fat_tail_config.yaml
```
Recruiter demo (synthetic stress):
```bash
python3 -m clearrisk.cli run --config examples/recruiter_demo_stress_config.yaml
```

## CLI Examples
```bash
python3 -m clearrisk.cli run --config examples/baseline_config.yaml
python3 -m clearrisk.cli stress --scenario fat_tail
python3 -m clearrisk.cli compare \
  --config-a examples/gaussian_var_config.yaml \
  --config-b examples/expected_shortfall_config.yaml \
  --comparison-csv reports/compare.csv
python3 -m clearrisk.cli report \
  --config examples/stressed_var_config.yaml \
  --compare-config examples/gaussian_var_config.yaml \
  --bundle-dir reports/example_bundle
```
Generated reports are written to `reports/` locally and are not committed by default.

## Dashboard Instructions
```bash
python3 -m clearrisk.cli dashboard
```
Then open Streamlit in your browser at the URL shown in terminal output (default `http://localhost:8501`).

## Testing
```bash
python3 -m pytest
```

## Key Risk Experiments
- Gaussian vs Student-t tail stress.
- Gaussian vs jump stress.
- VaR vs ES vs stressed VaR.
- No close-out cost vs liquidity-adjusted loss.
- Baseline Cover-2 vs stressed Cover-2 adequacy.
- Assessment burden and second-round default pressure.

## Assumptions and Limitations
- Synthetic data only in v1 (no live or proprietary market feeds).
- Simplified exposure model and close-out approximation.
- Educational waterfall mechanics; not CCP rulebook-specific legal implementation.
- Transparent approximations prioritized over black-box complexity.
- See docs:
  - `docs/model_assumptions.md`
  - `docs/risk_methodology.md`
  - `docs/margin_procyclicality.md`
  - `docs/tail_risk_experiments.md`

## Project Origin
Originally developed as a research-assistant collaboration at Tilburg University with Prof. Dr. Ron Berndsen, then independently extended into a modular CCP stress-testing lab focused on margin procyclicality, tail risk, Cover-2 adequacy, and waterfall loss allocation.

## Disclaimer
This project is for education, research, and portfolio demonstration only. It is not a production CCP model, regulatory capital model, investment tool, trading system, or financial advice.

## Roadmap
- Broader stress scenario templates and calibration controls.
- More explicit wrong-way risk factor modeling.
- Enhanced liquidation/auction approximation.
- Intraday margin mechanics and collateral extensions.
- Additional reporting bundles and dashboard narratives.
