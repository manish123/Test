"""
Planet Enrichment (Layer B)

Takes raw astronomical positions (longitudes, speeds, retro flags) and enriches
them with classical astrology features: nakshatra, dignity, sign lord relationship.

Dependencies: features.nakshatra, features.dignity (both Layer B)
Never imports swisseph. Never fetches positions. Pure enrichment from pre-computed data.
"""

from features.nakshatra import get_comprehensive_nakshatra_info, longitude_to_rashi_dms, planet_sanskrit_names
from features.dignity import get_planet_status, get_sign, SIGN_LORDS, _relationship_tier


# Sanskrit state mapping
_STATE_MAPPING = {
    "exalted": "Udita",
    "debilitated": "Kshudhita",
    "moolatrikona": "Moolatrikona",
    "own": "Swakshetra",
    "great_friend": "Prasanna",
    "friend": "Shanta",
    "neutral": "Dina",
    "enemy": "Kopita",
    "bitter_enemy": "Dukhita",
}

_RELATIONSHIP_MAPPING = {
    "great_friend": "Great Friend with Landlord",
    "friend": "Friend with Landlord",
    "neutral": "Neutral with Landlord",
    "enemy": "Enemy with Landlord",
    "bitter_enemy": "Bitter Enemy with Landlord",
}


def enrich_planet(name, longitude, latitude=0.0, speed=0.0, retrograde=False, ra=0.0, dec=0.0):
    """
    Enrich a single planet's raw astronomical data with classical astrology features.

    Args:
        name: planet name (e.g. "Mars")
        longitude: sidereal longitude (degrees)
        latitude: celestial latitude (degrees)
        speed: daily motion (degrees/day)
        retrograde: bool
        ra: right ascension (degrees)
        dec: declination (degrees)

    Returns:
        dict with all enriched fields
    """
    nakshatra_info = get_comprehensive_nakshatra_info(longitude)
    status = get_planet_status(name, longitude)
    sign = get_sign(longitude)
    sign_lord = SIGN_LORDS[sign]
    relationship = _relationship_tier(name, sign_lord)

    return {
        "longitude": round(longitude, 6),
        "latitude": round(latitude, 6),
        "speed": round(speed, 6),
        "retrograde": retrograde,
        "ra": round(ra, 6),
        "dec": round(dec, 6),
        "nakshatra": nakshatra_info,
        "state": _STATE_MAPPING.get(status, status),
        "status": status,
        "relationship": _RELATIONSHIP_MAPPING.get(relationship, relationship),
        "sign": sign,
        "sign_lord": sign_lord,
        "sanskrit_name": planet_sanskrit_names.get(name, name),
    }


def enrich_all_planets(positions, latitudes=None, speeds=None, retrograde_flags=None, ra_dec=None):
    """
    Enrich all planets from raw position dicts.

    Args:
        positions: dict {name: longitude}
        latitudes: dict {name: latitude} (optional)
        speeds: dict {name: speed} (optional)
        retrograde_flags: dict {name: bool} (optional)
        ra_dec: dict {name: {"ra": float, "dec": float}} (optional)

    Returns:
        dict {name: enriched_planet_dict}
    """
    latitudes = latitudes or {}
    speeds = speeds or {}
    retrograde_flags = retrograde_flags or {}
    ra_dec = ra_dec or {}

    result = {}
    for name, lon in positions.items():
        rd = ra_dec.get(name, {})
        result[name] = enrich_planet(
            name=name,
            longitude=lon,
            latitude=latitudes.get(name, 0.0),
            speed=speeds.get(name, 0.0),
            retrograde=retrograde_flags.get(name, False),
            ra=rd.get("ra", 0.0),
            dec=rd.get("dec", 0.0),
        )
    return result


def format_planet_report(name, enriched_data):
    """
    Format an enriched planet dict into a human-readable report string.

    Args:
        name: planet name
        enriched_data: dict from enrich_planet()

    Returns:
        str: formatted multi-line report
    """
    planet_symbols = {
        "Sun": "☉", "Moon": "☾", "Mars": "♂", "Mercury": "☿",
        "Jupiter": "♃", "Venus": "♀", "Saturn": "♄",
        "Rahu": "☊", "Ketu": "☋", "Ascendant": "☊",
    }

    symbol = planet_symbols.get(name, "")
    nak_info = enriched_data["nakshatra"]
    rashi_name, deg, min_val, sec = longitude_to_rashi_dms(enriched_data["longitude"])

    lat = enriched_data["latitude"]
    lat_deg = int(abs(lat))
    lat_min = int((abs(lat) - lat_deg) * 60)
    lat_sec = ((abs(lat) - lat_deg) * 60 - lat_min) * 60
    lat_dir = "S" if lat < 0 else "N"

    pada_suffix = {1: "st", 2: "nd", 3: "rd"}.get(nak_info["pada"], "th")
    motion_symbol = "↺" if enriched_data["retrograde"] else "↻"

    lines = [
        f"{symbol}" if symbol else "",
        f"{name} ({name[:3]})",
        f"{enriched_data['sanskrit_name']}",
        f"Longitude: {rashi_name} {deg}° {min_val}' {sec:.2f}\"",
        f"Latitude/Shara: {lat_deg:02d}° {lat_dir} {lat_min}' {lat_sec:.0f}\" ({lat:+.2f})",
        f"Speed: Planet Speed {enriched_data['speed']:+.2f} deg/day",
        f"Nakshatra: {nak_info['nakshatra']}, {nak_info['pada']}{pada_suffix} Pada",
        f"Motion: {motion_symbol} {'Retrograde' if enriched_data['retrograde'] else 'Forward'}",
        f"State: {enriched_data['state']}",
        f"Residing in: {enriched_data['relationship']}",
        f"Nakshatra Lord: {planet_sanskrit_names.get(nak_info['lord'], nak_info['lord'])}",
        f"Nakshatra Sub Lord: {planet_sanskrit_names.get(nak_info['sub_lord'], nak_info['sub_lord'])}",
        f"Right Ascension: {enriched_data['ra']:+.2f}",
        f"Declination/Kranti: {enriched_data['dec']:+.2f}",
        f"Raw Longitude: {enriched_data['longitude']:+.2f}",
    ]

    return "\n".join(line for line in lines if line)
