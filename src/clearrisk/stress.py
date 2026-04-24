from __future__ import annotations

from .config import MarketScenario


def apply_stress_overlay(
    scenario: MarketScenario,
    volatility_multiplier: float = 1.0,
    liquidity_multiplier: float = 1.0,
    correlation_stress_label: str = "stressed",
) -> MarketScenario:
    stressed = MarketScenario(
        scenario_name=f"{scenario.scenario_name}_{correlation_stress_label}",
        drift=scenario.drift,
        volatility=scenario.volatility * volatility_multiplier,
        correlation_matrix=scenario.correlation_matrix,
        jump_probability=scenario.jump_probability,
        jump_size_distribution=scenario.jump_size_distribution,
        liquidity_spread_multiplier=scenario.liquidity_spread_multiplier * liquidity_multiplier,
        stress_label=correlation_stress_label,
    )
    return stressed


def apply_wrong_way_risk(loss_amount: float, credit_quality_score: float, stress_level: float) -> float:
    quality_penalty = 1.0 + max(0.0, 1.0 - credit_quality_score)
    stress_penalty = 1.0 + max(0.0, stress_level)
    return float(loss_amount * quality_penalty * stress_penalty)

