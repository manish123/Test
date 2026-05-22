from features.dignity import get_planet_status, get_sign, SIGN_LORDS
from astronomy.utils import normalize_lon


def build_planet(name, lon, retro=False):
    lon = normalize_lon(lon)
    sign = get_sign(lon)
    return {
        "name": name,
        "longitude": lon,
        "sign": sign,
        "status": get_planet_status(name, lon),
        "dispositor": SIGN_LORDS[sign],
        "is_kendra": False,
        "nakshatra": None,
        "retrograde": retro,
        "multiplier": 1.0,
        "vimsopaka": 0,
    }
