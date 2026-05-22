"""
Planetary Conditions — Neutral Symbolic States (Layer C1)

Every function here returns a DESCRIPTION of what is happening astronomically
and symbolically. No judgment about whether it's "good" or "bad."

Domain interpretation layers (C2) decide what these conditions mean
for trading, career, relationships, health, or spirituality.
"""


# ═══════════════════════════════════════════════════════════════
# INTENSITY STATES (how strong is the planet's expression?)
# ═══════════════════════════════════════════════════════════════

def classify_intensity(multiplier):
    """
    Classify planet's current expressive intensity from its computed multiplier.
    Returns a neutral label — not good/bad.
    """
    if multiplier >= 1.3:
        return "amplified"
    if multiplier >= 1.0:
        return "expressed"
    if multiplier >= 0.6:
        return "subdued"
    if multiplier >= 0.3:
        return "restricted"
    return "dormant"


# ═══════════════════════════════════════════════════════════════
# PLANETARY CONDITION STATES
# ═══════════════════════════════════════════════════════════════

def describe_combustion(planet_name, is_combust, sun_distance_deg=None):
    """
    Combustion = planet too close to Sun, its independent expression is absorbed.
    Neutral meaning: the planet's significations are merged with solar authority.
    """
    if not is_combust:
        return {"condition": "visible", "description": f"{planet_name} expresses independently"}

    return {
        "condition": "combust",
        "description": f"{planet_name} merged with solar authority — its significations expressed through ego/power axis",
        "sun_distance": sun_distance_deg,
    }


def describe_retrograde(planet_name, is_retrograde, dignity_status):
    """
    Retrograde = apparent backward motion. Neutral meaning: internalization,
    revisiting, deepening. NOT inherently negative.
    """
    if not is_retrograde:
        return {"condition": "direct", "description": f"{planet_name} in forward expression"}

    descriptions = {
        "exalted": f"{planet_name} retrograde while exalted — potent internal processing, wisdom deepening",
        "debilitated": f"{planet_name} retrograde while debilitated — karmic correction active, hidden strength emerging",
        "own": f"{planet_name} retrograde in own sign — self-reflective mastery",
    }

    return {
        "condition": "retrograde",
        "description": descriptions.get(dignity_status, f"{planet_name} retrograde — internalized expression, revisiting themes"),
        "dignity_context": dignity_status,
    }


def describe_dignity(planet_name, status):
    """
    Dignity = relationship between planet and its current sign.
    Neutral: describes quality of expression, not good/bad.
    """
    descriptions = {
        "exalted": f"{planet_name} at peak expressive capacity — maximum natural alignment",
        "moolatrikona": f"{planet_name} in professional zone — structured, competent expression",
        "own": f"{planet_name} in comfort — authentic, unforced expression",
        "great_friend": f"{planet_name} well-supported — collaborative, enhanced expression",
        "friend": f"{planet_name} mildly supported — pleasant, easy expression",
        "neutral": f"{planet_name} in neutral territory — neither helped nor hindered",
        "enemy": f"{planet_name} in friction — expression requires extra effort",
        "bitter_enemy": f"{planet_name} in deep friction — fundamental tension with environment",
        "debilitated": f"{planet_name} at minimum natural alignment — expression redirected inward",
    }
    return {
        "condition": status,
        "description": descriptions.get(status, f"{planet_name} in {status} state"),
    }


# ═══════════════════════════════════════════════════════════════
# YOGA CONDITIONS (combination patterns)
# ═══════════════════════════════════════════════════════════════

def describe_kala_sarpa(is_active, sarpa_type):
    """
    Kala Sarpa = all planets between Rahu-Ketu axis.
    Neutral: concentrated karmic axis, energy flows along one channel.
    """
    if not is_active:
        return {"condition": "inactive", "description": "Planets distributed freely across zodiac"}

    return {
        "condition": "active",
        "type": sarpa_type,
        "description": "All planetary energy concentrated along Rahu-Ketu axis — focused karmic channel active",
        "themes": [
            "intense focus on specific life axis",
            "reduced flexibility / diversification",
            "deep karmic processing",
            "potential for concentrated breakthroughs OR concentrated pressure",
        ],
    }


def describe_dainya_yoga(is_active):
    """
    Dainya = exchange between trikona lord and trik lord.
    Neutral: energy exchange between support and challenge houses.
    """
    if not is_active:
        return {"condition": "inactive", "description": "No trik-trikona exchange"}

    return {
        "condition": "active",
        "description": "Energy exchange between supportive and challenging life areas",
        "themes": [
            "good fortune connected to overcoming difficulty",
            "resources tied to service/healing/debt",
            "growth through adversity pattern",
        ],
    }


def describe_mahapurusha(active_planets):
    """
    Mahapurusha = planet in own/exalted sign in kendra.
    Neutral: a planet at peak structural power in a cardinal house.
    """
    if not active_planets:
        return {"condition": "inactive", "description": "No mahapurusha yoga active"}

    yoga_names = {
        "Mars": "Ruchaka (courage, command, physical power)",
        "Mercury": "Bhadra (intelligence, communication, commerce)",
        "Jupiter": "Hamsa (wisdom, spirituality, fortune)",
        "Venus": "Malavya (beauty, luxury, artistic refinement)",
        "Saturn": "Sasha (discipline, endurance, authority through labor)",
    }

    return {
        "condition": "active",
        "planets": active_planets,
        "descriptions": [yoga_names.get(p, f"{p} at structural peak") for p in active_planets],
        "themes": ["exceptional capacity in the planet's domain", "structural advantage in cardinal life areas"],
    }


# ═══════════════════════════════════════════════════════════════
# TIMING CONDITIONS
# ═══════════════════════════════════════════════════════════════

def describe_sade_sati(phase):
    """
    Sade Sati = Saturn transiting near natal Moon (7.5 year cycle).
    Neutral: restructuring pressure on emotional/mental foundations.
    """
    descriptions = {
        "none": "Saturn not pressuring natal Moon — emotional baseline undisturbed",
        "rising": "Saturn approaching natal Moon — preparation phase, old structures loosening",
        "peak": "Saturn conjunct natal Moon — maximum restructuring of emotional foundations",
        "setting": "Saturn departing natal Moon — integration phase, new foundations settling",
        "ashtama": "Saturn in 8th from Moon — deep transformation of psychological patterns",
    }
    return {
        "condition": phase,
        "description": descriptions.get(phase, f"Sade Sati phase: {phase}"),
        "themes": [
            "emotional maturation",
            "reality testing",
            "structural change in inner life",
            "patience and endurance development",
        ] if phase != "none" else [],
    }


def describe_dasha_sandhi(is_sandhi, md_lord, ad_lord):
    """
    Dasha sandhi = transition zone between dasha periods.
    Neutral: liminal phase, old themes fading, new themes emerging.
    """
    if not is_sandhi:
        return {
            "condition": "stable",
            "description": f"{md_lord}/{ad_lord} dasha fully established",
        }

    return {
        "condition": "sandhi",
        "description": f"Transition zone — {md_lord}/{ad_lord} themes not yet fully anchored",
        "themes": [
            "ambiguity between old and new life themes",
            "reduced certainty in predictions",
            "transitional energy — flexibility required",
        ],
    }


def describe_chandrabala(count_from_moon):
    """
    Chandrabala = Moon's transit position relative to natal Moon.
    Neutral: describes emotional-energetic context.
    """
    descriptions = {
        1: "Moon in own natal position — emotional return, familiar ground",
        2: "2nd from Moon — resource/comfort focus",
        3: "3rd from Moon — courage, initiative, communication active",
        4: "4th from Moon — domestic/emotional depth",
        5: "5th from Moon — creativity, romance, speculation active",
        6: "6th from Moon — service, competition, effort required",
        7: "7th from Moon — partnership axis activated",
        8: "8th from Moon — transformation axis, hidden currents active",
        9: "9th from Moon — expansion, dharma, higher purpose",
        10: "10th from Moon — public action, career prominence",
        11: "11th from Moon — gains, fulfillment, network activation",
        12: "12th from Moon — withdrawal, reflection, expenditure",
    }
    return {
        "count": count_from_moon,
        "description": descriptions.get(count_from_moon, f"{count_from_moon}th from Moon"),
    }


def describe_moorthy(grade, factor):
    """
    Moorthy = quality of Moon's transit relative to natal Moon sign.
    Neutral: describes receptivity level.
    """
    descriptions = {
        "Swarna": "Gold receptivity — environment highly supportive of intentions",
        "Rajata": "Silver receptivity — moderate environmental support",
        "Taamra": "Copper receptivity — mild friction with environment",
        "Loha": "Iron receptivity — strong environmental resistance to intentions",
    }
    return {
        "grade": grade,
        "factor": factor,
        "description": descriptions.get(grade, f"Moorthy: {grade}"),
    }


# ═══════════════════════════════════════════════════════════════
# COMPOSITE STATE BUILDER
# ═══════════════════════════════════════════════════════════════

def build_symbolic_state(engine_result):
    """
    Extract all symbolic states from a legacy engine result dict.
    Returns a domain-neutral symbolic snapshot.

    Args:
        engine_result: dict from _run_single()

    Returns:
        dict with all symbolic conditions (no judgment, no domain bias)
    """
    planets_states = []
    for p in engine_result.get("planets", []):
        planets_states.append({
            "name": p["name"],
            "intensity": classify_intensity(p.get("multiplier", 1.0)),
            "dignity": describe_dignity(p["name"], p.get("status", "neutral")),
            "retrograde": describe_retrograde(p["name"], p.get("retrograde", False), p.get("status", "neutral")),
            "combustion": describe_combustion(p["name"], p.get("combust", False)),
            "house": p.get("house"),
            "nakshatra": p.get("nakshatra"),
            "lajjitadi": p.get("lajjitadi", "normal"),
        })

    yoga = engine_result.get("yoga", {})
    tara = engine_result.get("tara", {})
    moorthy = engine_result.get("moorthy", {})
    nodes = engine_result.get("nodes", {})
    dasha = engine_result.get("dasha", {})
    risk_context = engine_result.get("risk_context", {})

    # Chandrabala
    moon_house_from_natal = None
    for p in engine_result.get("planets", []):
        if p["name"] == "Moon":
            moon_house_from_natal = p.get("house")
            break

    return {
        "planets": planets_states,
        "yogas": {
            "kala_sarpa": describe_kala_sarpa(nodes.get("kala_sarpa", False), nodes.get("kala_sarpa_type")),
            "dainya": describe_dainya_yoga(yoga.get("dainya", False)),
            "mahapurusha": describe_mahapurusha(yoga.get("mahapurusha", [])),
            "bhanga": yoga.get("bhanga", False),
        },
        "timing": {
            "sade_sati": describe_sade_sati(risk_context.get("sade_sati_phase", "none")),
            "dasha_sandhi": describe_dasha_sandhi(dasha.get("sandhi", False), dasha.get("md", ""), dasha.get("ad", "")),
            "chandrabala": describe_chandrabala(moon_house_from_natal) if moon_house_from_natal else None,
            "moorthy": describe_moorthy(moorthy.get("grade", ""), moorthy.get("factor", 1.0)),
        },
        "tara": {
            "score": tara.get("score", 0),
            "janma_nakshatra": tara.get("janma_nakshatra", ""),
        },
        "risk_pressure": {
            "node_crisis": risk_context.get("node_crisis", 0),
            "maraka": risk_context.get("maraka", 0),
            "sade_sati": risk_context.get("sade_sati", 0),
        },
    }
