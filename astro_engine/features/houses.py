"""
House Feature Extraction (Layer B)

Given raw cusps from astronomy layer, determines planet-in-house placement.

Dependencies: astronomy.engine_base (get_house_cusps), astronomy.utils (normalize_lon)
Never imports swisseph directly.
"""

from astronomy.engine_base import get_house_cusps
from astronomy.utils import normalize_lon


def get_houses(jd, lat, lon):
    """Get house cusps via Layer A astronomy call."""
    return get_house_cusps(jd, lat, lon)


def get_planet_house(lon, houses):
    """Determine which house a planet occupies based on cusp longitudes."""
    lon = normalize_lon(lon)
    for i in range(12):
        current_cusp = normalize_lon(houses[i])
        next_cusp = normalize_lon(houses[(i + 1) % 12])

        if current_cusp <= next_cusp:
            if current_cusp <= lon < next_cusp:
                return i + 1
        else:
            if lon >= current_cusp or lon < next_cusp:
                return i + 1

    return 12


def _angular_distance(a, b):
    diff = abs((a - b) % 360)
    return min(diff, 360 - diff)


def get_operational_house(lon, houses, rashi_house):
    """Resolve operational house (chalit vs rashi)."""
    lon = normalize_lon(lon)
    chalit_house = get_planet_house(lon, houses)
    bhava_madhya = normalize_lon(houses[chalit_house - 1])
    if _angular_distance(lon, bhava_madhya) > 15:
        return chalit_house
    return rashi_house


def detect_strong_houses(planets):
    """Identify houses containing high-multiplier planets."""
    strong = []

    for p in planets:
        if p["multiplier"] > 1.2:
            strong.append(p["house"])

    return list(set(strong))
