"""
Fame Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow.
Domain: Fame & Public Recognition
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
RULES_DIR = Path(__file__).resolve().parent / "domains" / "status" / "fame_and_public_recognition"

# Fame-specific constants
FAME_KARAKAS = {"Sun", "Jupiter", "Moon", "Venus", "Rahu"}  # fame/recognition planets
FAME_HOUSES = {1, 5, 9, 10, 11}  # self, creativity, dharma, karma, gains




# ═══════════════════════════════════════════════════════════════
# CALIBRATION OVERLAY LOADER (Layer 3)
# ═══════════════════════════════════════════════════════════════

def _load_calibration():
    """
    Load calibration overlay from JSON.
    Returns dict with layer_weights, likelihood_thresholds, base_scores,
    outcome_calibration, and rule_adjustments.
    """
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
                    "fame_karaka_md_or_ad": 45,
                    "tenth_lord_md_or_ad": 42,
                    "first_lord_md_or_ad": 38,
                    "fifth_lord_md_or_ad": 35,
                    "ninth_lord_md_or_ad": 33,
                    "eleventh_lord_md_or_ad": 30,
                },
                "transit": {
                    "jupiter_conjunct_natal_sun": 50,
                    "jupiter_return": 42,
                    "benefics_in_10th": 35,
                    "abhishek_tara_28th_slow": 38,
                },
                "fast_trigger": {
                    "abhishek_tara_moon_28th": 30,
                    "abhishek_tara_mars_28th": 28,
                },
            },
            "outcome_calibration": {
                "mode_priority_order": [
                    "political_fame",
                    "artistic_fame",
                    "spiritual_fame",
                    "mass_influence",
                    "controversial",
                ],
                "quality_priority_order": [
                    "stable",
                    "charismatic",
                    "unstable",
                    "scandal_prone",
                ],
                "scale_priority_order": [
                    "international",
                    "national",
                    "local",
                ],
                "default_mode": "general_recognition",
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
    """Encapsulates all natal chart data needed for fame rule evaluation."""

    def __init__(self, birth_dt, lat, lon, alt=0):
        super().__init__(birth_dt, lat, lon, alt)


        # Key house lords (fame-focused)
        self.lagna_lord = SIGN_LORDS[self.asc_sign]
        self.first_sign = self.asc_sign
        self.first_lord = SIGN_LORDS[self.first_sign]
        self.fifth_sign = ((self.asc_sign + 4 - 1) % 12) + 1
        self.fifth_lord = SIGN_LORDS[self.fifth_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.tenth_sign = ((self.asc_sign + 9 - 1) % 12) + 1
        self.tenth_lord = SIGN_LORDS[self.tenth_sign]
        self.eleventh_sign = ((self.asc_sign + 10 - 1) % 12) + 1
        self.eleventh_lord = SIGN_LORDS[self.eleventh_sign]
        self.fourth_sign = ((self.asc_sign + 3 - 1) % 12) + 1
        self.fourth_lord = SIGN_LORDS[self.fourth_sign]
        self.second_sign = ((self.asc_sign + 1 - 1) % 12) + 1
        self.second_lord = SIGN_LORDS[self.second_sign]
        self.third_sign = ((self.asc_sign + 2 - 1) % 12) + 1
        self.third_lord = SIGN_LORDS[self.third_sign]
        self.sixth_sign = ((self.asc_sign + 5 - 1) % 12) + 1
        self.sixth_lord = SIGN_LORDS[self.sixth_sign]
        self.seventh_sign = ((self.asc_sign + 6 - 1) % 12) + 1
        self.seventh_lord = SIGN_LORDS[self.seventh_sign]
        self.eighth_sign = ((self.asc_sign + 7 - 1) % 12) + 1
        self.eighth_lord = SIGN_LORDS[self.eighth_sign]
        self.twelfth_sign = ((self.asc_sign + 11 - 1) % 12) + 1
        self.twelfth_lord = SIGN_LORDS[self.twelfth_sign]

        # Planets in 10th house (karma/fame)
        self.tenth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 10
        ]

        # Planets aspecting 10th house
        self.tenth_house_aspectors = self._get_aspectors_of_house(10)


        # Navamsa (D9) calculations
        self.d9_asc_sign = self._compute_d9_lagna()
        self.moon_d9_sign = self._get_d9_sign(self.moon_lon)
        self.moon_is_vargottama = (self.moon_sign == self.moon_d9_sign)
        self.lagna_is_vargottama = (self.asc_sign == self.d9_asc_sign)

        # Sensitive Fame Points
        # Point 1: Sun + 10th lord longitude sum (fame axis)
        sun_lon = self.birth_positions["Sun"]
        tenth_lord_lon = self.birth_positions[self.tenth_lord]
        self.sensitive_point_1 = (sun_lon + tenth_lord_lon) % 360

        # Point 2: Moon + Jupiter longitude sum (public wisdom axis)
        jupiter_lon = self.birth_positions["Jupiter"]
        self.sensitive_point_2 = (self.moon_lon + jupiter_lon) % 360

    def get_house_from_sign(self, transit_sign, reference_sign=None):
        """Get house number from a sign, relative to reference (default: lagna)."""
        ref = reference_sign or self.asc_sign
        return ((transit_sign - ref) % 12) + 1




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
# LAYER 1: DASHA EVALUATOR (Fame)
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate dasha rules for fame/recognition.
    Key lords: 1st lord, 10th lord, 5th lord, 9th lord, 11th lord.
    Positive: Saturn dignified, 1st-10th Parivartana, Gaja Kesari, Sun-Mercury,
              Rahu-Sun, Venus-Saturn.
    Recovery: Jupiter-Venus period reduces fame risk.
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Key lords for fame events
    key_lords = {
        chart.tenth_lord: ("10th lord", "karma/public action", 42),
        chart.first_lord: ("1st lord", "self/personality/image", 38),
        chart.fifth_lord: ("5th lord", "creativity/past merit", 35),
        chart.ninth_lord: ("9th lord", "dharma/fortune/guru", 33),
        chart.eleventh_lord: ("11th lord", "gains/networks/fulfillment", 30),
    }

    # Rule 1: Fame house lords in MD/AD (priority 98)
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
        fired.append(("fame_house_lord_dasha", r1_score, r1_reasons))

    # Rule 2: Fame karaka planets in MD/AD (priority 95)
    r2_score = 0
    r2_reasons = []
    karaka_scores = {
        "Sun": (45, "fame/authority/public standing"),
        "Jupiter": (40, "wisdom-fame/dharmic honor"),
        "Moon": (35, "public popularity/mass appeal"),
        "Venus": (38, "artistic fame/beauty/entertainment"),
        "Rahu": (36, "mass influence/sudden viral fame"),
    }
    if md_lord in FAME_KARAKAS:
        score, desc = karaka_scores[md_lord]
        r2_score += score
        r2_reasons.append(f"MD of fame karaka {md_lord} ({desc})")
    if ad_lord in FAME_KARAKAS:
        score, desc = karaka_scores[ad_lord]
        r2_score += int(score * 0.75)
        r2_reasons.append(f"AD of fame karaka {ad_lord} ({desc})")
    if r2_score > 0:
        fired.append(("fame_karaka_dasha", r2_score, r2_reasons))


    # Rule 3: Positive fame dasha combinations (priority 92)
    r3_score = 0
    r3_reasons = []

    # Saturn dignified fame (if Saturn in own/exalted sign)
    saturn_sign = chart.planets.get("Saturn", {}).get("sign", 0)
    if (md_lord == "Saturn" or ad_lord == "Saturn") and saturn_sign in [7, 10, 11]:
        r3_score += 40
        r3_reasons.append(f"Saturn dignified (sign {SIGN_NAMES.get(saturn_sign, '?')}) in dasha — enduring authority")

    # 1st-10th Parivartana activation
    first_lord_house = chart.planets.get(chart.first_lord, {}).get("house", 0)
    tenth_lord_house = chart.planets.get(chart.tenth_lord, {}).get("house", 0)
    if first_lord_house == 10 and tenth_lord_house == 1:
        if md_lord in [chart.first_lord, chart.tenth_lord] or ad_lord in [chart.first_lord, chart.tenth_lord]:
            r3_score += 45
            r3_reasons.append("1st-10th Parivartana active in dasha — self-career fame fusion")

    # Gaja Kesari activation
    jup_house = chart.planets.get("Jupiter", {}).get("house", 0)
    moon_house = chart.planets.get("Moon", {}).get("house", 0)
    jup_from_moon = ((jup_house - moon_house) % 12) + 1
    if jup_from_moon in [1, 4, 7, 10]:
        if md_lord in ["Jupiter", "Moon"] or ad_lord in ["Jupiter", "Moon"]:
            r3_score += 38
            r3_reasons.append("Gaja Kesari Yoga active in dasha — wisdom fame/public honor")

    # Sun-Mercury artistic fame
    if (md_lord == "Sun" and ad_lord == "Mercury") or (md_lord == "Mercury" and ad_lord == "Sun"):
        r3_score += 32
        r3_reasons.append("Sun-Mercury dasha — intellectual/artistic fame activation")

    # Rahu-Sun mass popularity
    if md_lord == "Rahu" and ad_lord == "Sun":
        r3_score += 35
        r3_reasons.append("Rahu-Sun dasha — mass popularity/sudden fame explosion")

    # Venus-Saturn artistic authority
    if (md_lord == "Venus" and ad_lord == "Saturn") or (md_lord == "Saturn" and ad_lord == "Venus"):
        r3_score += 30
        r3_reasons.append("Venus-Saturn dasha — artistic mastery/authority recognition")

    if r3_score > 0:
        fired.append(("fame_positive_dasha", r3_score, r3_reasons))


    # Rule 4: Recovery — Jupiter-Venus reduces fame risk (positive period)
    r4_score = 0
    r4_reasons = []
    if md_lord == "Jupiter" and ad_lord == "Venus":
        r4_score -= 20
        r4_reasons.append("Jupiter-Venus dasha — benevolent period, fame risk reduced (grace)")
    if md_lord == "Venus" and ad_lord == "Jupiter":
        r4_score -= 15
        r4_reasons.append("Venus-Jupiter dasha — creative grace period, smooth public standing")
    if r4_score != 0:
        fired.append(("fame_recovery_dasha", r4_score, r4_reasons))

    # Rule 5: MD/AD lord placed in fame houses (priority 80)
    r5_score = 0
    r5_reasons = []
    md_house = chart.planets.get(md_lord, {}).get("house", 0)
    ad_house = chart.planets.get(ad_lord, {}).get("house", 0)
    if md_house in FAME_HOUSES:
        r5_score += 20
        r5_reasons.append(f"MD lord {md_lord} placed in fame house {md_house}")
    if ad_house in FAME_HOUSES:
        r5_score += 15
        r5_reasons.append(f"AD lord {ad_lord} placed in fame house {ad_house}")
    if r5_score > 0:
        fired.append(("fame_lord_placement", r5_score, r5_reasons))

    return fired




# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR (Fame)
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate transit rules for fame activation.
    Key: Jupiter conjunct natal Sun (fame), Jupiter Return,
    Benefics transit 10th, Abhishek Tara (28th nak) transit.
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Rule 1: Jupiter conjunct natal Sun (priority 95)
    natal_sun_lon = chart.birth_positions["Sun"]
    if transit.jupiter_conjunct_natal(natal_sun_lon, orb=5.0):
        fired.append(("jupiter_conjunct_natal_sun", 50,
                      ["Transit Jupiter conjunct natal Sun — fame activation (strongest single transit)"]))

    # Rule 2: Jupiter Return (priority 90)
    natal_jupiter_lon = chart.birth_positions["Jupiter"]
    if transit.jupiter_conjunct_natal(natal_jupiter_lon, orb=5.0):
        fired.append(("jupiter_return_natal", 42,
                      ["Transit Jupiter return to natal position — dharma recognition cycle"]))

    # Rule 3: Benefics transit 10th house (priority 82)
    benefics_in_10th = []
    for planet in ["Jupiter", "Venus", "Mercury", "Moon"]:
        if transit.planet_houses_from_lagna.get(planet, 0) == 10:
            benefics_in_10th.append(planet)
    if len(benefics_in_10th) >= 2:
        fired.append(("benefics_transit_10th", 35,
                      [f"Multiple benefics ({', '.join(benefics_in_10th)}) transit 10th — public visibility window"]))

    # Rule 4: Abhishek Tara (28th nakshatra) transit by Jupiter/Saturn (priority 88)
    birth_moon_nak_idx = int((chart.moon_lon % 360) / 13.3333333333) % 27
    for planet in ["Jupiter", "Saturn"]:
        planet_lon = transit.positions[planet]
        planet_nak_idx = int((planet_lon % 360) / 13.3333333333) % 27
        nak_offset = ((planet_nak_idx - birth_moon_nak_idx) % 27) + 1
        if nak_offset == 1:  # 28th wraps to 1st (27+1=28, but mod 27 = 1)
            fired.append(("abhishek_tara_28th_slow", 38,
                          [f"Transit {planet} on Abhishek Tara (28th nak) — coronation/recognition window"]))

    return fired




# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR (Fame)
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate fast trigger rules for exact fame/recognition timing.
    Abhishek Tara (28th Nakshatra from Moon) = recognition day.
    Moon on 28th = public recognition moment.
    Mars on 28th = action-fame day (awards/announcements).
    Returns list of (rule_id, score, reasons) for fired rules.
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

    # Rule 1: Moon on Abhishek Tara (28th = wraps to position 1 in mod-27 system)
    if moon_nak_offset == 1:
        fired.append(("fast_trigger_moon_abhishek_28th", 30,
                      ["Moon on Abhishek Tara (28th nak) — recognition/coronation day"]))

    # Rule 2: Mars on Abhishek Tara (28th)
    if mars_nak_offset == 1:
        fired.append(("fast_trigger_mars_abhishek_28th", 28,
                      ["Mars on Abhishek Tara (28th nak) — action-fame/award announcement day"]))

    return fired




# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR (Fame)
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """
    Evaluate classical fame patterns (structural — not time-dependent).
    Checks: Amala Yoga, 1st-10th exchange, Moon 10th, Lords in 9th,
    Vargottama Moon, 10th lord benefic, Sun-Rahu-Venus charisma,
    Vargottama Lagna/Moon, Sun 10th, Malefics 3-6-11.
    Returns dict with confidence_boost and fired_patterns.
    """
    results = {
        "timing_modifier": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    sun_house = chart.planets["Sun"]["house"]
    moon_house = chart.planets["Moon"]["house"]
    jupiter_house = chart.planets["Jupiter"]["house"]
    venus_house = chart.planets["Venus"]["house"]
    mars_house = chart.planets["Mars"]["house"]
    saturn_house = chart.planets["Saturn"]["house"]
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    mercury_house = chart.planets.get("Mercury", {}).get("house", 0)
    tenth_lord_house = chart.planets[chart.tenth_lord]["house"]
    first_lord_house = chart.planets[chart.first_lord]["house"]

    # 10th house from Moon
    moon_sign = chart.moon_sign
    tenth_from_moon = ((moon_sign + 9 - 1) % 12) + 1


    # Pattern 1: Amala Yoga — benefic in 10th from Moon
    benefics_in_10th_from_moon = []
    for planet in ["Jupiter", "Venus", "Mercury"]:
        p_sign = chart.planets[planet]["sign"]
        if p_sign == tenth_from_moon:
            benefics_in_10th_from_moon.append(planet)
    if benefics_in_10th_from_moon:
        results["confidence_boost"] += 18
        results["fired_patterns"].append(
            f"Amala Yoga: {', '.join(benefics_in_10th_from_moon)} in 10th from Moon — spotless fame")

    # Pattern 2: 1st-10th lord exchange (Parivartana)
    if first_lord_house == 10 and tenth_lord_house == 1:
        results["confidence_boost"] += 20
        results["timing_modifier"] = "career_fame_fusion"
        results["fired_patterns"].append(
            f"1st-10th Parivartana: {chart.first_lord} in 10th, {chart.tenth_lord} in 1st — self-career fame")

    # Pattern 3: Moon in 10th with 10th lord in trine
    if moon_house == 10 and tenth_lord_house in [1, 5, 9]:
        results["confidence_boost"] += 15
        results["fired_patterns"].append(
            f"Moon in 10th + 10th lord ({chart.tenth_lord}) in trine (house {tenth_lord_house}) — public popularity")

    # Pattern 4: Multiple lords in 9th (dharma fame)
    lords_in_9th = 0
    for lord_name in [chart.first_lord, chart.fifth_lord, chart.ninth_lord, chart.tenth_lord, chart.eleventh_lord]:
        lord_house = chart.planets.get(lord_name, {}).get("house", 0)
        if lord_house == 9:
            lords_in_9th += 1
    if lords_in_9th >= 2:
        results["confidence_boost"] += 14
        results["fired_patterns"].append(
            f"{lords_in_9th} auspicious lords in 9th house — dharma-based fame/spiritual authority")


    # Pattern 5: Vargottama Moon
    if chart.moon_is_vargottama:
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            "Vargottama Moon — international recognition potential (emotional power doubled)")

    # Pattern 6: 10th lord with benefics (conjunct or aspected by Jupiter/Venus)
    tenth_lord_aspectors = chart._get_aspectors_of_house(tenth_lord_house)
    benefic_support = [p for p in ["Jupiter", "Venus"] if p in tenth_lord_aspectors or
                       chart.planets.get(p, {}).get("house", 0) == tenth_lord_house]
    if benefic_support:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(
            f"10th lord ({chart.tenth_lord}) supported by {', '.join(benefic_support)} — honored reputation")

    # Pattern 7: Sun-Rahu-Venus charisma pattern
    sun_sign = chart.planets["Sun"]["sign"]
    rahu_sign = chart.planets.get("Rahu", {}).get("sign", 0)
    venus_sign = chart.planets["Venus"]["sign"]
    if sun_sign == rahu_sign == venus_sign:
        results["confidence_boost"] += 16
        results["timing_modifier"] = "charismatic_volatile"
        results["fired_patterns"].append(
            "Sun-Rahu-Venus conjunction — extraordinary charisma/magnetic mass appeal")
    elif (sun_sign == rahu_sign or sun_sign == venus_sign or rahu_sign == venus_sign):
        partial_combo = []
        if sun_sign == rahu_sign:
            partial_combo = ["Sun", "Rahu"]
        elif sun_sign == venus_sign:
            partial_combo = ["Sun", "Venus"]
        elif rahu_sign == venus_sign:
            partial_combo = ["Rahu", "Venus"]
        if partial_combo:
            results["confidence_boost"] += 8
            results["fired_patterns"].append(
                f"{'-'.join(partial_combo)} conjunction — partial charisma pattern")


    # Pattern 8: Vargottama Lagna + Moon
    if chart.lagna_is_vargottama:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(
            "Vargottama Lagna — strong personality/memorable public persona")
        if chart.moon_is_vargottama:
            results["confidence_boost"] += 5
            results["fired_patterns"].append(
                "Double Vargottama (Lagna + Moon) — exceptional lasting fame potential")

    # Pattern 9: Sun in 10th
    if sun_house == 10:
        results["confidence_boost"] += 16
        results["timing_modifier"] = "political_authority"
        results["fired_patterns"].append(
            "Sun in 10th house — political/government fame (raja yoga of visibility)")

    # Pattern 10: Malefics in 3/6/11 (competitive fame)
    malefics_in_upachaya = 0
    for planet in ["Mars", "Saturn", "Sun", "Rahu", "Ketu"]:
        p_house = chart.planets.get(planet, {}).get("house", 0)
        if p_house in [3, 6, 11]:
            malefics_in_upachaya += 1
    if malefics_in_upachaya >= 2:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(
            f"{malefics_in_upachaya} malefics in upachaya (3/6/11) — competitive victory fame (grows with age)")

    return results




# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR (Fame)
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """
    Evaluate outcome/quality rules for fame classification.
    Mode: political_fame, artistic_fame, spiritual_fame, controversial, mass_influence
    Quality: stable, unstable, charismatic, scandal_prone
    Scale: local, national, international
    """
    fired_rules = []

    sun_house = chart.planets["Sun"]["house"]
    moon_house = chart.planets["Moon"]["house"]
    venus_house = chart.planets["Venus"]["house"]
    jupiter_house = chart.planets["Jupiter"]["house"]
    mars_house = chart.planets["Mars"]["house"]
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    tenth_lord_house = chart.planets[chart.tenth_lord]["house"]
    first_lord_house = chart.planets[chart.first_lord]["house"]

    # Amala Yoga check
    moon_sign = chart.moon_sign
    tenth_from_moon = ((moon_sign + 9 - 1) % 12) + 1
    has_amala = any(chart.planets[p]["sign"] == tenth_from_moon for p in ["Jupiter", "Venus", "Mercury"])

    # ─── MODE DETECTION ───
    if sun_house == 10:
        fired_rules.append(("sun_10th_political", "mode_political", 0.90,
            "Sun in 10th — political/government fame mode"))

    if venus_house == 10 or chart.tenth_lord == "Venus":
        fired_rules.append(("venus_10th_artistic", "mode_artistic", 0.85,
            "Venus in 10th or 10th lord — artistic/creative fame mode"))

    if jupiter_house in [9, 12] or (jupiter_house == 10 and has_amala):
        fired_rules.append(("jupiter_spiritual", "mode_spiritual", 0.80,
            f"Jupiter in house {jupiter_house} — spiritual/wisdom fame mode"))

    if rahu_house == 10:
        fired_rules.append(("rahu_10th_mass", "mode_mass", 0.82,
            "Rahu in 10th — mass influence/unconventional fame mode"))

    # Moon-Mars conjunction/opposition = controversial
    moon_mars_same = (moon_house == mars_house)
    moon_mars_opp = (abs(moon_house - mars_house) == 6 or abs(moon_house - mars_house) == 6)
    if moon_mars_same or moon_mars_opp:
        fired_rules.append(("chandra_mangala_controversial", "mode_controversial", 0.78,
            "Moon-Mars connection — controversial/bold fame mode"))


    # ─── QUALITY DETECTION ───
    if has_amala:
        fired_rules.append(("amala_stable", "quality_stable", 0.90,
            "Amala Yoga present — stable/untarnished fame quality"))

    # Sun-Venus-Rahu charisma
    sun_sign = chart.planets["Sun"]["sign"]
    venus_sign = chart.planets["Venus"]["sign"]
    rahu_sign = chart.planets.get("Rahu", {}).get("sign", 0)
    if sun_sign == venus_sign == rahu_sign:
        fired_rules.append(("charisma_triple", "quality_charismatic", 0.88,
            "Sun-Venus-Rahu conjunction — charismatic but volatile fame quality"))

    # Ascendant lord weak = unstable
    first_lord_in_dusthana = first_lord_house in [6, 8, 12]
    if first_lord_in_dusthana:
        fired_rules.append(("lagna_lord_weak", "quality_unstable", 0.80,
            f"Lagna lord ({chart.first_lord}) in dusthana house {first_lord_house} — unstable/blocked fame"))

    # Moon-Mars = scandal-prone
    if moon_mars_same or moon_mars_opp:
        fired_rules.append(("moon_mars_scandal", "quality_scandal", 0.75,
            "Moon-Mars = Chandra-Mangala — scandal-prone fame quality"))

    # ─── SCALE DETECTION ───
    if chart.moon_is_vargottama:
        fired_rules.append(("vargottama_international", "scale_international", 0.82,
            "Vargottama Moon — international scale fame"))
    elif rahu_house in [1, 10, 9]:
        fired_rules.append(("rahu_national", "scale_national", 0.78,
            f"Rahu in house {rahu_house} — national scale fame"))
    else:
        fired_rules.append(("default_local", "scale_local", 0.65,
            "Default — local scale fame"))


    # ═══════════════════════════════════════════════════════════
    # RESOLUTION (calibration-based)
    # ═══════════════════════════════════════════════════════════
    cal = CALIBRATION.get("outcome_calibration", {})
    mode_priority = cal.get("mode_priority_order", [])
    quality_priority = cal.get("quality_priority_order", [])
    scale_priority = cal.get("scale_priority_order", [])
    default_mode = cal.get("default_mode", "general_recognition")

    # Resolve MODE
    resolved_mode = default_mode
    mode_rules = [r for r in fired_rules if r[1].startswith("mode_")]
    if mode_rules:
        mode_rules.sort(key=lambda r: -r[2])
        mode_map = {
            "mode_political": "political_fame",
            "mode_artistic": "artistic_fame",
            "mode_spiritual": "spiritual_fame",
            "mode_mass": "mass_influence",
            "mode_controversial": "controversial",
        }
        resolved_mode = mode_map.get(mode_rules[0][1], default_mode)

    # Resolve QUALITY
    resolved_quality = "unknown"
    quality_rules = [r for r in fired_rules if r[1].startswith("quality_")]
    if quality_rules:
        quality_rules.sort(key=lambda r: -r[2])
        quality_map = {
            "quality_stable": "stable",
            "quality_charismatic": "charismatic",
            "quality_unstable": "unstable",
            "quality_scandal": "scandal_prone",
        }
        resolved_quality = quality_map.get(quality_rules[0][1], "unknown")

    # Resolve SCALE
    resolved_scale = "local"
    scale_rules = [r for r in fired_rules if r[1].startswith("scale_")]
    if scale_rules:
        scale_rules.sort(key=lambda r: -r[2])
        scale_map = {
            "scale_international": "international",
            "scale_national": "national",
            "scale_local": "local",
        }
        resolved_scale = scale_map.get(scale_rules[0][1], "local")

    return {
        "mode": resolved_mode,
        "quality": resolved_quality,
        "scale": resolved_scale,
        "fired_outcomes": [f"{r[0]}: {r[3]}" for r in fired_rules],
        "_classical_rules_fired": fired_rules,
        "_resolution_method": "calibration_priority_order",
        "_calibration_version": CALIBRATION.get("calibration_version", "unknown"),
    }




# ═══════════════════════════════════════════════════════════════
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE (Fame)
# ═══════════════════════════════════════════════════════════════

class FameWindowResult:
    """Result of evaluating a single fame time window."""

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




def scan_fame_windows(chart: ChartState, start_age=15, end_age=65, step_months=6):
    """
    Scan through life from start_age to end_age in step_months increments.
    Fame can happen from youth (15) to senior years (65).
    For each AD period in that range, evaluate the 5-layer engine.
    Returns sorted list of FameWindowResult.
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

            # Merge transit results
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
            result = FameWindowResult()
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
    print("  5-LAYER FAME RULE ENGINE — VEDIC TEXT BASED")
    print("  Native: 22 July 1975, 18:15 IST, Bhilai")
    print("=" * 80)

    # Build chart state
    chart = ChartState(BIRTH_DATE, BHILAI_LAT, BHILAI_LON, BHILAI_ALT)

    print(f"\n{'─' * 80}")
    print("  NATAL CHART SUMMARY (Fame Focus)")
    print(f"{'─' * 80}")
    print(f"  Lagna: {SIGN_NAMES[chart.asc_sign]} | Lagna Lord: {chart.lagna_lord}")
    print(f"  Moon: {SIGN_NAMES[chart.moon_sign]} ({chart.moon_nakshatra})")
    print(f"  Sun: house {chart.planets['Sun']['house']}, sign {SIGN_NAMES[chart.planets['Sun']['sign']]}")
    print(f"  1st Lord: {chart.first_lord} (house {chart.planets[chart.first_lord]['house']})")
    print(f"  5th Lord: {chart.fifth_lord} (house {chart.planets[chart.fifth_lord]['house']})")
    print(f"  9th Lord: {chart.ninth_lord} (house {chart.planets[chart.ninth_lord]['house']})")
    print(f"  10th Lord: {chart.tenth_lord} (house {chart.planets[chart.tenth_lord]['house']})")
    print(f"  11th Lord: {chart.eleventh_lord} (house {chart.planets[chart.eleventh_lord]['house']})")
    print(f"  Jupiter: house {chart.planets['Jupiter']['house']}, sign {SIGN_NAMES[chart.planets['Jupiter']['sign']]}")
    print(f"  Venus: house {chart.planets['Venus']['house']}, sign {SIGN_NAMES[chart.planets['Venus']['sign']]}")
    print(f"  Rahu: house {chart.planets['Rahu']['house']}, sign {SIGN_NAMES[chart.planets['Rahu']['sign']]}")
    print(f"  Moon Vargottama: {chart.moon_is_vargottama} | Lagna Vargottama: {chart.lagna_is_vargottama}")
    print(f"  Sensitive Point 1 (Sun+10L): {chart.sensitive_point_1:.2f}deg")
    print(f"  Sensitive Point 2 (Moon+Jup): {chart.sensitive_point_2:.2f}deg")


    # Layer 4 & 5 (structural)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    print(f"\n{'─' * 80}")
    print("  LAYER 4: CLASSICAL PATTERNS (Structural — Fame)")
    print(f"{'─' * 80}")
    print(f"  Timing Modifier: {classical['timing_modifier'].upper()}")
    print(f"  Confidence Boost: +{classical['confidence_boost']}")
    for p in classical["fired_patterns"]:
        print(f"    * {p}")
    if not classical["fired_patterns"]:
        print("    (No classical fame patterns detected)")

    print(f"\n{'─' * 80}")
    print("  LAYER 5: OUTCOME / QUALITY (Fame Classification)")
    print(f"{'─' * 80}")
    print(f"  Fame Mode: {outcome['mode']}")
    print(f"  Fame Quality: {outcome['quality']}")
    print(f"  Fame Scale: {outcome['scale']}")
    for o in outcome["fired_outcomes"]:
        print(f"    * {o}")

    # Scan fame windows
    print(f"\n{'─' * 80}")
    print("  SCANNING FAME WINDOWS (Age 15-65, step=6mo)...")
    print(f"{'─' * 80}")

    windows = scan_fame_windows(chart, start_age=15, end_age=65, step_months=6)

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
    print("  TOP 5 FAME WINDOWS — DETAILED 5-LAYER BREAKDOWN")
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
        print(f"\n  STRONGEST FAME WINDOW:")
        print(f"  {top.period_start.strftime('%B %Y')} - {top.period_end.strftime('%B %Y')}")
        print(f"  Age {top.age_start:.1f}-{top.age_end:.1f} | {top.md_lord}-{top.ad_lord}")
        print(f"  Score: {top.total_score:.1f} | {top.likelihood}")
        print(f"\n  Fame Mode: {outcome['mode']}")
        print(f"  Fame Quality: {outcome['quality']}")
        print(f"  Fame Scale: {outcome['scale']}")
        print(f"\n  The 5-layer engine evaluated {len(windows)} AD periods with")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['high'])} HIGH+ confidence windows.")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['very_high'])} VERY_HIGH confidence windows.")
    print(f"\n{'=' * 80}")
