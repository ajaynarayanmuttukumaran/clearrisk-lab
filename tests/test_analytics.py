from clearrisk.analytics import (
    compute_probability_metrics,
    expected_shortfall_statistics,
    scenario_comparison_outputs,
    tail_loss_ratio,
)
from clearrisk.config import SimulationResult


def _result(
    *,
    total_im: float,
    total_loss: float,
    residual_shortfall: float,
    defaulted: bool = False,
    default_fund_depletion: float = 0.0,
    assessment_total: float = 0.0,
) -> SimulationResult:
    return SimulationResult(
        im_by_member={"M1": total_im},
        member_losses={"M1": total_loss},
        defaulted_members=["M1"] if defaulted else [],
        default_fund_depletion=default_fund_depletion,
        assessments={"S1": assessment_total} if assessment_total > 0 else {},
        residual_shortfall=residual_shortfall,
        metrics={"cover2_adequacy_ratio": max(0.0, total_im / total_loss) if total_loss > 0 else 0.0},
    )


def test_probability_metrics_from_result_batch() -> None:
    results = [
        _result(
            total_im=100.0,
            total_loss=80.0,
            residual_shortfall=2.0,
            defaulted=True,
            default_fund_depletion=10.0,
            assessment_total=5.0,
        ),
        _result(total_im=100.0, total_loss=70.0, residual_shortfall=0.0),
        _result(total_im=100.0, total_loss=90.0, residual_shortfall=0.0, defaulted=True),
        _result(total_im=100.0, total_loss=60.0, residual_shortfall=3.0, assessment_total=2.0),
    ]
    metrics = compute_probability_metrics(results)

    assert metrics["prob_member_default"] == 0.5
    assert metrics["prob_default_fund_depletion"] == 0.25
    assert metrics["prob_assessment_calls"] == 0.5
    assert metrics["prob_residual_shortfall"] == 0.5
    assert metrics["expected_residual_shortfall"] == 1.25
    assert metrics["worst_case_residual_shortfall"] == 3.0


def test_expected_shortfall_statistics_properties() -> None:
    stats = expected_shortfall_statistics([1.0, 2.0, 3.0, 100.0], confidence_level=0.75)
    assert abs(stats["var"] - 27.25) < 1e-9
    assert abs(stats["expected_shortfall"] - 100.0) < 1e-9
    assert stats["expected_shortfall"] >= stats["var"]


def test_tail_loss_ratio_value() -> None:
    assert tail_loss_ratio(100.0, 250.0) == 2.5


def test_scenario_comparison_outputs_for_margin_and_tail() -> None:
    baseline = [
        _result(total_im=120.0, total_loss=100.0, residual_shortfall=1.0),
        _result(total_im=110.0, total_loss=100.0, residual_shortfall=2.0),
    ]
    stressed = [
        _result(total_im=95.0, total_loss=160.0, residual_shortfall=8.0, defaulted=True),
        _result(total_im=90.0, total_loss=150.0, residual_shortfall=10.0, defaulted=True),
    ]
    out = scenario_comparison_outputs(
        baseline,
        stressed,
        baseline_name="gaussian",
        stressed_name="fat_tail",
        confidence_level=0.5,
    )

    assert "gaussian" in out
    assert "fat_tail" in out
    assert out["comparison"]["tail_loss_ratio_es"] > 1.0
    assert out["comparison"]["margin_adequacy_delta"] < 0.0
    assert "cover2_adequacy_delta" in out["comparison"]
