from __future__ import annotations

from typing import Dict, Iterable

from .config import ClearingMember, Portfolio


def member_total_notional(member: ClearingMember) -> float:
    return member.portfolio.gross_notional()


def portfolio_concentration_index(portfolio: Portfolio) -> float:
    gross = portfolio.gross_notional()
    if gross <= 0:
        return 0.0
    weights = [abs(p.market_value()) / gross for p in portfolio.positions]
    return float(sum(w * w for w in weights))


def clone_member(member: ClearingMember) -> ClearingMember:
    payload = member.__dict__.copy()
    payload["portfolio"] = Portfolio(positions=list(member.portfolio.positions))
    return ClearingMember(**payload)


def assessment_caps_from_members(
    members: Iterable[ClearingMember],
    assessment_cap_multiple: float,
) -> Dict[str, float]:
    cap_mult = max(0.0, float(assessment_cap_multiple))
    caps: Dict[str, float] = {}
    for member in members:
        if member.is_defaulted:
            continue
        caps[member.member_id] = max(0.0, float(member.default_fund_contribution) * cap_mult)
    return caps


def allocate_capped_assessments(required_amount: float, caps_by_member: Dict[str, float]) -> Dict[str, float]:
    target = max(0.0, float(required_amount))
    caps = {k: max(0.0, float(v)) for k, v in caps_by_member.items()}
    allocations = {k: 0.0 for k in caps}
    total_cap = sum(caps.values())
    if target <= 0.0 or total_cap <= 0.0:
        return allocations

    target = min(target, total_cap)
    ordered_ids = sorted(caps)
    for member_id in ordered_ids:
        cap = caps[member_id]
        allocations[member_id] = target * (cap / total_cap)

    # Floating-point cleanup while preserving per-member caps.
    assigned = sum(allocations.values())
    residual = target - assigned
    if residual > 1e-12:
        for member_id in ordered_ids:
            room = caps[member_id] - allocations[member_id]
            if room <= 0.0:
                continue
            bump = min(room, residual)
            allocations[member_id] += bump
            residual -= bump
            if residual <= 1e-12:
                break

    # Hard clip for numerical safety.
    for member_id in ordered_ids:
        allocations[member_id] = min(caps[member_id], max(0.0, allocations[member_id]))
    return allocations
