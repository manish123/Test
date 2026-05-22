"""
SymbolicResult — Output of Layer C1 (neutral symbolic states).

Contains ONLY domain-neutral condition descriptions.
No judgment. No "good"/"bad". No "avoid"/"go".
Just: what IS happening in the sky relative to this chart.

Produced by: rules/symbolic/planetary_conditions.py → build_symbolic_state()
Consumed by: rules/domains/<domain>/interpreter.py → interpret()

This is the boundary between world-state and policy.
In reinforcement learning terms:
    SymbolicResult = environment observation
    DomainResult   = policy output
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class PlanetCondition:
    """Neutral condition description for a single planet."""
    name: str
    intensity: str                  # amplified / expressed / subdued / restricted / dormant
    dignity: Dict[str, str] = field(default_factory=dict)       # {"condition": "exalted", "description": "..."}
    retrograde: Dict[str, str] = field(default_factory=dict)    # {"condition": "direct/retrograde", "description": "..."}
    combustion: Dict[str, str] = field(default_factory=dict)    # {"condition": "visible/combust", "description": "..."}
    house: Optional[int] = None
    nakshatra: Optional[str] = None
    lajjitadi: str = "normal"


@dataclass(frozen=True)
class YogaConditions:
    """Neutral yoga state descriptions — no domain judgment."""
    kala_sarpa: Dict[str, Any] = field(default_factory=dict)    # {"condition": "active/inactive", "type": "anuloma/viloma", "themes": [...]}
    dainya: Dict[str, Any] = field(default_factory=dict)        # {"condition": "active/inactive", "themes": [...]}
    mahapurusha: Dict[str, Any] = field(default_factory=dict)   # {"condition": "active/inactive", "planets": [...]}
    bhanga: bool = False


@dataclass(frozen=True)
class TimingConditions:
    """Neutral timing state descriptions — no domain judgment."""
    sade_sati: Dict[str, Any] = field(default_factory=dict)     # {"condition": "none/rising/peak/setting/ashtama", "description": "..."}
    dasha_sandhi: Dict[str, Any] = field(default_factory=dict)  # {"condition": "stable/sandhi", "description": "..."}
    chandrabala: Dict[str, Any] = field(default_factory=dict)   # {"count": 8, "description": "8th from Moon — transformation axis"}
    moorthy: Dict[str, Any] = field(default_factory=dict)       # {"grade": "Loha", "factor": 0.7, "description": "iron receptivity"}


@dataclass(frozen=True)
class RiskPressure:
    """Raw pressure indicators — numeric, not interpreted."""
    node_crisis: float = 0.0        # 0-100 scale, raw pressure from Rahu/Ketu
    maraka: float = 0.0             # 0-100 scale, raw maraka lord activation
    sade_sati: float = 0.0          # 0-50 scale, raw Saturn-Moon pressure


@dataclass(frozen=True)
class SymbolicResult:
    """
    Immutable neutral symbolic state — the world observation.

    Produced by: build_symbolic_state(engine_result)
    Consumed by: domain interpreters (read-only)

    This object is the BOUNDARY between:
        - Universal astronomical/astrological truth (what IS)
        - Domain-specific interpretation (what it MEANS for you)

    It must NEVER contain:
        - "good" / "bad"
        - "avoid" / "go" / "block"
        - "dangerous" / "safe"
        - "favorable" / "unfavorable"
        - Any domain-specific vocabulary

    It must ONLY contain:
        - "active" / "inactive"
        - "amplified" / "subdued" / "dormant"
        - "restructuring" / "transition" / "stable"
        - "concentrated" / "distributed"
        - Neutral descriptive phrases
    """
    planets: List[PlanetCondition] = field(default_factory=list)
    yogas: YogaConditions = field(default_factory=YogaConditions)
    timing: TimingConditions = field(default_factory=TimingConditions)
    tara: Dict[str, Any] = field(default_factory=dict)          # {"score": float, "janma_nakshatra": str}
    risk_pressure: RiskPressure = field(default_factory=RiskPressure)
