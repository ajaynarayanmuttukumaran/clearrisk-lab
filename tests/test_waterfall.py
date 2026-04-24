from clearrisk.config import ClearingMember, WaterfallConfig
from clearrisk.waterfall import apply_waterfall


def _survivors() -> list[ClearingMember]:
    return [
        ClearingMember(member_id="S1", default_fund_contribution=100.0),
        ClearingMember(member_id="S2", default_fund_contribution=50.0),
    ]


def test_waterfall_logs_layers_in_required_order() -> None:
    result = apply_waterfall(
        loss_amount=180.0,
        defaulter_im=50.0,
        defaulter_df=20.0,
        survivor_df_pool=30.0,
        assessment_capacity=100.0,
        config=WaterfallConfig(ccp_skin_in_game=40.0, assessment_cap_multiple=0.5),
        survivor_members=_survivors(),
    )
    logged_order = [entry["layer"] for entry in result["layer_logs"]]
    assert logged_order == [
        "defaulter_im",
        "defaulter_df",
        "ccp_skin_in_game",
        "survivor_df",
        "assessment",
    ]


def test_waterfall_allocations_sum_to_loss_and_have_no_leakage() -> None:
    result = apply_waterfall(
        loss_amount=325.0,
        defaulter_im=60.0,
        defaulter_df=30.0,
        survivor_df_pool=80.0,
        assessment_capacity=100.0,
        config=WaterfallConfig(ccp_skin_in_game=40.0, assessment_cap_multiple=1.0),
        survivor_members=_survivors(),
    )
    allocated = result["total_applied"] + result["shortfall"]
    assert abs(allocated - 325.0) < 1e-9
    assert result["is_balanced"] is True
    assert result["balance_gap"] == 0.0


def test_survivor_assessment_caps_are_respected() -> None:
    result = apply_waterfall(
        loss_amount=500.0,
        defaulter_im=10.0,
        defaulter_df=5.0,
        survivor_df_pool=20.0,
        assessment_capacity=1_000.0,
        config=WaterfallConfig(ccp_skin_in_game=15.0, assessment_cap_multiple=0.20),
        survivor_members=_survivors(),
    )
    caps = result["assessment_caps_by_member"]
    allocations = result["assessment_by_member"]
    for member_id, paid in allocations.items():
        assert paid <= caps[member_id] + 1e-12
        assert paid >= 0.0
    assert result["assessment"] <= sum(caps.values()) + 1e-12
