from rules.avastha import get_jagradadi_multiplier, get_lajjitadi_state
from rules.retrograde import apply_retrograde
from rules.neechabhanga import check_neechabhanga
from features.combustion import apply_combustion
from rules.graha_yuddha import detect_graha_yuddha
from rules.aspects import build_graha_aspects
from features.shadbala import compute_shadbala


STATUS_MULTIPLIER = {
    "exalted": 1.5,
    "own": 1.2,
    "great_friend": 1.15,
    "friend": 1.05,
    "neutral": 1.0,
    "enemy": 0.9,
    "bitter_enemy": 0.75,
    "debilitated": 0.5,
}


def process_planet_state(planet, chart):
    base_avastha = get_jagradadi_multiplier(planet["status"])
    multiplier = STATUS_MULTIPLIER.get(planet["status"], 1.0) * base_avastha

    if check_neechabhanga(planet, chart):
        multiplier = max(multiplier, 1.5)

    multiplier = apply_retrograde(
        {
            "retrograde": planet["retrograde"],
            "status": planet["status"],
            "multiplier": multiplier,
        }
    )

    sun_lon = chart.get("sun_longitude")
    if sun_lon is not None:
        multiplier, combust = apply_combustion(
            planet["name"],
            multiplier,
            planet["longitude"],
            sun_lon,
            retrograde=planet.get("retrograde", False),
        )
        planet["combust"] = combust
    else:
        planet["combust"] = False

    losers = chart.get("graha_yuddha_losers", set())
    if planet["name"] in losers:
        multiplier = 0.0

    shadbala = compute_shadbala(planet, chart)
    multiplier *= shadbala["multiplier"]
    planet["shadbala"] = shadbala

    planet["lajjitadi"] = get_lajjitadi_state(planet, chart)

    planet["multiplier"] = multiplier
    return planet


def process_chart_states(planets, chart):
    chart_context = dict(chart)
    chart_context["sun_longitude"] = next(
        (p["longitude"] for p in planets if p["name"] == "Sun"),
        None,
    )
    chart_context["moon_house"] = next(
        (p.get("house") for p in planets if p["name"] == "Moon"),
        None,
    )
    chart_context.setdefault("aspects", {})

    for p in planets:
        chart_context[p["name"]] = p

    chart_context["aspects"] = build_graha_aspects(planets)

    chart_context["graha_yuddha_losers"] = detect_graha_yuddha(planets)

    return [process_planet_state(planet, chart_context) for planet in planets]
