from clearrisk import run_simulation
from clearrisk.config import (
    ClearingMember,
    CloseoutCostConfig,
    ContagionConfig,
    MarginConfig,
    MarketScenario,
    Portfolio,
    Position,
    SimulationConfig,
    WaterfallConfig,
)


def _member(member_id: str, notional: float, df: float, liquidity: float) -> ClearingMember:
    return ClearingMember(
        member_id=member_id,
        portfolio=Portfolio(positions=[Position(asset_id="IDX", quantity=notional, price=1.0)]),
        default_fund_contribution=df,
        liquidity_buffer=liquidity,
    )


def test_run_simulation_includes_cover2_and_closeout_breakdown() -> None:
    config = SimulationConfig(
        time_horizon_days=1000,
        include_liquidity_closeout_cost=True,
        margin=MarginConfig(method="gaussian_var", confidence_level=0.99, margin_period_of_risk_days=5),
        closeout=CloseoutCostConfig(
            base_spread_cost=0.01,
            volatility_liquidity_multiplier=0.02,
            concentration_penalty=0.03,
            market_depth_penalty=0.01,
        ),
        waterfall=WaterfallConfig(default_fund_method="cover2"),
        scenarios=[MarketScenario(volatility=0.8, liquidity_spread_multiplier=1.25)],
        members=[
            _member("A", notional=1_000_000.0, df=20_000.0, liquidity=100_000.0),
            _member("B", notional=800_000.0, df=15_000.0, liquidity=100_000.0),
        ],
    )
    result = run_simulation(config)

    assert result.metrics["cover2_required_resources"] >= 0.0
    assert result.metrics["available_prefunded_resources"] >= 0.0
    assert result.metrics["cover2_adequacy_ratio"] >= 0.0
    assert result.metrics["total_loss_with_closeout"] >= result.metrics["total_clean_loss"]
    assert set(result.clean_losses_by_member) == {"A", "B"}
    assert set(result.total_losses_with_closeout_by_member) == {"A", "B"}


def test_run_simulation_tracks_first_and_second_round_defaults() -> None:
    config = SimulationConfig(
        time_horizon_days=5000,
        include_liquidity_closeout_cost=False,
        margin=MarginConfig(method="gaussian_var", confidence_level=0.99, margin_period_of_risk_days=5),
        contagion=ContagionConfig(liquidity_breach_ratio=1.0),
        waterfall=WaterfallConfig(
            ccp_skin_in_game=0.0,
            assessment_cap_multiple=0.20,
            default_fund_method="fixed",
            default_fund_value=0.0,
        ),
        scenarios=[MarketScenario(volatility=0.8, liquidity_spread_multiplier=1.0)],
        members=[
            _member("D1", notional=10_000_000.0, df=0.0, liquidity=10_000.0),
            _member("S1", notional=200_000.0, df=130_000.0, liquidity=20_000.0),
            _member("S2", notional=200_000.0, df=130_000.0, liquidity=120_000.0),
        ],
    )
    result = run_simulation(config)

    assert "D1" in result.first_round_defaults
    assert "S1" in result.second_round_defaults
    assert "S2" not in result.second_round_defaults
    assert result.assessments["S1"] > 0.0
    assert result.metrics["second_round_default_count"] >= 1.0
