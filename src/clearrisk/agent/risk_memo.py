from __future__ import annotations

from .prompts import RISK_MEMO_PROMPT
from ..config import SimulationResult


def generate_risk_memo(result: SimulationResult) -> str:
    scenario = result.scenario_metadata.get("scenario_name", "unspecified")
    residual = result.residual_shortfall
    defaults = len(result.defaulted_members)
    return "\n".join(
        [
            "# Risk Memo (Structured Template)",
            "",
            f"Scenario: {scenario}",
            f"Observed defaults: {defaults}",
            f"Residual shortfall: {residual:.2f}",
            "",
            "Interpretation:",
            "- This memo is generated from simulation outputs only.",
            "- The optional AI narrative layer is not enabled in Phase 1.",
            "",
            "Limitations:",
            "- Educational/research simulator, not a production CCP model.",
            "- Simplified assumptions remain in place for v1.",
            "",
            "Prompt reference:",
            RISK_MEMO_PROMPT.strip(),
        ]
    )

