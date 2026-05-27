"""
Parent Health & Loss Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha > Transit > Fast Trigger > Classical > Outcome flow.
Domain: Parent Health & Loss (Family)

Follows the exact same pattern as vehicle_purchase_evaluator.py.
Key planets: Sun (father karaka), Moon (mother karaka), Saturn (longevity/death)
Key houses: 4 (mother), 9 (father), 8 (death/longevity), 10 (father alternate)
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
    NATURAL_BENEFICS, NATURAL_MALEFICS,
    JUPITER_ASPECTS, SATURN_ASPECTS, MARS_ASPECTS,
    BaseChartState, BaseTransitState,
    load_scoring_profile,
)

# ═══════════════════════════════════════════════════════════════
# CONSTANTS (domain-specific only)
# ═══════════════════════════════════════════════════════════════
RULES_DIR = Path(__file__).resolve().parent / "domains" / "family" / "parent_health_and_loss"

# Parent Health & Loss specific constants
PARENT_LOSS_KARAKAS = {"Sun", "Moon", "Saturn", "Rahu", "Ketu"}
PARENT_LOSS_HOUSES = {4, 9, 8, 10, 12}

# Dignity tables — kept here because this evaluator intentionally extends
# features/dignity.py with Rahu/Ketu entries (domain-semantic, not plumbing).
EXALTATION_SIGNS = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6,
    "Jupiter": 4, "Venus": 12, "Saturn": 7, "Rahu": 3, "Ketu": 9
}
OWN_SIGNS = {
    "Sun": [5], "Moon": [4], "Mars": [1, 8], "Mercury": [3, 6],
    "Jupiter": [9, 12], "Venus": [2, 7], "Saturn": [10, 11],
    "Rahu": [11], "Ketu": [8]
}
DEBILITATION_SIGNS = {
    "Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12,
    "Jupiter": 10, "Venus": 6, "Saturn": 1, "Rahu": 9, "Ketu": 3
}



# ===============================================================
# CALIBRATION OVERLAY LOADER
# ===============================================================

def _load_calibration():
    """Load calibration overlay from JSON."""
    calibration_path = RULES_DIR / "calibration_overlay.json"
    try:
        with open(calibration_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "layer_weights": {
                "dasha_weight": 0.35,
                "transit_weight": 0.30,
                "fast_trigger_weight": 0.20,
                "classical_weight": 0.15,
            },
            "likelihood_thresholds": {
                "very_high": 55, "high": 40, "moderate": 25, "low": 15,
            },
            "outcome_calibration": {
                "mode_priority_order": ["father_death", "mother_death",
                                        "parental_death", "parental_separation",
                                        "father_distress", "mother_distress"],
                "quality_priority_order": ["death", "sudden_crisis",
                                           "chronic_illness", "separation",
                                           "emotional_distance"],
                "default_mode": "parental_distress",
            },
        }


CALIBRATION = _load_calibration()

# ── Scoring profile (v3.0.0) ──────────────────────────────────
_SCORING_PROFILE = load_scoring_profile("general_life")






# ===============================================================
# CHART STATE BUILDER
# ===============================================================

class ChartState(BaseChartState):
    """Encapsulates all natal chart data needed for parent loss rule evaluation."""

    def __init__(self, birth_dt, lat, lon, alt=0):
        super().__init__(birth_dt, lat, lon, alt)

        # Parent-loss-specific: Sun data (father karaka)
        self.sun_lon = self.birth_positions["Sun"]
        self.sun_sign = get_sign(self.sun_lon)

        # Key house lords
        self.lagna_lord = SIGN_LORDS[self.asc_sign]
        self.fourth_sign = ((self.asc_sign + 3 - 1) % 12) + 1
        self.fourth_lord = SIGN_LORDS[self.fourth_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.eighth_sign = ((self.asc_sign + 7 - 1) % 12) + 1
        self.eighth_lord = SIGN_LORDS[self.eighth_sign]
        self.tenth_sign = ((self.asc_sign + 9 - 1) % 12) + 1
        self.tenth_lord = SIGN_LORDS[self.tenth_sign]
        self.twelfth_sign = ((self.asc_sign + 11 - 1) % 12) + 1
        self.twelfth_lord = SIGN_LORDS[self.twelfth_sign]

        # Moon lord (dispositor of Moon)
        self.moon_lord = SIGN_LORDS[self.moon_sign]
        # Sun lord (dispositor of Sun)
        self.sun_lord = SIGN_LORDS[self.sun_sign]


        # Planets in key houses
        self.fourth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 4
        ]
        self.ninth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 9
        ]
        self.eighth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 8
        ]
        self.tenth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 10
        ]
        self.twelfth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 12
        ]

        # Sensitive Parent Points
        # Father point: Sun + Saturn midpoint (paternal longevity axis)
        saturn_lon = self.birth_positions["Saturn"]
        self.father_sensitive_point = (self.sun_lon + saturn_lon) % 360
        # Mother point: Moon + 4th lord midpoint (maternal axis)
        fourth_lord_lon = self.birth_positions[self.fourth_lord]
        self.mother_sensitive_point = (self.moon_lon + fourth_lord_lon) % 360# ===============================================================
# TRANSIT STATE
# ===============================================================

class TransitState(BaseTransitState):
    """
    Transit state for this domain's evaluation.
    Extends BaseTransitState with degree-level conjunction checks
    and house-from-Sun computation needed by parent loss rules.
    """

    def __init__(self, eval_date, chart):
        super().__init__(eval_date, chart)
        # Precompute houses from Sun for malefic transit checks
        sun_sign = chart.sun_sign
        self.planet_houses_from_sun = {}
        for name, lon in self.positions.items():
            p_sign = int(lon // 30) + 1
            self.planet_houses_from_sun[name] = ((p_sign - sun_sign) % 12) + 1

    def planet_conjunct_natal(self, planet_name, natal_degree, orb=8.0):
        """Return True if transit planet is within orb of a natal degree."""
        transit_lon = self.positions.get(planet_name, 0)
        diff = abs((transit_lon - natal_degree) % 360)
        diff = min(diff, 360 - diff)
        return diff <= orb

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate dasha rules for parent health & loss.
    9 rules: 4th lord navamsa, 1st/4th/9th lord, Ketu-Saturn,
    Saturn-Rahu, Venus-Sun, Rahu-Moon, Jupiter-Moon, Saturn-Moon, Mercury-Jupiter.
    """
    fired = []

    # Rule 1: Hora Sara — 4th Lord Navamsa Dispositor Dasha (priority 90)
    fourth_lord_lon = chart.birth_positions[chart.fourth_lord]
    navamsa_index = int((fourth_lord_lon % 30) / 3.333333)
    fourth_lord_navamsa_sign = ((get_sign(fourth_lord_lon) - 1) * 9 + navamsa_index) % 12 + 1
    fourth_lord_navamsa_dispositor = SIGN_LORDS[fourth_lord_navamsa_sign]
    if md_lord == fourth_lord_navamsa_dispositor or ad_lord == fourth_lord_navamsa_dispositor:
        score = 42 if md_lord == fourth_lord_navamsa_dispositor else 32
        fired.append(("horasara_4th_lord_navamsa_father", score,
                      [f"{'MD' if md_lord == fourth_lord_navamsa_dispositor else 'AD'} of {fourth_lord_navamsa_dispositor} "
                       f"(4th lord's Navamsa dispositor) — father death window (Hora Sara)"]))

    # Rule 2: Jataka Parijata — 1st/4th/9th Lord Dasha (priority 85)
    for lord_name, lord_val in [("1st", chart.lagna_lord), ("4th", chart.fourth_lord), ("9th", chart.ninth_lord)]:
        if md_lord == lord_val or ad_lord == lord_val:
            score = 35 if md_lord == lord_val else 25
            fired.append(("jp_1st_4th_9th_mother_follows_father", score,
                          [f"{'MD' if md_lord == lord_val else 'AD'} of {lord_val} ({lord_name} lord) — "
                           f"mother may follow father (Jataka Parijata)"]))
            break  # Only fire once for this rule

    # Rule 3: BPHS — Ketu-Saturn Death of Parents (priority 92)
    if md_lord == "Ketu" and ad_lord == "Saturn":
        fired.append(("bphs_ketu_saturn_parental_death", 48,
                      ["Ketu MD + Saturn AD — death of parents indicated (BPHS)"]))
    elif md_lord == "Saturn" and ad_lord == "Ketu":
        fired.append(("bphs_saturn_ketu_parental_death", 40,
                      ["Saturn MD + Ketu AD — separation/death of parents (BPHS variant)"]))


    # Rule 4: BPHS — Saturn-Rahu Parents' Death (priority 93)
    if md_lord == "Saturn" and ad_lord == "Rahu":
        fired.append(("bphs_saturn_rahu_parental_destruction", 46,
                      ["Saturn MD + Rahu AD — destruction of parents, sudden crisis (BPHS)"]))
    elif md_lord == "Rahu" and ad_lord == "Saturn":
        fired.append(("bphs_rahu_saturn_parental_danger", 38,
                      ["Rahu MD + Saturn AD — parental danger, health deterioration (BPHS)"]))

    # Rule 5: BPHS — Venus-Sun Distress to Father (priority 82)
    if md_lord == "Venus" and ad_lord == "Sun":
        fired.append(("bphs_venus_sun_father_distress", 32,
                      ["Venus MD + Sun AD — distress to father, loss of authority (BPHS)"]))
    elif md_lord == "Sun" and ad_lord == "Venus":
        fired.append(("bphs_sun_venus_father_concern", 26,
                      ["Sun MD + Venus AD — father concern period (BPHS variant)"]))

    # Rule 6: BPHS — Rahu-Moon Distress to Father (priority 80)
    if md_lord == "Rahu" and ad_lord == "Moon":
        fired.append(("bphs_rahu_moon_father_distress", 30,
                      ["Rahu MD + Moon AD — danger to father, mental anxiety (BPHS)"]))

    # Rule 7: BPHS — Jupiter-Moon Distress to Mother (priority 78)
    if md_lord == "Jupiter" and ad_lord == "Moon":
        fired.append(("bphs_jupiter_moon_mother_distress", 28,
                      ["Jupiter MD + Moon AD — distress to mother, emotional turbulence (BPHS)"]))

    # Rule 8: BPHS — Saturn-Moon Separation from Parents (priority 84)
    if md_lord == "Saturn" and ad_lord == "Moon":
        fired.append(("bphs_saturn_moon_parental_separation", 38,
                      ["Saturn MD + Moon AD — separation from parents, loss of comfort (BPHS)"]))
    elif md_lord == "Moon" and ad_lord == "Saturn":
        fired.append(("bphs_moon_saturn_parental_distance", 30,
                      ["Moon MD + Saturn AD — emotional distance from parents (BPHS)"]))

    # Rule 9: BPHS — Mercury-Jupiter Death of Parents (priority 76)
    if md_lord == "Mercury" and ad_lord == "Jupiter":
        fired.append(("bphs_mercury_jupiter_parental_death", 26,
                      ["Mercury MD + Jupiter AD — death of parents possible (BPHS, context-dependent)"]))

    return fired



# ===============================================================
# LAYER 2: TRANSIT EVALUATOR (Parent Loss — 9 rules)
# ===============================================================

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate transit rules for parent health & loss activation.
    Key: Saturn on Sun/Moon sensitive points, malefics 4th from Sun.
    """
    fired = []

    # Rule 1: Saturn transit over natal Sun (Ashtakavarga father) — priority 92
    if transit.planet_conjunct_natal("Saturn", chart.sun_lon, orb=8.0):
        fired.append(("transit_saturn_sun_ashtakavarga_father", 42,
                      ["Transit Saturn conjunct natal Sun — father karaka under pressure"]))

    # Rule 2: Saturn transit over natal Moon (Ashtakavarga mother) — priority 92
    if transit.planet_conjunct_natal("Saturn", chart.moon_lon, orb=8.0):
        fired.append(("transit_saturn_moon_ashtakavarga_mother", 42,
                      ["Transit Saturn conjunct natal Moon — mother karaka under pressure (Sade-sati)"]))

    # Rule 3: Saturn/Rahu/Mars 4th from natal Sun — father death (priority 88)
    for malefic in ["Saturn", "Rahu", "Mars"]:
        house_from_sun = transit.planet_houses_from_sun.get(malefic, 0)
        if house_from_sun == 4:
            fired.append((f"transit_{malefic.lower()}_4th_from_sun_father", 38,
                          [f"Transit {malefic} in 4th from natal Sun — father's death house activated"]))

    # Rule 4: Sun trine Moon's Navamsa lord (mother) — priority 78
    moon_navamsa_idx = int((chart.moon_lon % 30) / 3.333333)
    moon_navamsa_sign = ((chart.moon_sign - 1) * 9 + moon_navamsa_idx) % 12 + 1
    moon_navamsa_lord = SIGN_LORDS[moon_navamsa_sign]
    moon_d9_lord_lon = chart.birth_positions.get(moon_navamsa_lord, 0)
    sun_transit_lon = transit.positions["Sun"]
    trine_diff = abs((sun_transit_lon - moon_d9_lord_lon) % 360)
    trine_diff = min(trine_diff, 360 - trine_diff)
    if abs(trine_diff - 120) <= 8 or abs(trine_diff - 240) <= 8:
        fired.append(("transit_sun_trine_moon_d9_mother", 28,
                      [f"Transit Sun trine Moon's D9 lord ({moon_navamsa_lord}) — maternal event timing"]))


    # Rule 5: Sun trine Lagna's Navamsa lord (father) — priority 78
    asc_navamsa_idx = int((chart.asc_lon % 30) / 3.333333)
    asc_navamsa_sign = ((chart.asc_sign - 1) * 9 + asc_navamsa_idx) % 12 + 1
    asc_navamsa_lord = SIGN_LORDS[asc_navamsa_sign]
    asc_d9_lord_lon = chart.birth_positions.get(asc_navamsa_lord, 0)
    trine_diff2 = abs((sun_transit_lon - asc_d9_lord_lon) % 360)
    trine_diff2 = min(trine_diff2, 360 - trine_diff2)
    if abs(trine_diff2 - 120) <= 8 or abs(trine_diff2 - 240) <= 8:
        fired.append(("transit_sun_trine_lagna_d9_father", 28,
                      [f"Transit Sun trine Lagna's D9 lord ({asc_navamsa_lord}) — paternal event timing"]))

    # Rule 6: Double Sun-Moon difference (mother) — priority 75
    double_diff_point = (2 * abs(chart.sun_lon - chart.moon_lon)) % 360
    for malefic in ["Saturn", "Rahu"]:
        if transit.planet_conjunct_natal(malefic, double_diff_point, orb=5.0):
            fired.append(("transit_double_sun_moon_diff_mother", 30,
                          [f"Transit {malefic} at 2x(Sun-Moon) sensitive point — maternal axis activated"]))
            break

    # Rule 7: Mandi-Sun difference (father) — priority 80
    # Approximate Mandi as Saturn's sub-point (1/8 of Saturn's longitude from Lagna)
    saturn_lon = chart.birth_positions["Saturn"]
    mandi_approx = (saturn_lon + chart.asc_lon) / 2 % 360
    mandi_sun_diff = (mandi_approx - chart.sun_lon) % 360
    for malefic in ["Saturn", "Rahu"]:
        if transit.planet_conjunct_natal(malefic, mandi_sun_diff, orb=5.0):
            fired.append(("transit_mandi_sun_diff_father", 32,
                          [f"Transit {malefic} at Mandi-Sun difference — father danger point activated"]))
            break

    # Rule 8: Yamakantaka-Sun difference (father) — priority 82
    # Approximate Yamakantaka as Jupiter's sub-point
    jupiter_lon = chart.birth_positions["Jupiter"]
    yamakantaka_approx = (jupiter_lon + chart.asc_lon) / 2 % 360
    yama_sun_diff = (yamakantaka_approx - chart.sun_lon) % 360
    for malefic in ["Saturn", "Rahu"]:
        if transit.planet_conjunct_natal(malefic, yama_sun_diff, orb=5.0):
            fired.append(("transit_yamakantaka_sun_diff_father", 35,
                          [f"Transit {malefic} at Yamakantaka-Sun difference — father death timing"]))
            break

    # Rule 9: Moon-Mandi difference (mother) — priority 80
    moon_mandi_diff = (chart.moon_lon - mandi_approx) % 360
    for malefic in ["Saturn", "Rahu"]:
        if transit.planet_conjunct_natal(malefic, moon_mandi_diff, orb=5.0):
            fired.append(("transit_moon_mandi_diff_mother", 32,
                          [f"Transit {malefic} at Moon-Mandi difference — mother danger point activated"]))
            break

    return fired



# ===============================================================
# LAYER 3: FAST TRIGGER EVALUATOR (Parent Loss — 5 rules)
# ===============================================================

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate fast trigger rules for exact parent loss timing.
    5 rules: Moon on Sun's D9 dispositor, Gandanta father/mother,
    Mars 4th from Sun, Sun in Moon's D9 sign.
    """
    fired = []

    # Rule 1: Moon transit over Sun's Navamsa dispositor (father) — priority 88
    sun_navamsa_idx = int((chart.sun_lon % 30) / 3.333333)
    sun_navamsa_sign = ((chart.sun_sign - 1) * 9 + sun_navamsa_idx) % 12 + 1
    sun_d9_dispositor = SIGN_LORDS[sun_navamsa_sign]
    sun_d9_disp_lon = chart.birth_positions.get(sun_d9_dispositor, 0)
    if transit.planet_conjunct_natal("Moon", sun_d9_disp_lon, orb=3.0):
        fired.append(("fast_moon_sun_d9_dispositor_father", 30,
                      [f"Transit Moon conjunct {sun_d9_dispositor} (Sun's D9 dispositor) — father event exact day"]))

    # Rule 2: Gandanta pada transit — father (priority 85)
    # Gandanta points: 0 Aries (360/0), 0 Leo (120), 0 Sagittarius (240)
    gandanta_points = [0.0, 120.0, 240.0]
    sun_transit_lon = transit.positions["Sun"]
    for gp in gandanta_points:
        diff = abs((sun_transit_lon - gp) % 360)
        diff = min(diff, 360 - diff)
        if diff <= 3.0:
            fired.append(("fast_gandanta_father_loss", 28,
                          [f"Transit Sun at Gandanta point ({gp:.0f} deg) — father karmic dissolution"]))
            break

    # Rule 3: Gandanta pada transit — mother (priority 85)
    moon_transit_lon = transit.positions["Moon"]
    for gp in gandanta_points:
        diff = abs((moon_transit_lon - gp) % 360)
        diff = min(diff, 360 - diff)
        if diff <= 3.0:
            fired.append(("fast_gandanta_mother_loss", 28,
                          [f"Transit Moon at Gandanta point ({gp:.0f} deg) — maternal karmic dissolution"]))
            break

    # Rule 4: Mars 4th from Sun — father death detonator (priority 82)
    mars_house_from_sun = transit.planet_houses_from_sun.get("Mars", 0)
    if mars_house_from_sun == 4:
        mars_transit_lon = transit.positions["Mars"]
        # Check tight orb for fast trigger
        sun_4th_point = (chart.sun_lon + 90) % 360  # approximate 4th from Sun
        diff = abs((mars_transit_lon - sun_4th_point) % 360)
        diff = min(diff, 360 - diff)
        if diff <= 10.0:
            fired.append(("fast_mars_4th_sun_detonator", 25,
                          ["Transit Mars in 4th from Sun (tight orb) — father death detonator"]))

    # Rule 5: Sun in Moon's Navamsa sign — mother timing (priority 80)
    moon_navamsa_idx = int((chart.moon_lon % 30) / 3.333333)
    moon_navamsa_sign = ((chart.moon_sign - 1) * 9 + moon_navamsa_idx) % 12 + 1
    sun_transit_sign = get_sign(sun_transit_lon)
    if sun_transit_sign == moon_navamsa_sign:
        fired.append(("fast_sun_moon_d9_sign_mother", 22,
                      [f"Transit Sun in Moon's Navamsa sign ({SIGN_NAMES[moon_navamsa_sign]}) — mother event window"]))

    return fired



# ===============================================================
# LAYER 4: CLASSICAL PATTERN EVALUATOR (Parent Loss — 8 rules)
# ===============================================================

def evaluate_classical_layer(chart: ChartState):
    """
    Evaluate classical parent loss patterns (structural — not time-dependent).
    8 rules: Moon 3 malefics, malefics 6/12 or 4/10, Sun papa kartari 7th,
    malefics 4/10/12, malefics 4th from Moon, Sun-Saturn 12th Moon 7th,
    malefics 6/8 from Sun, Pitru Shapa.
    """
    results = {
        "timing_modifier": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    # Get needed data
    fourth_aspectors = chart._get_aspectors_of_house(4)
    moon_house = chart.planets.get("Moon", {}).get("house", 0)
    sun_house = chart.planets.get("Sun", {}).get("house", 0)
    saturn_house = chart.planets.get("Saturn", {}).get("house", 0)
    ninth_lord_sign = chart.planets.get(chart.ninth_lord, {}).get("sign", 0)
    rahu_sign = chart.planets.get("Rahu", {}).get("sign", 0)
    ketu_sign = chart.planets.get("Ketu", {}).get("sign", 0)

    # Pattern 1: Moon aspected by 3 malefics — mother early death (priority 92)
    moon_aspectors = chart._get_aspectors_of_house(moon_house) if moon_house else []
    malefic_moon_aspectors = [p for p in moon_aspectors if p in NATURAL_MALEFICS]
    # Also count planets conjunct Moon
    moon_sign = chart.moon_sign
    malefics_with_moon = [n for n, d in chart.planets.items()
                          if d["sign"] == moon_sign and n in NATURAL_MALEFICS]
    total_malefic_influence = len(set(malefic_moon_aspectors + malefics_with_moon))
    if total_malefic_influence >= 3:
        benefic_aspectors = [p for p in moon_aspectors if p in NATURAL_BENEFICS]
        if not benefic_aspectors:
            results["confidence_boost"] += 25
            results["fired_patterns"].append(
                f"Moon afflicted by {total_malefic_influence} malefics (no benefic relief) — mother early death promise (BPHS)")


    # Pattern 2: Malefics in 6/12 or 4/10 axis — parental evil (priority 85)
    sixth_occ = [n for n, d in chart.planets.items() if d["house"] == 6 and n in NATURAL_MALEFICS]
    twelfth_occ = [n for n, d in chart.planets.items() if d["house"] == 12 and n in NATURAL_MALEFICS]
    fourth_mal = [n for n, d in chart.planets.items() if d["house"] == 4 and n in NATURAL_MALEFICS]
    tenth_mal = [n for n, d in chart.planets.items() if d["house"] == 10 and n in NATURAL_MALEFICS]
    if sixth_occ and twelfth_occ:
        results["confidence_boost"] += 18
        results["fired_patterns"].append(
            f"Malefics in 6/12 axis ({', '.join(sixth_occ)} / {', '.join(twelfth_occ)}) — hidden parental evil (BPHS)")
    if fourth_mal and tenth_mal:
        results["confidence_boost"] += 20
        results["fired_patterns"].append(
            f"Malefics in 4/10 axis ({', '.join(fourth_mal)} / {', '.join(tenth_mal)}) — direct mother/father affliction (BPHS)")

    # Pattern 3: Sun in 7th with Papa Kartari — father death (priority 88)
    if sun_house == 7:
        sixth_mal = [n for n, d in chart.planets.items() if d["house"] == 6 and n in NATURAL_MALEFICS]
        eighth_mal = [n for n, d in chart.planets.items() if d["house"] == 8 and n in NATURAL_MALEFICS]
        if sixth_mal and eighth_mal:
            results["confidence_boost"] += 22
            results["fired_patterns"].append(
                f"Sun in 7th with Papa Kartari ({', '.join(sixth_mal)} in 6th, {', '.join(eighth_mal)} in 8th) — father death promise (BPHS)")

    # Pattern 4: Malefics in 4th, 10th, 12th — separation (priority 86)
    twelfth_mal = [n for n, d in chart.planets.items() if d["house"] == 12 and n in NATURAL_MALEFICS]
    if fourth_mal and tenth_mal and twelfth_mal:
        results["confidence_boost"] += 22
        results["fired_patterns"].append(
            f"Malefics in 4/10/12 — parental separation/abandonment promise (BPHS)")

    # Pattern 5: Malefics 4th from Moon — mother death (priority 90)
    fourth_from_moon_sign = ((chart.moon_sign + 3 - 1) % 12) + 1
    malefics_4th_from_moon = [n for n, d in chart.planets.items()
                              if d["sign"] == fourth_from_moon_sign and n in NATURAL_MALEFICS]
    if malefics_4th_from_moon:
        # Check no benefic aspect
        fourth_from_moon_house = chart.get_house_from_sign(fourth_from_moon_sign)
        benefic_asp = [p for p in chart._get_aspectors_of_house(fourth_from_moon_house) if p in NATURAL_BENEFICS]
        if not benefic_asp:
            results["confidence_boost"] += 20
            results["fired_patterns"].append(
                f"Malefics 4th from Moon ({', '.join(malefics_4th_from_moon)}) — mother early death (Jataka Parijata)")


    # Pattern 6: Sun-Saturn in 12th + Moon in 7th — father loss (priority 88)
    if sun_house == 12 and saturn_house == 12 and moon_house == 7:
        results["confidence_boost"] += 22
        results["fired_patterns"].append(
            "Sun + Saturn in 12th, Moon in 7th — father early death, mental anguish (Jataka Parijata)")

    # Pattern 7: Malefics 6th and 8th from Sun — father chronic illness (priority 82)
    sun_sign = chart.sun_sign
    sixth_from_sun = ((sun_sign + 5 - 1) % 12) + 1
    eighth_from_sun = ((sun_sign + 7 - 1) % 12) + 1
    mal_6th_from_sun = [n for n, d in chart.planets.items()
                        if d["sign"] == sixth_from_sun and n in NATURAL_MALEFICS]
    mal_8th_from_sun = [n for n, d in chart.planets.items()
                        if d["sign"] == eighth_from_sun and n in NATURAL_MALEFICS]
    if mal_6th_from_sun and mal_8th_from_sun:
        results["confidence_boost"] += 16
        results["fired_patterns"].append(
            f"Malefics in 6th & 8th from Sun — father chronic illness (Hora Sara)")

    # Pattern 8: Pitru Shapa — 9th lord with Rahu/Ketu + Sun-Saturn (priority 94)
    ninth_lord_with_nodes = (ninth_lord_sign == rahu_sign or ninth_lord_sign == ketu_sign)
    sun_saturn_affliction = (chart.planets.get("Sun", {}).get("sign", 0) ==
                             chart.planets.get("Saturn", {}).get("sign", 0))
    sun_aspected_by_saturn = "Saturn" in chart._get_aspectors_of_house(sun_house)
    if ninth_lord_with_nodes and (sun_saturn_affliction or sun_aspected_by_saturn):
        results["confidence_boost"] += 25
        results["timing_modifier"] = "accelerated"
        results["fired_patterns"].append(
            f"PITRU SHAPA: 9th lord with Rahu/Ketu + Sun-Saturn affliction — ancestral curse active (BPHS)")

    return results



# ===============================================================
# LAYER 5: OUTCOME / QUALITY EVALUATOR (Parent Loss — 8 rules)
# ===============================================================

def evaluate_outcome_layer(chart: ChartState):
    """
    Evaluate outcome/quality rules for parent loss classification.
    8 rules: emotional distance, unstable relationship, abandonment,
    mother abandonment, inherited suffering, sudden crisis, maternal crisis, sudden orphan.
    """
    fired_rules = []

    moon_sign = chart.moon_sign
    ketu_sign = chart.planets.get("Ketu", {}).get("sign", 0)
    mars_house = chart.planets.get("Mars", {}).get("house", 0)
    mars_sign = chart.planets.get("Mars", {}).get("sign", 0)
    sun_house = chart.planets.get("Sun", {}).get("house", 0)
    moon_house = chart.planets.get("Moon", {}).get("house", 0)

    # Rule 1: Moon-Ketu conjunction — emotional distance (priority 78)
    if moon_sign == ketu_sign:
        fired_rules.append(("chandra_ketu_emotional_distance", "quality_challenging", 0.82,
            "Moon-Ketu conjunction — emotional distance from mother, spiritual detachment"))

    # Rule 2: Mars in 4th — unstable parental relationship (priority 75)
    if mars_house == 4:
        fired_rules.append(("mars_4th_unstable_relationship", "quality_challenging", 0.76,
            "Mars in 4th — unstable parental bond, domestic strife, aggression in home"))

    # Rule 3: Malefics in 4/10/12 — parental abandonment (priority 88)
    fourth_mal = [n for n, d in chart.planets.items() if d["house"] == 4 and n in NATURAL_MALEFICS]
    tenth_mal = [n for n, d in chart.planets.items() if d["house"] == 10 and n in NATURAL_MALEFICS]
    twelfth_mal = [n for n, d in chart.planets.items() if d["house"] == 12 and n in NATURAL_MALEFICS]
    if fourth_mal and tenth_mal and twelfth_mal:
        fired_rules.append(("bphs_malefics_4_10_12_abandonment", "quality_challenging", 0.86,
            "Malefics in 4th/10th/12th — complete parental abandonment"))

    # Rule 4: Waning Moon + malefic trines — mother abandonment (priority 84)
    # Check if Moon is waning (approximate: Moon behind Sun = waning)
    sun_lon = chart.sun_lon
    moon_lon = chart.moon_lon
    moon_sun_diff = (moon_lon - sun_lon) % 360
    is_waning = moon_sun_diff > 180  # Krishna Paksha
    if is_waning:
        malefics_in_trines = [n for n, d in chart.planets.items()
                              if d["house"] in {1, 5, 9} and n in NATURAL_MALEFICS]
        if len(malefics_in_trines) >= 2:
            fired_rules.append(("waning_moon_malefic_trines_abandonment", "quality_challenging", 0.80,
                f"Waning Moon + malefics in trines ({', '.join(malefics_in_trines)}) — mother abandonment"))


    # Rule 5: Pitru Shapa — inherited suffering (priority 90)
    ninth_lord_sign = chart.planets.get(chart.ninth_lord, {}).get("sign", 0)
    rahu_sign_val = chart.planets.get("Rahu", {}).get("sign", 0)
    ketu_sign_val = chart.planets.get("Ketu", {}).get("sign", 0)
    ninth_with_nodes = (ninth_lord_sign == rahu_sign_val or ninth_lord_sign == ketu_sign_val)
    sun_sign_val = chart.planets.get("Sun", {}).get("sign", 0)
    saturn_sign_val = chart.planets.get("Saturn", {}).get("sign", 0)
    sun_saturn_conj = (sun_sign_val == saturn_sign_val)
    if ninth_with_nodes and sun_saturn_conj:
        fired_rules.append(("pitru_shapa_inherited_suffering", "quality_challenging", 0.88,
            "Pitru Shapa active — inherited generational suffering through paternal line"))

    # Rule 6: Mars in 10th in enemy sign — sudden crisis (priority 80)
    if mars_house == 10:
        mars_enemy_signs = [4, 2, 7]  # Cancer, Taurus, Libra (Venus/Moon ruled)
        if mars_sign in mars_enemy_signs:
            fired_rules.append(("mars_10th_enemy_sudden_crisis", "quality_challenging", 0.78,
                "Mars in 10th in enemy sign — father faces sudden crisis/accident"))

    # Rule 7: Sun+Mars in 8th + afflicted Moon — maternal crisis (priority 82)
    sun_in_8th = sun_house == 8
    mars_in_8th = mars_house == 8
    moon_aspectors = chart._get_aspectors_of_house(moon_house) if moon_house else []
    moon_afflicted = any(p in NATURAL_MALEFICS for p in moon_aspectors)
    if sun_in_8th and mars_in_8th and moon_afflicted:
        fired_rules.append(("sun_mars_8th_maternal_crisis", "quality_challenging", 0.80,
            "Sun + Mars in 8th with afflicted Moon — maternal emergency/surgery"))

    # Rule 8: 5 planets in 2nd — sudden orphan (priority 95)
    second_house_count = len([n for n, d in chart.planets.items() if d["house"] == 2])
    if second_house_count >= 5:
        fired_rules.append(("five_planets_2nd_sudden_orphan", "quality_challenging", 0.88,
            "5+ planets in 2nd house — sudden orphanhood, complete family destruction"))

    # ===============================================================
    # RESOLUTION
    # ===============================================================
    cal = CALIBRATION.get("outcome_calibration", {})
    default_mode = cal.get("default_mode", "parental_distress")

    # Resolve MODE (father vs mother)
    resolved_mode = default_mode
    sun_afflicted = sun_house in {6, 8, 12}
    moon_afflicted_check = moon_house in {6, 8, 12}
    if sun_afflicted and not moon_afflicted_check:
        resolved_mode = "father_loss"
    elif moon_afflicted_check and not sun_afflicted:
        resolved_mode = "mother_loss"
    elif sun_afflicted and moon_afflicted_check:
        resolved_mode = "both_parents_at_risk"

    # Resolve QUALITY
    quality_rules = [r for r in fired_rules if r[1].startswith("quality_")]
    resolved_quality = "challenging"
    if not quality_rules:
        resolved_quality = "moderate_concern"

    return {
        "mode": resolved_mode,
        "quality": resolved_quality,
        "fired_outcomes": [f"{r[0]}: {r[3]}" for r in fired_rules],
        "_classical_rules_fired": fired_rules,
        "_resolution_method": "calibration_priority_order",
        "_calibration_version": CALIBRATION.get("calibration_version", "unknown"),
    }



# ===============================================================
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE (Parent Loss)
# ===============================================================

class ParentLossWindowResult:
    """Result of evaluating a single parent loss time window."""

    def __init__(self):
        self.period_start = None
        self.period_end = None
        self.md_lord = ""
        self.ad_lord = ""
        self.age_start = 0.0
        self.age_end = 0.0
        self.dasha_fired = []
        self.transit_fired = []
        self.fast_trigger_fired = []
        self.classical = {}
        self.outcome = {}
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



def scan_parent_loss_windows(chart: ChartState, start_age=18, end_age=60, step_months=6):
    """
    Scan through life from start_age to end_age.
    Parent loss typically occurs across entire adult life.
    For each AD period in that range, evaluate the 5-layer engine.
    Returns sorted list of ParentLossWindowResult.
    """
    results = []

    md_periods = _generate_md_periods(chart.birth_dt, chart.moon_lon, years=80)
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

            # LAYER 1: DASHA (gate)
            dasha_results = evaluate_dasha_layer(chart, md["lord"], ad["lord"])
            if not dasha_results:
                continue

            # LAYER 2: TRANSIT (evaluate at midpoint, start, end)
            mid_date = effective_start + (effective_end - effective_start) / 2
            transit = TransitState(mid_date, chart)
            transit_results = evaluate_transit_layer(chart, transit)

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

            # LAYER 3: FAST TRIGGER
            fast_trigger_results = evaluate_fast_trigger_layer(chart, transit)
            ft_start = evaluate_fast_trigger_layer(chart, transit_start)
            ft_end = evaluate_fast_trigger_layer(chart, transit_end)
            all_fast = {}
            for ft_list in [fast_trigger_results, ft_start, ft_end]:
                for rule_id, score, reasons in ft_list:
                    if rule_id not in all_fast or score > all_fast[rule_id][1]:
                        all_fast[rule_id] = (rule_id, score, reasons)
            merged_fast = list(all_fast.values())

            # Build result
            result = ParentLossWindowResult()
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



# ===============================================================
# MAIN — RUN FOR 22 JULY 1975 18:15 BHILAI
# ===============================================================

if __name__ == "__main__":
    BIRTH_DATE = datetime(1975, 7, 22, 18, 15)
    BHILAI_LAT = 21.2094
    BHILAI_LON = 81.4285
    BHILAI_ALT = 297

    print("=" * 80)
    print("  5-LAYER PARENT HEALTH & LOSS RULE ENGINE — VEDIC TEXT BASED")
    print("  Domain: Parent Health & Loss (Family)")
    print("  Native: 22 July 1975, 18:15 IST, Bhilai")
    print("=" * 80)

    # Build chart state
    chart = ChartState(BIRTH_DATE, BHILAI_LAT, BHILAI_LON, BHILAI_ALT)

    print(f"\n{'─' * 80}")
    print("  NATAL CHART SUMMARY (Parent Loss Focus)")
    print(f"{'─' * 80}")
    print(f"  Lagna: {SIGN_NAMES[chart.asc_sign]} | Lagna Lord: {chart.lagna_lord}")
    print(f"  Moon: {SIGN_NAMES[chart.moon_sign]} ({chart.moon_nakshatra})")
    print(f"  Sun: {SIGN_NAMES[chart.sun_sign]} (Father Karaka)")
    print(f"  4th Lord (Mother): {chart.fourth_lord} (house {chart.planets[chart.fourth_lord]['house']})")
    print(f"  9th Lord (Father): {chart.ninth_lord} (house {chart.planets[chart.ninth_lord]['house']})")
    print(f"  8th Lord (Death): {chart.eighth_lord} (house {chart.planets[chart.eighth_lord]['house']})")
    print(f"  10th Lord (Father alt): {chart.tenth_lord} (house {chart.planets[chart.tenth_lord]['house']})")
    print(f"  Saturn (Longevity): house {chart.planets['Saturn']['house']}, {SIGN_NAMES[chart.planets['Saturn']['sign']]}")
    print(f"  Rahu: house {chart.planets['Rahu']['house']}, {SIGN_NAMES[chart.planets['Rahu']['sign']]}")
    print(f"  Ketu: house {chart.planets['Ketu']['house']}, {SIGN_NAMES[chart.planets['Ketu']['sign']]}")
    print(f"  Father Sensitive Point (Sun+Saturn)/2: {chart.father_sensitive_point:.2f} deg")
    print(f"  Mother Sensitive Point (Moon+4L)/2: {chart.mother_sensitive_point:.2f} deg")


    # Layer 4 & 5 (structural)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    print(f"\n{'─' * 80}")
    print("  LAYER 4: CLASSICAL PATTERNS (Structural — Parent Loss)")
    print(f"{'─' * 80}")
    print(f"  Timing Modifier: {classical['timing_modifier'].upper()}")
    print(f"  Confidence Boost: {classical['confidence_boost']:+d}")
    for p in classical["fired_patterns"]:
        print(f"    * {p}")
    if not classical["fired_patterns"]:
        print("    (No classical parent loss patterns detected)")

    print(f"\n{'─' * 80}")
    print("  LAYER 5: OUTCOME / QUALITY (Parent Loss Classification)")
    print(f"{'─' * 80}")
    print(f"  Loss Mode: {outcome['mode']}")
    print(f"  Quality: {outcome['quality']}")
    for o in outcome["fired_outcomes"]:
        print(f"    * {o}")
    if not outcome["fired_outcomes"]:
        print("    (No specific outcome/quality patterns detected)")

    # Scan parent loss windows
    print(f"\n{'─' * 80}")
    print("  SCANNING PARENT LOSS WINDOWS (Age 18-60)...")
    print(f"{'─' * 80}")

    windows = scan_parent_loss_windows(chart, start_age=18, end_age=60)

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
    print("  TOP 5 PARENT LOSS CONCERN WINDOWS — DETAILED 5-LAYER BREAKDOWN")
    print(f"{'=' * 80}")

    for i, w in enumerate(windows[:5], 1):
        print(f"\n  +{'─' * 76}+")
        print(f"  | #{i} | {w.period_start.strftime('%B %Y')} - {w.period_end.strftime('%B %Y')}")
        print(f"  | Age: {w.age_start:.1f} - {w.age_end:.1f} | MD: {w.md_lord} | AD: {w.ad_lord}")
        print(f"  | COMPOSITE SCORE: {w.total_score:.1f} | Likelihood: {w.likelihood} | Band: {w.timing_band}")
        print(f"  +{'─' * 76}+")

        print(f"  | LAYER 1 - DASHA (Gate):")
        for rule_id, score, reasons in w.dasha_fired:
            for r in reasons:
                print(f"  |   [{score:>3}] {r}")

        print(f"  | LAYER 2 - TRANSIT (Activation):")
        if w.transit_fired:
            for rule_id, score, reasons in w.transit_fired:
                for r in reasons:
                    print(f"  |   [{score:>3}] {r}")
        else:
            print(f"  |   (No transit activation at sample points)")

        print(f"  | LAYER 3 - FAST TRIGGER (Exact):")
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
        print(f"\n  HIGHEST CONCERN PARENT LOSS WINDOW:")
        print(f"  {top.period_start.strftime('%B %Y')} - {top.period_end.strftime('%B %Y')}")
        print(f"  Age {top.age_start:.1f}-{top.age_end:.1f} | {top.md_lord}-{top.ad_lord}")
        print(f"  Score: {top.total_score:.1f} | {top.likelihood}")
        print(f"\n  Loss Mode: {outcome['mode']}")
        print(f"  Quality: {outcome['quality']}")
        print(f"\n  The 5-layer engine evaluated {len(windows)} AD periods with")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['high'])} HIGH+ concern windows.")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['very_high'])} VERY_HIGH concern windows.")
    else:
        print("\n  No parent loss concern windows detected in the scanned range.")
    print(f"\n{'=' * 80}")
