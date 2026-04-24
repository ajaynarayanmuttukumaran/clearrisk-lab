# Risk Methodology

ClearRisk Lab evaluates CCP resilience by comparing baseline and stress assumptions across margin, prefunded resources, and loss-allocation mechanics.

## Guiding Risk Question
When can a CCP margin and default waterfall setup appear robust under standard assumptions but become fragile under tail risk, wrong-way risk, liquidity close-out costs, concentration, and assessment pressure?

## Scenario Method
- Baseline Gaussian regime for reference.
- Fat-tail Student-t regime for heavier tail behavior.
- Jump-diffusion regime for discontinuous losses.
- High-volatility stress overlays for regime escalation.

## Margin Method
- Gaussian VaR, Expected Shortfall, and stressed VaR variants.
- MPOR scaling, volatility floor, anti-procyclicality buffer, and concentration/liquidity add-ons.
- Comparison outputs focus on margin adequacy under different assumptions.

## Default Fund and Cover Metrics
- Fixed and percent-of-IM prefunding options.
- Cover-1 and Cover-2 sizing logic based on uncovered stress losses.
- Adequacy ratios, surpluses/deficits, and concentration shares are reported.

## Waterfall Allocation Method
Losses are allocated in explicit order:
1. Defaulter IM
2. Defaulter DF
3. CCP skin-in-the-game
4. Survivor DF
5. Capped survivor assessments
6. Residual shortfall

Each layer is logged with capacity and usage to preserve auditability.

## Liquidity and Contagion Method
- Clean mark-to-market losses can be augmented by configurable close-out cost add-ons.
- Assessment burdens are allocated to survivors subject to caps.
- Second-round stress/default checks are triggered when assessment burden breaches survivor liquidity thresholds.

## Interpretation Discipline
- Results are comparative and assumption-sensitive, not predictive of real-world default probabilities.
- Methodology is educational and transparent by design, with limitations documented explicitly.
