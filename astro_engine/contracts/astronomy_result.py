"""
AstronomyResult — Output of Layer A (pure computation).

Contains ONLY raw coordinates, speeds, and motion data.
No astrology meaning. No interpretation. No signs. No nakshatras.
Just: where is the body? what is its speed? is it retrograde? what are the cusps?
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional


@dataclass(frozen=True)
class PlanetPosition:
    """Raw astronomical position for a single body."""
    name: str
    longitude: float          # sidereal longitude (degrees)
    latitude: float           # celestial latitude (degrees)
    speed: float              # daily motion (degrees/day)
    retrograde: bool          # speed < 0


@dataclass(frozen=True)
class AstronomyResult:
    """
    Immutable output of the astronomy layer.

    Produced by: astronomy/engine_base.py
    Consumed by: features layer

    Contains only raw numbers — no astrology meaning.
    """
    jd: float                                          # Julian Day of computation
    ayanamsa: str                                      # e.g. "FAGAN_BRADLEY"
    lat: float                                         # geographic latitude
    lon: float                                         # geographic longitude

    positions: Dict[str, float] = field(default_factory=dict)       # planet_name → sidereal longitude
    latitudes: Dict[str, float] = field(default_factory=dict)       # planet_name → celestial latitude
    speeds: Dict[str, float] = field(default_factory=dict)          # planet_name → daily speed
    retrograde_flags: Dict[str, bool] = field(default_factory=dict) # planet_name → is retrograde

    ascendant: float = 0.0                             # sidereal longitude of ascendant
    house_cusps: Tuple[float, ...] = field(default_factory=tuple)  # 12 cusp longitudes

    # Optional natal reference (for Mode 1 — person-specific)
    natal_positions: Optional[Dict[str, float]] = None  # birth chart positions (fixed)
    natal_jd: Optional[float] = None                    # birth chart Julian Day
