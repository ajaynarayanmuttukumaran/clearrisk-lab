from clearrisk.config import ClearingMember, CloseoutCostConfig
from clearrisk.contagion import compute_losses_with_closeout, evaluate_assessment_contagion


def test_closeout_costs_increase_total_default_loss() -> None:
    clean_losses = {"A": 100.0, "B": 80.0}
    concentrations = {"A": 0.8, "B": 0.4}
    closeout_cfg = CloseoutCostConfig(
        base_spread_cost=0.02,
        volatility_liquidity_multiplier=0.03,
        concentration_penalty=0.05,
        market_depth_penalty=0.01,
    )
    out = compute_losses_with_closeout(clean_losses, concentrations, closeout_cfg, volatility_stress_multiplier=1.0)
    assert out["total_loss_with_closeout"] > out["total_clean_loss"]
    assert out["total_closeout_addon"] > 0.0


def test_higher_concentration_increases_closeout_cost() -> None:
    clean_losses = {"A": 100.0, "B": 100.0}
    closeout_cfg = CloseoutCostConfig(
        base_spread_cost=0.01,
        volatility_liquidity_multiplier=0.02,
        concentration_penalty=0.08,
        market_depth_penalty=0.01,
    )
    low_conc = compute_losses_with_closeout(clean_losses, {"A": 0.2, "B": 0.2}, closeout_cfg)
    high_conc = compute_losses_with_closeout(clean_losses, {"A": 0.9, "B": 0.9}, closeout_cfg)
    assert high_conc["total_closeout_addon"] > low_conc["total_closeout_addon"]


def test_assessment_calls_trigger_second_round_default_when_liquidity_breached() -> None:
    survivors = [
        ClearingMember(member_id="S1", liquidity_buffer=10.0),
        ClearingMember(member_id="S2", liquidity_buffer=20.0),
    ]
    assessments = {"S1": 15.0, "S2": 5.0}
    out = evaluate_assessment_contagion(
        survivors,
        assessments,
        first_round_defaults=["D1"],
        liquidity_breach_ratio=1.0,
    )
    assert "S1" in out["second_round_defaults"]
    assert "S2" not in out["second_round_defaults"]
    assert out["first_round_defaults"] == ["D1"]


def test_no_second_round_default_when_liquidity_is_sufficient() -> None:
    survivors = [
        ClearingMember(member_id="S1", liquidity_buffer=30.0),
        ClearingMember(member_id="S2", liquidity_buffer=25.0),
    ]
    assessments = {"S1": 10.0, "S2": 8.0}
    out = evaluate_assessment_contagion(
        survivors,
        assessments,
        first_round_defaults=["D1"],
        liquidity_breach_ratio=1.0,
    )
    assert out["second_round_defaults"] == []
    assert out["systemic_shortfall"] == 0.0

