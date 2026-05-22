"""
Dignity Feature Extraction (Layer B)

Pure data tables and deterministic classification functions.
Given a planet name and longitude, returns dignity status.

Dependencies: astronomy.utils (normalize_lon) only.
Never calls ephemeris. Never fetches positions.
"""

from astronomy.utils import normalize_lon


# --- DATA TABLES (canonical Vedic astrology reference) ---

SIGN_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun",
    6: "Mercury", 7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn",
    11: "Saturn", 12: "Jupiter",
}

NATURAL_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}

NATURAL_ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}

EXALTATION = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6,
    "Jupiter": 4, "Venus": 12, "Saturn": 7,
}

DEBILITATION = {
    "Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12,
    "Jupiter": 10, "Venus": 6, "Saturn": 1,
}

MOOLATRIKONA = {
    "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 6,
    "Jupiter": 9, "Venus": 7, "Saturn": 11,
}


# --- PURE FUNCTIONS (no side effects, no I/O) ---

def _relationship_tier(planet_name, sign_lord):
    """Determine relationship tier between planet and sign lord."""
    friends = NATURAL_FRIENDS.get(planet_name, set())
    enemies = NATURAL_ENEMIES.get(planet_name, set())
    lord_friends = NATURAL_FRIENDS.get(sign_lord, set())
    lord_enemies = NATURAL_ENEMIES.get(sign_lord, set())

    mutual_friend = sign_lord in friends and planet_name in lord_friends
    mutual_enemy = sign_lord in enemies and planet_name in lord_enemies

    if mutual_friend:
        return "great_friend"
    if mutual_enemy:
        return "bitter_enemy"
    if sign_lord in friends:
        return "friend"
    if sign_lord in enemies:
        return "enemy"
    return "neutral"


def get_sign(lon):
    """Get sign number from longitude (1-12 for Aries-Pisces)."""
    return int(normalize_lon(lon) // 30) + 1


def get_planet_status(planet_name, lon):
    """
    Get basic dignity status of planet based on its longitude.

    Returns one of: exalted, debilitated, moolatrikona, own,
    great_friend, friend, neutral, enemy, bitter_enemy
    """
    sign = get_sign(lon)

    if planet_name in EXALTATION and sign == EXALTATION[planet_name]:
        return "exalted"

    if planet_name in DEBILITATION and sign == DEBILITATION[planet_name]:
        return "debilitated"

    if planet_name in MOOLATRIKONA and sign == MOOLATRIKONA[planet_name]:
        return "moolatrikona"

    if SIGN_LORDS[sign] == planet_name:
        return "own"

    return _relationship_tier(planet_name, SIGN_LORDS[sign])
