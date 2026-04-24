# Architecture (Phase 1 Skeleton)

ClearRisk Lab is being refactored from notebook-first code into a modular package:

- `src/clearrisk`: domain model, scenario generation, margin, waterfall, analytics, reporting, CLI.
- `tests`: invariants and behavior checks.
- `examples`: run configurations for regime comparison.
- `app`: Streamlit UI shell.

This phase intentionally scaffolds interfaces first; advanced model logic is added in later phases.

