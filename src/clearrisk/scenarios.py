from __future__ import annotations

from typing import Dict, List, Optional

from .config import MarketScenario
from .stress import apply_stress_overlay


def laptop_friendly_defaults() -> Dict[str, int]:
    return {
        "quickstart_n_paths": 500,
        "standard_n_paths": 1000,
        "dashboard_n_paths": 300,
        "stress_lab_n_paths": 5000,
        "default_horizon_days": 252,
        "default_member_count": 20,
        "default_asset_count": 3,
    }


def generate_scenario_set(base_scenario: Optional[MarketScenario] = None) -> List[MarketScenario]:
    base = base_scenario or MarketScenario(
        scenario_name="gaussian_baseline",
        drift=0.06,
        volatility=0.20,
        jump_probability=0.0,
        jump_size_distribution="none",
        liquidity_spread_multiplier=1.0,
        stress_label="baseline",
    )

    high_vol_stress = apply_stress_overlay(
        base,
        volatility_multiplier=1.75,
        liquidity_multiplier=1.30,
        correlation_stress_label="high_vol_stress",
    )
    high_vol_stress.scenario_name = "high_volatility_stress"
    high_vol_stress.jump_probability = 0.0
    high_vol_stress.jump_size_distribution = "none"

    fat_tail = MarketScenario(
        scenario_name="student_t_fat_tail",
        drift=base.drift,
        volatility=base.volatility,
        correlation_matrix=base.correlation_matrix,
        jump_probability=0.0,
        jump_size_distribution="student_t_df4",
        liquidity_spread_multiplier=base.liquidity_spread_multiplier * 1.15,
        stress_label="fat_tail",
    )

    jump = MarketScenario(
        scenario_name="jump_diffusion_stress",
        drift=base.drift,
        volatility=base.volatility,
        correlation_matrix=base.correlation_matrix,
        jump_probability=0.03,
        jump_size_distribution="normal(mean=-0.10,std=0.04)",
        liquidity_spread_multiplier=base.liquidity_spread_multiplier * 1.25,
        stress_label="jump_diffusion",
    )
    return [base, fat_tail, jump, high_vol_stress]

