"""
Astronomy Pipeline Stage (Layer A orchestration)

Produces AstronomyResult from date + location + birth_data.
Only this file touches swisseph. Everything downstream receives the Result object.
"""

import swisseph as swe
from datetime import datetime, timedelta

from astronomy.engine_base import (
    get_planet_positions,
    get_planet_latitudes,
    get_retrograde_flags,
    get_house_cusps,
    _get_configured_ayanamsa,
)
from contracts.astronomy_result import AstronomyResult


def _ist_to_utc(dt):
    return dt - timedelta(hours=5, minutes=30)


def run_astronomy(date, birth_data, location_override=None, location_mode="birth"):
    """
    Execute Layer A: compute all raw astronomical positions.

    Args:
        date: datetime (IST) for evaluation
        birth_data: dict with 'date', 'lat', 'lon'
        location_override: optional dict with 'lat', 'lon'
        location_mode: 'birth' | 'current'

    Returns:
        AstronomyResult (frozen dataclass)
    """
    birth = birth_data

    # --- Natal positions (fixed for birth chart) ---
    birth_utc = _ist_to_utc(birth["date"])
    birth_jd = swe.julday(
        birth_utc.year, birth_utc.month, birth_utc.day,
        birth_utc.hour + birth_utc.minute / 60.0,
    )
    natal_positions = get_planet_positions(birth_jd)

    # --- Transit positions (for evaluation date) ---
    date_utc = _ist_to_utc(date)
    jd = swe.julday(
        date_utc.year, date_utc.month, date_utc.day,
        date_utc.hour + date_utc.minute / 60.0,
    )

    # Resolve location
    mode = (location_mode or "birth").lower()
    if mode == "birth":
        lat, lon = birth["lat"], birth["lon"]
    elif mode == "current":
        if not location_override:
            raise ValueError("location_override required when location_mode='current'")
        lat, lon = location_override["lat"], location_override["lon"]
    else:
        lat = location_override["lat"] if location_override else birth["lat"]
        lon = location_override["lon"] if location_override else birth["lon"]

    positions = get_planet_positions(jd)
    latitudes = get_planet_latitudes(jd)
    retrograde_flags = get_retrograde_flags(jd)
    house_data = get_house_cusps(jd, lat, lon)

    return AstronomyResult(
        jd=jd,
        ayanamsa=_get_configured_ayanamsa(),
        lat=lat,
        lon=lon,
        positions=positions,
        latitudes=latitudes,
        speeds={},  # can be populated if needed
        retrograde_flags=retrograde_flags,
        ascendant=house_data["ascendant"],
        house_cusps=tuple(house_data["houses"]),
        natal_positions=natal_positions,
        natal_jd=birth_jd,
    )
