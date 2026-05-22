"""
RuleResult — Output of Layer C (interpretive rules).

Contains meaning: what combinations mean, which rules fired, how strong.
This is where yogas, event scores, risk factors, and personality emerge.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple


@dataclass(frozen=True)
class YogaResult:
    """Detected yogas and their activation status."""
    mahapurusha: List[str] = field(default_factory=list)
    dainya: bool = False
    dhana: bool = False
    bhanga: bool = False
    score: float = 0.0


@dataclass(frozen=True)
class RiskContext:
    """Aggregated risk factors from all rule modules."""
    sade_sati: int = 0
    node_crisis: int = 0
    maraka: int = 0
    maraka_trigger: int = 0
    av_vulnerability: int = 0
    tara_risk: int = 0
    dasha_sandhi: int = 0
    badhakesh: int = 0
    gochar_vedha: int = 0
    panchang_adverse: float = 0.0
    sbc_vedha: int = 0
    ashtama_shani: int = 0
    sade_sati_phase: str = "none"
    saturn_pressure: bool = False
    maraka_level: Optional[str] = None


@dataclass(frozen=True)
class RuleResult:
    """
    Immutable output of the rules layer.

    Produced by: rules layer
    Consumed by: decisions layer

    Contains interpretations — not raw numbers, not final actions.
    """
    # Event scoring
    event_scores: Dict[str, float] = field(default_factory=dict)
    top_events: List[Tuple[str, float]] = field(default_factory=list)

    # Yoga interpretations
    yoga: YogaResult = field(default_factory=YogaResult)

    # Risk interpretation
    risk_context: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0

    # Modifiers applied
    nakshatra_factor: float = 1.0
    moorthy_grade: str = ""
    moorthy_factor: float = 1.0
    tara_score: float = 0.0
    tara_remainder: int = 0
    rulebook_action: str = "NEUTRAL"
    rulebook_reason: str = ""

    # Structural interpretations
    kala_sarpa: bool = False
    kala_sarpa_type: Optional[str] = None
    vedha_blocked: bool = False
    badhakesh_active: bool = False

    # SBC analysis
    sbc_analysis: Dict[str, Any] = field(default_factory=dict)

    # Kakshya
    kakshya: Dict[str, Any] = field(default_factory=dict)
    kakshya_cluster: Dict[str, Any] = field(default_factory=dict)

    # Governance
    governance: Dict[str, Any] = field(default_factory=dict)

    # Personality (Mode A)
    personality_profile: Optional[Dict[str, Any]] = None

    # Longevity/Jaimini
    longevity: Optional[Dict[str, Any]] = None
