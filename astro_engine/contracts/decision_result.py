"""
DecisionResult — Output of Layer D (scoring and governance).

Contains ONLY actions: confidence, risk, gate status, and final trading action.
This layer does not know ephemeris math. It only consumes structured outputs from layers 1-3.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass(frozen=True)
class TradingGateResult:
    """3-level trading gate output."""
    enabled: bool = False
    overall_status: str = "DISABLED"   # CLEAR / WATCH / CAUTION / BLOCK / DISABLED
    score: Optional[float] = None
    suggested_action: Optional[str] = None
    profile: str = "strict"
    levels: Dict[str, Any] = field(default_factory=dict)
    no_trade_triggers: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DecisionResult:
    """
    Immutable output of the decisions layer.

    Produced by: decisions layer
    Consumed by: main.py / API response

    This is the final output of the engine for a single evaluation.
    """
    # Core decision
    action: str = "AVOID"              # GO FULL / CONTROLLED AGGRESSION / MODERATE / LOW SIZE / WAIT / AVOID / SURVIVE
    phase: str = "NORMAL"              # NORMAL / DESTRUCTIVE / TRADING_GATE_BLOCK / etc.
    confidence: float = 0.0            # 0-100, calibrated
    confidence_raw: float = 0.0        # 0-100, before calibration
    risk: float = 0.0                  # 0-100, sqrt-normalized

    # Top event
    top_event: str = ""
    top_event_score: float = 0.0

    # Position sizing
    position_multiplier: float = 1.0

    # Trading gate
    trading_gate: TradingGateResult = field(default_factory=TradingGateResult)

    # Asset signals
    asset_events: List[Dict[str, Any]] = field(default_factory=list)

    # Calibration trace
    calibration: Optional[Dict[str, Any]] = None
