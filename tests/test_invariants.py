from clearrisk.config import ClearingMember, WaterfallConfig
from clearrisk.waterfall import apply_waterfall


def _survivors() -> list[ClearingMember]:
    return [
        ClearingMember(member_id="S1", default_fund_contribution=25.0),
        ClearingMember(member_id="S2", default_fund_contribution=40.0),
    ]


def test_no_negative_layer_usage_or_balances() -> None:
    result = apply_waterfall(
        loss_amount=250.0,
        defaulter_im=-10.0,
        defaulter_df=-5.0,
        survivor_df_pool=20.0,
        assessment_capacity=30.0,
        config=WaterfallConfig(ccp_skin_in_game=-15.0, assessment_cap_multiple=0.5),
        survivor_members=_survivors(),
    )
    numeric_fields = [
        "defaulter_im",
        "defaulter_df",
        "ccp_skin_in_game",
        "survivor_df",
        "assessment",
        "shortfall",
        "total_applied",
    ]
    for field in numeric_fields:
        value = result[field]
        assert value >= 0.0


def test_assessment_layer_matches_member_allocations() -> None:
    result = apply_waterfall(
        loss_amount=150.0,
        defaulter_im=0.0,
        defaulter_df=0.0,
        survivor_df_pool=0.0,
        assessment_capacity=50.0,
        config=WaterfallConfig(ccp_skin_in_game=0.0, assessment_cap_multiple=1.0),
        survivor_members=_survivors(),
    )
    assessed_total = sum(result["assessment_by_member"].values())
    assert abs(assessed_total - result["assessment"]) < 1e-9
