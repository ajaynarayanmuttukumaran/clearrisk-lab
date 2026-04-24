from clearrisk.config import WaterfallConfig
from clearrisk.default_fund import compute_default_fund_metrics


def test_cover2_required_resources_from_two_largest_uncovered_losses() -> None:
    stress_losses = {"A": 180.0, "B": 150.0, "C": 120.0, "D": 90.0}
    im_by_member = {"A": 100.0, "B": 80.0, "C": 70.0, "D": 60.0}
    metrics = compute_default_fund_metrics(
        stress_losses,
        im_by_member,
        WaterfallConfig(default_fund_method="cover2"),
    )
    # Uncovered = {A:80, B:70, C:50, D:30}; top two = 150
    assert metrics.cover2_required_resources == 150.0


def test_higher_stress_losses_increase_cover2_required_resources() -> None:
    im = {"A": 50.0, "B": 50.0, "C": 50.0}
    low_stress = {"A": 90.0, "B": 80.0, "C": 70.0}
    high_stress = {"A": 140.0, "B": 130.0, "C": 120.0}
    low = compute_default_fund_metrics(low_stress, im, WaterfallConfig(default_fund_method="cover2"))
    high = compute_default_fund_metrics(high_stress, im, WaterfallConfig(default_fund_method="cover2"))
    assert high.cover2_required_resources > low.cover2_required_resources


def test_cover2_adequacy_ratio_is_calculated_correctly() -> None:
    stress_losses = {"A": 200.0, "B": 190.0, "C": 40.0}
    im_by_member = {"A": 100.0, "B": 100.0, "C": 20.0}
    cfg = WaterfallConfig(default_fund_method="fixed", default_fund_value=180.0)
    metrics = compute_default_fund_metrics(stress_losses, im_by_member, cfg)
    # Uncovered: A=100, B=90, C=20 => cover2 required=190; adequacy=180/190
    assert abs(metrics.cover2_required_resources - 190.0) < 1e-9
    assert abs(metrics.cover2_adequacy_ratio - (180.0 / 190.0)) < 1e-9
    assert abs(metrics.cover2_surplus_or_deficit - (180.0 - 190.0)) < 1e-9


def test_fixed_default_fund_mode_remains_fixed() -> None:
    stress_losses = {"A": 500.0, "B": 400.0}
    im_by_member = {"A": 10.0, "B": 20.0}
    cfg = WaterfallConfig(default_fund_method="fixed", default_fund_value=75.0)
    metrics = compute_default_fund_metrics(stress_losses, im_by_member, cfg)
    assert metrics.available_prefunded_resources == 75.0

