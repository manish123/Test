"""
FeatureResult — Output of Layer B (classical feature extraction).

Contains derived astrology facts: dignities, nakshatras, houses, dashas, strengths.
Still deterministic — no opinions, no judgments, just canonical transforms.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass(frozen=True)
class PlanetFeature:
    """Derived features for a single planet."""
    name: str
    longitude: float
    latitude: float
    sign: int                    # 1-12
    nakshatra: str
    status: str                  # exalted/debilitated/own/friend/enemy/neutral/etc.
    dispositor: str              # lord of the sign
    retrograde: bool
    house: int                   # chalit house (1-12)
    rashi_house: int             # rashi-based house
    operational_house: int       # resolved house
    is_kendra: bool
    vimsopaka: float             # vimsopaka bala score


@dataclass(frozen=True)
class DashaFeature:
    """Current dasha/antardasha state."""
    md: str                      # Mahadasha lord name
    ad: str                      # Antardasha lord name
    sandhi_active: bool          # within sandhi transition zone


@dataclass(frozen=True)
class AshtakavargaFeature:
    """Computed BAV/SAV data."""
    bav: Dict[str, List[int]]    # planet → 12-sign bindu array
    sav_raw: List[int]           # 12-sign raw SAV
    sav_trikona: List[int]       # after trikona shodhana
    sav_sodhya: List[int]        # after ekadhipatya shodhana


@dataclass(frozen=True)
class FeatureResult:
    """
    Immutable output of the features layer.

    Produced by: features layer
    Consumed by: rules layer

    Contains derived facts — not judgments.
    """
    planets: List[PlanetFeature] = field(default_factory=list)
    asc_sign: int = 1
    natal_moon_sign: int = 1

    # House system
    strong_houses: List[int] = field(default_factory=list)

    # Timing features
    dasha: Optional[DashaFeature] = None
    chara_dasha: Optional[Dict[str, Any]] = None
    yogini: Optional[Dict[str, Any]] = None

    # Ashtakavarga
    ashtakavarga: Optional[AshtakavargaFeature] = None

    # Panchang (derived from lon only)
    panchang: Optional[Dict[str, Any]] = None

    # Tara
    janma_nakshatra: str = ""
    tara_raw_score: float = 0.0
