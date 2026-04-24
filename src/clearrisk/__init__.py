from __future__ import annotations

import math
from typing import Dict

from .analytics import (
    compute_basic_metrics,
    compute_probability_metrics,
    expected_shortfall_statistics,
    scenario_comparison_outputs,
    tail_loss_ratio,
)
from .config import (
    ClearingMember,
    CloseoutCostConfig,
    ContagionConfig,
    DefaultFundMetrics,
    MarginConfig,
    MarketScenario,
    Position,
    Portfolio,
    SimulationConfig,
    SimulationResult,
    WaterfallConfig,
)
from .contagion import compute_closeout_cost, compute_losses_with_closeout, evaluate_assessment_contagion
from .default_fund import compute_default_fund_metrics, uncovered_stress_losses_by_member
from .margin import compute_initial_margin
from .members import clone_member, member_total_notional, portfolio_concentration_index
from .reporting import (
    build_practitioner_table_rows,
    build_scenario_comparison_summary,
    export_scenario_comparison_csv,
    export_scenario_comparison_json,
    format_scenario_comparison_summary,
    generate_report,
    write_report_bundle,
)
from .scenarios import generate_scenario_set
from .waterfall import apply_waterfall


def _default_result_metadata(config: SimulationConfig, scenario: MarketScenario) -> Dict[str, str]:
    return {
        "run_name": config.run_name,
        "scenario_name": scenario.scenario_name,
        "stress_label": scenario.stress_label,
    }


def _estimate_clean_loss(
    member: ClearingMember,
    scenario: MarketScenario,
    *,
    time_horizon_days: int,
) -> float:
    horizon_scale = math.sqrt(max(1, int(time_horizon_days)) / 252.0)
    notional = member_total_notional(member)
    volatility = max(0.0, float(scenario.volatility))
    clean_loss = notional * volatility * horizon_scale * 0.25
    return float(max(0.0, clean_loss))


def run_simulation(config: SimulationConfig) -> SimulationResult:
    scenario = config.scenarios[0] if config.scenarios else generate_scenario_set()[0]
    members = [clone_member(member) for member in config.members]

    im_by_member = {}
    clean_losses_by_member = {}
    concentration_by_member = {}
    vm_flows = {}
    for member in members:
        im_by_member[member.member_id] = compute_initial_margin(member, scenario, config.margin)
        clean_losses_by_member[member.member_id] = _estimate_clean_loss(
            member,
            scenario,
            time_horizon_days=config.time_horizon_days,
        )
        concentration_by_member[member.member_id] = portfolio_concentration_index(member.portfolio)
        vm_flows[member.member_id] = 0.0

    closeout_breakdown = compute_losses_with_closeout(
        clean_losses_by_member,
        concentration_by_member,
        config.closeout,
        volatility_stress_multiplier=scenario.liquidity_spread_multiplier,
    )
    total_losses_with_closeout_by_member = closeout_breakdown["total_losses_with_closeout_by_member"]
    closeout_addon_by_member = closeout_breakdown["closeout_addon_by_member"]
    if config.include_liquidity_closeout_cost:
        member_losses = dict(total_losses_with_closeout_by_member)
    else:
        member_losses = dict(clean_losses_by_member)

    first_round_defaults = []
    for member in members:
        member_id = member.member_id
        required_resources = im_by_member.get(member_id, 0.0) + max(0.0, member.default_fund_contribution)
        if member_losses.get(member_id, 0.0) > required_resources:
            member.is_defaulted = True
            member.default_round = "first_round"
            first_round_defaults.append(member_id)

    survivors = [member for member in members if not member.is_defaulted]
    defaulters = [member for member in members if member.is_defaulted]

    defaulter_loss = sum(member_losses.get(member.member_id, 0.0) for member in defaulters)
    defaulter_im = sum(im_by_member.get(member.member_id, 0.0) for member in defaulters)
    defaulter_df = sum(max(0.0, member.default_fund_contribution) for member in defaulters)
    survivor_df_pool = sum(max(0.0, member.default_fund_contribution) for member in survivors)
    assessment_capacity = survivor_df_pool * max(0.0, config.waterfall.assessment_cap_multiple)

    waterfall_out = apply_waterfall(
        loss_amount=defaulter_loss,
        defaulter_im=defaulter_im,
        defaulter_df=defaulter_df,
        survivor_df_pool=survivor_df_pool,
        assessment_capacity=assessment_capacity,
        config=config.waterfall,
        survivor_members=survivors,
    )
    assessment_burden_by_member = dict(waterfall_out.get("assessment_by_member", {}))

    contagion_out = evaluate_assessment_contagion(
        survivors,
        assessment_burden_by_member,
        first_round_defaults=first_round_defaults,
        liquidity_breach_ratio=config.contagion.liquidity_breach_ratio,
    )
    second_round_defaults = list(contagion_out["second_round_defaults"])
    defaulted_members = sorted(set(first_round_defaults + second_round_defaults))

    cover2_metrics = compute_default_fund_metrics(member_losses, im_by_member, config.waterfall).to_dict()
    residual_shortfall = float(waterfall_out["shortfall"] + contagion_out["systemic_shortfall"])

    interpretation_flags = []
    if config.include_liquidity_closeout_cost:
        interpretation_flags.append("closeout_costs_included")
    else:
        interpretation_flags.append("clean_losses_only")
    if second_round_defaults:
        interpretation_flags.append("second_round_contagion_triggered")

    result = SimulationResult(
        member_losses=member_losses,
        clean_losses_by_member=clean_losses_by_member,
        closeout_addon_by_member=closeout_addon_by_member,
        total_losses_with_closeout_by_member=total_losses_with_closeout_by_member,
        im_by_member=im_by_member,
        vm_flows=vm_flows,
        defaulted_members=defaulted_members,
        first_round_defaults=first_round_defaults,
        second_round_defaults=second_round_defaults,
        waterfall_layer_usage=waterfall_out["layer_usage"],
        waterfall_ledger=waterfall_out["layer_logs"],
        default_fund_depletion=float(waterfall_out["survivor_df"]),
        assessments=assessment_burden_by_member,
        assessment_caps_by_member=waterfall_out.get("assessment_caps_by_member", {}),
        residual_shortfall=residual_shortfall,
        balance_gap=float(waterfall_out.get("balance_gap", 0.0)),
        scenario_metadata=_default_result_metadata(config, scenario),
        interpretation_flags=interpretation_flags,
        metrics={},
    )
    result.metrics.update(
        {
            **cover2_metrics,
            "total_clean_loss": float(closeout_breakdown["total_clean_loss"]),
            "total_closeout_addon": float(closeout_breakdown["total_closeout_addon"]),
            "total_loss_with_closeout": float(closeout_breakdown["total_loss_with_closeout"]),
            "assessment_contagion_rate": float(contagion_out["contagion_multiplier"]),
            "first_round_default_count": float(len(first_round_defaults)),
            "second_round_default_count": float(len(second_round_defaults)),
            "waterfall_shortfall": float(waterfall_out["shortfall"]),
        }
    )
    result.metrics.update(compute_basic_metrics(result))
    return result


__all__ = [
    "ClearingMember",
    "CloseoutCostConfig",
    "ContagionConfig",
    "DefaultFundMetrics",
    "MarginConfig",
    "MarketScenario",
    "Position",
    "Portfolio",
    "SimulationConfig",
    "SimulationResult",
    "WaterfallConfig",
    "run_simulation",
    "generate_scenario_set",
    "compute_initial_margin",
    "compute_default_fund_metrics",
    "uncovered_stress_losses_by_member",
    "compute_probability_metrics",
    "expected_shortfall_statistics",
    "scenario_comparison_outputs",
    "tail_loss_ratio",
    "compute_closeout_cost",
    "compute_losses_with_closeout",
    "evaluate_assessment_contagion",
    "apply_waterfall",
    "build_practitioner_table_rows",
    "build_scenario_comparison_summary",
    "export_scenario_comparison_csv",
    "export_scenario_comparison_json",
    "format_scenario_comparison_summary",
    "generate_report",
    "write_report_bundle",
]
