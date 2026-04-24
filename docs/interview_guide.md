# Technical Interview Guide

## 30-Second Pitch
ClearRisk Lab is an educational CCP stress-testing simulator that shows how margin, default-fund sizing, and waterfall design can look robust under baseline assumptions but become fragile under tail risk, liquidity frictions, concentration, and assessment pressure.

## 90-Second Explanation
I built the project as a modular Python package around one core risk question: when does a CCP appear safe, and when does it break under stress assumptions? The simulator compares synthetic stress regimes (Gaussian, fat-tail, jump, and high-volatility), computes margin under multiple methods (VaR, ES, stressed VaR), sizes prefunded resources with Cover-1/Cover-2 logic, and then applies a deterministic default waterfall with layer-by-layer accounting. I also include liquidity close-out add-ons and second-round stress from assessment calls. Outputs are available through CLI commands, scenario configs, report bundles, and notebooks.

## 3-Minute Deep Explanation
The architecture is designed for auditability. Input assumptions are explicit in typed configs. Each simulation run computes member-level margin, stress losses, and concentration effects, then routes losses through an explicit waterfall order: defaulter IM, defaulter DF, CCP skin-in-the-game, survivor DF, capped assessments, and residual shortfall. Every layer is logged with starting loss, capacity, usage, and remaining loss, so there is no hidden loss leakage.

On top of first-round defaults, the model checks whether assessment burdens breach survivor liquidity thresholds and flags second-round defaults. This makes it possible to discuss a practical tradeoff: stronger prefunded defenses can reduce immediate shortfall, but stress can still migrate through liquidity channels.

The project is intentionally synthetic-data-first in v1. That keeps assumptions transparent and reproducible for portfolio use, while avoiding false precision from weak calibration. I present it as an educational research simulator, not a production CCP rulebook engine.

## Key Concepts to Know
- Initial Margin (IM): prefunded risk buffer against future exposure over MPOR.
- Variation Margin (VM): mark-to-market transfer that settles realized P&L.
- Default Fund (DF): mutualized prefunded resources beyond defaulter resources.
- Cover-2: adequacy benchmark based on the two largest uncovered member stress losses.
- VaR vs ES: VaR gives a quantile threshold; ES averages tail losses beyond that threshold.
- Waterfall: explicit loss-allocation sequence across defaulter, CCP, and survivors.
- Procyclicality: margin can rise sharply in stress and strain member liquidity.
- Liquidity Close-Out Cost: loss add-on beyond clean MTM due to liquidation friction.
- Assessment Contagion: survivor assessments can create second-round stress/defaults.

## Hard Interview Questions and Concise Answers
- Why synthetic data in v1?
  - It keeps assumptions transparent, reproducible, and legally clean while validating architecture and risk logic.
- How is this different from a toy notebook?
  - It is modular, test-backed, config-driven, and auditable with deterministic waterfall logs and comparison outputs.
- What does Cover-2 add here?
  - It quantifies prefunded adequacy against concentrated stress and makes deficits explicit.
- How did you validate correctness?
  - Through invariants and behavior tests for margin scaling, waterfall balance, stress comparisons, contagion triggers, and CLI/report smoke paths.
- Is this production CCP calibration?
  - No. It is educational and research-oriented, with stylized assumptions documented explicitly.

## Limitations to State Clearly
- Synthetic scenarios only in v1.
- Simplified member exposure/default behavior.
- Stylized close-out and wrong-way-risk treatment.
- Not legal or rulebook-specific CCP implementation.
- Not a production, regulatory, investment, or trading decision engine.

## Honest AI Assistance Framing
I used AI coding assistance to accelerate refactoring, scaffolding, tests, and documentation, while I owned the project thesis, requirements, review decisions, and final acceptance. I can explain the model assumptions, architecture, validations, and limitations directly.
