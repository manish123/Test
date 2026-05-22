from features.divisional import get_d9_sign
from features.dignity import SIGN_LORDS, get_planet_status
from features.planet_builder import build_planet
from astronomy.utils import normalize_lon
from features.nakshatra import get_nakshatra
from features.houses import get_houses, get_planet_house, get_operational_house
from rules.state_engine import process_chart_states
from features.vimsopaka import compute_vimsopaka


BENEFICS = {"Moon", "Mercury", "Jupiter", "Venus"}
MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

# Rahu and Ketu guna assignments (classical Jyotish)
# Rahu = Tamas, Ketu = Sattva
_NODE_GUNA = {"Rahu": "Tamas", "Ketu": "Sattva"}


def _ist_to_utc(dt):
    from datetime import timedelta
    return dt - timedelta(hours=5, minutes=30)


def _relative_house(base_sign, target_sign):
    return ((target_sign - base_sign) % 12) + 1


def _build_conjunctions(planets):
    """Group planets by operational_house and build conjunction map."""
    by_house = {}
    for p in planets:
        by_house.setdefault(p.get("operational_house", p.get("house")), []).append(p["name"])

    conjunctions = {p["name"]: [] for p in planets}
    for names in by_house.values():
        for name in names:
            conjunctions[name] = [n for n in names if n != name]

    return conjunctions


def _build_natal_planets(birth_data):
    """
    Build a fully-processed natal planet list from birth_data.

    This is the single source of truth for all natal-chart personality
    calculations. It mirrors the planet-building pipeline in main.py but
    uses the birth datetime and birth location so the results are fixed
    for a given birth chart and never change with the evaluation date.

    Args:
        birth_data: dict with keys 'date' (datetime IST), 'lat', 'lon'

    Returns:
        tuple: (natal_planets, natal_asc_sign)
    """
    from astronomy.engine_base import get_planet_positions, get_planet_latitudes, get_retrograde_flags
    import swisseph as swe

    birth_utc = _ist_to_utc(birth_data["date"])
    birth_jd = swe.julday(
        birth_utc.year,
        birth_utc.month,
        birth_utc.day,
        birth_utc.hour + birth_utc.minute / 60.0,
    )

    lat = birth_data["lat"]
    lon = birth_data["lon"]

    raw_positions = get_planet_positions(birth_jd)
    raw_latitudes = get_planet_latitudes(birth_jd)
    retro_flags = get_retrograde_flags(birth_jd)

    house_data = get_houses(birth_jd, lat, lon)
    asc_sign = int(normalize_lon(house_data["ascendant"]) // 30) + 1

    planets = []
    for name, plon in raw_positions.items():
        p = build_planet(name, plon, retro=retro_flags.get(name, False))
        p["latitude"] = raw_latitudes.get(name)
        p["nakshatra"] = get_nakshatra(plon)
        rashi_house = int((((p["sign"] - asc_sign) % 12) + 1))
        chalit_house = get_planet_house(p["longitude"], house_data["houses"])
        p["rashi_house"] = rashi_house
        p["house"] = chalit_house
        p["is_kendra"] = chalit_house in [1, 4, 7, 10]
        p["operational_house"] = get_operational_house(
            p["longitude"], house_data["houses"], rashi_house
        )
        planets.append(p)

    by_house = {}
    for p in planets:
        by_house.setdefault(p["house"], []).append(p["name"])
    conjunctions = {
        p["name"]: [x for x in by_house.get(p["house"], []) if x != p["name"]]
        for p in planets
    }

    planets = process_chart_states(
        planets, {"conjunctions": conjunctions, "datetime": birth_data["date"]}
    )
    for p in planets:
        p["vimsopaka"] = compute_vimsopaka(p)

    return planets, asc_sign


def compute_atmakaraka(planets, include_rahu=False):
    """
    Find the Atmakaraka — the planet with the highest degree in its sign.
    Rahu counts backwards (30 - degree_in_sign) per Jaimini convention.
    By default uses the 7 physical planets (Parashari system).
    Pass include_rahu=True for Jaimini 8-karaka system.
    """
    physical = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    eligible = set(physical)
    if include_rahu:
        eligible.add("Rahu")

    best_planet = None
    best_degree = -1

    for p in planets:
        if p["name"] not in eligible:
            continue

        if p["name"] == "Rahu":
            degree = 30 - (p["longitude"] % 30)
        else:
            degree = p["longitude"] % 30

        if degree > best_degree:
            best_degree = degree
            best_planet = p

    if not best_planet:
        return {}

    soul_nature = "benefic" if best_planet["name"] in BENEFICS else "malefic"
    karakamsha_sign = get_d9_sign(best_planet["longitude"])

    return {
        "atmakaraka": best_planet["name"],
        "degree_in_sign": round(best_degree, 3),
        "retrograde": bool(best_planet.get("retrograde")),
        "soul_nature": soul_nature,
        "deep_desire_flag": bool(best_planet.get("retrograde")),
        "karakamsha_sign": karakamsha_sign,
    }


def compute_karakamsha_profile(planets, karakamsha_sign):
    """
    Analyse planets relative to the Karakamsha sign (D9 sign of Atmakaraka).
    Houses 1, 2, 5, 9, 12 from Karakamsha are the key axes.
    """
    special_houses = {1, 2, 5, 9, 12}
    house_map = {h: [] for h in special_houses}

    for p in planets:
        house_from_karakamsha = _relative_house(karakamsha_sign, p["sign"])
        if house_from_karakamsha in special_houses:
            house_map[house_from_karakamsha].append(p["name"])

    return {
        "house_influences": house_map,
        "self_axis": house_map[1],       # identity / soul expression
        "wealth_axis": house_map[2],     # speech, wealth, family values
        "talent_axis": house_map[5],     # intelligence, creativity, past-life merit
        "dharma_axis": house_map[9],     # purpose, guru, higher learning
        "moksha_axis": house_map[12],    # liberation, spirituality, losses
    }


def compute_d1_d9_persona(planets):
    """
    Compare D1 (public) dignity vs D9 (private/soul) dignity for each planet.
    Reveals hidden strengths (debilitated in D1 but exalted/strong in D9)
    and hidden weaknesses (exalted in D1 but debilitated in D9).
    moolatrikona in D9 is treated as equivalent to 'own' strength.
    """
    hidden_weakness = []
    hidden_strength = []
    public_private = []

    for p in planets:
        d1_status = p.get("status", "neutral")
        d9_sign = get_d9_sign(p["longitude"])
        d9_proxy_lon = (d9_sign - 1) * 30 + 1
        d9_status = get_planet_status(p["name"], d9_proxy_lon)

        # Treat moolatrikona as equivalent to 'own' for hidden-strength detection
        d9_strong = d9_status in ("exalted", "own", "moolatrikona")
        d1_strong = d1_status in ("exalted", "own", "moolatrikona")

        if d1_strong and d9_status == "debilitated":
            hidden_weakness.append(p["name"])
        if d1_status == "debilitated" and d9_strong:
            hidden_strength.append(p["name"])

        public_private.append(
            {
                "planet": p["name"],
                "d1_public": d1_status,
                "d9_private": d9_status,
            }
        )

    return {
        "public_private_matrix": public_private,
        "hidden_weakness": hidden_weakness,
        "hidden_strength": hidden_strength,
    }


def compute_guna_tattva(planets):
    """
    Compute Sattva/Rajas/Tamas balance from planets in trikona houses (1, 5, 9).
    Rahu = Tamas, Ketu = Sattva (classical assignments, now included).
    Also computes elemental (tattva) distribution across all 9 planets by sign.
    """
    guna_map = {
        "Sattva": {"Sun", "Moon", "Jupiter", "Ketu"},
        "Rajas":  {"Mercury", "Venus"},
        "Tamas":  {"Mars", "Saturn", "Rahu"},
    }

    guna_scores = {"Sattva": 0, "Rajas": 0, "Tamas": 0}
    for p in planets:
        house = p.get("operational_house", p.get("house"))
        if house not in {1, 5, 9}:
            continue
        for guna, members in guna_map.items():
            if p["name"] in members:
                guna_scores[guna] += 1

    sign_elements = {
        "Fire":  {1, 5, 9},
        "Earth": {2, 6, 10},
        "Air":   {3, 7, 11},
        "Water": {4, 8, 12},
    }
    tattva = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}

    for p in planets:
        sign = p["sign"]
        for element, signs in sign_elements.items():
            if sign in signs:
                tattva[element] += 1
                break

    dominant_element = max(tattva.items(), key=lambda x: x[1])[0]

    return {
        "guna_scores": guna_scores,
        "dominant_guna": max(guna_scores.items(), key=lambda x: x[1])[0],
        "tattva_scores": tattva,
        "dominant_tattva": dominant_element,
    }


def compute_lajjitaadi_complexes(planets):
    """
    Compute Lajjitaadi (psychological) states for each planet.
    Uses operational_house consistently for both conjunction grouping
    and the lajjita house-5 check.
    """
    conjunctions = _build_conjunctions(planets)
    profiles = []

    for p in planets:
        conjoined = conjunctions.get(p["name"], [])
        states = set()

        # FIX: use operational_house (same field used by _build_conjunctions)
        op_house = p.get("operational_house", p.get("house"))

        if op_house == 5 and any(x in conjoined for x in ["Rahu", "Ketu", "Sun", "Saturn", "Mars"]):
            states.add("lajjita")
        if p.get("status") in ["exalted", "own", "moolatrikona"]:
            states.add("garvita")
        if p.get("status") in ["enemy", "bitter_enemy", "debilitated"] or "Saturn" in conjoined:
            states.add("kshudita")
        if p.get("sign") in [4, 8, 12] and not any(x in conjoined for x in ["Jupiter", "Venus", "Moon"]):
            states.add("trishita")
        if any(x in conjoined for x in ["Jupiter", "Venus"]):
            states.add("mudita")
        if "Sun" in conjoined:
            states.add("kshobhita")

        paradox = None
        if "garvita" in states and "kshudita" in states:
            paradox = "external_success_internal_emptiness"

        profiles.append(
            {
                "planet": p["name"],
                "states": sorted(states) if states else ["normal"],
                "paradox": paradox,
            }
        )

    return profiles


def compute_ethical_behavior_matrix(asc_sign, planets):
    """
    Assess honesty (2nd house) and professional ambition (10th house).
    Now also checks if the 2nd lord is combust — a classical indicator
    of speech/truth issues (combust field set by state_engine.py).
    """
    second_sign = (asc_sign % 12) + 1
    second_lord = SIGN_LORDS[second_sign]
    second_lord_obj = next((p for p in planets if p["name"] == second_lord), None)

    second_house_occupants = [
        p for p in planets if p.get("operational_house", p.get("house")) == 2
    ]
    malefic_hits = sum(1 for p in second_house_occupants if p["name"] in MALEFICS)

    truthlessness_risk = malefic_hits * 20
    if second_lord_obj and second_lord_obj.get("status") == "debilitated":
        truthlessness_risk += 25
    # Combust 2nd lord — speech/truth compromised (field available from state_engine)
    if second_lord_obj and second_lord_obj.get("combust", False):
        truthlessness_risk += 15

    honesty_index = max(0, 100 - truthlessness_risk)

    tenth_sign = ((asc_sign + 8) % 12) + 1
    tenth_lord = SIGN_LORDS[tenth_sign]
    tenth_lord_obj = next((p for p in planets if p["name"] == tenth_lord), None)

    ambition_score = 50
    if tenth_lord_obj:
        if tenth_lord_obj.get("status") in ["exalted", "own", "moolatrikona"]:
            ambition_score += 25
        if tenth_lord_obj.get("status") == "debilitated":
            ambition_score -= 20
        if tenth_lord_obj.get("operational_house", tenth_lord_obj.get("house")) in [10, 11, 1]:
            ambition_score += 15

    ambition_score = max(0, min(100, ambition_score))

    return {
        "second_house": {
            "lord": second_lord,
            "malefic_influence": malefic_hits,
            "second_lord_combust": bool(second_lord_obj.get("combust", False)) if second_lord_obj else False,
            "truthlessness_risk": truthlessness_risk,
            "honesty_index": honesty_index,
        },
        "professional_behavior": {
            "tenth_lord": tenth_lord,
            "ambition_score": ambition_score,
        },
    }


def compute_solar_lunar_balance(planets):
    """
    Determine whether the chart is solar-dominant, lunar-dominant, or balanced.
    Uses the planet multiplier (which incorporates shadbala, combustion,
    retrograde, and neechabhanga from the fixed state_engine pipeline).
    """
    sun = next((p for p in planets if p["name"] == "Sun"), None)
    moon = next((p for p in planets if p["name"] == "Moon"), None)

    if not sun or not moon:
        return {"archetype": "balanced", "solar_score": 50, "lunar_score": 50}

    solar_score = sun.get("multiplier", 1.0) * 45
    lunar_score = moon.get("multiplier", 1.0) * 45

    if sun.get("operational_house", sun.get("house")) in [1, 10]:
        solar_score += 15
    if moon.get("operational_house", moon.get("house")) in [4, 7]:
        lunar_score += 15

    total = max(1.0, solar_score + lunar_score)
    solar_pct = round((solar_score / total) * 100, 2)
    lunar_pct = round((lunar_score / total) * 100, 2)

    if solar_pct - lunar_pct > 15:
        archetype = "solar"
    elif lunar_pct - solar_pct > 15:
        archetype = "lunar"
    else:
        archetype = "balanced"

    return {
        "archetype": archetype,
        "solar_score": solar_pct,
        "lunar_score": lunar_pct,
    }


def build_personality_profile(planets, asc_sign, birth_data=None):
    """
    Build the complete natal personality profile.

    Args:
        planets:    Planet list. When birth_data is provided this argument is
                    ignored — natal planets are recomputed from birth_data so
                    the profile is always anchored to the birth chart, not to
                    whatever transit date _run_single() was called with.
                    Pass planets=None and birth_data=<dict> for the cleanest call.
        asc_sign:   Natal ascendant sign (1-indexed). Ignored when birth_data
                    is provided (asc_sign is derived from the birth chart).
        birth_data: Optional dict with keys 'date' (datetime IST), 'lat', 'lon'.
                    When supplied, natal planets are built fresh from the birth
                    chart — this is the correct path for all production use.

    Returns:
        dict with all personality sub-profiles.
    """
    if birth_data is not None:
        # Always use natal positions — the profile never changes with date
        natal_planets, natal_asc_sign = _build_natal_planets(birth_data)
    else:
        # Legacy path: caller passes pre-built planets (must be natal, not transit)
        natal_planets = planets
        natal_asc_sign = asc_sign

    ak = compute_atmakaraka(natal_planets)
    karakamsha = (
        compute_karakamsha_profile(natal_planets, ak.get("karakamsha_sign", natal_asc_sign))
        if ak else {}
    )

    return {
        "atmakaraka": ak,
        "karakamsha": karakamsha,
        "persona_d1_d9": compute_d1_d9_persona(natal_planets),
        "guna_tattva": compute_guna_tattva(natal_planets),
        "lajjitaadi": compute_lajjitaadi_complexes(natal_planets),
        "ethics_behavior": compute_ethical_behavior_matrix(natal_asc_sign, natal_planets),
        "solar_lunar": compute_solar_lunar_balance(natal_planets),
    }
