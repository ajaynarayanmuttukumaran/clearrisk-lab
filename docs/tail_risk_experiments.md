# Tail-Risk Experiments

ClearRisk Lab includes scenario comparisons designed to show when baseline assumptions can understate stress outcomes.

## Available Experiment Families
- Gaussian baseline vs Student-t fat-tail stress.
- Gaussian baseline vs jump-diffusion stress.
- Baseline volatility vs high-volatility stress overlays.
- Clean mark-to-market loss vs liquidity close-out adjusted loss.
- Baseline config vs recruiter synthetic demo stress config.

## Suggested Run Patterns
- `python3 -m clearrisk.cli compare --config-a examples/gaussian_var_config.yaml --config-b examples/fat_tail_config.yaml`
- `python3 -m clearrisk.cli compare --config-a examples/gaussian_var_config.yaml --config-b examples/stressed_var_config.yaml`
- `python3 -m clearrisk.cli run --config examples/recruiter_demo_stress_config.yaml`

## What to Look For
- Tail-loss amplification versus Gaussian baseline.
- Higher waterfall layer usage and increased residual shortfall under stress.
- Cover-2 adequacy deterioration in concentrated or liquidity-stressed settings.
- Assessment burden escalation and second-round stress flags.

## Interpretation Boundary
These experiments are educational stress tests under synthetic assumptions, not calibrated forecasts of actual CCP default events.
