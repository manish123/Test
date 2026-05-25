"""
Business Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow.
Domain: Business Launch / Expansion / Scaling
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
RULES_DIR = Path(__file__).resolve().parent / "domains" / "business" / "business_launch"

# Business-specific constants
BUSINESS_KARAKAS = {"Mercury", "Jupiter", "Rahu", "Saturn", "Mars"}
BUSINESS_HOUSES = {2, 3, 7, 10, 11}  # wealth, self-effort, partnerships, commerce, gains



# ═══════════════════════════════════════════════════════════════
# CALIBRATION OVERLAY LOADER (Layer 3)
# ═══════════════════════════════════════════════════════════════

def _load_calibration():
    """
    Load calibration overlay from JSON.
    Returns dict with layer_weights, likelihood_thresholds, base_scores,
    outcome_calibration, and rule_adjustments.

    If file not found, returns sensible defaults.
    Calibration is NEVER hardcoded — always loaded from external config.
    """
    calibration_path = RULES_DIR / "calibration_overlay.json"
    try:
        with open(calibration_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback defaults — should never be needed in production
        return {
            "layer_weights": {
                "dasha_weight": 0.35,
                "transit_weight": 0.35,
                "fast_trigger_weight": 0.20,
                "classical_weight": 0.10,
            },
            "likelihood_thresholds": {
                "very_high": 55,
                "high": 40,
                "moderate": 25,
                "low": 15,
            },
            "base_scores": {
                "dasha": {
                    "business_karaka_lord_md_or_ad": 45,
                    "tenth_lord_md_or_ad": 40,
                    "eleventh_lord_md_or_ad": 38,
                    "seventh_lord_md_or_ad": 30,
                    "second_lord_md_or_ad": 28,
                    "third_lord_md_or_ad": 22,
                },
                "transit": {
                    "double_transit_7_10_11": 50,
                    "jupiter_conjunct_natal_mercury": 35,
                    "saturn_11th_from_moon": 38,
                    "jupiter_11th_from_moon": 32,
                    "saturn_12th_from_moon_negative": -30,
                },
                "fast_trigger": {
                    "mitra_tara_moon": 25,
                    "param_mitra_tara_moon": 25,
                    "moon_9th_10th_eyes": 20,
                    "moon_25th_27th_right_hand": 22,
                    "mars_16th_17th_head": 18,
                    "sanghatika_16th_negative": -30,
                },
            },
            "outcome_calibration": {
                "mode_priority_order": [
                    "sole_proprietorship_sun_7th",
                    "partnership_venus_7th",
                    "speculative_5_11_connection",
                    "technology_mars_navamsa",
                    "family_business_moon_2nd",
                    "communications_mercury_airy",
                    "unconventional_rahu_involvement",
                    "industrial_saturn_10th",
                ],
                "quality_priority_order": [
                    "dhana_yoga_high_wealth",
                    "chandra_mangala_11th_scalable",
                    "lagnesha_3rd_administrator",
                    "venus_7th_luxury_stable",
                    "jupiter_saturn_contraction",
                    "jupiter_mars_overleveraged",
                ],
                "default_mode": "general_commerce",
            },
        }


# Module-level calibration (loaded once at import)
CALIBRATION = _load_calibration()



# ═══════════════════════════════════════════════════════════════
# CHART STATE BUILDER
# ═══════════════════════════════════════════════════════════════

class ChartState(BaseChartState):
    """Encapsulates all natal chart data needed for rule evaluation."""

    def __init__(self, birth_dt, lat, lon, alt=0):
        super().__init__(birth_dt, lat, lon, alt)

        # Key house lords
        self.lagna_lord = SIGN_LORDS[self.asc_sign]
        self.seventh_sign = ((self.asc_sign + 6 - 1) % 12) + 1
        self.seventh_lord = SIGN_LORDS[self.seventh_sign]
        self.second_sign = ((self.asc_sign + 1 - 1) % 12) + 1
        self.second_lord = SIGN_LORDS[self.second_sign]
        self.third_sign = ((self.asc_sign + 2 - 1) % 12) + 1
        self.third_lord = SIGN_LORDS[self.third_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.tenth_sign = ((self.asc_sign + 9 - 1) % 12) + 1
        self.tenth_lord = SIGN_LORDS[self.tenth_sign]
        self.eleventh_sign = ((self.asc_sign + 10 - 1) % 12) + 1
        self.eleventh_lord = SIGN_LORDS[self.eleventh_sign]
        self.fifth_sign = ((self.asc_sign + 4 - 1) % 12) + 1
        self.fifth_lord = SIGN_LORDS[self.fifth_sign]


        # Planets in 7th house
        self.seventh_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 7
        ]

        # Planets aspecting 7th house
        self.seventh_house_aspectors = self._get_aspectors_of_house(7)

        # 2nd lord dispositor (sign where 2nd lord sits -> lord of that sign)
        second_lord_sign = self.planets[self.second_lord]["sign"]
        self.second_lord_dispositor = SIGN_LORDS[second_lord_sign]

        # 7th lord dispositor (sign where 7th lord sits -> lord of that sign)
        seventh_lord_sign = self.planets[self.seventh_lord]["sign"]
        self.seventh_lord_dispositor = SIGN_LORDS[seventh_lord_sign]

        # Navamsa (D9) calculations
        self.d9_asc_sign = self._compute_d9_lagna()
        self.d9_seventh_sign = ((self.d9_asc_sign + 6 - 1) % 12) + 1
        self.seventh_lord_d9_sign = self._get_d9_sign(
            self.birth_positions[self.seventh_lord]
        )
        self.seventh_lord_d9_dispositor = SIGN_LORDS[self.seventh_lord_d9_sign]

        # Janma Nakshatra Lord
        nak_index = int((self.moon_lon % 360) / 13.3333333333)
        self.janma_nakshatra_lord = NAKSHATRA_LORDS[nak_index % 27]

        # Sensitive Business Points
        # Point 1: Mercury + 10th lord longitude sum
        mercury_lon = self.birth_positions["Mercury"]
        tenth_lord_lon = self.birth_positions[self.tenth_lord]
        self.sensitive_point_1 = (mercury_lon + tenth_lord_lon) % 360

        # Point 2: 11th lord + Lagna lord longitude sum
        eleventh_lord_lon = self.birth_positions[self.eleventh_lord]
        lagna_lord_lon = self.birth_positions[self.lagna_lord]
        self.sensitive_point_2 = (eleventh_lord_lon + lagna_lord_lon) % 360

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
# LAYER 1: DASHA EVALUATOR (Business)
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate dasha rules for business success/failure.
    Checks if current MD/AD lord is a business karaka or rules business houses.
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Key lords for business
    key_lords = {
        chart.tenth_lord: ("10th lord", "commerce/karma", 40),
        chart.eleventh_lord: ("11th lord", "gains", 38),
        chart.seventh_lord: ("7th lord", "partnerships", 30),
        chart.second_lord: ("2nd lord", "wealth", 28),
        chart.third_lord: ("3rd lord", "self-effort", 22),
    }

    # Rule 1: Business house lords in MD/AD (priority 98)
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
        fired.append(("business_house_lord_dasha", r1_score, r1_reasons))

    # Rule 2: Business karaka planets in MD/AD (priority 95)
    r2_score = 0
    r2_reasons = []

    karaka_scores = {
        "Mercury": (45, "commerce/trade"),
        "Jupiter": (38, "expansion/funding"),
        "Rahu": (35, "scale/disruption"),
        "Saturn": (32, "structure/discipline"),
        "Mars": (28, "execution/aggression"),
    }

    if md_lord in BUSINESS_KARAKAS:
        score, desc = karaka_scores[md_lord]
        r2_score += score
        r2_reasons.append(f"MD of business karaka {md_lord} ({desc})")
    if ad_lord in BUSINESS_KARAKAS:
        score, desc = karaka_scores[ad_lord]
        r2_score += int(score * 0.75)
        r2_reasons.append(f"AD of business karaka {ad_lord} ({desc})")

    if r2_score > 0:
        fired.append(("business_karaka_dasha", r2_score, r2_reasons))

    # Rule 3: Challenging combinations (negative — priority 88)
    r3_score = 0
    r3_reasons = []

    # Jupiter-Saturn: contraction risk
    if md_lord == "Jupiter" and ad_lord == "Saturn":
        r3_score -= 25
        r3_reasons.append("Jupiter MD + Saturn AD — expansion-restriction friction (business failure risk)")
    # Jupiter-Mars: impulsive overextension
    if md_lord == "Jupiter" and ad_lord == "Mars":
        r3_score -= 20
        r3_reasons.append("Jupiter MD + Mars AD — impulsive expansion failure risk")

    if r3_score != 0:
        fired.append(("business_challenging_dasha", r3_score, r3_reasons))

    # Rule 4: MD/AD lord rules business houses 2, 7, 10, 11 (priority 85)
    r4_score = 0
    r4_reasons = []

    md_house = chart.planets.get(md_lord, {}).get("house", 0)
    ad_house = chart.planets.get(ad_lord, {}).get("house", 0)

    if md_house in BUSINESS_HOUSES:
        r4_score += 20
        r4_reasons.append(f"MD lord {md_lord} placed in business house {md_house}")
    if ad_house in BUSINESS_HOUSES:
        r4_score += 15
        r4_reasons.append(f"AD lord {ad_lord} placed in business house {ad_house}")

    if r4_score > 0:
        fired.append(("business_lord_placement", r4_score, r4_reasons))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR (Business)
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate transit rules for business activation.
    Key: Double transit on 7/10/11, Jupiter conjunct natal Mercury,
    Saturn/Jupiter in 11th from Moon, Saturn in 12th from Moon (negative).
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Rule 1: Double Transit on 7th/10th/11th (priority 98)
    # Jupiter and Saturn must BOTH influence business houses
    dt_score = 0
    dt_reasons = []

    for target_house in [7, 10, 11]:
        jup_hits = transit.planet_aspects_house("Jupiter", target_house, "lagna")
        sat_hits = transit.planet_aspects_house("Saturn", target_house, "lagna")
        if jup_hits and sat_hits:
            dt_score += 50
            dt_reasons.append(f"Double transit (Jup+Sat) on house {target_house} from Lagna")
            break  # Count once for strongest hit

    if dt_score == 0:
        # Check from Moon reference
        for target_house in [7, 10, 11]:
            jup_hits = transit.planet_aspects_house("Jupiter", target_house, "moon")
            sat_hits = transit.planet_aspects_house("Saturn", target_house, "moon")
            if jup_hits and sat_hits:
                dt_score += 40
                dt_reasons.append(f"Double transit (Jup+Sat) on house {target_house} from Moon")
                break

    if dt_score > 0:
        fired.append(("double_transit_business_houses", dt_score, dt_reasons))

    # Rule 2: Jupiter conjunct natal Mercury (priority 92)
    natal_mercury_lon = chart.birth_positions["Mercury"]
    if transit.jupiter_conjunct_natal(natal_mercury_lon, orb=3.0):
        fired.append(("jupiter_conjunct_natal_mercury", 35,
                      [f"Transit Jupiter conjunct natal Mercury ({natal_mercury_lon:.1f}deg) — commercial expansion window"]))

    # Rule 3: Saturn in 11th from Moon (priority 88)
    sat_house_from_moon = transit.planet_houses_from_moon.get("Saturn", 0)
    if sat_house_from_moon == 11:
        fired.append(("saturn_11th_from_moon", 38,
                      ["Transit Saturn in 11th from Moon — structural gains, funding secured"]))

    # Rule 4: Jupiter in 11th from Moon (priority 85)
    jup_house_from_moon = transit.planet_houses_from_moon.get("Jupiter", 0)
    if jup_house_from_moon == 11:
        fired.append(("jupiter_11th_from_moon", 32,
                      ["Transit Jupiter in 11th from Moon — network expansion, customer growth"]))

    # Rule 5: Jupiter in 2nd from Moon (wealth expansion)
    if jup_house_from_moon == 2:
        fired.append(("jupiter_2nd_from_moon", 28,
                      ["Transit Jupiter in 2nd from Moon — wealth expansion window"]))

    # Rule 6: Saturn in 12th from Moon (NEGATIVE — priority 90)
    if sat_house_from_moon == 12:
        fired.append(("saturn_12th_from_moon_negative", -30,
                      ["Transit Saturn in 12th from Moon — business drain, restructuring needed (BLOCKING)"]))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR (Business)
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate fast trigger rules for exact business timing.
    Moon Nakshatra: 8th=Mitra, 9th=Param Mitra, 9-10th=eyes, 25-27th=right hand
    Mars Nakshatra: 16-17th=head
    Sanghatika: 16th=crisis
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Get Moon's birth nakshatra index (0-26)
    birth_moon_nak_idx = int((chart.moon_lon % 360) / 13.3333333333) % 27

    # Transit Moon nakshatra position relative to birth
    transit_moon_lon = transit.positions["Moon"]
    transit_moon_nak_idx = int((transit_moon_lon % 360) / 13.3333333333) % 27
    moon_nak_offset = ((transit_moon_nak_idx - birth_moon_nak_idx) % 27) + 1

    # Rule 1: Mitra Tara (8th Nakshatra from birth) — partnership/funding day
    if moon_nak_offset == 8:
        fired.append(("fast_trigger_mitra_tara", 25,
                      [f"Moon in 8th Nakshatra (Mitra Tara) — partnership/funding day"]))

    # Rule 2: Param Mitra Tara (9th Nakshatra) — co-founder/investor day
    if moon_nak_offset == 9:
        fired.append(("fast_trigger_param_mitra_tara", 25,
                      [f"Moon in 9th Nakshatra (Param Mitra Tara) — co-founder/investor day"]))

    # Rule 3: Moon 9th-10th Nakshatra (eyes) — vision/planning window
    if moon_nak_offset in [9, 10]:
        fired.append(("fast_trigger_moon_eyes", 20,
                      [f"Moon in Nakshatra {moon_nak_offset} (eyes position) — business vision window"]))

    # Rule 4: Moon 25th-27th Nakshatra (right hand) — wealth acquisition day
    if moon_nak_offset in [25, 26, 27]:
        fired.append(("fast_trigger_moon_right_hand", 22,
                      [f"Moon in Nakshatra {moon_nak_offset} (right hand) — wealth acquisition day"]))

    # Rule 5: Mars Nakshatra 16-17th (head) — aggressive gains window
    transit_mars_lon = transit.positions["Mars"]
    transit_mars_nak_idx = int((transit_mars_lon % 360) / 13.3333333333) % 27
    mars_nak_offset = ((transit_mars_nak_idx - birth_moon_nak_idx) % 27) + 1

    if mars_nak_offset in [16, 17]:
        fired.append(("fast_trigger_mars_head", 18,
                      [f"Mars in Nakshatra {mars_nak_offset} (head position) — aggressive gains window"]))

    # Rule 6: Sanghatika 16th star (CRISIS — NEGATIVE)
    if moon_nak_offset == 16:
        fired.append(("fast_trigger_sanghatika_crisis", -30,
                      [f"Moon in 16th Nakshatra (Sanghatika) — business CRISIS trigger (BLOCKING)"]))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR (Business)
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """
    Evaluate classical business patterns (structural — not time-dependent).
    Checks: 5th-11th lord connection, Mercury in 10th alone, Lagnesha in 3rd,
    Chandra-Mangala in 11th, Venus in 7th, Moon in 2nd, 5th-8th Parivartana.
    Returns dict with confidence_boost and fired_patterns.
    """
    results = {
        "timing_modifier": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    fifth_lord_house = chart.planets[chart.fifth_lord]["house"]
    eleventh_lord_house = chart.planets[chart.eleventh_lord]["house"]
    tenth_lord_house = chart.planets[chart.tenth_lord]["house"]
    lagna_lord_house = chart.planets[chart.lagna_lord]["house"]
    mercury_house = chart.planets["Mercury"]["house"]
    venus_house = chart.planets["Venus"]["house"]
    moon_house = chart.planets["Moon"]["house"]
    mars_house = chart.planets["Mars"]["house"]
    saturn_house = chart.planets["Saturn"]["house"]

    # Pattern 1: 5th-11th lord connection (speculative business acumen)
    if fifth_lord_house == eleventh_lord_house:
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            f"5th-11th lord conjunction: {chart.fifth_lord} and {chart.eleventh_lord} in house {fifth_lord_house} (speculative business acumen)")
    elif fifth_lord_house == 11 or eleventh_lord_house == 5:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(
            f"5th-11th lord exchange: 5L in 11th or 11L in 5th (speculative gains through business)")

    # Pattern 2: Mercury in 10th alone (merchant/trader archetype)
    planets_in_10th = [n for n, d in chart.planets.items() if d["house"] == 10]
    if mercury_house == 10 and len(planets_in_10th) == 1:
        results["confidence_boost"] += 15
        results["fired_patterns"].append(
            "Mercury alone in 10th house — merchant/trader archetype (Nirayana System)")

    # Pattern 3: Lagnesha in 3rd (born business administrator)
    if lagna_lord_house == 3:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(
            f"Lagna lord ({chart.lagna_lord}) in 3rd house — born business administrator")

    # Pattern 4: Chandra-Mangala in 11th (viral/network business)
    if moon_house == 11 and mars_house == 11:
        results["confidence_boost"] += 14
        results["fired_patterns"].append(
            "Chandra-Mangala yoga in 11th house — viral/network business potential")
    elif moon_house == mars_house and moon_house == 11:
        results["confidence_boost"] += 14
        results["fired_patterns"].append(
            "Moon+Mars conjunction in 11th — gains through aggressive marketing")

    # Pattern 5: Venus in 7th (luxury/partnership business)
    if venus_house == 7:
        results["confidence_boost"] += 8
        results["fired_patterns"].append(
            "Venus in 7th house — luxury/partnership business tendency")

    # Pattern 6: Moon in 2nd (family business / public-facing wealth)
    if moon_house == 2:
        results["confidence_boost"] += 7
        results["fired_patterns"].append(
            "Moon in 2nd house — family business / public-facing wealth")

    # Pattern 7: 5th-8th Parivartana (large-scale market investments)
    fifth_sign = chart.fifth_sign
    eighth_sign = ((chart.asc_sign + 7 - 1) % 12) + 1
    eighth_lord = SIGN_LORDS[eighth_sign]
    eighth_lord_house = chart.planets[eighth_lord]["house"]
    if fifth_lord_house == 8 and eighth_lord_house == 5:
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            f"5th-8th Parivartana: {chart.fifth_lord} in 8th, {eighth_lord} in 5th — large-scale market investments")

    # Pattern 8: Saturn in 10th (industrial/disciplined business)
    if saturn_house == 10:
        results["confidence_boost"] += 8
        results["timing_modifier"] = "delayed_but_stable"
        results["fired_patterns"].append(
            "Saturn in 10th house — industrial/disciplined business (delayed start, stable growth)")

    return results



# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR (Business)
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """
    Evaluate outcome/quality rules for business classification.
    Mode: sole_proprietorship, partnership, speculative, technology,
          family_business, communications, unconventional, industrial
    Quality: scalable, stable, volatile, painful, litigation_prone
    """
    fired_rules = []

    sun_house = chart.planets["Sun"]["house"]
    venus_house = chart.planets["Venus"]["house"]
    mars_house = chart.planets["Mars"]["house"]
    moon_house = chart.planets["Moon"]["house"]
    mercury_house = chart.planets["Mercury"]["house"]
    mercury_sign = chart.planets["Mercury"]["sign"]
    saturn_house = chart.planets["Saturn"]["house"]
    jupiter_house = chart.planets["Jupiter"]["house"]
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    fifth_lord_house = chart.planets[chart.fifth_lord]["house"]
    eleventh_lord_house = chart.planets[chart.eleventh_lord]["house"]
    tenth_lord_house = chart.planets[chart.tenth_lord]["house"]
    lagna_lord_house = chart.planets[chart.lagna_lord]["house"]

    # Mars Navamsa for technology check
    mars_d9_sign = chart._get_d9_sign(chart.planets["Mars"]["longitude"])

    # ─── MODE DETECTION ───

    # Sole proprietorship: Sun in 7th (rejects partnerships)
    if sun_house == 7:
        fired_rules.append(("sole_proprietorship_sun_7th", "mode_sole", 0.90,
            "Sun in 7th house — strong ego rejects partnerships, sole proprietorship"))

    # Partnership: Venus in 7th
    if venus_house == 7:
        fired_rules.append(("partnership_venus_7th", "mode_partnership", 0.85,
            "Venus in 7th — luxury/partnership business model"))

    # Speculative: 5th-11th lord connection
    if fifth_lord_house == eleventh_lord_house or fifth_lord_house == 11 or eleventh_lord_house == 5:
        fired_rules.append(("speculative_5_11_connection", "mode_speculative", 0.80,
            f"5L-11L connection — speculative/investment business acumen"))

    # Technology: Mars in fiery/technical Navamsa
    if mars_d9_sign in [1, 5, 9]:  # Fire navamsas
        fired_rules.append(("technology_mars_navamsa", "mode_technology", 0.70,
            f"Mars in fire Navamsa ({SIGN_NAMES[mars_d9_sign]}) — technology/engineering business"))

    # Family business: Moon in 2nd
    if moon_house == 2:
        fired_rules.append(("family_business_moon_2nd", "mode_family", 0.75,
            "Moon in 2nd house — family business / inherited enterprise"))

    # Communications: Mercury in airy sign
    airy_signs = {3, 7, 11}  # Gemini, Libra, Aquarius
    if mercury_sign in airy_signs:
        fired_rules.append(("communications_mercury_airy", "mode_communications", 0.65,
            f"Mercury in airy sign ({SIGN_NAMES[mercury_sign]}) — communications/media business"))

    # Unconventional: Rahu in 1, 7, 10, or 11
    if rahu_house in [1, 7, 10, 11]:
        fired_rules.append(("unconventional_rahu_involvement", "mode_unconventional", 0.75,
            f"Rahu in house {rahu_house} — unconventional/disruptive business model"))

    # Industrial: Saturn in 10th
    if saturn_house == 10:
        fired_rules.append(("industrial_saturn_10th", "mode_industrial", 0.80,
            "Saturn in 10th — industrial/manufacturing/infrastructure business"))


    # ─── QUALITY DETECTION ───

    # Scalable: Chandra-Mangala in 11th
    if moon_house == 11 and mars_house == 11:
        fired_rules.append(("chandra_mangala_11th_scalable", "quality_scalable", 0.88,
            "Chandra-Mangala in 11th — highly scalable/viral business potential"))

    # Stable: Venus strong in 7th + Jupiter aspecting
    if venus_house == 7 and "Jupiter" in chart._get_aspectors_of_house(7):
        fired_rules.append(("venus_7th_luxury_stable", "quality_stable", 0.85,
            "Venus in 7th + Jupiter aspect — stable luxury/partnership business"))
    elif jupiter_house in [1, 4, 7, 10]:  # Jupiter in kendra
        fired_rules.append(("jupiter_kendra_stable", "quality_stable", 0.70,
            f"Jupiter in kendra house {jupiter_house} — general business stability"))

    # Administrator: Lagnesha in 3rd
    if lagna_lord_house == 3:
        fired_rules.append(("lagnesha_3rd_administrator", "quality_stable", 0.80,
            f"Lagna lord in 3rd — born administrator, stable management"))

    # Volatile: Mars-Rahu conjunction or aspect
    if mars_house == rahu_house:
        fired_rules.append(("mars_rahu_volatile", "quality_volatile", 0.82,
            "Mars+Rahu conjunction — volatile/aggressive business style"))

    # Painful: 10th lord in 6/8/12
    if tenth_lord_house in [6, 8, 12]:
        fired_rules.append(("tenth_lord_dusthana_painful", "quality_painful", 0.80,
            f"10th lord in dusthana house {tenth_lord_house} — business challenges/pain"))

    # Litigation prone: Saturn aspects 7th + Rahu in 7th or 10th
    if "Saturn" in chart._get_aspectors_of_house(7) and rahu_house in [7, 10]:
        fired_rules.append(("saturn_rahu_litigation", "quality_litigation", 0.78,
            "Saturn aspects 7th + Rahu in 7/10 — litigation-prone partnerships"))

    # Dhana Yoga: 2nd lord in 11th or 11th lord in 2nd
    second_lord_house = chart.planets[chart.second_lord]["house"]
    if second_lord_house == 11 or eleventh_lord_house == 2:
        fired_rules.append(("dhana_yoga_high_wealth", "quality_scalable", 0.90,
            "Dhana Yoga (2L-11L exchange) — high wealth generation potential"))

    # ═══════════════════════════════════════════════════════════
    # RESOLUTION (Layer 3 — calibration-based)
    # ═══════════════════════════════════════════════════════════
    cal = CALIBRATION.get("outcome_calibration", {})
    mode_priority = cal.get("mode_priority_order", [])
    quality_priority = cal.get("quality_priority_order", [])
    default_mode = cal.get("default_mode", "general_commerce")

    # Resolve MODE
    resolved_mode = "unknown"
    mode_rules = [r for r in fired_rules if r[1].startswith("mode_")]
    if mode_rules:
        def _mode_sort_key(rule):
            tag = rule[0]
            try:
                priority_idx = mode_priority.index(tag)
            except ValueError:
                priority_idx = 999
            return (priority_idx, -rule[2])

        mode_rules.sort(key=_mode_sort_key)
        best_mode_rule = mode_rules[0]
        mode_map = {
            "mode_sole": "sole_proprietorship",
            "mode_partnership": "partnership",
            "mode_speculative": "speculative",
            "mode_technology": "technology",
            "mode_family": "family_business",
            "mode_communications": "communications",
            "mode_unconventional": "unconventional",
            "mode_industrial": "industrial",
        }
        resolved_mode = mode_map.get(best_mode_rule[1], default_mode)
    else:
        resolved_mode = default_mode

    # Resolve QUALITY
    resolved_quality = "unknown"
    quality_rules = [r for r in fired_rules if r[1].startswith("quality_")]
    if quality_rules:
        def _quality_sort_key(rule):
            tag = rule[0]
            try:
                priority_idx = quality_priority.index(tag)
            except ValueError:
                priority_idx = 999
            return (priority_idx, -rule[2])

        quality_rules.sort(key=_quality_sort_key)
        best_quality_rule = quality_rules[0]
        quality_map = {
            "quality_scalable": "scalable",
            "quality_stable": "stable",
            "quality_volatile": "volatile",
            "quality_painful": "painful",
            "quality_litigation": "litigation_prone",
        }
        resolved_quality = quality_map.get(best_quality_rule[1], "unknown")
    else:
        resolved_quality = "unknown"

    results = {
        "mode": resolved_mode,
        "quality": resolved_quality,
        "fired_outcomes": [f"{r[0]}: {r[3]}" for r in fired_rules],
        "_classical_rules_fired": fired_rules,
        "_resolution_method": "calibration_priority_order",
        "_calibration_version": CALIBRATION.get("calibration_version", "unknown"),
    }

    return results



# ═══════════════════════════════════════════════════════════════
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE (Business)
# ═══════════════════════════════════════════════════════════════

class BusinessWindowResult:
    """Result of evaluating a single business time window."""

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
        """
        Compute total score from all layers.
        Weights and thresholds loaded from calibration overlay (Layer 3).
        Classical rules provide detection; calibration provides scoring.
        """
        dasha_score = sum(s for _, s, _ in self.dasha_fired)
        transit_score = sum(s for _, s, _ in self.transit_fired)
        fast_score = sum(s for _, s, _ in self.fast_trigger_fired)
        classical_boost = self.classical.get("confidence_boost", 0)

        # Layer weights from calibration (NOT hardcoded)
        lw = CALIBRATION["layer_weights"]
        self.total_score = (
            dasha_score * lw["dasha_weight"] +
            transit_score * lw["transit_weight"] +
            fast_score * lw["fast_trigger_weight"] +
            classical_boost * lw["classical_weight"]
        )

        # Determine timing band
        if fast_score > 20:
            self.timing_band = "exact"
        elif transit_score > 25:
            self.timing_band = "narrow"
        elif dasha_score > 20:
            self.timing_band = "broad"

        # Likelihood thresholds from calibration (NOT hardcoded)
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



def scan_business_windows(chart: ChartState, start_age=20, end_age=55, step_months=6):
    """
    Scan through life from start_age to end_age in step_months increments.
    Business is a lifecycle (not one event), so wider range: age 20-55.
    For each AD period in that range, evaluate the 5-layer engine.
    Returns sorted list of BusinessWindowResult.
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

        # Skip MDs entirely outside our age range
        if md_age_end < start_age or md_age_start > end_age:
            continue

        # Generate AD periods within this MD
        ad_periods = _generate_ad_periods(md)

        for ad in ad_periods:
            ad_age_start = (ad["start"] - chart.birth_dt).days / 365.25
            ad_age_end = (ad["end"] - chart.birth_dt).days / 365.25

            # Skip ADs outside our age range
            if ad_age_end < start_age or ad_age_start > end_age:
                continue

            # Effective window (clipped to age range)
            effective_start = max(ad["start"], chart.birth_dt + timedelta(days=start_age * 365.25))
            effective_end = min(ad["end"], chart.birth_dt + timedelta(days=end_age * 365.25))

            # LAYER 1: DASHA
            dasha_results = evaluate_dasha_layer(chart, md["lord"], ad["lord"])

            # If NO dasha rule fires, skip (gate)
            if not dasha_results:
                continue

            # LAYER 2: TRANSIT (evaluate at midpoint of AD period)
            mid_date = effective_start + (effective_end - effective_start) / 2
            transit = TransitState(mid_date, chart)
            transit_results = evaluate_transit_layer(chart, transit)

            # LAYER 3: FAST TRIGGER (same midpoint)
            fast_trigger_results = evaluate_fast_trigger_layer(chart, transit)

            # Also check transit at start and end of period
            transit_start = TransitState(effective_start, chart)
            transit_end = TransitState(effective_end, chart)

            transit_results_start = evaluate_transit_layer(chart, transit_start)
            transit_results_end = evaluate_transit_layer(chart, transit_end)

            # Merge transit results (take best from any point)
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
            result = BusinessWindowResult()
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

    # Sort by total score descending
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
    print("  5-LAYER BUSINESS RULE ENGINE — VEDIC TEXT BASED")
    print("  Native: 22 July 1975, 18:15 IST, Bhilai")
    print("=" * 80)

    # Build chart state
    chart = ChartState(BIRTH_DATE, BHILAI_LAT, BHILAI_LON, BHILAI_ALT)

    print(f"\n{'─' * 80}")
    print("  NATAL CHART SUMMARY (Business Focus)")
    print(f"{'─' * 80}")
    print(f"  Lagna: {SIGN_NAMES[chart.asc_sign]} | Lagna Lord: {chart.lagna_lord}")
    print(f"  Moon: {SIGN_NAMES[chart.moon_sign]} ({chart.moon_nakshatra})")
    print(f"  10th Lord: {chart.tenth_lord} (in house {chart.planets[chart.tenth_lord]['house']}, sign {SIGN_NAMES[chart.planets[chart.tenth_lord]['sign']]})")
    print(f"  11th Lord: {chart.eleventh_lord} (in house {chart.planets[chart.eleventh_lord]['house']})")
    print(f"  7th Lord: {chart.seventh_lord} (in house {chart.planets[chart.seventh_lord]['house']})")
    print(f"  2nd Lord: {chart.second_lord} (in house {chart.planets[chart.second_lord]['house']})")
    print(f"  3rd Lord: {chart.third_lord} (in house {chart.planets[chart.third_lord]['house']})")
    print(f"  Mercury: house {chart.planets['Mercury']['house']}, sign {SIGN_NAMES[chart.planets['Mercury']['sign']]}")
    print(f"  Jupiter: house {chart.planets['Jupiter']['house']}, sign {SIGN_NAMES[chart.planets['Jupiter']['sign']]}")
    print(f"  Saturn: house {chart.planets['Saturn']['house']}, sign {SIGN_NAMES[chart.planets['Saturn']['sign']]}")
    print(f"  Rahu: house {chart.planets['Rahu']['house']}, sign {SIGN_NAMES[chart.planets['Rahu']['sign']]}")
    print(f"  D9 Lagna: {SIGN_NAMES[chart.d9_asc_sign]} | D9 7th: {SIGN_NAMES[chart.d9_seventh_sign]}")
    print(f"  Sensitive Point 1 (Mercury+10L): {chart.sensitive_point_1:.2f}deg")
    print(f"  Sensitive Point 2 (11L+LagnaL): {chart.sensitive_point_2:.2f}deg")


    # Layer 4 & 5 (structural)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    print(f"\n{'─' * 80}")
    print("  LAYER 4: CLASSICAL PATTERNS (Structural — Business)")
    print(f"{'─' * 80}")
    print(f"  Timing Modifier: {classical['timing_modifier'].upper()}")
    print(f"  Confidence Boost: +{classical['confidence_boost']}")
    for p in classical["fired_patterns"]:
        print(f"    * {p}")
    if not classical["fired_patterns"]:
        print("    (No classical business patterns detected)")

    print(f"\n{'─' * 80}")
    print("  LAYER 5: OUTCOME / QUALITY (Business Classification)")
    print(f"{'─' * 80}")
    print(f"  Business Mode: {outcome['mode']}")
    print(f"  Business Quality: {outcome['quality']}")
    for o in outcome["fired_outcomes"]:
        print(f"    * {o}")

    # Scan business windows
    print(f"\n{'─' * 80}")
    print("  SCANNING BUSINESS WINDOWS (Age 20-55, step=6mo)...")
    print(f"{'─' * 80}")

    windows = scan_business_windows(chart, start_age=20, end_age=55, step_months=6)

    print(f"\n  Found {len(windows)} windows where dasha rules fired.")
    print(f"  Showing top 15 ranked by composite 5-layer score:\n")

    print(f"  {'#':<3} {'Period':<28} {'Age':<10} {'Score':<7} {'Band':<8} {'Likelihood':<12} {'MD-AD':<18}")
    print(f"  {'---':<3} {'---':<28} {'---':<10} {'---':<7} {'---':<8} {'---':<12} {'---':<18}")

    for i, w in enumerate(windows[:15], 1):
        period = f"{w.period_start.strftime('%b %Y')} - {w.period_end.strftime('%b %Y')}"
        age = f"{w.age_start:.1f}-{w.age_end:.1f}"
        md_ad = f"{w.md_lord}-{w.ad_lord}"
        print(f"  {i:<3} {period:<28} {age:<10} {w.total_score:<7.1f} {w.timing_band:<8} {w.likelihood:<12} {md_ad:<18}")


    # Detailed top 5
    print(f"\n{'=' * 80}")
    print("  TOP 5 BUSINESS WINDOWS — DETAILED 5-LAYER BREAKDOWN")
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
        print(f"\n  STRONGEST BUSINESS WINDOW:")
        print(f"  {top.period_start.strftime('%B %Y')} - {top.period_end.strftime('%B %Y')}")
        print(f"  Age {top.age_start:.1f}-{top.age_end:.1f} | {top.md_lord}-{top.ad_lord}")
        print(f"  Score: {top.total_score:.1f} | {top.likelihood}")
        print(f"\n  Business Mode: {outcome['mode']}")
        print(f"  Business Quality: {outcome['quality']}")
        print(f"\n  The 5-layer engine evaluated {len(windows)} AD periods with")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['high'])} HIGH+ confidence windows.")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['very_high'])} VERY_HIGH confidence windows.")
    print(f"\n{'=' * 80}")
