"""
Marriage Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow.
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
RULES_DIR = Path(__file__).resolve().parent / "domains" / "relationship" / "marriage"


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
                "dasha_weight": 0.40,
                "transit_weight": 0.35,
                "fast_trigger_weight": 0.20,
                "classical_weight": 0.05,
            },
            "likelihood_thresholds": {
                "very_high": 50,
                "high": 35,
                "moderate": 22,
                "low": 12,
            },
            "base_scores": {
                "dasha": {
                    "seventh_lord_md_or_ad": 40,
                    "seventh_house_occupant_md_or_ad": 35,
                    "seventh_house_aspector_md_or_ad": 25,
                    "second_lord_md_or_ad": 30,
                    "lagna_lord_md_plus_seventh_lord_ad": 45,
                    "natural_karaka_md": 25,
                    "natural_karaka_ad": 20,
                    "ninth_lord": 18,
                    "tenth_lord": 15,
                    "seventh_lord_dispositor": 20,
                    "second_lord_dispositor": 18,
                },
                "transit": {
                    "double_transit_lagna": 45,
                    "double_transit_moon": 35,
                    "jupiter_trine_7th_lord": 30,
                    "venus_trine_lagna_lord": 20,
                    "seventh_lord_trine_lagna_lord": 22,
                    "lagna_lord_in_7th": 28,
                    "jupiter_over_d9_lagna": 25,
                    "jupiter_over_d9_7th": 25,
                    "saturn_over_d9_lagna": 22,
                    "saturn_over_d9_7th": 22,
                    "sensitive_point_1_activation": 35,
                    "sensitive_point_2_activation": 28,
                },
                "fast_trigger": {
                    "moon_in_7th_or_9th": 20,
                    "mars_in_7th_or_9th": 22,
                    "jupiter_exact_sensitive_point_1": 40,
                    "jupiter_trine_sensitive_point_1": 32,
                    "jupiter_exact_sensitive_point_2": 35,
                },
            },
            "outcome_calibration": {
                "mode_priority_order": [
                    "venus_mars_conjunction",
                    "5L_7L_9L_connection",
                    "venus_mars_aspect",
                    "rahu_on_1_7_axis",
                    "saturn_7th_influence",
                    "jupiter_7th_default",
                ],
                "quality_priority_order": [
                    "venus_double_debilitated",
                    "7L_dusthana",
                    "kuja_dosha_active",
                    "venus_mars_volatile",
                    "venus_saturn_stable",
                    "jupiter_aspect_7th",
                    "7L_kendra_stable",
                ],
                "default_mode": "arranged",
            },
        }


# Module-level calibration (loaded once at import)
CALIBRATION = _load_calibration()



# ═══════════════════════════════════════════════════════════════
# CHART STATE BUILDER
# ═══════════════════════════════════════════════════════════════

class ChartState(BaseChartState):
    """
    Marriage-domain chart state.
    Extends BaseChartState with marriage-specific house lords,
    D9 calculations, and sensitive points.

    API is identical to the pre-refactor class — all callers
    (career_evaluator, childbirth_evaluator, etc.) continue to work.
    """

    def __init__(self, birth_dt, lat, lon, alt=0):
        super().__init__(birth_dt, lat, lon, alt)

        # Marriage-specific house lords
        self.seventh_sign  = ((self.asc_sign + 6 - 1) % 12) + 1
        self.seventh_lord  = SIGN_LORDS[self.seventh_sign]
        self.second_sign   = ((self.asc_sign + 1 - 1) % 12) + 1
        self.second_lord   = SIGN_LORDS[self.second_sign]
        self.ninth_sign    = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord    = SIGN_LORDS[self.ninth_sign]
        self.tenth_sign    = ((self.asc_sign + 9 - 1) % 12) + 1
        self.tenth_lord    = SIGN_LORDS[self.tenth_sign]
        self.eleventh_sign = ((self.asc_sign + 10 - 1) % 12) + 1
        self.eleventh_lord = SIGN_LORDS[self.eleventh_sign]

        # Planets in / aspecting 7th house
        self.seventh_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 7
        ]
        self.seventh_house_aspectors = self._get_aspectors_of_house(7)

        # Dispositors
        second_lord_sign = self.planets[self.second_lord]["sign"]
        self.second_lord_dispositor = SIGN_LORDS[second_lord_sign]

        seventh_lord_sign = self.planets[self.seventh_lord]["sign"]
        self.seventh_lord_dispositor = SIGN_LORDS[seventh_lord_sign]

        # Navamsa (D9)
        self.d9_asc_sign     = self._compute_d9_lagna()
        self.d9_seventh_sign = ((self.d9_asc_sign + 6 - 1) % 12) + 1
        self.seventh_lord_d9_sign = self._get_d9_sign(
            self.birth_positions[self.seventh_lord]
        )
        self.seventh_lord_d9_dispositor = SIGN_LORDS[self.seventh_lord_d9_sign]

        # Janma Nakshatra Lord
        nak_index = int((self.moon_lon % 360) / 13.3333333333)
        self.janma_nakshatra_lord = NAKSHATRA_LORDS[nak_index % 27]

        # Sensitive Marriage Points
        lagna_lord_lon  = self.birth_positions[self.lagna_lord]
        seventh_lord_lon = self.birth_positions[self.seventh_lord]
        self.sensitive_point_1 = (lagna_lord_lon + seventh_lord_lon) % 360

        nakshatra_lord_lon = self.birth_positions[self.janma_nakshatra_lord]
        self.sensitive_point_2 = (nakshatra_lord_lon + seventh_lord_lon) % 360



# ═══════════════════════════════════════════════════════════════
# TRANSIT STATE (computed for a specific date)
# ═══════════════════════════════════════════════════════════════

class TransitState(BaseTransitState):
    """
    Transit state for marriage-domain evaluation.
    Thin subclass of BaseTransitState — no additional logic needed.
    Kept as a named class so existing imports of TransitState from
    this module continue to work unchanged.
    """
    pass



# ═══════════════════════════════════════════════════════════════
# LAYER 1: DASHA EVALUATOR
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate all dasha rules against current MD/AD combination.
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Collect marriage-significant planets
    primary_planets = set()
    primary_planets.add(chart.seventh_lord)           # 7th lord
    primary_planets.update(chart.seventh_house_occupants)  # occupants of 7th
    primary_planets.update(chart.seventh_house_aspectors)  # aspectors of 7th
    primary_planets.add(chart.second_lord)            # 2nd lord
    primary_planets.add(chart.lagna_lord)             # Lagna lord

    karaka_planets = {"Venus", "Rahu", "Moon"}
    alternative_planets = {
        chart.seventh_lord_dispositor,
        chart.second_lord_dispositor,
        chart.ninth_lord,
        chart.tenth_lord,
    }

    # Rule 1: Primary marriage triggers (priority 98)
    r1_score = 0
    r1_reasons = []

    if md_lord == chart.seventh_lord or ad_lord == chart.seventh_lord:
        r1_score += 40
        r1_reasons.append(f"{'MD' if md_lord == chart.seventh_lord else 'AD'} of 7th lord ({chart.seventh_lord})")

    if md_lord in chart.seventh_house_occupants or ad_lord in chart.seventh_house_occupants:
        r1_score += 35
        occ = md_lord if md_lord in chart.seventh_house_occupants else ad_lord
        r1_reasons.append(f"{'MD' if occ == md_lord else 'AD'} of 7th house occupant ({occ})")

    if md_lord in chart.seventh_house_aspectors or ad_lord in chart.seventh_house_aspectors:
        r1_score += 25
        asp = md_lord if md_lord in chart.seventh_house_aspectors else ad_lord
        r1_reasons.append(f"{'MD' if asp == md_lord else 'AD'} of 7th house aspector ({asp})")

    if md_lord == chart.second_lord or ad_lord == chart.second_lord:
        r1_score += 30
        r1_reasons.append(f"{'MD' if md_lord == chart.second_lord else 'AD'} of 2nd lord ({chart.second_lord})")

    if md_lord == chart.lagna_lord and ad_lord == chart.seventh_lord:
        r1_score += 45
        r1_reasons.append(f"MD of Lagna lord ({chart.lagna_lord}) + AD of 7th lord ({chart.seventh_lord})")

    if r1_score > 0:
        fired.append(("jyothishi_dasha_primary_marriage_triggers", r1_score, r1_reasons))

    # Rule 2: Natural karakas (priority 85)
    r2_score = 0
    r2_reasons = []

    if md_lord in karaka_planets:
        r2_score += 25
        r2_reasons.append(f"MD of natural karaka {md_lord}")
    if ad_lord in karaka_planets:
        r2_score += 20
        r2_reasons.append(f"AD of natural karaka {ad_lord}")

    if r2_score > 0:
        fired.append(("jyothishi_dasha_natural_karakas", r2_score, r2_reasons))

    # Rule 3: Alternative lords (priority 80)
    r3_score = 0
    r3_reasons = []

    if md_lord in alternative_planets or ad_lord in alternative_planets:
        if md_lord == chart.ninth_lord or ad_lord == chart.ninth_lord:
            r3_score += 18
            r3_reasons.append(f"Period of 9th lord ({chart.ninth_lord})")
        if md_lord == chart.tenth_lord or ad_lord == chart.tenth_lord:
            r3_score += 15
            r3_reasons.append(f"Period of 10th lord ({chart.tenth_lord})")
        if md_lord == chart.seventh_lord_dispositor or ad_lord == chart.seventh_lord_dispositor:
            r3_score += 20
            r3_reasons.append(f"Period of 7th lord dispositor ({chart.seventh_lord_dispositor})")
        if md_lord == chart.second_lord_dispositor or ad_lord == chart.second_lord_dispositor:
            r3_score += 18
            r3_reasons.append(f"Period of 2nd lord dispositor ({chart.second_lord_dispositor})")

    if r3_score > 0:
        fired.append(("jataka_parijata_dasha_alternative_lords", r3_score, r3_reasons))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate transit rules against current planetary positions.
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Rule 1: Double Transit (priority 98)
    # Jupiter and Saturn must BOTH influence 1-7 axis
    jup_on_7_lagna = transit.planet_aspects_house("Jupiter", 7, "lagna")
    jup_on_1_lagna = transit.planet_aspects_house("Jupiter", 1, "lagna")
    sat_on_7_lagna = transit.planet_aspects_house("Saturn", 7, "lagna")
    sat_on_1_lagna = transit.planet_aspects_house("Saturn", 1, "lagna")

    jup_on_7_moon = transit.planet_aspects_house("Jupiter", 7, "moon")
    sat_on_7_moon = transit.planet_aspects_house("Saturn", 7, "moon")

    double_transit_lagna = (jup_on_7_lagna or jup_on_1_lagna) and (sat_on_7_lagna or sat_on_1_lagna)
    double_transit_moon = jup_on_7_moon and sat_on_7_moon

    dt_score = 0
    dt_reasons = []
    if double_transit_lagna:
        dt_score += 45
        dt_reasons.append("Double transit (Jup+Sat) on 1-7 axis from Lagna")
    if double_transit_moon:
        dt_score += 35
        dt_reasons.append("Double transit (Jup+Sat) on 7th from Moon")

    if dt_score > 0:
        fired.append(("jyothishi_double_transit_marriage", dt_score, dt_reasons))

    # Rule 2: Jupiter trine to 7th lord's natal sign (priority 90)
    seventh_lord_sign = chart.planets[chart.seventh_lord]["sign"]
    jup_transit_sign = transit.planet_signs["Jupiter"]
    trine_signs = [seventh_lord_sign, ((seventh_lord_sign + 4 - 1) % 12) + 1,
                   ((seventh_lord_sign + 8 - 1) % 12) + 1]

    if jup_transit_sign in trine_signs:
        score = 30
        reasons = [f"Transit Jupiter in {SIGN_NAMES[jup_transit_sign]} (trine to 7th lord's natal {SIGN_NAMES[seventh_lord_sign]})"]
        fired.append(("phaladeepika_transit_jupiter_trine_7th_lord", score, reasons))

    # Rule 3: Transit Venus/7th lord trine to Lagna lord's sign (priority 85)
    lagna_lord_sign = chart.planets[chart.lagna_lord]["sign"]
    lagna_trines = [lagna_lord_sign, ((lagna_lord_sign + 4 - 1) % 12) + 1,
                    ((lagna_lord_sign + 8 - 1) % 12) + 1]

    venus_transit_sign = transit.planet_signs["Venus"]
    seventh_lord_transit_sign = transit.planet_signs.get(chart.seventh_lord)

    vt_score = 0
    vt_reasons = []
    if venus_transit_sign in lagna_trines:
        vt_score += 20
        vt_reasons.append(f"Transit Venus trine to Lagna lord's sign ({SIGN_NAMES[lagna_lord_sign]})")
    if seventh_lord_transit_sign and seventh_lord_transit_sign in lagna_trines:
        vt_score += 22
        vt_reasons.append(f"Transit 7th lord trine to Lagna lord's sign")

    if vt_score > 0:
        fired.append(("phaladeepika_transit_venus_7th_lord", vt_score, vt_reasons))

    # Rule 4: Lagna lord transits 7th house sign (priority 82)
    lagna_lord_transit_sign = transit.planet_signs.get(chart.lagna_lord)
    if lagna_lord_transit_sign == chart.seventh_sign:
        fired.append(("phaladeepika_transit_lagna_lord_7th", 28,
                      [f"Transit Lagna lord ({chart.lagna_lord}) in 7th house sign ({SIGN_NAMES[chart.seventh_sign]})"]))

    # Rule 5: Jupiter/Saturn over D9 Lagna or 7th (priority 88)
    d9_score = 0
    d9_reasons = []
    if jup_transit_sign == chart.d9_asc_sign:
        d9_score += 25
        d9_reasons.append(f"Transit Jupiter over D9 Lagna ({SIGN_NAMES[chart.d9_asc_sign]})")
    if jup_transit_sign == chart.d9_seventh_sign:
        d9_score += 25
        d9_reasons.append(f"Transit Jupiter over D9 7th ({SIGN_NAMES[chart.d9_seventh_sign]})")
    sat_transit_sign = transit.planet_signs["Saturn"]
    if sat_transit_sign == chart.d9_asc_sign:
        d9_score += 22
        d9_reasons.append(f"Transit Saturn over D9 Lagna ({SIGN_NAMES[chart.d9_asc_sign]})")
    if sat_transit_sign == chart.d9_seventh_sign:
        d9_score += 22
        d9_reasons.append(f"Transit Saturn over D9 7th ({SIGN_NAMES[chart.d9_seventh_sign]})")

    if d9_score > 0:
        fired.append(("jyothishi_navamsa_transit_trigger", d9_score, d9_reasons))

    # Rule 6: Sensitive point 1 (priority 92)
    if transit.jupiter_trine_degree(chart.sensitive_point_1, orb=2.5):
        fired.append(("jyothishi_longitude_sum_lagna_7th", 35,
                      [f"Transit Jupiter activating sensitive point 1 ({chart.sensitive_point_1:.1f}°)"]))

    # Rule 7: Sensitive point 2 (priority 88)
    if transit.jupiter_trine_degree(chart.sensitive_point_2, orb=2.5):
        fired.append(("jyothishi_longitude_sum_nakshatra_7th", 28,
                      [f"Transit Jupiter activating sensitive point 2 ({chart.sensitive_point_2:.1f}°)"]))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate fast trigger rules (Moon, Mars, Jupiter degree hits).
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Rule 1: Moon in 7th or 9th house (priority 95)
    moon_house = transit.planet_houses_from_lagna.get("Moon", 0)
    if moon_house in [7, 9]:
        fired.append(("fast_trigger_moon_72_days", 20,
                      [f"Transit Moon in house {moon_house} (72-day trigger)"]))

    # Rule 2: Mars in 7th or 9th house (priority 90)
    mars_house = transit.planet_houses_from_lagna.get("Mars", 0)
    if mars_house in [7, 9]:
        fired.append(("fast_trigger_mars_2_months", 22,
                      [f"Transit Mars in house {mars_house} (2-month trigger)"]))

    # Rule 3: Jupiter exact hit on sensitive point 1 (priority 97)
    if transit.jupiter_on_degree(chart.sensitive_point_1, orb=1.5):
        fired.append(("exact_longitude_sum_lagna_7th", 40,
                      [f"Jupiter EXACT on sensitive point 1 ({chart.sensitive_point_1:.1f}°)"]))
    # Also check trines/opposition
    jup_lon = transit.positions["Jupiter"]
    for offset in [120, 240, 180]:
        target = (chart.sensitive_point_1 + offset) % 360
        diff = abs((jup_lon - target) % 360)
        diff = min(diff, 360 - diff)
        if diff <= 1.5:
            fired.append(("exact_longitude_sum_lagna_7th", 32,
                          [f"Jupiter trine/opp sensitive point 1 (offset {offset}°)"]))
            break

    # Rule 4: Jupiter exact hit on sensitive point 2 (priority 93)
    if transit.jupiter_on_degree(chart.sensitive_point_2, orb=1.5):
        fired.append(("exact_longitude_sum_nakshatra_7th", 35,
                      [f"Jupiter EXACT on sensitive point 2 ({chart.sensitive_point_2:.1f}°)"]))

    return fired


# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """
    Evaluate classical patterns (structural — not time-dependent).
    Returns dict with timing_modifier and confidence_adjustment.
    """
    results = {
        "timing_modifier": "normal",  # early, normal, delayed
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    seventh_lord_house = chart.planets[chart.seventh_lord]["house"]
    venus_house = chart.planets["Venus"]["house"]
    venus_sign = chart.planets["Venus"]["sign"]

    # Check for early marriage indicators
    venus_exalted = venus_sign == 12  # Pisces
    venus_own = venus_sign in [2, 7]  # Taurus, Libra
    seventh_lord_in_benefic = seventh_lord_house in BENEFIC_HOUSES

    if (venus_exalted or venus_own) and seventh_lord_in_benefic:
        results["timing_modifier"] = "early"
        results["confidence_boost"] += 10
        results["fired_patterns"].append("bphs_early_marriage_venus_exalted: Venus strong + 7L in benefic house")

    # Venus in 2nd + 7th lord in 11th
    seventh_lord_house_val = chart.planets[chart.seventh_lord]["house"]
    if venus_house == 2 and seventh_lord_house_val == 11:
        results["timing_modifier"] = "early"
        results["confidence_boost"] += 8
        results["fired_patterns"].append("bphs_early_marriage_venus_2nd_7th_11th")

    # Delayed: 8th lord in 7th
    eighth_sign = ((chart.asc_sign + 7 - 1) % 12) + 1
    eighth_lord = SIGN_LORDS[eighth_sign]
    if chart.planets[eighth_lord]["house"] == 7:
        results["timing_modifier"] = "delayed"
        results["confidence_boost"] -= 8
        results["fired_patterns"].append(f"bphs_delayed_marriage_8th_7th: {eighth_lord} (8L) in 7th house")

    # Delayed: Venus in 5th + Rahu in 5th/9th
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    if venus_house == 5 and rahu_house in [5, 9]:
        results["timing_modifier"] = "delayed"
        results["confidence_boost"] -= 5
        results["fired_patterns"].append("bphs_delayed_marriage_venus_rahu_5th_9th")

    # Normal: 7th lord in 12th + Lagna lord in D9 7th
    lagna_lord_d9 = chart._get_d9_sign(chart.birth_positions[chart.lagna_lord])
    if seventh_lord_house == 12 and lagna_lord_d9 == chart.d9_seventh_sign:
        results["timing_modifier"] = "normal"
        results["confidence_boost"] += 5
        results["fired_patterns"].append("bphs_normal_marriage_7th_12th_navamsa")

    return results



# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """
    Evaluate outcome/quality rules (structural — what kind of marriage).

    ARCHITECTURE (per calibration philosophy):
      Step 1: DETECT all classical rules that fire (Layer 1 — immutable)
      Step 2: RESOLVE conflicts using calibration priority order (Layer 3 — adjustable)

    Classical rules are NEVER overwritten. Calibration resolves ambiguity.
    """
    # ═══════════════════════════════════════════════════════════
    # STEP 1: CLASSICAL RULE DETECTION (Layer 1 — immutable)
    # Each detected rule is tagged with its source and confidence.
    # No scoring, no conflict resolution, no final assignment here.
    # ═══════════════════════════════════════════════════════════
    fired_rules = []  # List of (tag, category, confidence, description)

    fifth_sign = ((chart.asc_sign + 4 - 1) % 12) + 1
    fifth_lord = SIGN_LORDS[fifth_sign]
    fifth_lord_house = chart.planets[fifth_lord]["house"]
    fifth_lord_sign = chart.planets[fifth_lord]["sign"]
    seventh_lord_house = chart.planets[chart.seventh_lord]["house"]
    seventh_lord_sign = chart.planets[chart.seventh_lord]["sign"]
    ninth_lord_house = chart.planets[chart.ninth_lord]["house"]
    ninth_lord_sign = chart.planets[chart.ninth_lord]["sign"]

    venus_house = chart.planets["Venus"]["house"]
    venus_sign = chart.planets["Venus"]["sign"]
    saturn_house = chart.planets["Saturn"]["house"]
    mars_house = chart.planets["Mars"]["house"]
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    jupiter_house = chart.planets["Jupiter"]["house"]
    moon_house = chart.planets["Moon"]["house"]

    def _planet_aspects_planet(p1_house, p2_house, p1_name=""):
        """Check if planet at p1_house aspects p2_house (Vedic aspects)."""
        aspected = [((p1_house + 6) % 12) + 1]
        if p1_name == "Jupiter":
            aspected.extend([((p1_house + 4) % 12) + 1, ((p1_house + 8) % 12) + 1])
        elif p1_name == "Saturn":
            aspected.extend([((p1_house + 2) % 12) + 1, ((p1_house + 9) % 12) + 1])
        elif p1_name == "Mars":
            aspected.extend([((p1_house + 3) % 12) + 1, ((p1_house + 7) % 12) + 1])
        return p2_house in aspected

    # ─── PROMISE DETECTION ───
    if seventh_lord_house == 7:
        fired_rules.append(("strong_promise", "promise", 0.95,
            f"7th lord ({chart.seventh_lord}) in OWN 7th house"))
    if chart.seventh_lord == "Saturn" and seventh_lord_sign == 7:
        fired_rules.append(("strong_promise", "promise", 0.90,
            f"7th lord ({chart.seventh_lord}) exalted in Libra"))
    if len(chart.seventh_house_occupants) >= 2:
        fired_rules.append(("strong_promise", "promise", 0.88,
            f"Multiple planets in 7th house ({', '.join(chart.seventh_house_occupants)})"))
    if venus_house == 8:
        if saturn_house == 8 or chart.planets["Mercury"]["house"] == 8:
            fired_rules.append(("weak_promise", "promise", 0.85,
                "Venus in 8th with Saturn/Mercury (JYOTHISHI denial rule)"))
    if venus_sign == 6:  # Virgo = debilitated
        venus_d9_sign = chart._get_d9_sign(chart.planets["Venus"]["longitude"])
        if venus_d9_sign == 6:
            fired_rules.append(("weak_promise", "promise", 0.85,
                "Venus debilitated in BOTH D1 and D9"))

    # ─── MODE DETECTION: LOVE indicators ───
    lords_houses = [fifth_lord_house, seventh_lord_house, ninth_lord_house]
    if len(set(lords_houses)) < 3:
        fired_rules.append(("5L_7L_9L_connection", "mode_love", 0.90,
            "5L/7L/9L conjunct (same house) — JYOTHISHI love marriage rule"))
    lords_signs = [fifth_lord_sign, seventh_lord_sign, ninth_lord_sign]
    if len(set(lords_signs)) < 3:
        fired_rules.append(("5L_7L_9L_connection", "mode_love", 0.85,
            "5L/7L/9L in same sign"))

    if _planet_aspects_planet(fifth_lord_house, seventh_lord_house, fifth_lord):
        fired_rules.append(("venus_mars_aspect", "mode_love", 0.70,
            f"5L ({fifth_lord}, H{fifth_lord_house}) aspects 7L ({chart.seventh_lord}, H{seventh_lord_house})"))
    elif _planet_aspects_planet(seventh_lord_house, fifth_lord_house, chart.seventh_lord):
        fired_rules.append(("venus_mars_aspect", "mode_love", 0.70,
            f"7L ({chart.seventh_lord}, H{seventh_lord_house}) aspects 5L ({fifth_lord}, H{fifth_lord_house})"))

    # Venus-Mars conjunction (STRONGEST love indicator per AstroSight)
    if venus_house == mars_house:
        fired_rules.append(("venus_mars_conjunction", "mode_love", 0.92,
            "Venus+Mars same house (passionate love)"))
    elif _planet_aspects_planet(mars_house, venus_house, "Mars"):
        fired_rules.append(("venus_mars_aspect", "mode_love", 0.65,
            "Mars aspects Venus (passion in relationships — aspect only, weaker)"))

    # Venus-Moon connection (love/emotional bond)
    if venus_house == moon_house:
        fired_rules.append(("venus_moon_connection", "mode_love", 0.75,
            "Venus+Moon same house (emotional romance)"))
    elif _planet_aspects_planet(venus_house, moon_house, "Venus"):
        fired_rules.append(("venus_moon_connection", "mode_love", 0.60,
            "Venus aspects Moon (romantic emotional nature)"))

    # ─── MODE DETECTION: MIXED/UNCONVENTIONAL indicators ───
    if rahu_house in [1, 7]:
        fired_rules.append(("rahu_on_1_7_axis", "mode_mixed", 0.85,
            f"Rahu in house {rahu_house} — JYOTHISHI intercaste rule"))
    elif ((rahu_house + 6) % 12) + 1 == 7:
        fired_rules.append(("rahu_on_1_7_axis", "mode_mixed", 0.70,
            f"Rahu (H{rahu_house}) aspects 7th house"))

    # ─── MODE DETECTION: ARRANGED indicators ───
    if saturn_house == 7 or "Saturn" in chart.seventh_house_aspectors:
        fired_rules.append(("saturn_7th_influence", "mode_arranged", 0.75,
            "Saturn connected to 7th house (traditional/arranged tendency)"))
    if (jupiter_house == 7 or "Jupiter" in chart.seventh_house_aspectors):
        # Only fire as arranged if NO love indicators present
        fired_rules.append(("jupiter_7th_default", "mode_arranged", 0.55,
            "Jupiter blesses 7th without romance axis (arranged tendency — weak)"))

    # ─── QUALITY DETECTION ───
    if "Jupiter" in chart.seventh_house_aspectors:
        fired_rules.append(("jupiter_aspect_7th", "quality_stable", 0.88,
            "Jupiter aspects 7th house (benefic protection, good marriage)"))
    if venus_house == saturn_house:
        fired_rules.append(("venus_saturn_stable", "quality_stable", 0.85,
            "Venus+Saturn same house (delayed but very stable)"))
    elif _planet_aspects_planet(venus_house, saturn_house, "Venus") or \
         _planet_aspects_planet(saturn_house, venus_house, "Saturn"):
        fired_rules.append(("venus_saturn_stable", "quality_stable", 0.75,
            "Venus-Saturn mutual aspect (mature, committed partnership)"))

    if venus_house == mars_house:
        fired_rules.append(("venus_mars_volatile", "quality_unstable", 0.80,
            "Venus+Mars same house (volatile quality)"))
    elif _planet_aspects_planet(mars_house, venus_house, "Mars"):
        fired_rules.append(("venus_mars_volatile", "quality_unstable", 0.55,
            "Mars aspects Venus (mild volatility — aspect only)"))

    if seventh_lord_house in [1, 4, 7, 10]:
        fired_rules.append(("7L_kendra_stable", "quality_stable", 0.80,
            f"7th lord in kendra house {seventh_lord_house} (strong foundation)"))
    if seventh_lord_house in [6, 8, 12]:
        fired_rules.append(("7L_dusthana", "quality_painful", 0.82,
            f"7th lord in dusthana house {seventh_lord_house} (challenges)"))

    # Kuja Dosha
    if mars_house in [1, 2, 4, 7, 8, 12]:
        mars_sign = chart.planets["Mars"]["sign"]
        cancelled = mars_sign in [1, 8, 10] or "Jupiter" in chart._get_aspectors_of_house(mars_house)
        if cancelled:
            fired_rules.append(("kuja_dosha_cancelled", "quality_note", 0.70,
                f"Kuja Dosha in H{mars_house} but CANCELLED (own/exalted sign or Jupiter aspect)"))
        else:
            fired_rules.append(("kuja_dosha_active", "quality_conflict", 0.80,
                f"Kuja Dosha: Mars in house {mars_house} (marital friction)"))

    # ─── SECOND MARRIAGE ───
    dual_signs = {3, 6, 9, 12}
    if seventh_lord_sign in dual_signs and venus_sign in dual_signs:
        fired_rules.append(("dual_signs_d1", "second_marriage", 0.75,
            "7L and Venus both in dual signs in D1"))
    venus_d9 = chart._get_d9_sign(chart.planets["Venus"]["longitude"])
    seventh_lord_d9 = chart.seventh_lord_d9_sign
    if seventh_lord_d9 in dual_signs and venus_d9 in dual_signs:
        fired_rules.append(("dual_signs_d9", "second_marriage", 0.80,
            "7L and Venus both in dual signs in D9"))

    # ─── DHARMA CONNECTION ───
    if _planet_aspects_planet(seventh_lord_house, ninth_lord_house, chart.seventh_lord):
        fired_rules.append(("dharma_connect", "quality_note", 0.70,
            "7L aspects 9L (marriage blessed by dharma)"))
    elif _planet_aspects_planet(ninth_lord_house, seventh_lord_house, chart.ninth_lord):
        fired_rules.append(("dharma_connect", "quality_note", 0.70,
            "9L aspects 7L (dharma blesses marriage)"))

    # 7th lord in trikona
    if seventh_lord_house in [5, 9]:
        fired_rules.append(("7L_trikona", "quality_note", 0.75,
            f"7th lord in trikona house {seventh_lord_house} (dharmic marriage)"))

    # ═══════════════════════════════════════════════════════════
    # STEP 2: CALIBRATION-BASED RESOLUTION (Layer 3 — adjustable)
    # Uses priority orders from calibration_overlay.json to resolve
    # conflicts when multiple rules fire for the same dimension.
    # ═══════════════════════════════════════════════════════════
    cal = CALIBRATION.get("outcome_calibration", {})
    mode_priority = cal.get("mode_priority_order", [])
    quality_priority = cal.get("quality_priority_order", [])
    default_mode = cal.get("default_mode", "unknown")

    # Resolve MODE
    resolved_mode = "unknown"
    mode_rules = [r for r in fired_rules if r[1].startswith("mode_")]
    if mode_rules:
        # Sort by calibration priority order, then by confidence
        def _mode_sort_key(rule):
            tag = rule[0]
            try:
                priority_idx = mode_priority.index(tag)
            except ValueError:
                priority_idx = 999
            return (priority_idx, -rule[2])  # lower index = higher priority, higher confidence wins ties

        mode_rules.sort(key=_mode_sort_key)
        best_mode_rule = mode_rules[0]
        if best_mode_rule[1] == "mode_love":
            resolved_mode = "love"
        elif best_mode_rule[1] == "mode_mixed":
            resolved_mode = "mixed"
        elif best_mode_rule[1] == "mode_arranged":
            resolved_mode = "arranged"
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
        if "stable" in best_quality_rule[1]:
            resolved_quality = "stable"
        elif "unstable" in best_quality_rule[1] or "volatile" in best_quality_rule[1]:
            resolved_quality = "unstable"
        elif "painful" in best_quality_rule[1]:
            resolved_quality = "painful"
        elif "conflict" in best_quality_rule[1]:
            resolved_quality = "conflict_prone"
    else:
        resolved_quality = "unknown"

    # Resolve PROMISE
    promise_rules = [r for r in fired_rules if r[1] == "promise"]
    resolved_promise = "unknown"
    if promise_rules:
        # Strong overrides weak unless weak has higher confidence
        strong = [r for r in promise_rules if r[0] == "strong_promise"]
        weak = [r for r in promise_rules if r[0] == "weak_promise"]
        if weak and not strong:
            resolved_promise = "weak"
        elif strong:
            resolved_promise = "strong"

    # Second marriage risk
    second_marriage = any(r[1] == "second_marriage" for r in fired_rules)

    # ═══════════════════════════════════════════════════════════
    # COMPOSE FINAL RESULT
    # ═══════════════════════════════════════════════════════════
    results = {
        "mode": resolved_mode,
        "quality": resolved_quality,
        "second_marriage_risk": second_marriage,
        "marriage_promise": resolved_promise,
        "fired_outcomes": [f"{r[0]}: {r[3]}" for r in fired_rules],
        # Preserve raw fired rules for traceability
        "_classical_rules_fired": fired_rules,
        "_resolution_method": "calibration_priority_order",
        "_calibration_version": CALIBRATION.get("calibration_version", "unknown"),
    }

    return results



# ═══════════════════════════════════════════════════════════════
# INTRA-DASHA TIMING REFINEMENT (Jataka Parijata rule)
# ═══════════════════════════════════════════════════════════════

def refine_timing_within_dasha(chart: ChartState, md_lord: str, ad_lord: str, ad_start, ad_end):
    """
    Jataka Parijata 14:30 — Benefic in benefic house = early in dasha,
    Benefic in malefic house = middle, Malefic in malefic = late.

    Classical Rule (Layer 1): Determines WHICH segment of the dasha period.
    The rule itself is immutable from Jataka Parijata Ch.14 V.30.

    Returns (refined_start, refined_end, segment_label).
    """
    duration = ad_end - ad_start
    third = duration / 3

    # Check nature of the AD lord (as it's the narrower period)
    is_benefic = ad_lord in NATURAL_BENEFICS
    lord_house = chart.planets.get(ad_lord, {}).get("house", 1)
    in_benefic_house = lord_house in BENEFIC_HOUSES

    if is_benefic and in_benefic_house:
        # Early in dasha
        return ad_start, ad_start + third, "early"
    elif is_benefic and not in_benefic_house:
        # Middle of dasha
        return ad_start + third, ad_start + 2 * third, "middle"
    else:
        # Late in dasha (malefic or malefic in malefic house)
        return ad_start + 2 * third, ad_end, "late"


# ═══════════════════════════════════════════════════════════════
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE
# ═══════════════════════════════════════════════════════════════

class MarriageWindowResult:
    """Result of evaluating a single time window."""

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



def scan_marriage_windows(chart: ChartState, start_age=18, end_age=36, step_months=3):
    """
    Scan through life from start_age to end_age in step_months increments.
    For each AD period in that range, evaluate the 5-layer engine.
    Returns sorted list of MarriageWindowResult.
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

            # Also check transit at start and end of period for more coverage
            transit_start = TransitState(effective_start, chart)
            transit_end = TransitState(effective_end, chart)

            transit_results_start = evaluate_transit_layer(chart, transit_start)
            transit_results_end = evaluate_transit_layer(chart, transit_end)

            # Merge transit results (take best from any point in the window)
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
            result = MarriageWindowResult()
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
    print("  5-LAYER MARRIAGE RULE ENGINE — VEDIC TEXT BASED")
    print("  Native: 22 July 1975, 18:15 IST, Bhilai")
    print("=" * 80)

    # Build chart state
    chart = ChartState(BIRTH_DATE, BHILAI_LAT, BHILAI_LON, BHILAI_ALT)

    print(f"\n{'─' * 80}")
    print("  NATAL CHART SUMMARY")
    print(f"{'─' * 80}")
    print(f"  Lagna: {SIGN_NAMES[chart.asc_sign]} | Lagna Lord: {chart.lagna_lord}")
    print(f"  Moon: {SIGN_NAMES[chart.moon_sign]} ({chart.moon_nakshatra})")
    print(f"  7th Lord: {chart.seventh_lord} (in house {chart.planets[chart.seventh_lord]['house']}, sign {SIGN_NAMES[chart.planets[chart.seventh_lord]['sign']]})")
    print(f"  2nd Lord: {chart.second_lord} (in house {chart.planets[chart.second_lord]['house']})")
    print(f"  7th House Occupants: {chart.seventh_house_occupants or 'None'}")
    print(f"  7th House Aspectors: {chart.seventh_house_aspectors or 'None'}")
    print(f"  D9 Lagna: {SIGN_NAMES[chart.d9_asc_sign]} | D9 7th: {SIGN_NAMES[chart.d9_seventh_sign]}")
    print(f"  Sensitive Point 1 (LL+7L): {chart.sensitive_point_1:.2f}°")
    print(f"  Sensitive Point 2 (NakL+7L): {chart.sensitive_point_2:.2f}°")
    print(f"  Janma Nakshatra Lord: {chart.janma_nakshatra_lord}")

    # Layer 4 & 5 (structural)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    print(f"\n{'─' * 80}")
    print("  LAYER 4: CLASSICAL PATTERNS (Structural)")
    print(f"{'─' * 80}")
    print(f"  Timing Modifier: {classical['timing_modifier'].upper()}")
    for p in classical["fired_patterns"]:
        print(f"    • {p}")
    if not classical["fired_patterns"]:
        print("    (No classical early/delayed patterns detected)")

    print(f"\n{'─' * 80}")
    print("  LAYER 5: OUTCOME / QUALITY")
    print(f"{'─' * 80}")
    print(f"  Marriage Mode: {outcome['mode']}")
    print(f"  Marriage Quality: {outcome['quality']}")
    print(f"  Second Marriage Risk: {outcome['second_marriage_risk']}")
    for o in outcome["fired_outcomes"]:
        print(f"    • {o}")

    # Scan marriage windows
    print(f"\n{'─' * 80}")
    print("  SCANNING MARRIAGE WINDOWS (Age 18–35)...")
    print(f"{'─' * 80}")

    windows = scan_marriage_windows(chart, start_age=18, end_age=35)

    print(f"\n  Found {len(windows)} windows where dasha rules fired.")
    print(f"  Showing top 15 ranked by composite 5-layer score:\n")

    print(f"  {'#':<3} {'Period':<28} {'Age':<10} {'Score':<7} {'Band':<8} {'Likelihood':<12} {'MD-AD':<18}")
    print(f"  {'─'*3} {'─'*28} {'─'*10} {'─'*7} {'─'*8} {'─'*12} {'─'*18}")

    for i, w in enumerate(windows[:15], 1):
        period = f"{w.period_start.strftime('%b %Y')} – {w.period_end.strftime('%b %Y')}"
        age = f"{w.age_start:.1f}–{w.age_end:.1f}"
        md_ad = f"{w.md_lord}–{w.ad_lord}"
        print(f"  {i:<3} {period:<28} {age:<10} {w.total_score:<7.1f} {w.timing_band:<8} {w.likelihood:<12} {md_ad:<18}")

    # Detailed top 5
    print(f"\n{'═' * 80}")
    print("  TOP 5 MARRIAGE WINDOWS — DETAILED 5-LAYER BREAKDOWN")
    print(f"{'═' * 80}")

    for i, w in enumerate(windows[:5], 1):
        print(f"\n  ┌{'─' * 76}┐")
        print(f"  │ #{i} | {w.period_start.strftime('%B %Y')} – {w.period_end.strftime('%B %Y')}")
        print(f"  │ Age: {w.age_start:.1f} – {w.age_end:.1f} | MD: {w.md_lord} | AD: {w.ad_lord}")
        print(f"  │ COMPOSITE SCORE: {w.total_score:.1f} | Likelihood: {w.likelihood} | Band: {w.timing_band}")
        print(f"  ├{'─' * 76}┤")

        print(f"  │ LAYER 1 — DASHA (Gate):")
        for rule_id, score, reasons in w.dasha_fired:
            for r in reasons:
                print(f"  │   [{score:>3}] {r}")

        print(f"  │ LAYER 2 — TRANSIT (Activation):")
        if w.transit_fired:
            for rule_id, score, reasons in w.transit_fired:
                for r in reasons:
                    print(f"  │   [{score:>3}] {r}")
        else:
            print(f"  │   (No transit activation at sample points)")

        print(f"  │ LAYER 3 — FAST TRIGGER (Exact):")
        if w.fast_trigger_fired:
            for rule_id, score, reasons in w.fast_trigger_fired:
                for r in reasons:
                    print(f"  │   [{score:>3}] {r}")
        else:
            print(f"  │   (No fast trigger at sample points)")

        print(f"  └{'─' * 76}┘")

    print(f"\n{'═' * 80}")
    print("  CONCLUSION")
    print(f"{'═' * 80}")
    if windows:
        top = windows[0]
        print(f"\n  MOST LIKELY MARRIAGE WINDOW:")
        print(f"  {top.period_start.strftime('%B %Y')} – {top.period_end.strftime('%B %Y')}")
        print(f"  Age {top.age_start:.1f}–{top.age_end:.1f} | {top.md_lord}–{top.ad_lord}")
        print(f"  Score: {top.total_score:.1f} | {top.likelihood}")
        print(f"\n  Marriage likely happened during one of the top-scored windows.")
        print(f"  The 5-layer engine evaluated {len(windows)} AD periods with")
        print(f"  {sum(1 for w in windows if w.total_score >= 35)} HIGH+ confidence windows.")
    print(f"\n{'═' * 80}")
