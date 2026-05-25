"""
Property Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow.
Domain: Ancestral Property & Inheritance
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
RULES_DIR = Path(__file__).resolve().parent / "domains" / "finance" / "ancestral_property_and_inheritance"

# Property-specific constants
# Mars=land, Saturn=structures, Jupiter=expansion, Moon=home/comfort, Venus=luxury assets
PROPERTY_KARAKAS = {"Mars", "Saturn", "Jupiter", "Moon", "Venus"}
# 2=family wealth, 4=property, 8=inheritance, 9=father/fortune, 11=gains, 12=paternal property
PROPERTY_HOUSES = {2, 4, 8, 9, 11, 12}



# ═══════════════════════════════════════════════════════════════
# CALIBRATION OVERLAY LOADER (Layer 3)
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
                "fast_trigger_weight": 0.15,
                "classical_weight": 0.20,
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
                    "ninth_lord_md_or_ad": 42,
                    "eighth_lord_md_or_ad": 40,
                    "second_lord_md_or_ad": 35,
                    "twelfth_lord_md_or_ad": 30,
                    "property_karaka_md_or_ad": 38,
                },
                "transit": {
                    "jupiter_4th_from_moon": 50,
                    "jupiter_9th_from_moon": 45,
                    "jupiter_8th_from_moon": 42,
                    "jupiter_conjunct_natal_sun": 48,
                    "saturn_conjunct_natal_mars": -35,
                    "saturn_9th_from_moon": 30,
                },
                "fast_trigger": {
                    "jati_tara_26th": 30,
                    "moon_right_hand_25_27": 28,
                    "moon_two_eyes_9_10": 22,
                    "mars_head_16_17": 26,
                },
            },
            "outcome_calibration": {
                "mode_priority_order": [
                    "smooth_inheritance",
                    "disputed_property",
                    "sudden_gain",
                    "karmic_pattern",
                    "inherited_debt",
                ],
                "quality_priority_order": ["supportive", "mixed", "challenging"],
                "asset_type_priority_order": ["land", "liquid_wealth", "luxury_assets", "inaccessible"],
                "default_mode": "smooth_inheritance",
            },
        }


# Module-level calibration (loaded once at import)
CALIBRATION = _load_calibration()



def ist_to_utc(dt):
    return dt - IST_OFFSET


def get_jd(dt_ist):
    dt_utc = ist_to_utc(dt_ist)
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute / 60.0)


# ═══════════════════════════════════════════════════════════════
# CHART STATE BUILDER
# ═══════════════════════════════════════════════════════════════

class ChartState(BaseChartState):
    """Encapsulates all natal chart data needed for property rule evaluation."""

    def __init__(self, birth_dt, lat, lon, alt=0):
        super().__init__(birth_dt, lat, lon, alt)


        # Key house lords (property-focused)
        self.lagna_lord = SIGN_LORDS[self.asc_sign]
        self.first_sign = self.asc_sign
        self.first_lord = SIGN_LORDS[self.first_sign]
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

        # Planets in property houses
        self.fourth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 4
        ]
        self.eighth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 8
        ]

        # Sensitive Property Points
        # Point 1: 4th lord + 9th lord longitude sum (property-fortune axis)
        fourth_lord_lon = self.birth_positions[self.fourth_lord]
        ninth_lord_lon = self.birth_positions[self.ninth_lord]
        self.sensitive_point_1 = (fourth_lord_lon + ninth_lord_lon) % 360

        # Point 2: Mars + 8th lord longitude sum (land-inheritance axis)
        mars_lon = self.birth_positions["Mars"]
        eighth_lord_lon = self.birth_positions[self.eighth_lord]
        self.sensitive_point_2 = (mars_lon + eighth_lord_lon) % 360
# ═══════════════════════════════════════════════════════════════
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
# LAYER 1: DASHA EVALUATOR (Property)
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate dasha rules for property/inheritance.
    Key lords: 4th lord (property), 8th lord (inheritance), 9th lord (father/fortune),
    2nd lord (family wealth), 12th lord (paternal property).
    Positive combos: Rahu-Jupiter land, Saturn-Venus luxury, Mars-Sun authority.
    Negative: 8th lord disputes, Jupiter past exaltation = ancestral loss.
    """
    fired = []

    # Key lords for property events
    key_lords = {
        chart.fourth_lord: ("4th lord", "property/land/home", 45),
        chart.ninth_lord: ("9th lord", "father/fortune/paternal legacy", 42),
        chart.eighth_lord: ("8th lord", "inheritance/hidden wealth", 40),
        chart.second_lord: ("2nd lord", "family wealth/accumulation", 35),
        chart.twelfth_lord: ("12th lord", "paternal property/distant", 30),
    }

    # Rule 1: Property house lords in MD/AD (priority 98)
    r1_score = 0
    r1_reasons = []
    for lord, (label, domain, base_score) in key_lords.items():
        if md_lord == lord:
            r1_score += base_score
            r1_reasons.append(f"MD of {label} ({lord}) — {domain}")
        if ad_lord == lord:
            r1_score += int(base_score * 0.8)
            r1_reasons.append(f"AD of {label} ({lord}) — {domain}")
    if r1_score > 0:
        fired.append(("property_house_lord_dasha", r1_score, r1_reasons))

    # Rule 2: Property karaka planets in MD/AD (priority 95)
    r2_score = 0
    r2_reasons = []
    karaka_scores = {
        "Mars": (42, "land/real estate/physical property"),
        "Saturn": (38, "structures/old buildings/ancestral"),
        "Jupiter": (40, "expansion/wealth growth/blessings"),
        "Moon": (35, "home/comfort/emotional security"),
        "Venus": (36, "luxury assets/vehicles/beautiful homes"),
    }
    if md_lord in PROPERTY_KARAKAS:
        score, desc = karaka_scores[md_lord]
        r2_score += score
        r2_reasons.append(f"MD of property karaka {md_lord} ({desc})")
    if ad_lord in PROPERTY_KARAKAS:
        score, desc = karaka_scores[ad_lord]
        r2_score += int(score * 0.75)
        r2_reasons.append(f"AD of property karaka {ad_lord} ({desc})")
    if r2_score > 0:
        fired.append(("property_karaka_dasha", r2_score, r2_reasons))


    # Rule 3: Positive property dasha combinations (priority 92)
    r3_score = 0
    r3_reasons = []

    # Rahu-Jupiter land acquisition
    if md_lord == "Rahu" and ad_lord == "Jupiter":
        r3_score += 45
        r3_reasons.append("Rahu-Jupiter dasha — expansive land acquisition, unexpected property gains")
    if md_lord == "Jupiter" and ad_lord == "Rahu":
        r3_score += 38
        r3_reasons.append("Jupiter-Rahu dasha — wealth expansion through unconventional property")

    # Saturn-Venus luxury property
    if (md_lord == "Saturn" and ad_lord == "Venus") or (md_lord == "Venus" and ad_lord == "Saturn"):
        r3_score += 40
        r3_reasons.append("Saturn-Venus dasha — luxury property acquisition, ancestral renovation")

    # Mars-Sun land through authority
    if (md_lord == "Mars" and ad_lord == "Sun") or (md_lord == "Sun" and ad_lord == "Mars"):
        r3_score += 38
        r3_reasons.append("Mars-Sun dasha — land through authority, government property, father's estate")

    # 4th lord + 9th lord combo
    if md_lord == chart.fourth_lord and ad_lord == chart.ninth_lord:
        r3_score += 48
        r3_reasons.append(f"4th lord ({chart.fourth_lord}) MD + 9th lord ({chart.ninth_lord}) AD — property-fortune fusion")
    elif md_lord == chart.ninth_lord and ad_lord == chart.fourth_lord:
        r3_score += 45
        r3_reasons.append(f"9th lord ({chart.ninth_lord}) MD + 4th lord ({chart.fourth_lord}) AD — fortune-property fusion")

    if r3_score > 0:
        fired.append(("property_positive_dasha", r3_score, r3_reasons))

    # Rule 4: Negative — 8th lord disputes (priority 90)
    r4_score = 0
    r4_reasons = []
    eighth_lord_sign = chart.planets.get(chart.eighth_lord, {}).get("sign", 0)
    # 8th lord afflicted = disputes
    eighth_lord_house = chart.planets.get(chart.eighth_lord, {}).get("house", 0)
    if md_lord == chart.eighth_lord or ad_lord == chart.eighth_lord:
        if eighth_lord_house in [6, 8, 12]:
            r4_score += 35
            r4_reasons.append(f"8th lord ({chart.eighth_lord}) in dusthana house {eighth_lord_house} — property disputes/litigation")
        elif eighth_lord_sign in [10]:  # debilitated Jupiter
            r4_score += 30
            r4_reasons.append(f"8th lord ({chart.eighth_lord}) weakened — contested inheritance likely")
    if r4_score > 0:
        fired.append(("property_dispute_dasha", r4_score, r4_reasons))


    # Rule 5: Jupiter past exaltation — ancestral loss (priority 85)
    r5_score = 0
    r5_reasons = []
    jupiter_lon = chart.birth_positions.get("Jupiter", 0)
    jupiter_sign = chart.planets.get("Jupiter", {}).get("sign", 0)
    # Jupiter exaltation = 5 deg Cancer (sign 4). Past exaltation = in Cancer but > 5 deg or debilitated
    if md_lord == "Jupiter" or ad_lord == "Jupiter":
        if jupiter_sign == 10:  # Capricorn = debilitated
            r5_score += 35
            r5_reasons.append("Jupiter debilitated (Capricorn) in dasha — ancestral property loss risk")
        elif jupiter_sign == 4 and (jupiter_lon % 30) > 5:
            r5_score += 25
            r5_reasons.append("Jupiter past exaltation degree in Cancer — declining fortune, property loss risk")
    if r5_score > 0:
        fired.append(("jupiter_ancestral_loss_dasha", r5_score, r5_reasons))

    # Rule 6: MD/AD lord placed in property houses (priority 80)
    r6_score = 0
    r6_reasons = []
    md_house = chart.planets.get(md_lord, {}).get("house", 0)
    ad_house = chart.planets.get(ad_lord, {}).get("house", 0)
    if md_house in PROPERTY_HOUSES:
        r6_score += 20
        r6_reasons.append(f"MD lord {md_lord} placed in property house {md_house}")
    if ad_house in PROPERTY_HOUSES:
        r6_score += 15
        r6_reasons.append(f"AD lord {ad_lord} placed in property house {ad_house}")
    if r6_score > 0:
        fired.append(("property_lord_placement", r6_score, r6_reasons))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR (Property)
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate transit rules for property activation.
    Key: Jupiter transit 4th/9th/8th from Moon, Jupiter conjunct natal Sun,
    Saturn conjunct natal Mars (loss), Saturn 9th from Moon (father/legacy).
    """
    fired = []

    # Rule 1: Jupiter transit 4th from Moon (priority 95)
    jup_house_from_moon = transit.planet_houses_from_moon.get("Jupiter", 0)
    if jup_house_from_moon == 4:
        fired.append(("jupiter_4th_from_moon", 50,
                      ["Transit Jupiter in 4th from Moon — property acquisition window (strongest)"]))

    # Rule 2: Jupiter transit 9th from Moon (priority 92)
    if jup_house_from_moon == 9:
        fired.append(("jupiter_9th_from_moon", 45,
                      ["Transit Jupiter in 9th from Moon — father's property/fortune activation"]))

    # Rule 3: Jupiter transit 8th from Moon (priority 90)
    if jup_house_from_moon == 8:
        fired.append(("jupiter_8th_from_moon", 42,
                      ["Transit Jupiter in 8th from Moon — inheritance activation, hidden wealth surfaces"]))

    # Rule 4: Jupiter conjunct natal Sun — father's wealth (priority 93)
    natal_sun_lon = chart.birth_positions["Sun"]
    if transit.planet_conjunct_natal("Jupiter", natal_sun_lon, orb=5.0):
        fired.append(("jupiter_conjunct_natal_sun", 48,
                      ["Transit Jupiter conjunct natal Sun — father's wealth transfer activation"]))

    # Rule 5: Saturn conjunct natal Mars — property loss (priority 88)
    natal_mars_lon = chart.birth_positions["Mars"]
    if transit.planet_conjunct_natal("Saturn", natal_mars_lon, orb=5.0):
        fired.append(("saturn_conjunct_natal_mars", -35,
                      ["Transit Saturn conjunct natal Mars — property loss/disputes risk"]))

    # Rule 6: Saturn transit 9th from Moon — father/legacy (priority 86)
    sat_house_from_moon = transit.planet_houses_from_moon.get("Saturn", 0)
    if sat_house_from_moon == 9:
        fired.append(("saturn_9th_from_moon", 30,
                      ["Transit Saturn in 9th from Moon — father/legacy matters (karmic duty)"]))

    # Bonus: Jupiter transit 2nd from Moon (family wealth)
    if jup_house_from_moon == 2:
        fired.append(("jupiter_2nd_from_moon", 35,
                      ["Transit Jupiter in 2nd from Moon — family wealth activation"]))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR (Property)
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate fast trigger rules for exact property timing.
    Jati Tara (26th nak), Moon right hand (25-27th), Moon two eyes (9-10th),
    Mars head (16-17th).
    """
    fired = []

    birth_moon_nak_idx = int((chart.moon_lon % 360) / 13.3333333333) % 27

    # Transit Moon nakshatra position relative to birth
    transit_moon_lon = transit.positions["Moon"]
    transit_moon_nak_idx = int((transit_moon_lon % 360) / 13.3333333333) % 27
    moon_nak_offset = ((transit_moon_nak_idx - birth_moon_nak_idx) % 27) + 1

    # Transit Mars nakshatra position relative to birth
    transit_mars_lon = transit.positions["Mars"]
    transit_mars_nak_idx = int((transit_mars_lon % 360) / 13.3333333333) % 27
    mars_nak_offset = ((transit_mars_nak_idx - birth_moon_nak_idx) % 27) + 1

    # Rule 1: Jati Tara (26th nakshatra) — ancestral property day
    if moon_nak_offset == 26:
        fired.append(("jati_tara_26th_moon", 30,
                      ["Moon on Jati Tara (26th nak) — ancestral property culmination day"]))
    if mars_nak_offset == 26:
        fired.append(("jati_tara_26th_mars", 28,
                      ["Mars on Jati Tara (26th nak) — land/property action day (ancestral)"]))

    # Rule 2: Moon right hand (25-27th nakshatra) — property transfer moment
    if moon_nak_offset in [25, 26, 27]:
        fired.append(("moon_right_hand_25_27", 28,
                      [f"Moon in right hand zone ({moon_nak_offset}th nak) — property transfer moment"]))

    # Rule 3: Moon two eyes (9-10th nakshatra) — asset visibility
    if moon_nak_offset in [9, 10]:
        fired.append(("moon_two_eyes_9_10", 22,
                      [f"Moon in Netra zone ({moon_nak_offset}th nak) — hidden assets become visible"]))

    # Rule 4: Mars head (16-17th nakshatra) — land action day
    if mars_nak_offset in [16, 17]:
        fired.append(("mars_head_16_17", 26,
                      [f"Mars in Shiras zone ({mars_nak_offset}th nak) — decisive land action day"]))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR (Property)
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """
    Evaluate classical property patterns (structural — not time-dependent).
    Checks: Benefic in 8th, hostile drishti on 8th, strong 4th house,
    strong 2nd house, 12th house paternal, 3rd house windfalls,
    Mars-4th lord, Jupiter aspects 4th/8th, Saturn in 4th.
    """
    results = {
        "timing_modifier": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    # Get house occupants
    fourth_house_occ = chart.fourth_house_occupants
    eighth_house_occ = chart.eighth_house_occupants
    fourth_lord_house = chart.planets.get(chart.fourth_lord, {}).get("house", 0)
    eighth_lord_house = chart.planets.get(chart.eighth_lord, {}).get("house", 0)
    second_lord_house = chart.planets.get(chart.second_lord, {}).get("house", 0)
    ninth_lord_house = chart.planets.get(chart.ninth_lord, {}).get("house", 0)
    twelfth_lord_house = chart.planets.get(chart.twelfth_lord, {}).get("house", 0)
    third_lord_house = chart.planets.get(chart.third_lord, {}).get("house", 0)

    # Pattern 1: Benefic in 8th — smooth inheritance
    benefics_in_8th = [p for p in eighth_house_occ if p in NATURAL_BENEFICS]
    if benefics_in_8th:
        results["confidence_boost"] += 18
        results["fired_patterns"].append(
            f"Benefic in 8th ({', '.join(benefics_in_8th)}) — smooth inheritance, hidden wealth surfaces")

    # Pattern 2: 8th hostile drishti — disputes
    malefics_in_8th = [p for p in eighth_house_occ if p in NATURAL_MALEFICS]
    eighth_aspectors = chart._get_aspectors_of_house(8)
    malefic_aspectors_8th = [p for p in eighth_aspectors if p in NATURAL_MALEFICS]
    if malefics_in_8th or len(malefic_aspectors_8th) >= 2:
        results["confidence_boost"] -= 12
        results["timing_modifier"] = "disputed"
        hostile_list = malefics_in_8th + malefic_aspectors_8th
        results["fired_patterns"].append(
            f"8th hostile drishti ({', '.join(set(hostile_list))}) — property disputes/litigation risk")


    # Pattern 3: Strong 4th house — inherited land
    benefics_in_4th = [p for p in fourth_house_occ if p in NATURAL_BENEFICS]
    fourth_aspectors = chart._get_aspectors_of_house(4)
    benefic_aspectors_4th = [p for p in fourth_aspectors if p in NATURAL_BENEFICS]
    if fourth_lord_house in [1, 4, 5, 7, 9, 10] and (benefics_in_4th or benefic_aspectors_4th):
        results["confidence_boost"] += 16
        results["fired_patterns"].append(
            f"Strong 4th house (lord in house {fourth_lord_house}, benefics: {', '.join(benefics_in_4th + benefic_aspectors_4th)}) — inherited land")

    # Pattern 4: Strong 2nd house — family money
    second_house_occ = [name for name, data in chart.planets.items() if data["house"] == 2]
    benefics_in_2nd = [p for p in second_house_occ if p in NATURAL_BENEFICS]
    if second_lord_house in [1, 2, 4, 5, 9, 10, 11] and benefics_in_2nd:
        results["confidence_boost"] += 14
        results["fired_patterns"].append(
            f"Strong 2nd house (lord in house {second_lord_house}, benefics: {', '.join(benefics_in_2nd)}) — family money/gold")

    # Pattern 5: 12th house — paternal property
    if twelfth_lord_house in [4, 9, 11]:
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            f"12th lord ({chart.twelfth_lord}) in house {twelfth_lord_house} — paternal property transfer")

    # Pattern 6: 3rd house — sudden windfalls
    if third_lord_house in [2, 4, 8, 11]:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(
            f"3rd lord ({chart.third_lord}) in house {third_lord_house} — sudden windfalls/brother's property")

    # Pattern 7: Mars conjunct 4th lord — land power
    mars_sign = chart.planets.get("Mars", {}).get("sign", 0)
    fourth_lord_sign = chart.planets.get(chart.fourth_lord, {}).get("sign", 0)
    if mars_sign == fourth_lord_sign and chart.fourth_lord != "Mars":
        results["confidence_boost"] += 15
        results["fired_patterns"].append(
            f"Mars conjunct 4th lord ({chart.fourth_lord}) — land power, real estate dominance")

    # Pattern 8: Jupiter aspects 4th and/or 8th
    jup_aspects_4 = "Jupiter" in fourth_aspectors or "Jupiter" in fourth_house_occ
    jup_aspects_8 = "Jupiter" in eighth_aspectors or "Jupiter" in eighth_house_occ
    if jup_aspects_4 and jup_aspects_8:
        results["confidence_boost"] += 16
        results["fired_patterns"].append(
            "Jupiter aspects/occupies both 4th and 8th — wealth protection, smooth property expansion")
    elif jup_aspects_4:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(
            "Jupiter aspects/occupies 4th house — property blessed and protected")
    elif jup_aspects_8:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(
            "Jupiter aspects/occupies 8th house — inheritance protected")

    # Pattern 9: Saturn in 4th — ancestral structures
    saturn_house = chart.planets.get("Saturn", {}).get("house", 0)
    if saturn_house == 4:
        saturn_sign = chart.planets["Saturn"]["sign"]
        if saturn_sign in [10, 11, 7]:  # Own/exalted
            results["confidence_boost"] += 12
            results["fired_patterns"].append(
                f"Saturn dignified in 4th ({SIGN_NAMES.get(saturn_sign, '?')}) — strong ancestral structures")
        else:
            results["confidence_boost"] += 5
            results["fired_patterns"].append(
                "Saturn in 4th — ancestral property (old buildings, needs maintenance)")

    return results



# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR (Property)
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """
    Evaluate outcome/quality rules for property classification.
    Mode: smooth_inheritance, disputed_property, sudden_gain, karmic_pattern, inherited_debt
    Quality: supportive, challenging, mixed
    Asset type: land, liquid_wealth, luxury_assets, inaccessible
    """
    fired_rules = []

    fourth_lord_house = chart.planets.get(chart.fourth_lord, {}).get("house", 0)
    eighth_lord_house = chart.planets.get(chart.eighth_lord, {}).get("house", 0)
    ninth_lord_house = chart.planets.get(chart.ninth_lord, {}).get("house", 0)
    sixth_lord_house = chart.planets.get(chart.sixth_lord, {}).get("house", 0)
    mars_house = chart.planets.get("Mars", {}).get("house", 0)
    saturn_house = chart.planets.get("Saturn", {}).get("house", 0)
    jupiter_house = chart.planets.get("Jupiter", {}).get("house", 0)
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    ketu_house = chart.planets.get("Ketu", {}).get("house", 0)
    venus_house = chart.planets.get("Venus", {}).get("house", 0)

    # Benefics in 8th check
    benefics_in_8th = [p for p in chart.eighth_house_occupants if p in NATURAL_BENEFICS]

    # ─── MODE DETECTION ───
    # Smooth inheritance: benefics in 8th + strong 4th lord
    if benefics_in_8th and fourth_lord_house in [1, 4, 5, 7, 9, 10]:
        fired_rules.append(("smooth_inheritance_indicated", "mode_smooth", 0.90,
            "Benefics in 8th + strong 4th lord — smooth inheritance mode"))

    # Disputed property: 6th lord connected to 4th/8th
    if sixth_lord_house in [4, 8] or (eighth_lord_house == 6):
        fired_rules.append(("disputed_property_indicated", "mode_disputed", 0.85,
            f"6th lord in house {sixth_lord_house}, 8th lord in house {eighth_lord_house} — disputed property mode"))

    # Sudden gain: Rahu/Ketu in 4th/8th/11th
    if rahu_house in [4, 8, 11] or ketu_house in [4, 8, 11]:
        fired_rules.append(("sudden_gain_indicated", "mode_sudden", 0.82,
            f"Rahu(h{rahu_house})/Ketu(h{ketu_house}) in property houses — sudden gain mode"))

    # Karmic pattern: Saturn afflicts 4th/8th + Ketu in property houses
    if saturn_house in [4, 8] and ketu_house in [4, 8, 12]:
        fired_rules.append(("karmic_pattern_indicated", "mode_karmic", 0.80,
            "Saturn + Ketu in property axis — karmic pattern mode"))

    # Inherited debt: 8th lord in 12th + 6th lord aspects 4th
    if eighth_lord_house == 12 and sixth_lord_house in [4, 10]:
        fired_rules.append(("inherited_debt_indicated", "mode_debt", 0.78,
            "8th lord in 12th + 6th lord afflicts 4th — inherited debt mode"))


    # ─── QUALITY DETECTION ───
    if benefics_in_8th and not any(p in chart.eighth_house_occupants for p in NATURAL_MALEFICS):
        fired_rules.append(("quality_supportive", "quality_supportive", 0.88,
            "Clean benefic 8th house — supportive quality"))
    elif any(p in chart.eighth_house_occupants for p in NATURAL_MALEFICS) and benefics_in_8th:
        fired_rules.append(("quality_mixed", "quality_mixed", 0.80,
            "Both benefics and malefics in 8th — mixed quality"))
    elif any(p in chart.eighth_house_occupants for p in NATURAL_MALEFICS):
        fired_rules.append(("quality_challenging", "quality_challenging", 0.82,
            "Malefics dominate 8th — challenging quality"))
    else:
        fired_rules.append(("quality_default_mixed", "quality_mixed", 0.70,
            "No strong 8th house occupation — mixed quality (default)"))

    # ─── ASSET TYPE DETECTION ───
    if mars_house in [4, 2, 11] or chart.fourth_lord == "Mars":
        fired_rules.append(("asset_land", "asset_land", 0.85,
            f"Mars in house {mars_house} or 4th lord is Mars — land/real estate"))
    if venus_house in [4, 2, 7]:
        fired_rules.append(("asset_luxury", "asset_luxury", 0.82,
            f"Venus in house {venus_house} — luxury assets/vehicles/beautiful property"))
    if jupiter_house in [2, 8, 11]:
        fired_rules.append(("asset_liquid", "asset_liquid", 0.80,
            f"Jupiter in house {jupiter_house} — liquid wealth/investments/gold"))
    if eighth_lord_house in [6, 8, 12] and not benefics_in_8th:
        fired_rules.append(("asset_inaccessible", "asset_inaccessible", 0.78,
            f"8th lord in {eighth_lord_house}, no benefic in 8th — inaccessible/locked assets"))

    # ═══════════════════════════════════════════════════════════
    # RESOLUTION (calibration-based)
    # ═══════════════════════════════════════════════════════════
    cal = CALIBRATION.get("outcome_calibration", {})
    default_mode = cal.get("default_mode", "smooth_inheritance")

    # Resolve MODE
    resolved_mode = default_mode
    mode_rules = [r for r in fired_rules if r[1].startswith("mode_")]
    if mode_rules:
        mode_rules.sort(key=lambda r: -r[2])
        mode_map = {
            "mode_smooth": "smooth_inheritance",
            "mode_disputed": "disputed_property",
            "mode_sudden": "sudden_gain",
            "mode_karmic": "karmic_pattern",
            "mode_debt": "inherited_debt",
        }
        resolved_mode = mode_map.get(mode_rules[0][1], default_mode)

    # Resolve QUALITY
    resolved_quality = "mixed"
    quality_rules = [r for r in fired_rules if r[1].startswith("quality_")]
    if quality_rules:
        quality_rules.sort(key=lambda r: -r[2])
        quality_map = {
            "quality_supportive": "supportive",
            "quality_mixed": "mixed",
            "quality_challenging": "challenging",
        }
        resolved_quality = quality_map.get(quality_rules[0][1], "mixed")

    # Resolve ASSET TYPE
    resolved_asset = "land"
    asset_rules = [r for r in fired_rules if r[1].startswith("asset_")]
    if asset_rules:
        asset_rules.sort(key=lambda r: -r[2])
        asset_map = {
            "asset_land": "land",
            "asset_luxury": "luxury_assets",
            "asset_liquid": "liquid_wealth",
            "asset_inaccessible": "inaccessible",
        }
        resolved_asset = asset_map.get(asset_rules[0][1], "land")

    return {
        "mode": resolved_mode,
        "quality": resolved_quality,
        "asset_type": resolved_asset,
        "fired_outcomes": [f"{r[0]}: {r[3]}" for r in fired_rules],
        "_classical_rules_fired": fired_rules,
        "_resolution_method": "calibration_priority_order",
        "_calibration_version": CALIBRATION.get("calibration_version", "unknown"),
    }



# ═══════════════════════════════════════════════════════════════
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE (Property)
# ═══════════════════════════════════════════════════════════════

class PropertyWindowResult:
    """Result of evaluating a single property time window."""

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



def scan_property_windows(chart: ChartState, start_age=20, end_age=65, step_months=6):
    """
    Scan through life from start_age to end_age in step_months increments.
    Property events typically happen from age 20-65.
    For each AD period in that range, evaluate the 5-layer engine.
    Returns sorted list of PropertyWindowResult.
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

            # Also check at start and end
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
            result = PropertyWindowResult()
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
    print("  5-LAYER PROPERTY RULE ENGINE — VEDIC TEXT BASED")
    print("  Domain: Ancestral Property & Inheritance")
    print("  Native: 22 July 1975, 18:15 IST, Bhilai")
    print("=" * 80)

    # Build chart state
    chart = ChartState(BIRTH_DATE, BHILAI_LAT, BHILAI_LON, BHILAI_ALT)

    print(f"\n{'─' * 80}")
    print("  NATAL CHART SUMMARY (Property Focus)")
    print(f"{'─' * 80}")
    print(f"  Lagna: {SIGN_NAMES[chart.asc_sign]} | Lagna Lord: {chart.lagna_lord}")
    print(f"  Moon: {SIGN_NAMES[chart.moon_sign]} ({chart.moon_nakshatra})")
    print(f"  4th Lord: {chart.fourth_lord} (house {chart.planets[chart.fourth_lord]['house']})")
    print(f"  8th Lord: {chart.eighth_lord} (house {chart.planets[chart.eighth_lord]['house']})")
    print(f"  9th Lord: {chart.ninth_lord} (house {chart.planets[chart.ninth_lord]['house']})")
    print(f"  2nd Lord: {chart.second_lord} (house {chart.planets[chart.second_lord]['house']})")
    print(f"  12th Lord: {chart.twelfth_lord} (house {chart.planets[chart.twelfth_lord]['house']})")
    print(f"  Mars: house {chart.planets['Mars']['house']}, sign {SIGN_NAMES[chart.planets['Mars']['sign']]}")
    print(f"  Saturn: house {chart.planets['Saturn']['house']}, sign {SIGN_NAMES[chart.planets['Saturn']['sign']]}")
    print(f"  Jupiter: house {chart.planets['Jupiter']['house']}, sign {SIGN_NAMES[chart.planets['Jupiter']['sign']]}")
    print(f"  Venus: house {chart.planets['Venus']['house']}, sign {SIGN_NAMES[chart.planets['Venus']['sign']]}")
    print(f"  Sensitive Point 1 (4L+9L): {chart.sensitive_point_1:.2f}deg")
    print(f"  Sensitive Point 2 (Mars+8L): {chart.sensitive_point_2:.2f}deg")


    # Layer 4 & 5 (structural)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    print(f"\n{'─' * 80}")
    print("  LAYER 4: CLASSICAL PATTERNS (Structural — Property)")
    print(f"{'─' * 80}")
    print(f"  Timing Modifier: {classical['timing_modifier'].upper()}")
    print(f"  Confidence Boost: {classical['confidence_boost']:+d}")
    for p in classical["fired_patterns"]:
        print(f"    * {p}")
    if not classical["fired_patterns"]:
        print("    (No classical property patterns detected)")

    print(f"\n{'─' * 80}")
    print("  LAYER 5: OUTCOME / QUALITY (Property Classification)")
    print(f"{'─' * 80}")
    print(f"  Property Mode: {outcome['mode']}")
    print(f"  Quality: {outcome['quality']}")
    print(f"  Asset Type: {outcome['asset_type']}")
    for o in outcome["fired_outcomes"]:
        print(f"    * {o}")

    # Scan property windows
    print(f"\n{'─' * 80}")
    print("  SCANNING PROPERTY WINDOWS (Age 20-65, step=6mo)...")
    print(f"{'─' * 80}")

    windows = scan_property_windows(chart, start_age=20, end_age=65, step_months=6)

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
    print("  TOP 5 PROPERTY WINDOWS — DETAILED 5-LAYER BREAKDOWN")
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
        print(f"\n  STRONGEST PROPERTY WINDOW:")
        print(f"  {top.period_start.strftime('%B %Y')} - {top.period_end.strftime('%B %Y')}")
        print(f"  Age {top.age_start:.1f}-{top.age_end:.1f} | {top.md_lord}-{top.ad_lord}")
        print(f"  Score: {top.total_score:.1f} | {top.likelihood}")
        print(f"\n  Property Mode: {outcome['mode']}")
        print(f"  Quality: {outcome['quality']}")
        print(f"  Asset Type: {outcome['asset_type']}")
        print(f"\n  The 5-layer engine evaluated {len(windows)} AD periods with")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['high'])} HIGH+ confidence windows.")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['very_high'])} VERY_HIGH confidence windows.")
    print(f"\n{'=' * 80}")
