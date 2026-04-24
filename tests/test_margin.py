from clearrisk.config import ClearingMember, MarginConfig, MarketScenario, Portfolio, Position
from clearrisk.margin import compute_initial_margin


def _member() -> ClearingMember:
    return ClearingMember(
        member_id="CM_1",
        portfolio=Portfolio(positions=[Position(asset_id="IDX", quantity=1_000_000, price=1.0)]),
    )


def test_margin_increases_with_volatility() -> None:
    member = _member()
    margin_cfg = MarginConfig(method="gaussian_var", confidence_level=0.99, margin_period_of_risk_days=5)
    low = compute_initial_margin(member, MarketScenario(volatility=0.1), margin_cfg)
    high = compute_initial_margin(member, MarketScenario(volatility=0.3), margin_cfg)
    assert high > low


def test_margin_scales_with_sqrt_mpor() -> None:
    member = _member()
    scenario = MarketScenario(volatility=0.2)
    mpor_1 = compute_initial_margin(
        member,
        scenario,
        MarginConfig(method="gaussian_var", confidence_level=0.99, margin_period_of_risk_days=1),
    )
    mpor_9 = compute_initial_margin(
        member,
        scenario,
        MarginConfig(method="gaussian_var", confidence_level=0.99, margin_period_of_risk_days=9),
    )
    ratio = mpor_9 / mpor_1
    assert abs(ratio - 3.0) < 0.05


def test_expected_shortfall_is_at_least_var() -> None:
    member = _member()
    scenario = MarketScenario(volatility=0.25)
    var_im = compute_initial_margin(
        member,
        scenario,
        MarginConfig(method="gaussian_var", confidence_level=0.99, margin_period_of_risk_days=5),
    )
    es_im = compute_initial_margin(
        member,
        scenario,
        MarginConfig(method="expected_shortfall", confidence_level=0.99, margin_period_of_risk_days=5),
    )
    assert es_im >= var_im


def test_anti_procyclicality_buffer_increases_margin() -> None:
    member = _member()
    scenario = MarketScenario(volatility=0.2, liquidity_spread_multiplier=1.0)
    unbuffered = compute_initial_margin(
        member,
        scenario,
        MarginConfig(method="gaussian_var", anti_procyclicality_buffer=0.0),
    )
    buffered = compute_initial_margin(
        member,
        scenario,
        MarginConfig(method="gaussian_var", anti_procyclicality_buffer=0.10),
    )
    assert buffered > unbuffered


def test_volatility_floor_prevents_low_margin() -> None:
    member = _member()
    low_vol_scenario = MarketScenario(volatility=0.001)
    no_floor = compute_initial_margin(
        member,
        low_vol_scenario,
        MarginConfig(method="gaussian_var", volatility_floor=0.0),
    )
    with_floor = compute_initial_margin(
        member,
        low_vol_scenario,
        MarginConfig(method="gaussian_var", volatility_floor=0.15),
    )
    assert with_floor > no_floor
