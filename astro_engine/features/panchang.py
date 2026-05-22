"""
Panchang Feature Extraction (Layer B)

Pure mathematical derivation of panchang elements from pre-computed longitudes.
No ephemeris calls. No position fetching. Takes moon_lon, sun_lon as inputs.

Dependencies: features.nakshatra (get_nakshatra), astronomy.utils (normalize_lon)
"""

from datetime import datetime as _datetime
from features.nakshatra import get_nakshatra


# --- CONSTANTS ---

RESTRICTIVE_KARANAS = {"Vishti", "Kinstughna", "Shakuni", "Chatushpada", "Naga"}
DANGEROUS_YOGAS = {6, 9, 10, 17}
AUSPICIOUS_YOGAS = {2, 4, 11, 21}
BENEFIC_WEEKDAYS = {2, 3, 4, 6}
KARANA_LIST = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Naga", "Kinstughna",
]


# --- PURE DERIVATION FUNCTIONS ---

def compute_tithi(moon_lon, sun_lon):
    """Compute tithi number (1-30) from moon and sun longitudes."""
    distance = (moon_lon - sun_lon) % 360
    return int(distance / 12) + 1


def compute_nakshatra(moon_lon):
    """Compute nakshatra from moon longitude."""
    return get_nakshatra(moon_lon)


def compute_yoga(sun_lon, moon_lon):
    """Compute yoga number (1-27) from sun and moon longitudes."""
    yoga_long = (sun_lon + moon_lon) % 360
    return int(yoga_long / (360 / 27)) + 1


def get_karana(moon_lon, sun_lon):
    """Get karana name from moon and sun longitudes."""
    diff = (moon_lon - sun_lon) % 360
    index = int(diff / 6)
    return KARANA_LIST[index % 11]


def compute_dhana_tithi(moon_lon, sun_lon):
    """Compute dhana tithi (wealth tithi)."""
    distance = (moon_lon - sun_lon) % 360
    scaled = (distance * 2) % 360
    return int(scaled / 12) + 1


def compute_karma_tithi(moon_lon, sun_lon):
    """Compute karma tithi (work tithi)."""
    distance = (moon_lon - sun_lon) % 360
    scaled = (distance * 10) % 360
    return int(scaled / 12) + 1


# --- SCORING FUNCTIONS ---

def tara_adjustment(tara_index):
    """Tara-based score adjustment."""
    adjustments = {
        1: -5, 2: 10, 3: -10, 4: 10, 5: -10, 6: 10, 7: -15, 8: 10, 9: 10,
    }
    return adjustments.get(tara_index, 0)


def tithi_score(tithi):
    """Score a tithi for favorability."""
    if tithi in [5, 10, 15]:
        return 15
    if tithi in [3, 8, 13]:
        return 10
    if tithi in [2, 7, 12]:
        return 5
    if tithi in [4, 9, 14]:
        return -15
    return 0


def karana_score(karana_name):
    """Score a karana for favorability."""
    if karana_name == "Vishti":
        return -15
    if karana_name in RESTRICTIVE_KARANAS:
        return -10
    return 5


def nitya_yoga_score(yoga_index):
    """Score a yoga for favorability."""
    if yoga_index in DANGEROUS_YOGAS:
        return -15
    if yoga_index in AUSPICIOUS_YOGAS:
        return 10
    return 0


def vara_score(date_obj):
    """Score weekday for favorability."""
    weekday = date_obj.weekday()
    return 10 if weekday in BENEFIC_WEEKDAYS else -10


# --- COMPOSITE SCORING FUNCTION (used by engine) ---

def compute_panchang_score(moon_lon, sun_lon, tara_index, karana_name=None, date_obj=None):
    """
    Compute composite panchang score from pre-computed longitudes.

    Args:
        moon_lon: Moon sidereal longitude (from Layer A)
        sun_lon: Sun sidereal longitude (from Layer A)
        tara_index: Tara remainder (1-9)
        karana_name: Optional override for karana
        date_obj: datetime for weekday scoring

    Returns:
        dict with tithi, karana, dhana_tithi, karma_tithi, yoga, score
    """
    date_obj = date_obj or _datetime.utcnow()
    tithi = compute_tithi(moon_lon, sun_lon)
    karana_name = karana_name or get_karana(moon_lon, sun_lon)
    yoga_index = int(((sun_lon + moon_lon) % 360) / (360 / 27)) + 1

    total = 0
    total += tithi_score(tithi)
    total += karana_score(karana_name)
    total += nitya_yoga_score(yoga_index)
    total += vara_score(date_obj)
    total += tara_adjustment(tara_index)

    return {
        "tithi": tithi,
        "karana": karana_name,
        "dhana_tithi": compute_dhana_tithi(moon_lon, sun_lon),
        "karma_tithi": compute_karma_tithi(moon_lon, sun_lon),
        "yoga": yoga_index,
        "score": total,
    }
