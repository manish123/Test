"""
Property Purchase Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow.
Domain: Property Purchase & House Acquisition
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import swisseph as swe
from astronomy.engine_base import get_planet_positions, get_house_cusps, configure_ephemeris
from astronomy.utils import normalize_lon
from features.dasha import get_current_vimshottari, _generate_md_periods, _generate_ad_periods
from features.dignity import SIGN_LORDS, get_sign
from features.nakshatra import get_nakshatra

# ── Shared infrastructure (Phase 1 refactor) ─────────────────
from rules.evaluator_base import (
    IST_OFFSET, ist_to_utc, get_jd,
    SIGN_NAMES, NAKSHATRA_LORDS,
    NATURAL_BENEFICS, NATURAL_MALEFICS, BENEFIC_HOUSES, MALEFIC_HOUSES,
    JUPITER_ASPECTS, SATURN_ASPECTS, MARS_ASPECTS,
    BaseChartState, BaseTransitState,
)

# ═══════════════════════════════════════════════════════════════
# CONSTANTS (domain-specific only)
# ═══════════════════════════════════════════════════════════════
RULES_DIR = Path(__file__).resolve().parent / "domains" / "property" / "property_purchase_and_house_acquisition"

# Property Purchase-specific constants
# Mars=land(Bhumi Karaka), Moon=home/comfort, Venus=luxury, Jupiter=expansion, Saturn=structures
PROPERTY_PURCHASE_KARAKAS = {"Mars", "Moon", "Venus", "Jupiter", "Saturn"}
# 4=property, 2=wealth, 9=fortune, 10=karma, 11=gains
PROPERTY_PURCHASE_HOUSES = {4, 2, 9, 10, 11}




# ═══════════════════════════════════════════════════════════════
# CALIBRATION OVERLAY LOADER
# ═══════════════════════════════════════════════════════════════

def _load_calibration():
    """Load calibration overlay from JSON."""
    calibration_path = RULES_DIR / "calibration_overlay.json"
    try:
        with open(calibration_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "layer_weights": {
                "dasha_weight": 0.30,
                "transit_weight": 0.35,
                "fast_trigger_weight": 0.20,
                "classical_weight": 0.15,
            },
            "likelihood_thresholds": {
                "very_high": 55,
                "high": 40,
                "moderate": 25,
                "low": 15,
            },
            "base_scores": {
                "dasha": {
                    "fourth_lord_md_or_ad": 45,
                    "mars_jupiter_land_expansion": 48,
                    "saturn_mars_construction": 42,
                    "moon_jupiter_expansion": 40,
                    "moon_moon_home": 40,
                },
                "transit": {
                    "jupiter_4th_from_lagna": 50,
                    "jupiter_9th_from_lagna": 45,
                    "lagna_lord_4th_activation": 38,
                },
                "fast_trigger": {
                    "sbc_benefic_janma_nakshatra": 30,
                    "lagna_4th_lord_conjunction": 28,
                    "mars_exact_lagna_moon_lord": 26,
                },
            },
            "outcome_calibration": {
                "mode_priority_order": [
                    "house_purchase",
                    "land_acquisition",
                    "construction",
                    "luxury_property",
                    "investment",
                ],
                "quality_priority_order": ["stable", "profitable", "unstable", "debt_heavy", "disputed"],
                "default_mode": "house_purchase",
            },
        }


# Module-level calibration (loaded once at import)
CALIBRATION = _load_calibration()






# ═══════════════════════════════════════════════════════════════
# CHART STATE BUILDER
# ═══════════════════════════════════════════════════════════════

class ChartState(BaseChartState):
    """Encapsulates all natal chart data needed for property purchase rule evaluation."""

    def __init__(self, birth_dt, lat, lon, alt=0):
        super().__init__(birth_dt, lat, lon, alt)
        # Key house lords (property purchase-focused)
        self.lagna_lord = SIGN_LORDS[self.asc_sign]
        self.first_sign = self.asc_sign
        self.second_sign = ((self.asc_sign + 1 - 1) % 12) + 1
        self.second_lord = SIGN_LORDS[self.second_sign]
        self.third_sign = ((self.asc_sign + 2 - 1) % 12) + 1
        self.third_lord = SIGN_LORDS[self.third_sign]
        self.fourth_sign = ((self.asc_sign + 3 - 1) % 12) + 1
        self.fourth_lord = SIGN_LORDS[self.fourth_sign]
        self.fifth_sign = ((self.asc_sign + 4 - 1) % 12) + 1
        self.fifth_lord = SIGN_LORDS[self.fifth_sign]
        self.sixth_sign = ((self.asc_sign + 5 - 1) % 12) + 1
        self.sixth_lord = SIGN_LORDS[self.sixth_sign]
        self.seventh_sign = ((self.asc_sign + 6 - 1) % 12) + 1
        self.seventh_lord = SIGN_LORDS[self.seventh_sign]
        self.eighth_sign = ((self.asc_sign + 7 - 1) % 12) + 1
        self.eighth_lord = SIGN_LORDS[self.eighth_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.tenth_sign = ((self.asc_sign + 9 - 1) % 12) + 1
        self.tenth_lord = SIGN_LORDS[self.tenth_sign]
        self.eleventh_sign = ((self.asc_sign + 10 - 1) % 12) + 1
        self.eleventh_lord = SIGN_LORDS[self.eleventh_sign]
        self.twelfth_sign = ((self.asc_sign + 11 - 1) % 12) + 1
        self.twelfth_lord = SIGN_LORDS[self.twelfth_sign]


        # Moon lord (dispositor of Moon)
        self.moon_lord = SIGN_LORDS[self.moon_sign]

        # Planets in property purchase houses
        self.fourth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 4
        ]

        # Sensitive Property Purchase Points
        # Point 1: 4th lord + Mars longitude sum (property axis)
        fourth_lord_lon = self.birth_positions[self.fourth_lord]
        mars_lon = self.birth_positions["Mars"]
        self.sensitive_point_1 = (fourth_lord_lon + mars_lon) % 360

        # Point 2: Moon + 4th lord longitude sum (home comfort axis)
        self.sensitive_point_2 = (self.moon_lon + fourth_lord_lon) % 360# ═══════════════════════════════════════════════════════════════
# TRANSIT STATE (computed for a specific date)
# ═══════════════════════════════════════════════════════════════

class TransitState(BaseTransitState):
    """
    Transit state for this domain's evaluation.
    Thin subclass of BaseTransitState — all logic lives in the base class.
    Kept as a named class so existing call-sites continue to work unchanged.
    """
    pass

# ═══════════════════════════════════════════════════════════════
# LAYER 1: DASHA EVALUATOR (Property Purchase)
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate dasha rules for property purchase.
    Key lords: 4th lord (property), 10th lord (career property), 9th lord (fortune), Lagna lord.
    10 rules: 4th lord, Moon-Moon, Sun-Mars, Mars-Jupiter, Mars-Venus,
              Saturn-Mars, Moon-Venus, Mercury-Moon, Moon-Jupiter, Jupiter-Saturn.
    """
    fired = []

    # Rule 1: 4th lord MD/AD — primary property purchase gate (priority 95)
    r1_score = 0
    r1_reasons = []
    if md_lord == chart.fourth_lord:
        r1_score += 45
        r1_reasons.append(f"MD of 4th lord ({chart.fourth_lord}) — primary property purchase gate")
    if ad_lord == chart.fourth_lord:
        r1_score += 36
        r1_reasons.append(f"AD of 4th lord ({chart.fourth_lord}) — property sub-period active")
    if r1_score > 0:
        fired.append(("fourth_lord_property_gate", r1_score, r1_reasons))

    # Rule 2: Moon-Moon — home and comfort period (priority 90)
    if md_lord == "Moon" and ad_lord == "Moon":
        fired.append(("moon_moon_home_comfort", 40,
                      ["Moon MD + Moon AD — intense home/comfort desire, residential purchase window"]))

    # Rule 3: Sun-Mars — house through authority/land (priority 88)
    if md_lord == "Sun" and ad_lord == "Mars":
        fired.append(("sun_mars_authority_house", 35,
                      ["Sun MD + Mars AD — house through authority, government allotment, paternal land"]))
    elif md_lord == "Mars" and ad_lord == "Sun":
        fired.append(("mars_sun_land_authority", 32,
                      ["Mars MD + Sun AD — land acquisition through paternal/government channels"]))


    # Rule 4: Mars-Jupiter — land acquisition expansion (priority 92)
    if md_lord == "Mars" and ad_lord == "Jupiter":
        fired.append(("mars_jupiter_land_expansion", 48,
                      ["Mars MD + Jupiter AD — powerful land acquisition, big property expansion"]))
    elif md_lord == "Jupiter" and ad_lord == "Mars":
        fired.append(("jupiter_mars_expansion_land", 42,
                      ["Jupiter MD + Mars AD — wealth-backed land purchase"]))

    # Rule 5: Mars-Venus — villages and luxury property (priority 88)
    if md_lord == "Mars" and ad_lord == "Venus":
        fired.append(("mars_venus_village_luxury", 36,
                      ["Mars MD + Venus AD — village land, luxury residential, farmhouse"]))
    elif md_lord == "Venus" and ad_lord == "Mars":
        fired.append(("venus_mars_luxury_land", 34,
                      ["Venus MD + Mars AD — luxury property with land component"]))

    # Rule 6: Saturn-Mars — construction and structure building (priority 90)
    if md_lord == "Saturn" and ad_lord == "Mars":
        fired.append(("saturn_mars_construction", 42,
                      ["Saturn MD + Mars AD — construction, building a house, structural investment"]))
    elif md_lord == "Mars" and ad_lord == "Saturn":
        fired.append(("mars_saturn_land_structure", 38,
                      ["Mars MD + Saturn AD — land with construction, permanent structure"]))

    # Rule 7: Moon-Venus — agricultural and comfort property (priority 86)
    if md_lord == "Moon" and ad_lord == "Venus":
        fired.append(("moon_venus_agricultural_comfort", 34,
                      ["Moon MD + Venus AD — agricultural land, waterfront, beautiful home"]))
    elif md_lord == "Venus" and ad_lord == "Moon":
        fired.append(("venus_moon_comfort_beauty", 32,
                      ["Venus MD + Moon AD — comfortable beautiful residence"]))


    # Rule 8: Mercury-Moon — construction through planning (priority 84)
    if md_lord == "Mercury" and ad_lord == "Moon":
        fired.append(("mercury_moon_planned_construction", 32,
                      ["Mercury MD + Moon AD — planned construction, architectural project"]))
    elif md_lord == "Moon" and ad_lord == "Mercury":
        fired.append(("moon_mercury_home_planning", 30,
                      ["Moon MD + Mercury AD — home purchase through careful planning"]))

    # Rule 9: Moon-Jupiter — property expansion/big home (priority 90)
    if md_lord == "Moon" and ad_lord == "Jupiter":
        fired.append(("moon_jupiter_property_expansion", 40,
                      ["Moon MD + Jupiter AD — bigger home, property expansion, wealth-backed"]))
    elif md_lord == "Jupiter" and ad_lord == "Moon":
        fired.append(("jupiter_moon_expansion_home", 38,
                      ["Jupiter MD + Moon AD — expansive comfortable home purchase"]))

    # Rule 10: Jupiter-Saturn — large lands/institutional property (priority 88)
    if md_lord == "Jupiter" and ad_lord == "Saturn":
        fired.append(("jupiter_saturn_large_lands", 38,
                      ["Jupiter MD + Saturn AD — large land holdings, institutional property, long-term"]))
    elif md_lord == "Saturn" and ad_lord == "Jupiter":
        fired.append(("saturn_jupiter_structure_wealth", 36,
                      ["Saturn MD + Jupiter AD — permanent structures with wealth backing"]))

    # Bonus: Property karaka in MD/AD but not already captured
    karaka_bonus = 0
    karaka_reasons = []
    if md_lord in PROPERTY_PURCHASE_KARAKAS and not any(md_lord in str(f) for f in fired):
        karaka_bonus += 20
        karaka_reasons.append(f"MD of property karaka {md_lord}")
    if ad_lord in PROPERTY_PURCHASE_KARAKAS and not any(ad_lord in str(f) for f in fired):
        karaka_bonus += 15
        karaka_reasons.append(f"AD of property karaka {ad_lord}")
    if karaka_bonus > 0:
        fired.append(("property_karaka_bonus", karaka_bonus, karaka_reasons))

    return fired




# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR (Property Purchase)
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate transit rules for property purchase activation.
    4 rules: Jupiter 4th/9th, Lagna lord 4th, Jupiter trine 4th lord navamsa,
    Mars karaka conjunct Lagna/Moon lord.
    """
    fired = []

    # Rule 1: Jupiter transit 4th/9th from Lagna (priority 92)
    jup_house_from_lagna = transit.planet_houses_from_lagna.get("Jupiter", 0)
    if jup_house_from_lagna == 4:
        fired.append(("jupiter_4th_from_lagna", 50,
                      ["Transit Jupiter in 4th from Lagna — strongest property purchase activation"]))
    elif jup_house_from_lagna == 9:
        fired.append(("jupiter_9th_from_lagna", 45,
                      ["Transit Jupiter in 9th from Lagna — fortune/father property activation"]))

    # Rule 2: Lagna lord transit through 4th house (priority 88)
    lagna_lord = chart.lagna_lord
    lagna_lord_transit_house = transit.planet_houses_from_lagna.get(lagna_lord, 0)
    if lagna_lord_transit_house == 4:
        fired.append(("lagna_lord_4th_activation", 38,
                      [f"Transit {lagna_lord} (Lagna lord) in 4th house — self enters property domain"]))

    # Rule 3: Jupiter trine 4th lord navamsa (priority 85)
    # Approximate: check if Jupiter is trine (120°) to natal 4th lord
    fourth_lord_lon = chart.birth_positions[chart.fourth_lord]
    jup_transit_lon = transit.positions["Jupiter"]
    trine_diff = abs((jup_transit_lon - fourth_lord_lon) % 360)
    trine_diff = min(trine_diff, 360 - trine_diff)
    # Trine = 120° ± 8° OR 240° ± 8°
    is_trine = (abs(trine_diff - 120) <= 8) or (abs(trine_diff - 240) <= 8)
    if is_trine:
        fired.append(("jupiter_trine_4th_lord", 35,
                      [f"Transit Jupiter trine natal 4th lord ({chart.fourth_lord}) — deep property karma activation"]))


    # Rule 4: Mars (Bhumi Karaka) conjunct Lagna lord or Moon lord (priority 86)
    natal_lagna_lord_lon = chart.birth_positions[chart.lagna_lord]
    natal_moon_lord_lon = chart.birth_positions[chart.moon_lord]
    if transit.planet_conjunct_natal("Mars", natal_lagna_lord_lon, orb=5.0):
        fired.append(("mars_conjunct_lagna_lord", 32,
                      [f"Transit Mars conjunct natal {chart.lagna_lord} (Lagna lord) — land action activated"]))
    if transit.planet_conjunct_natal("Mars", natal_moon_lord_lon, orb=5.0):
        fired.append(("mars_conjunct_moon_lord", 30,
                      [f"Transit Mars conjunct natal {chart.moon_lord} (Moon lord) — home comfort action"]))

    return fired


# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR (Property Purchase)
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate fast trigger rules for exact property purchase timing.
    3 rules: SBC house entry, Lagna-4th lord conjunction, Mars exact on Lagna/Moon lord.
    """
    fired = []

    # Rule 1: SBC benefic house entry on Janma Nakshatra (priority 92)
    # Approximate: Check if benefic transits are on or near Janma Nakshatra
    birth_moon_nak_idx = int((chart.moon_lon % 360) / 13.3333333333) % 27
    for benefic in ["Jupiter", "Venus", "Mercury"]:
        ben_lon = transit.positions[benefic]
        ben_nak_idx = int((ben_lon % 360) / 13.3333333333) % 27
        if ben_nak_idx == birth_moon_nak_idx:
            fired.append(("sbc_benefic_janma_nakshatra", 30,
                          [f"{benefic} on Janma Nakshatra (SBC activation) — property culmination trigger"]))
            break


    # Rule 2: Lagna lord + 4th lord conjunction exact within 3° (priority 90)
    lagna_lord_transit_lon = transit.positions.get(chart.lagna_lord, 0)
    fourth_lord_transit_lon = transit.positions.get(chart.fourth_lord, 0)
    conj_diff = abs((lagna_lord_transit_lon - fourth_lord_transit_lon) % 360)
    conj_diff = min(conj_diff, 360 - conj_diff)
    if conj_diff <= 3.0 and chart.lagna_lord != chart.fourth_lord:
        fired.append(("lagna_4th_lord_conjunction", 28,
                      [f"Transit {chart.lagna_lord} (Lagna lord) conjunct {chart.fourth_lord} (4th lord) within {conj_diff:.1f}° — property deal moment"]))

    # Rule 3: Mars conjunct Lagna/Moon lord exact within 2° (priority 88)
    mars_lon = transit.positions["Mars"]
    natal_lagna_lord_lon = chart.birth_positions[chart.lagna_lord]
    natal_moon_lord_lon = chart.birth_positions[chart.moon_lord]

    mars_lagna_diff = abs((mars_lon - natal_lagna_lord_lon) % 360)
    mars_lagna_diff = min(mars_lagna_diff, 360 - mars_lagna_diff)
    if mars_lagna_diff <= 2.0:
        fired.append(("mars_exact_lagna_lord", 26,
                      [f"Transit Mars exact on natal {chart.lagna_lord} (Lagna lord) within {mars_lagna_diff:.1f}° — land action day"]))

    mars_moon_diff = abs((mars_lon - natal_moon_lord_lon) % 360)
    mars_moon_diff = min(mars_moon_diff, 360 - mars_moon_diff)
    if mars_moon_diff <= 2.0 and chart.moon_lord != chart.lagna_lord:
        fired.append(("mars_exact_moon_lord", 24,
                      [f"Transit Mars exact on natal {chart.moon_lord} (Moon lord) within {mars_moon_diff:.1f}° — home action day"]))

    return fired




# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR (Property Purchase)
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """
    Evaluate classical property purchase patterns (structural — not time-dependent).
    7 rules: 4th house benefics, 10th-4th kendra, Karakamsa patterns (3),
    5th lord dignity, 9th-4th connection.
    """
    results = {
        "timing_modifier": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    fourth_house_occ = chart.fourth_house_occupants
    fourth_lord_house = chart.planets.get(chart.fourth_lord, {}).get("house", 0)
    tenth_lord_house = chart.planets.get(chart.tenth_lord, {}).get("house", 0)
    fifth_lord_house = chart.planets.get(chart.fifth_lord, {}).get("house", 0)
    ninth_lord_house = chart.planets.get(chart.ninth_lord, {}).get("house", 0)
    fourth_aspectors = chart._get_aspectors_of_house(4)

    # Pattern 1: 4th house with benefics — residential comforts (priority 90)
    benefics_in_4th = [p for p in fourth_house_occ if p in NATURAL_BENEFICS]
    benefic_aspectors_4th = [p for p in fourth_aspectors if p in NATURAL_BENEFICS]
    if benefics_in_4th or benefic_aspectors_4th:
        results["confidence_boost"] += 18
        all_benefics = list(set(benefics_in_4th + benefic_aspectors_4th))
        results["fired_patterns"].append(
            f"4th house benefics ({', '.join(all_benefics)}) — residential comforts from birth")

    # Pattern 2: 10th lord + 4th lord in kendras — mansions (priority 88)
    kendras = {1, 4, 7, 10}
    if fourth_lord_house in kendras and tenth_lord_house in kendras:
        results["confidence_boost"] += 16
        results["fired_patterns"].append(
            f"10th lord (h{tenth_lord_house}) + 4th lord (h{fourth_lord_house}) in kendras — mansions/large properties")


    # Pattern 3: Karakamsa — benefic in 4th from Karakamsa = palatial (priority 86)
    # Approximate Karakamsa: find Atmakaraka (planet with highest degree in sign)
    atmakaraka = None
    max_degree = -1
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        degree_in_sign = chart.birth_positions[planet] % 30
        if degree_in_sign > max_degree:
            max_degree = degree_in_sign
            atmakaraka = planet
    if atmakaraka:
        ak_sign = chart.planets[atmakaraka]["sign"]
        fourth_from_karakamsa = ((ak_sign + 3 - 1) % 12) + 1
        for planet_name, pdata in chart.planets.items():
            if pdata["sign"] == fourth_from_karakamsa:
                if planet_name in ["Jupiter", "Venus"]:
                    results["confidence_boost"] += 14
                    results["fired_patterns"].append(
                        f"Karakamsa: {planet_name} in 4th from AK ({atmakaraka}) — palatial residence destiny")
                elif planet_name == "Saturn":
                    results["confidence_boost"] += 10
                    results["fired_patterns"].append(
                        f"Karakamsa: Saturn in 4th from AK ({atmakaraka}) — stone/cement durable house")
                elif planet_name == "Mars":
                    results["confidence_boost"] += 8
                    results["fired_patterns"].append(
                        f"Karakamsa: Mars in 4th from AK ({atmakaraka}) — brick/independent house")

    # Pattern 4: 5th lord dignified + connected to 4th (priority 84)
    fifth_lord_sign = chart.planets.get(chart.fifth_lord, {}).get("sign", 0)
    fifth_lord_own = (chart.fifth_lord == SIGN_LORDS.get(fifth_lord_sign, ""))
    fifth_lord_connected = (fifth_lord_house == 4 or
                            chart.planets.get(chart.fifth_lord, {}).get("sign", 0) ==
                            chart.planets.get(chart.fourth_lord, {}).get("sign", 0))
    if fifth_lord_own and fifth_lord_connected:
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            f"5th lord ({chart.fifth_lord}) dignified + connected to 4th — lands through intelligence")
    elif fifth_lord_house == 4:
        results["confidence_boost"] += 8
        results["fired_patterns"].append(
            f"5th lord ({chart.fifth_lord}) in 4th house — property through past merit")


    # Pattern 5: 9th lord + 4th lord connection — wealth from fortune (priority 88)
    ninth_lord_sign = chart.planets.get(chart.ninth_lord, {}).get("sign", 0)
    fourth_lord_sign_val = chart.planets.get(chart.fourth_lord, {}).get("sign", 0)
    # Check conjunction (same sign) or mutual aspect
    ninth_fourth_conjunct = (ninth_lord_sign == fourth_lord_sign_val and
                            chart.ninth_lord != chart.fourth_lord)
    ninth_in_4th = (ninth_lord_house == 4)
    fourth_in_9th = (fourth_lord_house == 9)
    if ninth_fourth_conjunct or ninth_in_4th or fourth_in_9th:
        results["confidence_boost"] += 16
        if ninth_fourth_conjunct:
            results["fired_patterns"].append(
                f"9th lord ({chart.ninth_lord}) conjunct 4th lord ({chart.fourth_lord}) — fortune-property Rajayoga")
        elif ninth_in_4th:
            results["fired_patterns"].append(
                f"9th lord ({chart.ninth_lord}) in 4th house — fortune flows to property")
        elif fourth_in_9th:
            results["fired_patterns"].append(
                f"4th lord ({chart.fourth_lord}) in 9th house — property through fortune/dharma")

    return results




# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR (Property Purchase)
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """
    Evaluate outcome/quality rules for property purchase classification.
    8 rules: Saturn drishti unstable, Mars 4th conflict, 4th lord benefic comforts,
    11th from 6th mortgage, 5th from 4th value, malefic 4th destruction,
    Saturn-Mars neecha bhanga, exalted Jupiter real estate.
    Mode: house_purchase, land_acquisition, construction, luxury_property, investment
    Quality: stable, unstable, profitable, debt_heavy, disputed
    """
    fired_rules = []

    fourth_lord_house = chart.planets.get(chart.fourth_lord, {}).get("house", 0)
    sixth_lord_house = chart.planets.get(chart.sixth_lord, {}).get("house", 0)
    mars_house = chart.planets.get("Mars", {}).get("house", 0)
    saturn_house = chart.planets.get("Saturn", {}).get("house", 0)
    jupiter_house = chart.planets.get("Jupiter", {}).get("house", 0)
    jupiter_sign = chart.planets.get("Jupiter", {}).get("sign", 0)
    fourth_aspectors = chart._get_aspectors_of_house(4)
    fourth_house_occ = chart.fourth_house_occupants

    # Rule 1: Saturn drishti on 4th — unstable property (priority 85)
    if "Saturn" in fourth_aspectors or saturn_house == 4:
        fired_rules.append(("saturn_drishti_4th_unstable", "quality_unstable", 0.82,
            "Saturn drishti/occupancy on 4th — unstable property, delays, structural issues"))

    # Rule 2: Mars in 4th — conflict over property (priority 84)
    if mars_house == 4:
        fired_rules.append(("mars_4th_conflict", "quality_disputed", 0.80,
            "Mars in 4th house — conflict, disputes, boundary issues over property"))


    # Rule 3: 4th lord with benefics — comfortable acquisition (priority 88)
    fourth_lord_sign = chart.planets.get(chart.fourth_lord, {}).get("sign", 0)
    benefics_with_4th_lord = []
    for p_name, p_data in chart.planets.items():
        if p_name != chart.fourth_lord and p_data["sign"] == fourth_lord_sign and p_name in NATURAL_BENEFICS:
            benefics_with_4th_lord.append(p_name)
    benefic_aspects_4th_lord = [p for p in fourth_aspectors if p in NATURAL_BENEFICS]
    if benefics_with_4th_lord or benefic_aspects_4th_lord:
        fired_rules.append(("4th_lord_benefic_comforts", "quality_stable", 0.88,
            f"4th lord with benefics ({', '.join(benefics_with_4th_lord + benefic_aspects_4th_lord)}) — comfortable, smooth acquisition"))

    # Rule 4: 11th from 6th (= 4th house) mortgage (priority 82)
    # 6th lord connected to 4th = mortgage/loan property
    if sixth_lord_house == 4 or chart.planets.get(chart.sixth_lord, {}).get("sign", 0) == fourth_lord_sign:
        fired_rules.append(("11th_from_6th_mortgage", "quality_debt_heavy", 0.80,
            f"6th lord ({chart.sixth_lord}) connected to 4th — mortgage/loan funded property"))

    # Rule 5: 5th from 4th (= 8th house) value appreciation (priority 83)
    eighth_house_occ = [n for n, d in chart.planets.items() if d["house"] == 8]
    benefics_in_8th = [p for p in eighth_house_occ if p in NATURAL_BENEFICS]
    if benefics_in_8th:
        fired_rules.append(("5th_from_4th_value", "quality_profitable", 0.82,
            f"Benefics in 8th ({', '.join(benefics_in_8th)}) — property value appreciation"))

    # Rule 6: Malefic in 4th — destruction/renovation (priority 80)
    malefics_in_4th = [p for p in fourth_house_occ if p in NATURAL_MALEFICS]
    benefics_in_4th = [p for p in fourth_house_occ if p in NATURAL_BENEFICS]
    if malefics_in_4th and not benefics_in_4th:
        fired_rules.append(("malefic_4th_destruction", "quality_unstable", 0.78,
            f"Malefics in 4th ({', '.join(malefics_in_4th)}) unaspected by benefics — renovation/structural issues"))


    # Rule 7: Saturn-Mars neecha bhanga — unexpected property through hardship (priority 82)
    saturn_sign = chart.planets.get("Saturn", {}).get("sign", 0)
    mars_sign = chart.planets.get("Mars", {}).get("sign", 0)
    # Saturn debilitated in Aries (1), Mars debilitated in Cancer (4)
    saturn_neecha_bhanga = (saturn_sign == 1 and mars_house in {1, 4, 7, 10})
    mars_neecha_bhanga = (mars_sign == 4 and jupiter_house in {1, 4, 7, 10})
    if saturn_neecha_bhanga or mars_neecha_bhanga:
        fired_rules.append(("saturn_mars_neecha_bhanga", "quality_unstable", 0.80,
            "Saturn/Mars neecha bhanga — unexpected property through hardship and persistence"))

    # Rule 8: Exalted Jupiter aspecting 4th — premium real estate (priority 90)
    # Jupiter exalted in Cancer (sign 4)
    if jupiter_sign == 4 and ("Jupiter" in fourth_aspectors or jupiter_house == 4):
        fired_rules.append(("exalted_jupiter_real_estate", "quality_profitable", 0.92,
            "Exalted Jupiter aspecting/in 4th — premium real estate, prime location"))

    # ═══════════════════════════════════════════════════════════
    # RESOLUTION
    # ═══════════════════════════════════════════════════════════
    cal = CALIBRATION.get("outcome_calibration", {})
    default_mode = cal.get("default_mode", "house_purchase")

    # Resolve MODE based on chart indicators
    resolved_mode = default_mode
    if mars_house in [4, 2, 11] or chart.fourth_lord == "Mars":
        resolved_mode = "land_acquisition"
    if saturn_house == 4 or (chart.fourth_lord == "Saturn"):
        resolved_mode = "construction"
    if "Venus" in fourth_house_occ or chart.fourth_lord == "Venus":
        resolved_mode = "luxury_property"
    if jupiter_house in [4, 11] and saturn_house in [10, 11]:
        resolved_mode = "investment"

    # Resolve QUALITY
    quality_rules = [r for r in fired_rules if r[1].startswith("quality_")]
    resolved_quality = "stable"
    if quality_rules:
        quality_rules.sort(key=lambda r: -r[2])
        quality_map = {
            "quality_stable": "stable",
            "quality_unstable": "unstable",
            "quality_profitable": "profitable",
            "quality_debt_heavy": "debt_heavy",
            "quality_disputed": "disputed",
        }
        resolved_quality = quality_map.get(quality_rules[0][1], "stable")

    return {
        "mode": resolved_mode,
        "quality": resolved_quality,
        "fired_outcomes": [f"{r[0]}: {r[3]}" for r in fired_rules],
        "_classical_rules_fired": fired_rules,
        "_resolution_method": "calibration_priority_order",
        "_calibration_version": CALIBRATION.get("calibration_version", "unknown"),
    }




# ═══════════════════════════════════════════════════════════════
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE (Property Purchase)
# ═══════════════════════════════════════════════════════════════

class PropertyPurchaseWindowResult:
    """Result of evaluating a single property purchase time window."""

    def __init__(self):
        self.period_start = None
        self.period_end = None
        self.md_lord = ""
        self.ad_lord = ""
        self.age_start = 0.0
        self.age_end = 0.0

        # Layer results
        self.dasha_fired = []
        self.transit_fired = []
        self.fast_trigger_fired = []
        self.classical = {}
        self.outcome = {}

        # Composite
        self.total_score = 0
        self.timing_band = "broad"
        self.likelihood = "low"

    def compute_composite_score(self):
        """Compute total score from all layers using calibration weights."""
        dasha_score = sum(s for _, s, _ in self.dasha_fired)
        transit_score = sum(s for _, s, _ in self.transit_fired)
        fast_score = sum(s for _, s, _ in self.fast_trigger_fired)
        classical_boost = self.classical.get("confidence_boost", 0)

        lw = CALIBRATION["layer_weights"]
        self.total_score = (
            dasha_score * lw["dasha_weight"] +
            transit_score * lw["transit_weight"] +
            fast_score * lw["fast_trigger_weight"] +
            classical_boost * lw["classical_weight"]
        )

        if fast_score > 20:
            self.timing_band = "exact"
        elif transit_score > 25:
            self.timing_band = "narrow"
        elif dasha_score > 20:
            self.timing_band = "broad"

        lt = CALIBRATION["likelihood_thresholds"]
        if self.total_score >= lt["very_high"]:
            self.likelihood = "VERY_HIGH"
        elif self.total_score >= lt["high"]:
            self.likelihood = "HIGH"
        elif self.total_score >= lt["moderate"]:
            self.likelihood = "MODERATE"
        elif self.total_score >= lt["low"]:
            self.likelihood = "LOW"
        else:
            self.likelihood = "VERY_LOW"




def scan_property_purchase_windows(chart: ChartState, start_age=22, end_age=60, step_months=6):
    """
    Scan through life from start_age to end_age in step_months increments.
    Property purchase events typically happen from age 22-60.
    For each AD period in that range, evaluate the 5-layer engine.
    Returns sorted list of PropertyPurchaseWindowResult.
    """
    results = []

    # Generate MD periods for the relevant age range
    md_periods = _generate_md_periods(chart.birth_dt, chart.moon_lon, years=80)

    # Classical patterns (structural, computed once)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    for md in md_periods:
        md_age_start = (md["start"] - chart.birth_dt).days / 365.25
        md_age_end = (md["end"] - chart.birth_dt).days / 365.25

        if md_age_end < start_age or md_age_start > end_age:
            continue

        ad_periods = _generate_ad_periods(md)

        for ad in ad_periods:
            ad_age_start = (ad["start"] - chart.birth_dt).days / 365.25
            ad_age_end = (ad["end"] - chart.birth_dt).days / 365.25

            if ad_age_end < start_age or ad_age_start > end_age:
                continue

            effective_start = max(ad["start"], chart.birth_dt + timedelta(days=start_age * 365.25))
            effective_end = min(ad["end"], chart.birth_dt + timedelta(days=end_age * 365.25))

            # LAYER 1: DASHA
            dasha_results = evaluate_dasha_layer(chart, md["lord"], ad["lord"])
            if not dasha_results:
                continue

            # LAYER 2: TRANSIT (evaluate at midpoint)
            mid_date = effective_start + (effective_end - effective_start) / 2
            transit = TransitState(mid_date, chart)
            transit_results = evaluate_transit_layer(chart, transit)

            # LAYER 3: FAST TRIGGER
            fast_trigger_results = evaluate_fast_trigger_layer(chart, transit)


            # Also check at start and end for better coverage
            transit_start = TransitState(effective_start, chart)
            transit_end = TransitState(effective_end, chart)

            transit_results_start = evaluate_transit_layer(chart, transit_start)
            transit_results_end = evaluate_transit_layer(chart, transit_end)

            # Merge transit results (best score per rule)
            all_transit = {}
            for tr_list in [transit_results, transit_results_start, transit_results_end]:
                for rule_id, score, reasons in tr_list:
                    if rule_id not in all_transit or score > all_transit[rule_id][1]:
                        all_transit[rule_id] = (rule_id, score, reasons)
            merged_transit = list(all_transit.values())

            all_fast = {}
            ft_start = evaluate_fast_trigger_layer(chart, transit_start)
            ft_end = evaluate_fast_trigger_layer(chart, transit_end)
            for ft_list in [fast_trigger_results, ft_start, ft_end]:
                for rule_id, score, reasons in ft_list:
                    if rule_id not in all_fast or score > all_fast[rule_id][1]:
                        all_fast[rule_id] = (rule_id, score, reasons)
            merged_fast = list(all_fast.values())

            # Build result
            result = PropertyPurchaseWindowResult()
            result.period_start = effective_start
            result.period_end = effective_end
            result.md_lord = md["lord"]
            result.ad_lord = ad["lord"]
            result.age_start = max(ad_age_start, start_age)
            result.age_end = min(ad_age_end, end_age)
            result.dasha_fired = dasha_results
            result.transit_fired = merged_transit
            result.fast_trigger_fired = merged_fast
            result.classical = classical
            result.outcome = outcome
            result.compute_composite_score()

            results.append(result)

    results.sort(key=lambda r: r.total_score, reverse=True)
    return results




# ═══════════════════════════════════════════════════════════════
# MAIN — RUN FOR 22 JULY 1975 18:15 BHILAI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    BIRTH_DATE = datetime(1975, 7, 22, 18, 15)
    BHILAI_LAT = 21.2094
    BHILAI_LON = 81.4285
    BHILAI_ALT = 297

    print("=" * 80)
    print("  5-LAYER PROPERTY PURCHASE RULE ENGINE — VEDIC TEXT BASED")
    print("  Domain: Property Purchase & House Acquisition")
    print("  Native: 22 July 1975, 18:15 IST, Bhilai")
    print("=" * 80)

    # Build chart state
    chart = ChartState(BIRTH_DATE, BHILAI_LAT, BHILAI_LON, BHILAI_ALT)

    print(f"\n{'─' * 80}")
    print("  NATAL CHART SUMMARY (Property Purchase Focus)")
    print(f"{'─' * 80}")
    print(f"  Lagna: {SIGN_NAMES[chart.asc_sign]} | Lagna Lord: {chart.lagna_lord}")
    print(f"  Moon: {SIGN_NAMES[chart.moon_sign]} ({chart.moon_nakshatra})")
    print(f"  Moon Lord: {chart.moon_lord}")
    print(f"  4th Lord: {chart.fourth_lord} (house {chart.planets[chart.fourth_lord]['house']})")
    print(f"  9th Lord: {chart.ninth_lord} (house {chart.planets[chart.ninth_lord]['house']})")
    print(f"  10th Lord: {chart.tenth_lord} (house {chart.planets[chart.tenth_lord]['house']})")
    print(f"  5th Lord: {chart.fifth_lord} (house {chart.planets[chart.fifth_lord]['house']})")
    print(f"  Mars (Bhumi Karaka): house {chart.planets['Mars']['house']}, {SIGN_NAMES[chart.planets['Mars']['sign']]}")
    print(f"  Jupiter: house {chart.planets['Jupiter']['house']}, {SIGN_NAMES[chart.planets['Jupiter']['sign']]}")
    print(f"  Saturn: house {chart.planets['Saturn']['house']}, {SIGN_NAMES[chart.planets['Saturn']['sign']]}")
    print(f"  Venus: house {chart.planets['Venus']['house']}, {SIGN_NAMES[chart.planets['Venus']['sign']]}")
    print(f"  Moon: house {chart.planets['Moon']['house']}, {SIGN_NAMES[chart.planets['Moon']['sign']]}")
    print(f"  Sensitive Point 1 (4L+Mars): {chart.sensitive_point_1:.2f}°")
    print(f"  Sensitive Point 2 (Moon+4L): {chart.sensitive_point_2:.2f}°")


    # Layer 4 & 5 (structural)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    print(f"\n{'─' * 80}")
    print("  LAYER 4: CLASSICAL PATTERNS (Structural — Property Purchase)")
    print(f"{'─' * 80}")
    print(f"  Timing Modifier: {classical['timing_modifier'].upper()}")
    print(f"  Confidence Boost: {classical['confidence_boost']:+d}")
    for p in classical["fired_patterns"]:
        print(f"    * {p}")
    if not classical["fired_patterns"]:
        print("    (No classical property purchase patterns detected)")

    print(f"\n{'─' * 80}")
    print("  LAYER 5: OUTCOME / QUALITY (Property Purchase Classification)")
    print(f"{'─' * 80}")
    print(f"  Property Mode: {outcome['mode']}")
    print(f"  Quality: {outcome['quality']}")
    for o in outcome["fired_outcomes"]:
        print(f"    * {o}")

    # Scan property purchase windows
    print(f"\n{'─' * 80}")
    print("  SCANNING PROPERTY PURCHASE WINDOWS (Age 22-60, step=6mo)...")
    print(f"{'─' * 80}")

    windows = scan_property_purchase_windows(chart, start_age=22, end_age=60, step_months=6)

    print(f"\n  Found {len(windows)} windows where dasha rules fired.")
    print(f"  Showing top 10 ranked by composite 5-layer score:\n")

    print(f"  {'#':<3} {'Period':<28} {'Age':<10} {'Score':<7} {'Band':<8} {'Likelihood':<12} {'MD-AD':<18}")
    print(f"  {'---':<3} {'---':<28} {'---':<10} {'---':<7} {'---':<8} {'---':<12} {'---':<18}")

    for i, w in enumerate(windows[:10], 1):
        period = f"{w.period_start.strftime('%b %Y')} - {w.period_end.strftime('%b %Y')}"
        age = f"{w.age_start:.1f}-{w.age_end:.1f}"
        md_ad = f"{w.md_lord}-{w.ad_lord}"
        print(f"  {i:<3} {period:<28} {age:<10} {w.total_score:<7.1f} {w.timing_band:<8} {w.likelihood:<12} {md_ad:<18}")


    # Detailed top 5
    print(f"\n{'=' * 80}")
    print("  TOP 5 PROPERTY PURCHASE WINDOWS — DETAILED 5-LAYER BREAKDOWN")
    print(f"{'=' * 80}")

    for i, w in enumerate(windows[:5], 1):
        print(f"\n  +{'─' * 76}+")
        print(f"  | #{i} | {w.period_start.strftime('%B %Y')} - {w.period_end.strftime('%B %Y')}")
        print(f"  | Age: {w.age_start:.1f} - {w.age_end:.1f} | MD: {w.md_lord} | AD: {w.ad_lord}")
        print(f"  | COMPOSITE SCORE: {w.total_score:.1f} | Likelihood: {w.likelihood} | Band: {w.timing_band}")
        print(f"  +{'─' * 76}+")

        print(f"  | LAYER 1 — DASHA (Gate):")
        for rule_id, score, reasons in w.dasha_fired:
            for r in reasons:
                print(f"  |   [{score:>3}] {r}")

        print(f"  | LAYER 2 — TRANSIT (Activation):")
        if w.transit_fired:
            for rule_id, score, reasons in w.transit_fired:
                for r in reasons:
                    print(f"  |   [{score:>3}] {r}")
        else:
            print(f"  |   (No transit activation at sample points)")

        print(f"  | LAYER 3 — FAST TRIGGER (Exact):")
        if w.fast_trigger_fired:
            for rule_id, score, reasons in w.fast_trigger_fired:
                for r in reasons:
                    print(f"  |   [{score:>3}] {r}")
        else:
            print(f"  |   (No fast trigger at sample points)")

        print(f"  +{'─' * 76}+")

    print(f"\n{'=' * 80}")
    print("  CONCLUSION")
    print(f"{'=' * 80}")
    if windows:
        top = windows[0]
        print(f"\n  STRONGEST PROPERTY PURCHASE WINDOW:")
        print(f"  {top.period_start.strftime('%B %Y')} - {top.period_end.strftime('%B %Y')}")
        print(f"  Age {top.age_start:.1f}-{top.age_end:.1f} | {top.md_lord}-{top.ad_lord}")
        print(f"  Score: {top.total_score:.1f} | {top.likelihood}")
        print(f"\n  Property Mode: {outcome['mode']}")
        print(f"  Quality: {outcome['quality']}")
        print(f"\n  The 5-layer engine evaluated {len(windows)} AD periods with")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['high'])} HIGH+ confidence windows.")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['very_high'])} VERY_HIGH confidence windows.")
    print(f"\n{'=' * 80}")
