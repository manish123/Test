"""
Childbirth Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow
for childbirth/progeny events.

Reuses ChartState and TransitState from marriage_evaluator (generic infra).
Domain-specific logic is isolated here per Astrolyn architecture.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rules.marriage_evaluator import (
    ChartState, TransitState, SIGN_NAMES, CALIBRATION as _MARRIAGE_CAL,
    NATURAL_BENEFICS, NATURAL_MALEFICS, BENEFIC_HOUSES, MALEFIC_HOUSES,
    IST_OFFSET, ist_to_utc, get_jd, NAKSHATRA_LORDS,
)
from features.dasha import _generate_md_periods, _generate_ad_periods
from features.dignity import SIGN_LORDS, get_sign

# ═══════════════════════════════════════════════════════════════
# CHILDBIRTH CALIBRATION (Layer 3 — domain-isolated)
# ═══════════════════════════════════════════════════════════════
RULES_DIR = Path(__file__).resolve().parent / "domains" / "family" / "childbirth"



def _load_childbirth_calibration():
    """Load childbirth-specific calibration overlay."""
    calibration_path = RULES_DIR / "calibration_overlay.json"
    try:
        with open(calibration_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
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
        }

CALIBRATION = _load_childbirth_calibration()



# ═══════════════════════════════════════════════════════════════
# LAYER 1: DASHA EVALUATOR (Childbirth-specific)
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate childbirth dasha rules against current MD/AD.
    Key planets: 5th lord, Jupiter, 1st lord, 7th lord,
    5th house occupants, 5th house aspectors.
    """
    fired = []

    fifth_sign = ((chart.asc_sign + 4 - 1) % 12) + 1
    fifth_lord = SIGN_LORDS[fifth_sign]
    fifth_house_occupants = [
        n for n, d in chart.planets.items() if d["house"] == 5
    ]
    fifth_house_aspectors = chart._get_aspectors_of_house(5)

    # Primary childbirth significators
    primary = {fifth_lord, "Jupiter", chart.lagna_lord, chart.seventh_lord}
    primary.update(fifth_house_occupants)
    primary.update(fifth_house_aspectors)

    # Rule 1: Primary triggers (Phaladeepika 12:25)
    r1_score = 0
    r1_reasons = []

    if md_lord == fifth_lord or ad_lord == fifth_lord:
        r1_score += 40
        r1_reasons.append(
            f"{'MD' if md_lord == fifth_lord else 'AD'} of 5th lord ({fifth_lord})")

    if md_lord == "Jupiter" or ad_lord == "Jupiter":
        r1_score += 35
        r1_reasons.append(
            f"{'MD' if md_lord == 'Jupiter' else 'AD'} of Jupiter (Putrakaraka)")

    if md_lord in fifth_house_occupants or ad_lord in fifth_house_occupants:
        r1_score += 30
        occ = md_lord if md_lord in fifth_house_occupants else ad_lord
        r1_reasons.append(
            f"{'MD' if occ == md_lord else 'AD'} of 5th house occupant ({occ})")

    if md_lord in fifth_house_aspectors or ad_lord in fifth_house_aspectors:
        r1_score += 25
        asp = md_lord if md_lord in fifth_house_aspectors else ad_lord
        r1_reasons.append(
            f"{'MD' if asp == md_lord else 'AD'} of 5th house aspector ({asp})")


    if md_lord == chart.lagna_lord or ad_lord == chart.lagna_lord:
        r1_score += 20
        r1_reasons.append(
            f"{'MD' if md_lord == chart.lagna_lord else 'AD'} of Lagna lord ({chart.lagna_lord})")

    if md_lord == chart.seventh_lord or ad_lord == chart.seventh_lord:
        r1_score += 18
        r1_reasons.append(
            f"{'MD' if md_lord == chart.seventh_lord else 'AD'} of 7th lord ({chart.seventh_lord})")

    if r1_score > 0:
        fired.append(("phaladeepika_dasha_primary_childbirth_triggers",
                      r1_score, r1_reasons))

    # Rule 2: Strongest significator (Phaladeepika 12:28)
    fifth_lord_sign = chart.planets[fifth_lord]["sign"]
    fifth_lord_dispositor = SIGN_LORDS[fifth_lord_sign]
    fifth_lord_d9 = chart._get_d9_sign(chart.planets[fifth_lord]["longitude"])
    fifth_lord_d9_dispositor = SIGN_LORDS[fifth_lord_d9]
    jupiter_sign = chart.planets["Jupiter"]["sign"]
    jupiter_dispositor = SIGN_LORDS[jupiter_sign]
    jupiter_d9 = chart._get_d9_sign(chart.planets["Jupiter"]["longitude"])
    jupiter_d9_dispositor = SIGN_LORDS[jupiter_d9]

    alt_planets = {fifth_lord_dispositor, fifth_lord_d9_dispositor,
                   jupiter_dispositor, jupiter_d9_dispositor}

    r2_score = 0
    r2_reasons = []
    if md_lord in alt_planets or ad_lord in alt_planets:
        if md_lord == fifth_lord_dispositor or ad_lord == fifth_lord_dispositor:
            r2_score += 20
            r2_reasons.append(f"Period of 5th lord dispositor ({fifth_lord_dispositor})")
        if md_lord == jupiter_dispositor or ad_lord == jupiter_dispositor:
            r2_score += 18
            r2_reasons.append(f"Period of Jupiter dispositor ({jupiter_dispositor})")
        if md_lord == fifth_lord_d9_dispositor or ad_lord == fifth_lord_d9_dispositor:
            r2_score += 15
            r2_reasons.append(f"Period of 5L D9 dispositor ({fifth_lord_d9_dispositor})")

    if r2_score > 0:
        fired.append(("phaladeepika_dasha_strongest_progeny_significator",
                      r2_score, r2_reasons))

    # Rule 3: Benefic overlaps (BPHS 53/54/59)
    r3_score = 0
    r3_reasons = []
    moon_house = chart.planets["Moon"]["house"]
    jupiter_house = chart.planets["Jupiter"]["house"]
    venus_house = chart.planets["Venus"]["house"]

    kendra_trikona_11 = {1, 4, 5, 7, 9, 10, 11}

    if md_lord == "Jupiter" and ad_lord == "Moon" and moon_house in kendra_trikona_11:
        r3_score += 25
        r3_reasons.append("Jupiter MD + Moon AD (Moon well-placed)")
    if md_lord == "Saturn" and ad_lord == "Venus" and venus_house in kendra_trikona_11:
        r3_score += 22
        r3_reasons.append("Saturn MD + Venus AD (Venus well-placed)")
    if md_lord == "Ketu" and ad_lord == "Jupiter" and jupiter_house in kendra_trikona_11:
        r3_score += 22
        r3_reasons.append("Ketu MD + Jupiter AD (Jupiter well-placed)")

    if r3_score > 0:
        fired.append(("bphs_dasha_natural_benefic_overlaps", r3_score, r3_reasons))

    # Rule 4: Rahu/Ketu give results of dispositor
    # If Rahu's dispositor is a 5th house significator, Rahu period = childbirth
    r4_score = 0
    r4_reasons = []
    rahu_sign = chart.planets["Rahu"]["sign"]
    rahu_dispositor = SIGN_LORDS[rahu_sign]
    ketu_sign = chart.planets["Ketu"]["sign"]
    ketu_dispositor = SIGN_LORDS[ketu_sign]

    rahu_connected_to_5th = (
        rahu_dispositor == fifth_lord or
        rahu_dispositor in fifth_house_occupants or
        rahu_dispositor == "Jupiter"
    )
    ketu_connected_to_5th = (
        ketu_dispositor == fifth_lord or
        ketu_dispositor in fifth_house_occupants or
        ketu_dispositor == "Jupiter"
    )

    if (md_lord == "Rahu" or ad_lord == "Rahu") and rahu_connected_to_5th:
        r4_score += 28
        r4_reasons.append(
            f"{'MD' if md_lord == 'Rahu' else 'AD'} of Rahu "
            f"(dispositor {rahu_dispositor} connected to 5th)")
    if (md_lord == "Ketu" or ad_lord == "Ketu") and ketu_connected_to_5th:
        r4_score += 22
        r4_reasons.append(
            f"{'MD' if md_lord == 'Ketu' else 'AD'} of Ketu "
            f"(dispositor {ketu_dispositor} connected to 5th)")

    if r4_score > 0:
        fired.append(("nodes_dispositor_childbirth", r4_score, r4_reasons))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR (Childbirth-specific)
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate childbirth transit rules.
    Key: Jupiter trine 5th lord, Jupiter in 1/5/9, Lagna lord in 5th.
    """
    fired = []

    fifth_sign = ((chart.asc_sign + 4 - 1) % 12) + 1
    fifth_lord = SIGN_LORDS[fifth_sign]
    fifth_lord_natal_sign = chart.planets[fifth_lord]["sign"]
    jup_transit_sign = transit.planet_signs["Jupiter"]

    # Rule 1: Jupiter trine to 5th lord's natal sign (priority 95)
    trine_signs = [fifth_lord_natal_sign,
                   ((fifth_lord_natal_sign + 4 - 1) % 12) + 1,
                   ((fifth_lord_natal_sign + 8 - 1) % 12) + 1]

    if jup_transit_sign in trine_signs:
        fired.append(("phaladeepika_transit_jupiter_trine_5th_lord", 35,
                      [f"Transit Jupiter in {SIGN_NAMES[jup_transit_sign]} "
                       f"(trine to 5th lord's natal {SIGN_NAMES[fifth_lord_natal_sign]})"]))

    # Rule 2: Jupiter in 1st, 5th, or 9th from lagna (priority 92)
    jup_house = transit.planet_houses_from_lagna.get("Jupiter", 0)
    if jup_house in [1, 5, 9]:
        fired.append(("horasara_conception_jupiter_transit", 30,
                      [f"Transit Jupiter in house {jup_house} (dharma trikona)"]))

    # Rule 3: Lagna lord transits 5th house sign (priority 88)
    lagna_lord_transit_sign = transit.planet_signs.get(chart.lagna_lord)
    if lagna_lord_transit_sign == fifth_sign:
        fired.append(("phaladeepika_transit_lagna_lord_5th", 28,
                      [f"Transit Lagna lord ({chart.lagna_lord}) in 5th house sign "
                       f"({SIGN_NAMES[fifth_sign]})"]))

    # Rule 4: Jupiter trine to 5th from Jupiter (Bhavat Bhavam)
    jupiter_natal_sign = chart.planets["Jupiter"]["sign"]
    fifth_from_jup_sign = ((jupiter_natal_sign + 4 - 1) % 12) + 1
    fifth_from_jup_lord = SIGN_LORDS[fifth_from_jup_sign]
    fifth_from_jup_lord_sign = chart.planets.get(fifth_from_jup_lord, {}).get("sign")

    if fifth_from_jup_lord_sign:
        bhavat_trines = [fifth_from_jup_lord_sign,
                         ((fifth_from_jup_lord_sign + 4 - 1) % 12) + 1,
                         ((fifth_from_jup_lord_sign + 8 - 1) % 12) + 1]
        if jup_transit_sign in bhavat_trines:
            fired.append(("phaladeepika_transit_jupiter_trine_dispositor", 25,
                          [f"Transit Jupiter trine to lord of 5th-from-Jupiter"]))

    # Rule 5: Sensitive progeny point
    # Formula: Moon_Nakshatra_Lord_Lon + 5th_Nakshatra_Lord_Lon
    moon_nak_index = int((chart.moon_lon % 360) / 13.3333333333) % 27
    moon_nak_lord = NAKSHATRA_LORDS[moon_nak_index]
    fifth_nak_index = (moon_nak_index + 4) % 27
    fifth_nak_lord = NAKSHATRA_LORDS[fifth_nak_index]

    if moon_nak_lord in chart.birth_positions and fifth_nak_lord in chart.birth_positions:
        sensitive_progeny_point = (
            chart.birth_positions[moon_nak_lord] +
            chart.birth_positions[fifth_nak_lord]
        ) % 360

        if transit.jupiter_trine_degree(sensitive_progeny_point, orb=2.5):
            fired.append(("phaladeepika_transit_jupiter_longitude_sum", 32,
                          [f"Transit Jupiter activating sensitive progeny point "
                           f"({sensitive_progeny_point:.1f}°)"]))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR (Childbirth-specific)
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate fast trigger rules: Moon/Sun/Mars in 5th or 9th house.
    """
    fired = []

    moon_house = transit.planet_houses_from_lagna.get("Moon", 0)
    if moon_house in [5, 9]:
        fired.append(("fast_trigger_childbirth_moon_72_days", 20,
                      [f"Transit Moon in house {moon_house} (72-day trigger)"]))

    sun_house = transit.planet_houses_from_lagna.get("Sun", 0)
    if sun_house in [5, 9]:
        fired.append(("fast_trigger_childbirth_sun_2_months", 22,
                      [f"Transit Sun in house {sun_house} (2-month trigger)"]))

    mars_house = transit.planet_houses_from_lagna.get("Mars", 0)
    if mars_house in [5, 9]:
        fired.append(("fast_trigger_childbirth_mars_75_days", 22,
                      [f"Transit Mars in house {mars_house} (75-day trigger)"]))

    return fired


# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR (Childbirth structural)
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """Evaluate structural patterns: promise, denial, delay."""
    results = {
        "fertility_promise": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    fifth_sign = ((chart.asc_sign + 4 - 1) % 12) + 1
    fifth_lord = SIGN_LORDS[fifth_sign]
    fifth_lord_house = chart.planets[fifth_lord]["house"]
    fifth_house_occupants = [
        n for n, d in chart.planets.items() if d["house"] == 5
    ]
    jupiter_house = chart.planets["Jupiter"]["house"]
    jupiter_sign = chart.planets["Jupiter"]["sign"]

    # Strong: Jupiter in kendra/trikona + 5th lord well placed
    if jupiter_house in {1, 4, 5, 7, 9, 10}:
        results["fertility_promise"] = "strong"
        results["confidence_boost"] += 8
        results["fired_patterns"].append(
            f"jupiter_strong: Jupiter in house {jupiter_house} (kendra/trikona)")

    if fifth_lord_house in BENEFIC_HOUSES:
        results["confidence_boost"] += 5
        results["fired_patterns"].append(
            f"5L_well_placed: 5th lord ({fifth_lord}) in house {fifth_lord_house}")

    # Challenging: 5th lord in dusthana
    if fifth_lord_house in {6, 8, 12}:
        results["fertility_promise"] = "delayed"
        results["confidence_boost"] -= 5
        results["fired_patterns"].append(
            f"5L_dusthana: 5th lord ({fifth_lord}) in house {fifth_lord_house} (delayed)")

    # Jupiter debilitated (Capricorn, sign 10)
    if jupiter_sign == 10:
        results["fertility_promise"] = "delayed"
        results["confidence_boost"] -= 8
        results["fired_patterns"].append(
            "jupiter_debilitated: Jupiter in Capricorn (weak Putrakaraka)")

    # Rahu in 5th aspected by Mars = karmic blockage
    if "Rahu" in fifth_house_occupants:
        rahu_aspected_by_mars = 5 in [
            ((chart.planets["Mars"]["house"] + offset - 1) % 12) + 1
            for offset in [7, 4, 8]  # Mars aspects: 7th, 4th, 8th
        ]
        if rahu_aspected_by_mars:
            results["fertility_promise"] = "blocked"
            results["confidence_boost"] -= 10
            results["fired_patterns"].append(
                "sarpa_shap: Rahu in 5th aspected by Mars (karmic blockage)")

    return results



# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR (Childbirth)
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """Structural assessment of childbirth quality/type."""
    results = {
        "fertility_count": "normal",  # multiple, single, denied
        "conception_mode": "natural",  # natural, ivf, adoption
        "quality": "unknown",  # supportive, difficult, painful
        "fired_outcomes": [],
    }

    fifth_sign = ((chart.asc_sign + 4 - 1) % 12) + 1
    fifth_lord = SIGN_LORDS[fifth_sign]
    fifth_lord_sign = chart.planets[fifth_lord]["sign"]
    fifth_house_occupants = [
        n for n, d in chart.planets.items() if d["house"] == 5
    ]

    # Multiple children: 5L + Jupiter + Mars + Sun in male navamsas
    male_signs = {1, 3, 5, 7, 9, 11}
    fifth_lord_d9 = chart._get_d9_sign(chart.planets[fifth_lord]["longitude"])
    jupiter_d9 = chart._get_d9_sign(chart.planets["Jupiter"]["longitude"])
    mars_d9 = chart._get_d9_sign(chart.planets["Mars"]["longitude"])
    sun_d9 = chart._get_d9_sign(chart.planets["Sun"]["longitude"])

    male_d9_count = sum(1 for s in [fifth_lord_d9, jupiter_d9, mars_d9, sun_d9]
                        if s in male_signs)
    if male_d9_count >= 3:
        results["fertility_count"] = "multiple"
        results["fired_outcomes"].append(
            f"multiple_children: {male_d9_count}/4 key planets in male D9 signs")

    # Single child (Kakavandhya): 5L debilitated + Mercury/Ketu in 5th
    fifth_lord_debilitated = False
    from features.dignity import DEBILITATION
    if fifth_lord in DEBILITATION and fifth_lord_sign == DEBILITATION[fifth_lord]:
        fifth_lord_debilitated = True

    if (fifth_lord_debilitated and
        "Mercury" in fifth_house_occupants and
        "Ketu" in fifth_house_occupants):
        results["fertility_count"] = "single"
        results["fired_outcomes"].append(
            "kakavandhya: 5L debilitated + Mercury + Ketu in 5th (single child only)")

    # Adoption indicator
    if fifth_sign in [3, 6, 10, 11]:  # Owned by Mercury or Saturn
        if ("Saturn" in fifth_house_occupants):
            results["conception_mode"] = "adoption"
            results["fired_outcomes"].append(
                "adoption_indicated: Saturn in 5th house owned by Mercury/Saturn")

    # Difficult quality: malefics in 5th
    malefics_in_5 = [p for p in fifth_house_occupants
                     if p in NATURAL_MALEFICS]
    if len(malefics_in_5) >= 2:
        results["quality"] = "difficult"
        results["fired_outcomes"].append(
            f"difficult_progeny: {len(malefics_in_5)} malefics in 5th ({', '.join(malefics_in_5)})")

    # Jupiter aspecting 5th = protective
    if "Jupiter" in chart._get_aspectors_of_house(5):
        if results["quality"] == "unknown":
            results["quality"] = "supportive"
        results["fired_outcomes"].append(
            "jupiter_protects_5th: Jupiter aspects 5th house (benefic for children)")

    return results



# ═══════════════════════════════════════════════════════════════
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE
# ═══════════════════════════════════════════════════════════════

class ChildbirthWindowResult:
    """Result of evaluating a single time window for childbirth."""

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
        """Compute score using childbirth calibration weights."""
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



def scan_childbirth_windows(chart: ChartState, start_age=18, end_age=45):
    """
    Scan through life for childbirth windows.
    For each AD period, evaluate the 5-layer engine.
    Returns sorted list of ChildbirthWindowResult.
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

            effective_start = max(ad["start"],
                chart.birth_dt + timedelta(days=start_age * 365.25))
            effective_end = min(ad["end"],
                chart.birth_dt + timedelta(days=end_age * 365.25))

            # LAYER 1: DASHA (gate)
            dasha_results = evaluate_dasha_layer(chart, md["lord"], ad["lord"])
            if not dasha_results:
                continue

            # LAYER 2: TRANSIT (midpoint + start + end)
            mid_date = effective_start + (effective_end - effective_start) / 2
            transit_mid = TransitState(mid_date, chart)
            transit_start = TransitState(effective_start, chart)
            transit_end = TransitState(effective_end, chart)

            all_transit = {}
            for ts in [transit_mid, transit_start, transit_end]:
                for rule_id, score, reasons in evaluate_transit_layer(chart, ts):
                    if rule_id not in all_transit or score > all_transit[rule_id][1]:
                        all_transit[rule_id] = (rule_id, score, reasons)
            merged_transit = list(all_transit.values())

            # LAYER 3: FAST TRIGGER
            all_fast = {}
            for ts in [transit_mid, transit_start, transit_end]:
                for rule_id, score, reasons in evaluate_fast_trigger_layer(chart, ts):
                    if rule_id not in all_fast or score > all_fast[rule_id][1]:
                        all_fast[rule_id] = (rule_id, score, reasons)
            merged_fast = list(all_fast.values())

            # Build result
            result = ChildbirthWindowResult()
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
# MAIN — TEST EXECUTION
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from datetime import datetime

    # Sachin Tendulkar: 24/04/1973, 16:25, Mumbai
    # First child: Sara - 12/10/1997 (age ~24.5)
    BIRTH = datetime(1973, 4, 24, 16, 25)
    LAT, LON = 19.076, 72.8777

    print("=" * 70)
    print("  CHILDBIRTH ENGINE — Sachin Tendulkar")
    print("  First child (Sara): 12 Oct 1997")
    print("=" * 70)

    chart = ChartState(BIRTH, LAT, LON)

    fifth_sign = ((chart.asc_sign + 4 - 1) % 12) + 1
    fifth_lord = SIGN_LORDS[fifth_sign]

    print(f"\n  Lagna: {SIGN_NAMES[chart.asc_sign]} | 5th sign: {SIGN_NAMES[fifth_sign]}")
    print(f"  5th Lord: {fifth_lord} (house {chart.planets[fifth_lord]['house']})")
    print(f"  Jupiter: house {chart.planets['Jupiter']['house']}, {SIGN_NAMES[chart.planets['Jupiter']['sign']]}")

    classical = evaluate_classical_layer(chart)
    print(f"\n  Classical: promise={classical['fertility_promise']}")
    for p in classical["fired_patterns"]:
        print(f"    * {p}")

    outcome = evaluate_outcome_layer(chart)
    print(f"  Outcome: count={outcome['fertility_count']}, mode={outcome['conception_mode']}, quality={outcome['quality']}")
    for o in outcome["fired_outcomes"]:
        print(f"    * {o}")

    print(f"\n  Scanning windows (age 20-30)...")
    windows = scan_childbirth_windows(chart, start_age=20, end_age=30)

    print(f"  Found {len(windows)} windows. Top 10:")
    print(f"  {'#':<3} {'Period':<26} {'Age':<10} {'Score':<7} {'Band':<7} {'MD-AD':<16}")
    print(f"  {'─'*3} {'─'*26} {'─'*10} {'─'*7} {'─'*7} {'─'*16}")

    for i, w in enumerate(windows[:10], 1):
        period = f"{w.period_start.strftime('%b %Y')}-{w.period_end.strftime('%b %Y')}"
        age = f"{w.age_start:.1f}-{w.age_end:.1f}"
        print(f"  {i:<3} {period:<26} {age:<10} {w.total_score:<7.1f} {w.timing_band:<7} {w.md_lord}-{w.ad_lord:<16}")

    # Check if actual date falls in a window
    actual = datetime(1997, 10, 12)
    print(f"\n  Actual childbirth: {actual.strftime('%d %b %Y')}")
    for i, w in enumerate(windows):
        if w.period_start <= actual <= w.period_end:
            print(f"  MATCH at rank #{i+1} (score {w.total_score:.1f})")
            break
    else:
        print("  NOT in any detected window")
