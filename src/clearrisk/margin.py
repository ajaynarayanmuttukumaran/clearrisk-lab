from __future__ import annotations

import math

from scipy.stats import norm

from .config import ClearingMember, MarginConfig, MarketScenario
from .members import member_total_notional, portfolio_concentration_index


def _z_score(confidence_level: float) -> float:
    return float(norm.ppf(confidence_level))


def _normal_es_multiplier(confidence_level: float) -> float:
    alpha = min(max(float(confidence_level), 1e-6), 1.0 - 1e-6)
    z = _z_score(alpha)
    return float(norm.pdf(z) / (1.0 - alpha))


def _mpor_scale(mpor_days: int) -> float:
    return math.sqrt(max(1, int(mpor_days)) / 252.0)


def _effective_volatility(
    scenario: MarketScenario,
    margin_config: MarginConfig,
    *,
    stressed: bool = False,
) -> float:
    sigma = max(float(scenario.volatility), float(margin_config.volatility_floor))
    if stressed:
        multiplier = max(1.0, float(margin_config.stressed_var_vol_multiplier))
        sigma *= multiplier
    return sigma


def compute_initial_margin(
    member: ClearingMember,
    scenario: MarketScenario,
    margin_config: MarginConfig,
) -> float:
    mpor_scale = _mpor_scale(margin_config.margin_period_of_risk_days)
    gross_notional = member_total_notional(member)
    alpha = min(max(float(margin_config.confidence_level), 1e-6), 1.0 - 1e-6)
    z = _z_score(alpha)

    if margin_config.method == "expected_shortfall":
        sigma = _effective_volatility(scenario, margin_config, stressed=False)
        tail_mult = _normal_es_multiplier(alpha)
        core_margin = gross_notional * sigma * mpor_scale * tail_mult
    elif margin_config.method == "stressed_var":
        sigma = _effective_volatility(scenario, margin_config, stressed=True)
        core_margin = gross_notional * sigma * mpor_scale * z
    else:
        # Gaussian VaR baseline for gaussian_var / buffered_var / historical_var placeholder.
        sigma = _effective_volatility(scenario, margin_config, stressed=False)
        core_margin = gross_notional * sigma * mpor_scale * z

    concentration_idx = portfolio_concentration_index(member.portfolio)
    concentration_factor = max(0.0, margin_config.concentration_addon) * concentration_idx
    liquidity_factor = max(0.0, margin_config.liquidity_addon) * max(1.0, scenario.liquidity_spread_multiplier)
    addon_factor = 1.0 + concentration_factor + liquidity_factor
    buffered_factor = 1.0 + max(0.0, margin_config.anti_procyclicality_buffer)

    margin_total = core_margin * addon_factor * buffered_factor
    return float(max(0.0, margin_total))
