"""
evaluator_base.py — Shared infrastructure for all domain evaluators.

Phase 1 refactor: centralises pure plumbing that was copy-pasted across
every evaluator file.  No domain semantics live here.

Exports
-------
Constants
    IST_OFFSET, SIGN_NAMES, NAKSHATRA_LORDS
    NATURAL_BENEFICS, NATURAL_MALEFICS, BENEFIC_HOUSES, MALEFIC_HOUSES
    JUPITER_ASPECTS, SATURN_ASPECTS, MARS_ASPECTS

Utilities
    ist_to_utc(dt)  → datetime
    get_jd(dt_ist)  → float (Julian Day)

Classes
    BaseChartState   — natal chart loader + shared helpers
    BaseTransitState — transit position loader + aspect helpers

Rules
    - This module MUST NOT import from rules/, decisions/, or pipeline/.
    - It MAY import from astronomy/ and features/ (Layer A / B only).
    - Domain-specific constants (BUSINESS_KARAKAS, MEDICAL_HOUSES, etc.)
      stay in their respective evaluator files.
    - Rahu/Ketu dignity tables (EXALTATION_SIGNS, OWN_SIGNS, DEBILITATION_SIGNS)
      are NOT centralised here because evaluators have intentionally diverged
      from features/dignity.py on those entries.  That is a domain-semantic
      decision, not plumbing.
"""

import swisseph as swe
from datetime import timedelta
from pathlib import Path

from astronomy.engine_base import get_planet_positions, get_house_cusps, configure_ephemeris
from astronomy.utils import normalize_lon
from features.dignity import SIGN_LORDS, get_sign
from features.nakshatra import get_nakshatra


import json as _json

# ═══════════════════════════════════════════════════════════════
# CALIBRATION LOADER UTILITY
# ═══════════════════════════════════════════════════════════════

def load_calibration(calibration_path, fallback_defaults: dict) -> dict:
    """
    Load a domain calibration overlay from a JSON file.

    Parameters
    ----------
    calibration_path : Path or str
        Absolute path to the calibration_overlay.json file.
    fallback_defaults : dict
        Default calibration dict returned if the file is missing or invalid.

    Returns
    -------
    dict — the loaded calibration, or fallback_defaults on error.
    """
    try:
        with open(calibration_path, "r") as f:
            return _json.load(f)
    except (FileNotFoundError, _json.JSONDecodeError):
        return fallback_defaults


# ═══════════════════════════════════════════════════════════════
# TIMEZONE PLUMBING
# ═══════════════════════════════════════════════════════════════

IST_OFFSET = timedelta(hours=5, minutes=30)


def ist_to_utc(dt):
    """Convert IST datetime to UTC."""
    return dt - IST_OFFSET


def get_jd(dt_ist):
    """Convert an IST datetime to a Swiss Ephemeris Julian Day number."""
    dt_utc = ist_to_utc(dt_ist)
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0,
    )


# ═══════════════════════════════════════════════════════════════
# SIGN / NAKSHATRA LOOKUP TABLES
# ═══════════════════════════════════════════════════════════════

SIGN_NAMES = {
    1: "Aries",       2: "Taurus",    3: "Gemini",      4: "Cancer",
    5: "Leo",         6: "Virgo",     7: "Libra",        8: "Scorpio",
    9: "Sagittarius", 10: "Capricorn", 11: "Aquarius",   12: "Pisces",
}

# Vimshottari nakshatra lords — 27-element repeating sequence.
# Canonical source: features/nakshatra.nakshatra_lords (same order).
# Kept here so evaluators have a single local import rather than
# reaching into features/ directly.
NAKSHATRA_LORDS = [
    "Ketu",    "Venus",   "Sun",     "Moon",    "Mars",
    "Rahu",    "Jupiter", "Saturn",  "Mercury",
    "Ketu",    "Venus",   "Sun",     "Moon",    "Mars",
    "Rahu",    "Jupiter", "Saturn",  "Mercury",
    "Ketu",    "Venus",   "Sun",     "Moon",    "Mars",
    "Rahu",    "Jupiter", "Saturn",  "Mercury",
]


# ═══════════════════════════════════════════════════════════════
# PLANET CLASSIFICATION CONSTANTS
# ═══════════════════════════════════════════════════════════════

NATURAL_BENEFICS  = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS  = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
BENEFIC_HOUSES    = {1, 2, 4, 5, 7, 9, 11}
MALEFIC_HOUSES    = {3, 6, 8, 12}

# Special aspect offsets (houses away from the planet's own house).
# All planets also aspect the 7th — that is handled inline in the
# aspect methods below.
JUPITER_ASPECTS = [5, 7, 9]   # houses from Jupiter's position
SATURN_ASPECTS  = [3, 7, 10]  # houses from Saturn's position
MARS_ASPECTS    = [4, 7, 8]   # houses from Mars's position


# ═══════════════════════════════════════════════════════════════
# BASE CHART STATE
# ═══════════════════════════════════════════════════════════════

class BaseChartState:
    """
    Loads and caches natal chart data shared by every domain evaluator.

    Subclasses add domain-specific house lords and sensitive points in
    their own __init__ after calling super().__init__().

    Attributes set here
    -------------------
    birth_dt, lat, lon, alt, location
    birth_jd
    birth_positions   : {planet_name: longitude_float}
    house_data        : raw dict from get_house_cusps()
    asc_lon, asc_sign
    moon_lon, moon_sign, moon_nakshatra
    planets           : {name: {longitude, sign, house, nakshatra}}
    lagna_lord
    """

    def __init__(self, birth_dt, lat, lon, alt=0):
        self.birth_dt = birth_dt
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.location = {"latitude": lat, "longitude": lon, "altitude": alt}

        configure_ephemeris()
        self.birth_jd = get_jd(birth_dt)
        self.birth_positions = get_planet_positions(self.birth_jd, self.location)
        self.house_data = get_house_cusps(self.birth_jd, lat, lon)

        self.asc_lon  = self.house_data["ascendant"]
        self.asc_sign = int(normalize_lon(self.asc_lon) // 30) + 1

        self.moon_lon       = self.birth_positions["Moon"]
        self.moon_sign      = get_sign(self.moon_lon)
        self.moon_nakshatra = get_nakshatra(self.moon_lon)

        # Build per-planet dict
        self.planets = {}
        for name, lon_val in self.birth_positions.items():
            sign  = get_sign(lon_val)
            house = ((sign - self.asc_sign) % 12) + 1
            self.planets[name] = {
                "longitude": lon_val,
                "sign":      sign,
                "house":     house,
                "nakshatra": get_nakshatra(lon_val),
            }

        self.lagna_lord = SIGN_LORDS[self.asc_sign]

    # ── Aspect helpers ────────────────────────────────────────

    def _get_aspectors_of_house(self, target_house):
        """
        Return list of planet names that aspect *target_house* via
        Vedic aspects (7th for all; special aspects for Jup/Sat/Mars).
        """
        aspectors = []
        for name, data in self.planets.items():
            ph = data["house"]
            # Universal 7th aspect
            if ((ph + 7 - 1 - 1) % 12) + 1 == target_house:
                aspectors.append(name)
            # Jupiter: 5th and 9th (7th already covered above)
            if name == "Jupiter":
                for asp in [5, 9]:
                    if ((ph + asp - 1 - 1) % 12) + 1 == target_house:
                        aspectors.append(name)
            # Saturn: 3rd and 10th
            if name == "Saturn":
                for asp in [3, 10]:
                    if ((ph + asp - 1 - 1) % 12) + 1 == target_house:
                        aspectors.append(name)
            # Mars: 4th and 8th
            if name == "Mars":
                for asp in [4, 8]:
                    if ((ph + asp - 1 - 1) % 12) + 1 == target_house:
                        aspectors.append(name)
        return list(set(aspectors))

    # ── Navamsa helpers ───────────────────────────────────────

    def _get_d9_sign(self, longitude):
        """Return the Navamsa (D9) sign for a given ecliptic longitude."""
        lon  = normalize_lon(longitude)
        sign = int(lon // 30) + 1
        deg_in_sign   = lon % 30
        navamsa_index = int(deg_in_sign / 3.333333333)  # 0–8

        # Starting navamsa by element
        if sign in [1, 5, 9]:    # Fire  → Aries
            start = 1
        elif sign in [2, 6, 10]: # Earth → Capricorn
            start = 10
        elif sign in [3, 7, 11]: # Air   → Libra
            start = 7
        else:                    # Water → Cancer
            start = 4

        return ((start - 1 + navamsa_index) % 12) + 1

    def _compute_d9_lagna(self):
        """Return the Navamsa lagna sign."""
        return self._get_d9_sign(self.asc_lon)

    # ── House / sign utilities ────────────────────────────────

    def get_house_from_sign(self, transit_sign, reference_sign=None):
        """
        Return the house number of *transit_sign* relative to
        *reference_sign* (defaults to natal lagna).
        """
        ref = reference_sign or self.asc_sign
        return ((transit_sign - ref) % 12) + 1


# ═══════════════════════════════════════════════════════════════
# BASE TRANSIT STATE
# ═══════════════════════════════════════════════════════════════

class BaseTransitState:
    """
    Loads transit positions for a specific date and exposes
    aspect / degree-hit helpers used by every evaluator.

    Parameters
    ----------
    date  : datetime (IST)
    chart : BaseChartState (or any subclass)
    """

    def __init__(self, date, chart: BaseChartState):
        self.date  = date
        self.chart = chart

        configure_ephemeris()
        self.jd        = get_jd(date)
        self.positions = get_planet_positions(self.jd, chart.location)

        self.planet_signs               = {}
        self.planet_houses_from_lagna   = {}
        self.planet_houses_from_moon    = {}

        for name, lon_val in self.positions.items():
            sign = get_sign(lon_val)
            self.planet_signs[name]             = sign
            self.planet_houses_from_lagna[name] = chart.get_house_from_sign(sign)
            self.planet_houses_from_moon[name]  = chart.get_house_from_sign(
                sign, chart.moon_sign
            )

    # ── Aspect helpers ────────────────────────────────────────

    def planet_aspects_house(self, planet, target_house, from_ref="lagna"):
        """
        Return True if *planet* (in transit) aspects *target_house*.
        Includes conjunction (being in the house).
        """
        if from_ref == "lagna":
            p_house = self.planet_houses_from_lagna[planet]
        else:
            p_house = self.planet_houses_from_moon[planet]

        # Universal 7th aspect
        aspected = [((p_house + 6) % 12) + 1]

        if planet == "Jupiter":
            aspected.extend([((p_house + 4) % 12) + 1, ((p_house + 8) % 12) + 1])
        elif planet == "Saturn":
            aspected.extend([((p_house + 2) % 12) + 1, ((p_house + 9) % 12) + 1])
        elif planet == "Mars":
            aspected.extend([((p_house + 3) % 12) + 1, ((p_house + 7) % 12) + 1])

        # Conjunction
        aspected.append(p_house)

        return target_house in aspected

    def planet_in_sign(self, planet, target_sign):
        """Return True if transit *planet* is in *target_sign*."""
        return self.planet_signs.get(planet) == target_sign

    # ── Degree-hit helpers ────────────────────────────────────

    def jupiter_on_degree(self, target_degree, orb=2.0):
        """Return True if transit Jupiter is within *orb* of *target_degree*."""
        jup_lon = self.positions["Jupiter"]
        diff    = abs((jup_lon - target_degree) % 360)
        diff    = min(diff, 360 - diff)
        return diff <= orb

    def jupiter_trine_degree(self, target_degree, orb=2.0):
        """
        Return True if transit Jupiter is within *orb* of *target_degree*
        or any of its trines (120°, 240°) or opposition (180°).
        """
        jup_lon = self.positions["Jupiter"]
        for offset in [0, 120, 240, 180]:
            check = (target_degree + offset) % 360
            diff  = abs((jup_lon - check) % 360)
            diff  = min(diff, 360 - diff)
            if diff <= orb:
                return True
        return False


# ═══════════════════════════════════════════════════════════════
# TARA SCORING (shared between main.py and rule_pipeline.py)
# ═══════════════════════════════════════════════════════════════
# These constants and functions were duplicated verbatim in both files.
# Canonical home is here; both files import from this module.

from features.nakshatra import nakshatra_list as _nakshatra_list

TARA_SCORES: dict = {1: -1, 2: 2, 3: -2, 4: 1.5, 5: -1.5, 6: 2, 7: -3, 8: 1, 9: 2}

PLANET_WEIGHTS: dict = {
    "Moon": 3, "Mercury": 2.5, "Jupiter": 2, "Saturn": 2,
    "Mars": 1.5, "Venus": 1, "Sun": 1,
}

PANCHANG_RISK_WEIGHT: float = 0.5
TRADING_EVENT_BOOST: float = 1.15
NON_TRADING_EVENT_MULTIPLIER: float = 0.35


def get_tara(janma: str, transit: str) -> int:
    """Return the Tara number (1-9) for a transit nakshatra relative to janma."""
    j = _nakshatra_list.index(janma)
    t = _nakshatra_list.index(transit)
    count = (t - j) % 27 + 1
    tara = count % 9
    return 9 if tara == 0 else tara


def calculate_tara_score(janma_nak: str, pdata: dict) -> float:
    """
    Compute the weighted Tara score for all planets.

    Parameters
    ----------
    janma_nak : str
        Janma (birth) nakshatra name.
    pdata : dict
        Mapping of planet_name → {"nakshatra": str, ...}
    """
    score = 0.0
    for planet in PLANET_WEIGHTS:
        nak = pdata[planet]["nakshatra"]
        tara = get_tara(janma_nak, nak)
        score += TARA_SCORES[tara] * PLANET_WEIGHTS[planet]
    return round(score, 2)


# Nakshatra rulebook for trade decisions
_TRADE_HEAVILY_MOON = {"Vishakha", "Rohini", "Pushya", "Anuradha", "Uttara Ashadha"}
_DO_NOT_TRADE_MOON = {
    "Dhanishta", "Mrigashira", "Ashlesha", "Jyeshtha", "Shravana",
    "Ashwini", "Magha", "Mula", "Bharani", "Purva Phalguni",
    "Purva Ashadha", "Ardra", "Shatabhisha", "Purva Bhadrapada", "Krittika",
}


def get_trade_decision(pdata: dict) -> tuple:
    """
    Return (action, reason) based on nakshatra rulebook.
    action is one of: "TRADE HEAVILY", "DO NOT TRADE", "NEUTRAL"
    """
    m    = pdata["Moon"]["nakshatra"]
    s    = pdata["Sun"]["nakshatra"]
    v    = pdata["Venus"]["nakshatra"]
    mars = pdata["Mars"]["nakshatra"]

    if m in _TRADE_HEAVILY_MOON:
        return "TRADE HEAVILY", f"Moon in {m}"
    if s == "Krittika":
        return "TRADE HEAVILY", "Sun in Krittika"
    if v in {"Krittika", "Shravana"}:
        return "TRADE HEAVILY", f"Venus in {v}"
    if m in _DO_NOT_TRADE_MOON:
        return "DO NOT TRADE", f"Moon in {m}"
    if mars == "Dhanishta":
        return "DO NOT TRADE", "Mars in Dhanishta"
    if v in {"Rohini", "Shatabhisha"}:
        return "DO NOT TRADE", f"Venus in {v}"
    if s in {"Rohini", "Dhanishta"}:
        return "DO NOT TRADE", f"Sun in {s}"
    if m in {"Chitra", "Revati", "Uttara Bhadrapada", "Swati"}:
        return "NEUTRAL", f"Moon in {m}"
    return "NEUTRAL", "No rule triggered"
