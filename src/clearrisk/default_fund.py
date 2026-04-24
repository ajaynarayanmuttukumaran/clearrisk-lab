from __future__ import annotations

from typing import Dict

from .config import DefaultFundMetrics, WaterfallConfig


def _non_negative(value: float) -> float:
    return max(0.0, float(value))


def uncovered_stress_losses_by_member(
    stress_losses_by_member: Dict[str, float],
    im_by_member: Dict[str, float],
) -> Dict[str, float]:
    uncovered: Dict[str, float] = {}
    all_members = set(stress_losses_by_member) | set(im_by_member)
    for member_id in all_members:
        loss = _non_negative(stress_losses_by_member.get(member_id, 0.0))
        im = _non_negative(im_by_member.get(member_id, 0.0))
        uncovered[member_id] = max(0.0, loss - im)
    return uncovered


def compute_default_fund_metrics(
    stress_losses_by_member: Dict[str, float],
    im_by_member: Dict[str, float],
    config: WaterfallConfig,
) -> DefaultFundMetrics:
    uncovered = uncovered_stress_losses_by_member(stress_losses_by_member, im_by_member)
    ordered = sorted(uncovered.values(), reverse=True)
    largest = ordered[0] if len(ordered) >= 1 else 0.0
    second_largest = ordered[1] if len(ordered) >= 2 else 0.0

    cover1_required = largest
    cover2_required = largest + second_largest
    total_uncovered = sum(uncovered.values())

    total_im = sum(_non_negative(v) for v in im_by_member.values())
    method = config.default_fund_method
    value = _non_negative(config.default_fund_value)

    if method == "fixed":
        available_prefunded = value
    elif method == "percent_im":
        available_prefunded = value * total_im
    elif method == "cover1":
        available_prefunded = cover1_required
    elif method == "cover2":
        available_prefunded = cover2_required
    elif method == "stress_cover2":
        stress_multiplier = value if value > 0.0 else 1.25
        stress_multiplier = max(1.0, stress_multiplier)
        available_prefunded = cover2_required * stress_multiplier
    else:
        available_prefunded = 0.0

    surplus_or_deficit = available_prefunded - cover2_required
    adequacy_ratio = (available_prefunded / cover2_required) if cover2_required > 0 else 1.0
    largest_two_share = (cover2_required / total_uncovered) if total_uncovered > 0 else 0.0

    return DefaultFundMetrics(
        cover2_required_resources=float(cover2_required),
        available_prefunded_resources=float(available_prefunded),
        cover2_surplus_or_deficit=float(surplus_or_deficit),
        cover2_adequacy_ratio=float(adequacy_ratio),
        largest_two_member_loss_share=float(largest_two_share),
        cover1_required_resources=float(cover1_required),
    )

