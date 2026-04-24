from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional

DefaultRound = Literal["none", "first_round", "second_round"]
MarginMethod = Literal[
    "gaussian_var",
    "historical_var",
    "expected_shortfall",
    "stressed_var",
    "buffered_var",
]
DefaultFundMethod = Literal["fixed", "percent_im", "cover1", "cover2", "stress_cover2"]


@dataclass
class Position:
    asset_id: str
    quantity: float
    price: float

    def market_value(self) -> float:
        return float(self.quantity * self.price)


@dataclass
class Portfolio:
    positions: List[Position] = field(default_factory=list)

    def gross_notional(self) -> float:
        return float(sum(abs(p.market_value()) for p in self.positions))


@dataclass
class ClearingMember:
    member_id: str
    portfolio: Portfolio = field(default_factory=Portfolio)
    default_fund_contribution: float = 0.0
    liquidity_buffer: float = 0.0
    capital_buffer: float = 0.0
    credit_quality_score: float = 1.0
    is_defaulted: bool = False
    default_round: DefaultRound = "none"


@dataclass
class MarketScenario:
    scenario_name: str = "baseline_gaussian"
    drift: float = 0.06
    volatility: float = 0.20
    correlation_matrix: Optional[List[List[float]]] = None
    jump_probability: float = 0.0
    jump_size_distribution: str = "none"
    liquidity_spread_multiplier: float = 1.0
    stress_label: str = "baseline"


@dataclass
class MarginConfig:
    method: MarginMethod = "gaussian_var"
    confidence_level: float = 0.99
    margin_period_of_risk_days: int = 5
    stressed_var_vol_multiplier: float = 1.5
    anti_procyclicality_buffer: float = 0.0
    volatility_floor: float = 0.0
    lookback_window: int = 252
    concentration_addon: float = 0.0
    liquidity_addon: float = 0.0


@dataclass
class WaterfallConfig:
    ccp_skin_in_game: float = 100_000_000.0
    assessment_cap_multiple: float = 0.20
    include_defaulter_df: bool = True
    allow_vm_haircut_placeholder: bool = False
    recovery_tool_placeholder: bool = False
    default_fund_method: DefaultFundMethod = "percent_im"
    default_fund_value: float = 0.0


@dataclass
class DefaultFundMetrics:
    cover2_required_resources: float = 0.0
    available_prefunded_resources: float = 0.0
    cover2_surplus_or_deficit: float = 0.0
    cover2_adequacy_ratio: float = 0.0
    largest_two_member_loss_share: float = 0.0
    cover1_required_resources: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CloseoutCostConfig:
    base_spread_cost: float = 0.0
    volatility_liquidity_multiplier: float = 0.0
    concentration_penalty: float = 0.0
    market_depth_penalty: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContagionConfig:
    liquidity_breach_ratio: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WaterfallLayerLog:
    layer: str
    starting_loss: float
    capacity: float
    used: float
    remaining_loss: float
    payer: str


@dataclass
class WaterfallOutcome:
    total_loss: float
    layer_usage: Dict[str, float] = field(default_factory=dict)
    layer_logs: List[WaterfallLayerLog] = field(default_factory=list)
    assessment_by_member: Dict[str, float] = field(default_factory=dict)
    assessment_caps_by_member: Dict[str, float] = field(default_factory=dict)
    shortfall: float = 0.0
    total_applied: float = 0.0
    balance_gap: float = 0.0
    is_balanced: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SimulationConfig:
    run_name: str = "baseline_run"
    random_seed: int = 42
    n_paths: int = 1000
    time_horizon_days: int = 252
    members: List[ClearingMember] = field(default_factory=list)
    scenarios: List[MarketScenario] = field(default_factory=list)
    margin: MarginConfig = field(default_factory=MarginConfig)
    waterfall: WaterfallConfig = field(default_factory=WaterfallConfig)
    closeout: CloseoutCostConfig = field(default_factory=CloseoutCostConfig)
    contagion: ContagionConfig = field(default_factory=ContagionConfig)
    enable_wrong_way_risk: bool = True
    include_liquidity_closeout_cost: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationConfig":
        members = []
        for m in data.get("members", []):
            positions = [Position(**p) for p in m.get("portfolio", {}).get("positions", [])]
            portfolio = Portfolio(positions=positions)
            member_payload = dict(m)
            member_payload["portfolio"] = portfolio
            members.append(ClearingMember(**member_payload))

        scenarios = [MarketScenario(**s) for s in data.get("scenarios", [])]
        margin = MarginConfig(**data.get("margin", {}))
        waterfall = WaterfallConfig(**data.get("waterfall", {}))
        closeout = CloseoutCostConfig(**data.get("closeout", {}))
        contagion = ContagionConfig(**data.get("contagion", {}))
        return cls(
            run_name=data.get("run_name", "baseline_run"),
            random_seed=int(data.get("random_seed", 42)),
            n_paths=int(data.get("n_paths", 1000)),
            time_horizon_days=int(data.get("time_horizon_days", 252)),
            members=members,
            scenarios=scenarios,
            margin=margin,
            waterfall=waterfall,
            closeout=closeout,
            contagion=contagion,
            enable_wrong_way_risk=bool(data.get("enable_wrong_way_risk", True)),
            include_liquidity_closeout_cost=bool(data.get("include_liquidity_closeout_cost", False)),
        )


@dataclass
class SimulationResult:
    member_losses: Dict[str, float] = field(default_factory=dict)
    clean_losses_by_member: Dict[str, float] = field(default_factory=dict)
    closeout_addon_by_member: Dict[str, float] = field(default_factory=dict)
    total_losses_with_closeout_by_member: Dict[str, float] = field(default_factory=dict)
    im_by_member: Dict[str, float] = field(default_factory=dict)
    vm_flows: Dict[str, float] = field(default_factory=dict)
    defaulted_members: List[str] = field(default_factory=list)
    first_round_defaults: List[str] = field(default_factory=list)
    second_round_defaults: List[str] = field(default_factory=list)
    waterfall_layer_usage: Dict[str, float] = field(default_factory=dict)
    waterfall_ledger: List[Dict[str, Any]] = field(default_factory=list)
    default_fund_depletion: float = 0.0
    assessments: Dict[str, float] = field(default_factory=dict)
    assessment_caps_by_member: Dict[str, float] = field(default_factory=dict)
    residual_shortfall: float = 0.0
    balance_gap: float = 0.0
    scenario_metadata: Dict[str, Any] = field(default_factory=dict)
    interpretation_flags: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationResult":
        return cls(**data)
