"""
Planetary Position Calculator API (Layer B — Composite Feature Module)

Production-ready function for calculating enriched planetary positions.
Uses Layer A (astronomy.engine_base) for raw positions and Layer B
(features.planet_enrichment) for classical astrology enrichment.

No direct swisseph import in this module — all ephemeris access goes through Layer A.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, timedelta

from astronomy.engine_base import (
    get_planet_positions,
    get_planet_latitudes,
    get_planet_speeds,
    get_retrograde_flags,
    get_right_ascension_declination,
    get_house_cusps,
    configure_ephemeris,
    compute_julian_day,
    get_ayanamsa_value,
    set_topocentric_location,
)
from astronomy.ephemeris import configure_ayanamsa
from astronomy.utils import normalize_lon
from features.planet_enrichment import enrich_planet, format_planet_report
from features.nakshatra import get_comprehensive_nakshatra_info, longitude_to_rashi_dms, planet_sanskrit_names


def _ist_to_utc(dt):
    """Convert IST datetime to UTC."""
    if dt.tzinfo is None:
        return datetime.combine(dt.date(), dt.time(), timezone.utc) - timedelta(hours=5, minutes=30)
    return dt.astimezone(timezone.utc)


def _datetime_to_jd(dt):
    """Convert UTC datetime to Julian Day."""
    return compute_julian_day(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0 + dt.second / 3600.0)


def calculate_planetary_positions(date_time, location=None, ayanamsa="FAGAN_BRADLEY"):
    """
    Calculate comprehensive planetary positions with full enrichment.

    This is the production API. It calls Layer A for raw positions,
    then enriches with Layer B features (nakshatra, dignity, relationship).

    Args:
        date_time (datetime): datetime object (local time, assumed IST if no tzinfo)
        location (dict): Optional location with "latitude", "longitude", "altitude"
                        If None, uses Pune as default
        ayanamsa (str): "FAGAN_BRADLEY" (default), "LAHIRI", "RAMAN", "KRISHNAMURTI"

    Returns:
        dict: Complete planetary data with success/error status
    """
    try:
        if not isinstance(date_time, datetime):
            return {"success": False, "error": "date_time must be a datetime object", "data": None}

        if location is None:
            location = {"latitude": 18.5204, "longitude": 73.8567, "altitude": 560}

        if not all(key in location for key in ["latitude", "longitude", "altitude"]):
            return {"success": False, "error": "location must contain latitude, longitude, and altitude", "data": None}

        # Convert to UTC and JD
        utc_time = _ist_to_utc(date_time)
        jd = _datetime_to_jd(utc_time)

        # Set ayanamsa
        ayanamsa_map = {
            "FAGAN_BRADLEY": "FAGAN_BRADLEY",
            "LAHIRI": "LAHIRI",
            "RAMAN": "RAMAN",
            "KRISHNAMURTI": "KRISHNAMURTI",
        }
        if ayanamsa not in ayanamsa_map:
            ayanamsa = "FAGAN_BRADLEY"
        configure_ayanamsa(ayanamsa)

        # Set topocentric location
        set_topocentric_location(location["longitude"], location["latitude"], location["altitude"])

        # --- Layer A: raw positions ---
        loc_dict = location
        positions = get_planet_positions(jd, loc_dict)
        latitudes = get_planet_latitudes(jd, loc_dict)
        speeds = get_planet_speeds(jd, loc_dict)
        retro_flags = get_retrograde_flags(jd, loc_dict)
        ra_dec = get_right_ascension_declination(jd, loc_dict)

        # --- Layer B: enrichment ---
        planet_data = {}
        for name, lon in positions.items():
            rd = ra_dec.get(name, {"ra": 0.0, "dec": 0.0})
            planet_data[name] = enrich_planet(
                name=name,
                longitude=lon,
                latitude=latitudes.get(name, 0.0),
                speed=speeds.get(name, 0.0),
                retrograde=retro_flags.get(name, False),
                ra=rd["ra"] if isinstance(rd, dict) else rd,
                dec=rd["dec"] if isinstance(rd, dict) else 0.0,
            )

        # Ascendant
        cusps = get_house_cusps(jd, location["latitude"], location["longitude"])
        ascendant_sidereal = cusps["ascendant"] % 360  # already sidereal from get_house_cusps

        planet_data["Ascendant"] = {
            "longitude": round(ascendant_sidereal, 6),
            "latitude": 0.0,
            "speed": 368.15,
            "retrograde": False,
            "ra": 0.0,
            "dec": 0.0,
            "nakshatra": get_comprehensive_nakshatra_info(ascendant_sidereal),
            "state": "Never Asta",
            "status": "n/a",
            "relationship": "",
            "sign": int(ascendant_sidereal // 30) + 1,
            "sign_lord": "",
            "sanskrit_name": "Lagna",
        }

        return {
            "success": True,
            "error": None,
            "data": planet_data,
            "metadata": {
                "date_time": date_time.isoformat(),
                "utc_time": utc_time.isoformat(),
                "julian_day": round(jd, 6),
                "location": location,
                "ayanamsa": ayanamsa,
                "planets_calculated": list(planet_data.keys()),
            },
        }

    except Exception as e:
        return {"success": False, "error": f"Calculation error: {str(e)}", "data": None}


def get_planet_report(planet_name, planet_data):
    """Format individual planet data into report string."""
    return format_planet_report(planet_name, planet_data)


def get_all_planet_reports(date_time, location=None, ayanamsa="FAGAN_BRADLEY"):
    """Get formatted reports for all planets."""
    result = calculate_planetary_positions(date_time, location, ayanamsa)
    if not result["success"]:
        return result

    planet_order = [
        "Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ]
    reports = {}
    for name in planet_order:
        if name in result["data"]:
            reports[name] = format_planet_report(name, result["data"][name])

    return {"success": True, "error": None, "data": reports, "metadata": result["metadata"]}


def get_supported_ayanamsas():
    """Get list of supported ayanamsas."""
    return {
        "FAGAN_BRADLEY": {"name": "Fagan-Bradley", "description": "Default for this system", "default": True},
        "LAHIRI": {"name": "Lahiri", "description": "Traditional Vedic astrology", "default": False},
        "RAMAN": {"name": "Raman", "description": "Raman ayanamsa", "default": False},
        "KRISHNAMURTI": {"name": "Krishnamurti", "description": "KP system", "default": False},
    }


API_VERSION = "2.0.0"
LAST_UPDATED = "2026-05-22"
