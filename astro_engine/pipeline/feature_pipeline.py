"""
Feature Pipeline Stage (Layer B orchestration)

Consumes AstronomyResult, produces FeatureResult.
Applies canonical astrology transforms: dignity, nakshatra, houses, dasha, ashtakavarga.
"""

from contracts.astronomy_result import AstronomyResult
from contracts.feature_result import FeatureResult, PlanetFeature, DashaFeature, AshtakavargaFeature

from astronomy.utils import normalize_lon
from features.dignity import SIGN_LORDS
from features.planet_builder import build_planet
from features.nakshatra import get_nakshatra
from features.houses import get_planet_house, get_operational_house, detect_strong_houses
from features.vimsopaka import compute_vimsopaka
from features.ashtakavarga import compute_ashtakavarga
from features.dasha import get_current_vimshottari
from features.panchang import compute_panchang_score


def run_features(astro: AstronomyResult, birth_data: dict, eval_date) -> FeatureResult:
    """
    Execute Layer B: extract classical astrology features from raw positions.

    Args:
        astro: AstronomyResult from astronomy pipeline
        birth_data: dict with 'date', 'lat', 'lon' (for dasha calculation)
        eval_date: datetime of evaluation (for panchang weekday)

    Returns:
        FeatureResult (frozen dataclass)
    """
    asc_sign = int(normalize_lon(astro.ascendant) // 30) + 1
    natal_moon_sign = int(normalize_lon(astro.natal_positions["Moon"]) // 30) + 1

    # --- Build planet feature objects ---
    planets_raw = []
    for name, lon in astro.positions.items():
        p = build_planet(name, lon, retro=astro.retrograde_flags.get(name, False))
        p["latitude"] = astro.latitudes.get(name)
        p["nakshatra"] = get_nakshatra(lon)
        rashi_house = int((((p["sign"] - asc_sign) % 12) + 1))
        chalit_house = get_planet_house(p["longitude"], astro.house_cusps)
        p["rashi_house"] = rashi_house
        p["house"] = chalit_house
        p["is_kendra"] = chalit_house in [1, 4, 7, 10]
        p["operational_house"] = get_operational_house(p["longitude"], astro.house_cusps, rashi_house)
        planets_raw.append(p)

    # --- Ashtakavarga ---
    planet_signs = {
        p["name"]: p["sign"] for p in planets_raw
        if p["name"] in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    }
    ashtakavarga_data = compute_ashtakavarga(planet_signs, asc_sign=asc_sign)

    # --- Dasha ---
    vim = get_current_vimshottari(birth_data["date"], eval_date, astro.natal_positions["Moon"])
    dasha_feature = DashaFeature(
        md=vim["md"],
        ad=vim["ad"],
        sandhi_active=vim["sandhi_active"],
    )

    # --- Strong houses ---
    # Note: strong_houses needs multiplier which is set by state_engine (rules layer).
    # At this stage we pass planets_raw without multiplier processing.
    # detect_strong_houses will be called again after rules layer processes states.
    strong_houses = []  # populated after state_engine in rules layer

    # --- Panchang (derived from longitudes) ---
    moon_lon = astro.positions.get("Moon", 0)
    sun_lon = astro.positions.get("Sun", 0)
    janma_nak = get_nakshatra(astro.natal_positions["Moon"])

    # --- Ashtakavarga as contract ---
    av_feature = AshtakavargaFeature(
        bav=ashtakavarga_data["bav"],
        sav_raw=ashtakavarga_data["sav_raw"],
        sav_trikona=ashtakavarga_data["sav_trikona"],
        sav_sodhya=ashtakavarga_data["sav_sodhya"],
    )

    # --- Build PlanetFeature objects ---
    planet_features = []
    for p in planets_raw:
        pf = PlanetFeature(
            name=p["name"],
            longitude=p["longitude"],
            latitude=p.get("latitude", 0.0),
            sign=p["sign"],
            nakshatra=p.get("nakshatra", ""),
            status=p.get("status", "neutral"),
            dispositor=p.get("dispositor", ""),
            retrograde=p.get("retrograde", False),
            house=p.get("house", 1),
            rashi_house=p.get("rashi_house", 1),
            operational_house=p.get("operational_house", 1),
            is_kendra=p.get("is_kendra", False),
            vimsopaka=compute_vimsopaka(p),
        )
        planet_features.append(pf)

    return FeatureResult(
        planets=planet_features,
        asc_sign=asc_sign,
        natal_moon_sign=natal_moon_sign,
        strong_houses=strong_houses,
        dasha=dasha_feature,
        ashtakavarga=av_feature,
        janma_nakshatra=janma_nak,
    )
