# Model Assumptions

## Scope
- Educational, research-oriented CCP stress-testing simulator.
- Synthetic-data-only v1 design for reproducibility and assumption control.
- Transparent, auditable waterfall accounting with explicit layer usage logs.

## Core Simplifications
- Member/default behavior is stylized and driven by configured stress losses and buffers.
- Liquidity close-out costs are modeled as configurable heuristics, not auction microstructure.
- Wrong-way risk treatment is stylized (extension-oriented), not a calibrated credit-default model.
- Portfolio representation is simplified compared with production clearing stacks.

## Data Assumptions
- No live market feeds.
- No exchange-proprietary or paid vendor datasets.
- No Bloomberg/Refinitiv or rulebook-embedded calibration datasets in v1.

## Out of Scope
- Production CCP rulebook implementation.
- Legal/regulatory capital model usage.
- Trading or investment decision support.
- Full collateral eligibility, settlement operations, and intraday liquidation operations.

## Integrity Statement
This project is for education, research, and portfolio demonstration. It is not a production CCP model, regulatory model, investment tool, or trading advice system.
