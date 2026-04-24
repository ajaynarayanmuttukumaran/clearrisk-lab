from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .config import ClearingMember, CloseoutCostConfig


def compute_closeout_cost(
    clean_loss: float,
    concentration_score: float,
    config: CloseoutCostConfig,
    volatility_stress_multiplier: float = 1.0,
) -> float:
    clean = max(0.0, float(clean_loss))
    concentration = max(0.0, float(concentration_score))
    stress_mult = max(0.0, float(volatility_stress_multiplier))
    rate = (
        max(0.0, float(config.base_spread_cost))
        + max(0.0, float(config.volatility_liquidity_multiplier)) * stress_mult
        + max(0.0, float(config.concentration_penalty)) * concentration
        + max(0.0, float(config.market_depth_penalty))
    )
    return float(clean * rate)


def compute_losses_with_closeout(
    clean_losses_by_member: Dict[str, float],
    concentration_by_member: Dict[str, float],
    config: CloseoutCostConfig,
    volatility_stress_multiplier: float = 1.0,
) -> Dict[str, object]:
    clean_losses: Dict[str, float] = {}
    closeout_addon_by_member: Dict[str, float] = {}
    total_losses_with_closeout: Dict[str, float] = {}

    member_ids = set(clean_losses_by_member) | set(concentration_by_member)
    for member_id in sorted(member_ids):
        clean = max(0.0, float(clean_losses_by_member.get(member_id, 0.0)))
        concentration = max(0.0, float(concentration_by_member.get(member_id, 0.0)))
        addon = compute_closeout_cost(clean, concentration, config, volatility_stress_multiplier)
        clean_losses[member_id] = clean
        closeout_addon_by_member[member_id] = addon
        total_losses_with_closeout[member_id] = clean + addon

    total_clean_loss = sum(clean_losses.values())
    total_closeout_addon = sum(closeout_addon_by_member.values())
    total_loss_with_closeout = sum(total_losses_with_closeout.values())

    return {
        "clean_losses_by_member": clean_losses,
        "closeout_addon_by_member": closeout_addon_by_member,
        "total_losses_with_closeout_by_member": total_losses_with_closeout,
        "total_clean_loss": float(total_clean_loss),
        "total_closeout_addon": float(total_closeout_addon),
        "total_loss_with_closeout": float(total_loss_with_closeout),
    }


def evaluate_assessment_contagion(
    survivors: Iterable[ClearingMember],
    assessment_burden_by_member: Dict[str, float],
    *,
    first_round_defaults: Optional[List[str]] = None,
    liquidity_breach_ratio: float = 1.0,
) -> Dict[str, object]:
    first_round = list(first_round_defaults or [])
    first_round_set = set(first_round)
    threshold_ratio = max(0.0, float(liquidity_breach_ratio))

    second_round_defaults: List[str] = []
    burden_cleaned: Dict[str, float] = {}
    breach_excess_by_member: Dict[str, float] = {}

    for member in survivors:
        burden = max(0.0, float(assessment_burden_by_member.get(member.member_id, 0.0)))
        burden_cleaned[member.member_id] = burden

        if member.member_id in first_round_set or member.is_defaulted:
            breach_excess_by_member[member.member_id] = 0.0
            continue

        liquidity_limit = max(0.0, float(member.liquidity_buffer)) * threshold_ratio
        breach_excess = max(0.0, burden - liquidity_limit)
        breach_excess_by_member[member.member_id] = breach_excess

        if breach_excess > 0.0:
            member.is_defaulted = True
            member.default_round = "second_round"
            second_round_defaults.append(member.member_id)

    first_count = len(first_round)
    second_count = len(second_round_defaults)
    contagion_multiplier = float(second_count / first_count) if first_count > 0 else float(second_count)

    return {
        "first_round_defaults": first_round,
        "second_round_defaults": second_round_defaults,
        "assessment_burden_by_member": burden_cleaned,
        "breach_excess_by_member": breach_excess_by_member,
        "contagion_multiplier": contagion_multiplier,
        "systemic_shortfall": float(sum(breach_excess_by_member.values())),
    }

