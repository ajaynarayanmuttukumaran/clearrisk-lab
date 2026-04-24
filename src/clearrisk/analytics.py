from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

import numpy as np

from .config import SimulationResult


def _safe_mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return float(np.mean(np.asarray(values, dtype=float)))


def _margin_adequacy_ratio(result: SimulationResult) -> float:
    total_im = float(sum(result.im_by_member.values()))
    total_loss = float(sum(result.member_losses.values()))
    if total_loss <= 0.0:
        return 0.0
    return total_im / total_loss


def _cover2_adequacy_ratio(result: SimulationResult) -> float:
    return float(result.metrics.get("cover2_adequacy_ratio", 0.0))


def compute_basic_metrics(result: SimulationResult) -> Dict[str, float]:
    total_im = float(sum(result.im_by_member.values()))
    total_loss = float(sum(result.member_losses.values()))
    margin_adequacy_ratio = (total_im / total_loss) if total_loss > 0 else 0.0
    metrics = {
        "default_count": float(len(result.defaulted_members)),
        "residual_shortfall": float(result.residual_shortfall),
        "total_im": total_im,
        "total_loss": total_loss,
        "margin_adequacy_ratio": margin_adequacy_ratio,
        "cover2_required_resources": float(result.metrics.get("cover2_required_resources", 0.0)),
        "available_prefunded_resources": float(result.metrics.get("available_prefunded_resources", 0.0)),
        "cover2_surplus_or_deficit": float(result.metrics.get("cover2_surplus_or_deficit", 0.0)),
        "cover2_adequacy_ratio": float(result.metrics.get("cover2_adequacy_ratio", 0.0)),
        "largest_two_member_loss_share": float(result.metrics.get("largest_two_member_loss_share", 0.0)),
        "im_procyclicality_score": float(result.metrics.get("im_procyclicality_score", 0.0)),
        "assessment_contagion_rate": float(result.metrics.get("assessment_contagion_rate", 0.0)),
    }
    return metrics


def tail_loss_ratio(gaussian_loss: float, fat_tail_loss: float) -> float:
    if gaussian_loss <= 0:
        return 0.0
    return float(fat_tail_loss / gaussian_loss)


def compute_probability_metrics(results: Iterable[SimulationResult]) -> Dict[str, float]:
    rows = list(results)
    n = len(rows)
    if n == 0:
        return {
            "prob_member_default": 0.0,
            "prob_default_fund_depletion": 0.0,
            "prob_assessment_calls": 0.0,
            "prob_residual_shortfall": 0.0,
            "expected_residual_shortfall": 0.0,
            "worst_case_residual_shortfall": 0.0,
        }

    default_events = sum(1 for r in rows if len(r.defaulted_members) > 0)
    df_depletion_events = sum(1 for r in rows if float(r.default_fund_depletion) > 0.0)
    assessment_events = sum(1 for r in rows if sum(r.assessments.values()) > 0.0)
    shortfall_events = sum(1 for r in rows if float(r.residual_shortfall) > 0.0)
    residuals = [float(r.residual_shortfall) for r in rows]

    return {
        "prob_member_default": float(default_events / n),
        "prob_default_fund_depletion": float(df_depletion_events / n),
        "prob_assessment_calls": float(assessment_events / n),
        "prob_residual_shortfall": float(shortfall_events / n),
        "expected_residual_shortfall": float(np.mean(residuals)),
        "worst_case_residual_shortfall": float(np.max(residuals)),
    }


def expected_shortfall_statistics(losses: Sequence[float], confidence_level: float = 0.99) -> Dict[str, float]:
    if not losses:
        return {"var": 0.0, "expected_shortfall": 0.0, "mean_loss": 0.0}

    arr = np.asarray(losses, dtype=float)
    arr = np.maximum(arr, 0.0)
    alpha = min(max(float(confidence_level), 0.0), 1.0)
    var = float(np.quantile(arr, alpha))
    tail = arr[arr >= var]
    es = float(np.mean(tail)) if tail.size > 0 else var
    return {
        "var": var,
        "expected_shortfall": es,
        "mean_loss": float(np.mean(arr)),
    }


def scenario_comparison_outputs(
    baseline_results: Iterable[SimulationResult],
    stressed_results: Iterable[SimulationResult],
    *,
    baseline_name: str = "baseline",
    stressed_name: str = "stressed",
    confidence_level: float = 0.99,
) -> Dict[str, Dict[str, float] | Dict[str, Dict[str, float]]]:
    baseline_rows = list(baseline_results)
    stressed_rows = list(stressed_results)

    baseline_prob = compute_probability_metrics(baseline_rows)
    stressed_prob = compute_probability_metrics(stressed_rows)

    baseline_residuals = [float(r.residual_shortfall) for r in baseline_rows]
    stressed_residuals = [float(r.residual_shortfall) for r in stressed_rows]
    baseline_es = expected_shortfall_statistics(baseline_residuals, confidence_level)
    stressed_es = expected_shortfall_statistics(stressed_residuals, confidence_level)

    baseline_margin_adequacy = _safe_mean([_margin_adequacy_ratio(r) for r in baseline_rows])
    stressed_margin_adequacy = _safe_mean([_margin_adequacy_ratio(r) for r in stressed_rows])
    baseline_cover2_adequacy = _safe_mean([_cover2_adequacy_ratio(r) for r in baseline_rows])
    stressed_cover2_adequacy = _safe_mean([_cover2_adequacy_ratio(r) for r in stressed_rows])

    comparison = {
        "tail_loss_ratio_es": tail_loss_ratio(baseline_es["expected_shortfall"], stressed_es["expected_shortfall"]),
        "margin_adequacy_baseline": baseline_margin_adequacy,
        "margin_adequacy_stressed": stressed_margin_adequacy,
        "margin_adequacy_delta": stressed_margin_adequacy - baseline_margin_adequacy,
        "margin_adequacy_ratio": (
            stressed_margin_adequacy / baseline_margin_adequacy if baseline_margin_adequacy > 0 else 0.0
        ),
        "cover2_adequacy_baseline": baseline_cover2_adequacy,
        "cover2_adequacy_stressed": stressed_cover2_adequacy,
        "cover2_adequacy_delta": stressed_cover2_adequacy - baseline_cover2_adequacy,
        "cover2_adequacy_ratio": (
            stressed_cover2_adequacy / baseline_cover2_adequacy if baseline_cover2_adequacy > 0 else 0.0
        ),
    }

    return {
        baseline_name: {
            **baseline_prob,
            **baseline_es,
            "mean_margin_adequacy_ratio": baseline_margin_adequacy,
            "mean_cover2_adequacy_ratio": baseline_cover2_adequacy,
        },
        stressed_name: {
            **stressed_prob,
            **stressed_es,
            "mean_margin_adequacy_ratio": stressed_margin_adequacy,
            "mean_cover2_adequacy_ratio": stressed_cover2_adequacy,
        },
        "comparison": comparison,
    }
