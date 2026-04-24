# Margin Procyclicality

Margin procyclicality is the tradeoff between stronger CCP protection and higher member liquidity pressure during stress.

## Core Tradeoff
- Higher margin generally improves prefunded loss absorbency.
- The same margin sensitivity can increase liquidity demands on members when volatility spikes.
- Risk governance should evaluate both adequacy and liquidity burden, not one in isolation.

## Current Diagnostics in ClearRisk Lab
- Member-level IM outputs (`im_by_member`) for each run.
- Total IM and margin adequacy ratio (`total_im / total_loss`) in summary metrics.
- Baseline-vs-stress comparison outputs for mean margin adequacy deltas.
- Stress scenarios with volatility, fat tails, and jump assumptions to test margin sensitivity.

## Practical Interpretation
- If stressed regimes increase IM while shortfall risk remains high, margin design may still be insufficient.
- If margin appears adequate but survivor liquidity stress rises through assessments, resilience is mixed rather than absolute.
- Procyclicality should be discussed together with Cover-2 adequacy and contagion channels.

## Scope Note
Current implementation focuses on scenario-level comparisons and transparent diagnostics, not full intraday margin-call path modeling.
