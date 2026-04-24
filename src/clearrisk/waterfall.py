from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Optional

from .config import ClearingMember, WaterfallConfig, WaterfallLayerLog, WaterfallOutcome
from .members import allocate_capped_assessments, assessment_caps_from_members


def apply_waterfall(
    loss_amount: float,
    defaulter_im: float,
    defaulter_df: float,
    survivor_df_pool: float,
    assessment_capacity: float,
    config: WaterfallConfig,
    survivor_members: Optional[List[ClearingMember]] = None,
    survivor_assessment_caps: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    total_loss = max(0.0, float(loss_amount))
    remaining = total_loss
    usage = {
        "defaulter_im": 0.0,
        "defaulter_df": 0.0,
        "ccp_skin_in_game": 0.0,
        "survivor_df": 0.0,
        "assessment": 0.0,
    }
    layer_logs: List[WaterfallLayerLog] = []

    def take(layer: str, capacity: float, payer: str) -> float:
        nonlocal remaining
        clean_capacity = max(0.0, float(capacity))
        starting_loss = remaining
        amount = min(clean_capacity, remaining)
        usage[layer] = amount
        remaining -= amount
        layer_logs.append(
            WaterfallLayerLog(
                layer=layer,
                starting_loss=float(starting_loss),
                capacity=float(clean_capacity),
                used=float(amount),
                remaining_loss=float(remaining),
                payer=payer,
            )
        )
        return amount

    take("defaulter_im", defaulter_im, payer="defaulter")
    defaulter_df_capacity = defaulter_df if config.include_defaulter_df else 0.0
    take("defaulter_df", defaulter_df_capacity, payer="defaulter")
    take("ccp_skin_in_game", config.ccp_skin_in_game, payer="ccp")
    take("survivor_df", survivor_df_pool, payer="survivors_df")

    if survivor_assessment_caps is not None:
        caps_by_member = {k: max(0.0, float(v)) for k, v in survivor_assessment_caps.items()}
    elif survivor_members is not None:
        caps_by_member = assessment_caps_from_members(survivor_members, config.assessment_cap_multiple)
    else:
        caps_by_member = {}

    cap_from_members = sum(caps_by_member.values())
    assessment_layer_capacity = min(max(0.0, float(assessment_capacity)), cap_from_members) if caps_by_member else max(
        0.0, float(assessment_capacity)
    )
    assessment_used = take("assessment", assessment_layer_capacity, payer="survivors_assessment")

    if caps_by_member:
        assessment_by_member = allocate_capped_assessments(assessment_used, caps_by_member)
    else:
        assessment_by_member = {"survivor_pool": assessment_used} if assessment_used > 0.0 else {}

    shortfall = max(0.0, remaining)
    total_applied = sum(usage.values())
    balance_gap = total_loss - (total_applied + shortfall)
    is_balanced = abs(balance_gap) <= 1e-9
    if is_balanced:
        balance_gap = 0.0

    outcome = WaterfallOutcome(
        total_loss=total_loss,
        layer_usage=usage,
        layer_logs=layer_logs,
        assessment_by_member=assessment_by_member,
        assessment_caps_by_member=caps_by_member,
        shortfall=shortfall,
        total_applied=total_applied,
        balance_gap=balance_gap,
        is_balanced=is_balanced,
    )
    output = asdict(outcome)
    output.update(
        {
            "shortfall": shortfall,
            "total_applied": total_applied,
            "balance_gap": balance_gap,
            "is_balanced": is_balanced,
        }
    )
    output.update(usage)
    # Backward-compat alias used by early scaffolding.
    output["mutualized_df"] = usage["survivor_df"]
    return output
