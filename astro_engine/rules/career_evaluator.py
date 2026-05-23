"""
Career Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow
for career/profession events.

Reuses ChartState and TransitState from marriage_evaluator (generic infra).
Domain-specific logic is isolated here per Astrolyn architecture.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rules.marriage_evaluator import (
    ChartState, TransitState, SIGN_NAMES,
    NATURAL_BENEFICS, NATURAL_MALEFICS, BENEFIC_HOUSES, MALEFIC_HOUSES,
    IST_OFFSET, ist_to_utc, get_jd, NAKSHATRA_LORDS,
)
from features.dasha import _generate_md_periods, _generate_ad_periods
from features.dignity import SIGN_LORDS, get_sign

# ═══════════════════════════════════════════════════════════════
# CAREER CALIBRATION (Layer 3 — domain-isolated)
# ═══════════════════════════════════════════════════════════════
RULES_DIR = Path(__file__).resolve().parent / "domains" / "career" / "career_profession"


def _load_career_calibration():
    """Load career-specific calibration overlay."""
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
                "very_high": 50, "high": 35,
                "moderate": 22, "low": 12,
            },
        }

CALIBRATION = _load_career_calibration()




# ═══════════════════════════════════════════════════════════════
# LAYER 1: DASHA EVALUATOR (Career-specific)
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate career dasha rules against current MD/AD.
    Key planets: 10th lord, Sun, Saturn, 9th lord, Lagna lord,
    10th house occupants, 10th house aspectors.
    """
    fired = []

    tenth_sign = ((chart.asc_sign + 9 - 1) % 12) + 1
    tenth_lord = SIGN_LORDS[tenth_sign]
    ninth_sign = ((chart.asc_sign + 8 - 1) % 12) + 1
    ninth_lord = SIGN_LORDS[ninth_sign]
    fifth_sign = ((chart.asc_sign + 4 - 1) % 12) + 1
    fifth_lord = SIGN_LORDS[fifth_sign]
    fourth_sign = ((chart.asc_sign + 3 - 1) % 12) + 1
    fourth_lord = SIGN_LORDS[fourth_sign]

    tenth_house_occupants = [
        n for n, d in chart.planets.items() if d["house"] == 10
    ]
    tenth_house_aspectors = chart._get_aspectors_of_house(10)

    # Rule 1: Primary — 10th lord MD/AD (priority 98)
    r1_score = 0
    r1_reasons = []

    if md_lord == tenth_lord:
        r1_score += 45
        r1_reasons.append(f"MD of 10th lord ({tenth_lord})")
    elif ad_lord == tenth_lord:
        r1_score += 35
        r1_reasons.append(f"AD of 10th lord ({tenth_lord})")

    if md_lord in tenth_house_occupants or ad_lord in tenth_house_occupants:
        r1_score += 30
        occ = md_lord if md_lord in tenth_house_occupants else ad_lord
        r1_reasons.append(f"{'MD' if occ == md_lord else 'AD'} of 10th occupant ({occ})")

    if md_lord in tenth_house_aspectors or ad_lord in tenth_house_aspectors:
        r1_score += 22
        asp = md_lord if md_lord in tenth_house_aspectors else ad_lord
        r1_reasons.append(f"{'MD' if asp == md_lord else 'AD'} of 10th aspector ({asp})")

    if md_lord == chart.lagna_lord or ad_lord == chart.lagna_lord:
        r1_score += 18
        r1_reasons.append(f"Period of Lagna lord ({chart.lagna_lord})")

    if r1_score > 0:
        fired.append(("bphs_dasha_10th_lord", r1_score, r1_reasons))

    # Rule 2: Rajayoga lords — 9th/10th/5th conjunction (priority 90)
    raja_lords = {ninth_lord, tenth_lord, fifth_lord, fourth_lord}
    r2_score = 0
    r2_reasons = []

    if md_lord in raja_lords:
        r2_score += 25
        r2_reasons.append(f"MD of Rajayoga lord {md_lord}")
    if ad_lord in raja_lords and ad_lord != md_lord:
        r2_score += 20
        r2_reasons.append(f"AD of Rajayoga lord {ad_lord}")

    if r2_score > 0:
        fired.append(("bphs_dasha_rajayoga_9_10_5", r2_score, r2_reasons))


    # Rule 3: Saturn-Saturn strong (priority 88)
    r3_score = 0
    r3_reasons = []
    saturn_house = chart.planets["Saturn"]["house"]
    saturn_sign = chart.planets["Saturn"]["sign"]
    kendra_trikona = {1, 4, 5, 7, 9, 10}

    if md_lord == "Saturn" and ad_lord == "Saturn":
        if saturn_sign in [7, 10, 11] or saturn_house in kendra_trikona:
            r3_score += 30
            r3_reasons.append(f"Saturn-Saturn with Saturn strong (H{saturn_house})")

    if r3_score > 0:
        fired.append(("bphs_dasha_saturn_saturn_strong", r3_score, r3_reasons))

    # Rule 4: Saturn-Venus (priority 92)
    r4_score = 0
    r4_reasons = []
    venus_house = chart.planets["Venus"]["house"]
    kendra_trikona_11 = {1, 4, 5, 7, 9, 10, 11}

    if md_lord == "Saturn" and ad_lord == "Venus" and venus_house in kendra_trikona_11:
        r4_score += 32
        r4_reasons.append(f"Saturn-Venus with Venus well-placed (H{venus_house})")

    if r4_score > 0:
        fired.append(("bphs_dasha_saturn_venus_career", r4_score, r4_reasons))

    # Rule 5: Sun-Mercury / Sun-Jupiter (priority 80-82)
    r5_score = 0
    r5_reasons = []
    if md_lord == "Sun" and ad_lord == "Mercury":
        r5_score += 25
        r5_reasons.append("Sun-Mercury (administrative authority)")
    elif md_lord == "Sun" and ad_lord == "Jupiter":
        r5_score += 25
        r5_reasons.append("Sun-Jupiter (government recognition)")
    elif md_lord == "Mercury" and ad_lord == "Jupiter":
        r5_score += 22
        r5_reasons.append("Mercury-Jupiter (business profits)")

    if r5_score > 0:
        fired.append(("bphs_dasha_specific_combos", r5_score, r5_reasons))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR (Career-specific)
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """Evaluate career transit rules."""
    fired = []

    tenth_sign = ((chart.asc_sign + 9 - 1) % 12) + 1
    tenth_lord = SIGN_LORDS[tenth_sign]

    # Rule 1: Double transit on 10th house (priority 98)
    jup_on_10 = transit.planet_aspects_house("Jupiter", 10, "lagna")
    sat_on_10 = transit.planet_aspects_house("Saturn", 10, "lagna")

    if jup_on_10 and sat_on_10:
        fired.append(("double_transit_career_enhancement", 45,
                      ["Double transit (Jup+Sat) on 10th house from Lagna"]))

    # Rule 2: Saturn in 10th house (priority 90)
    sat_house = transit.planet_houses_from_lagna.get("Saturn", 0)
    if sat_house == 10:
        fired.append(("saturn_transit_10th_house", 30,
                      ["Transit Saturn in 10th house (career restructuring)"]))

    # Rule 3: 10th lord in upachaya (priority 85)
    tenth_lord_transit_sign = transit.planet_signs.get(tenth_lord)
    if tenth_lord_transit_sign:
        tenth_lord_transit_house = chart.get_house_from_sign(tenth_lord_transit_sign)
        if tenth_lord_transit_house in [3, 6, 10, 11]:
            fired.append(("transit_10th_lord_upachaya", 28,
                          [f"Transit 10th lord ({tenth_lord}) in upachaya H{tenth_lord_transit_house}"]))

    # Rule 4: Jupiter trine to 10th lord natal sign (general support)
    tenth_lord_natal_sign = chart.planets[tenth_lord]["sign"]
    jup_transit_sign = transit.planet_signs["Jupiter"]
    trine_signs = [tenth_lord_natal_sign,
                   ((tenth_lord_natal_sign + 4 - 1) % 12) + 1,
                   ((tenth_lord_natal_sign + 8 - 1) % 12) + 1]
    if jup_transit_sign in trine_signs:
        fired.append(("jupiter_trine_10th_lord", 25,
                      [f"Transit Jupiter trine to 10th lord's sign ({SIGN_NAMES[tenth_lord_natal_sign]})"]))

    return fired




# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR (Career-specific)
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """Evaluate fast triggers: karma nakshatra, Sun/Mars in 10th."""
    fired = []

    # Sun in 10th or 11th = career visibility trigger
    sun_house = transit.planet_houses_from_lagna.get("Sun", 0)
    if sun_house in [10, 11]:
        fired.append(("fast_trigger_sun_10_11", 20,
                      [f"Transit Sun in house {sun_house} (career visibility)"]))

    # Mars in 10th = action/initiative trigger
    mars_house = transit.planet_houses_from_lagna.get("Mars", 0)
    if mars_house == 10:
        fired.append(("fast_trigger_mars_10th", 22,
                      ["Transit Mars in 10th house (action/initiative trigger)"]))

    # Karma nakshatra (10th from Moon) — benefic hit
    moon_nak_index = int((chart.moon_lon % 360) / 13.3333333333) % 27
    karma_nak_index = (moon_nak_index + 9) % 27  # 10th from Moon
    karma_nak_start = karma_nak_index * 13.3333333333
    karma_nak_mid = karma_nak_start + 6.6666

    jup_lon = transit.positions.get("Jupiter", 0)
    diff = abs((jup_lon - karma_nak_mid) % 360)
    diff = min(diff, 360 - diff)
    if diff <= 7:  # Within the nakshatra span
        fired.append(("fast_trigger_karma_nakshatra_success", 28,
                      [f"Jupiter near Karma Nakshatra (10th star, {diff:.1f}° from mid)"]))

    return fired


# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR (Career structural)
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """Evaluate structural patterns: rajayogas, planet placements."""
    results = {
        "career_promise": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    tenth_sign = ((chart.asc_sign + 9 - 1) % 12) + 1
    tenth_lord = SIGN_LORDS[tenth_sign]
    tenth_lord_house = chart.planets[tenth_lord]["house"]
    jupiter_house = chart.planets["Jupiter"]["house"]
    mars_house = chart.planets["Mars"]["house"]
    saturn_house = chart.planets["Saturn"]["house"]

    # Jupiter in kendra/trikona = strong career support
    if jupiter_house in {1, 4, 5, 7, 9, 10}:
        results["confidence_boost"] += 8
        results["fired_patterns"].append(
            f"jupiter_strong: Jupiter in H{jupiter_house} (career support)")

    # 10th lord in kendra = strong career foundation
    if tenth_lord_house in {1, 4, 7, 10}:
        results["career_promise"] = "strong"
        results["confidence_boost"] += 10
        results["fired_patterns"].append(
            f"10L_kendra: 10th lord ({tenth_lord}) in kendra H{tenth_lord_house}")

    # 10th lord in dusthana = career challenges
    if tenth_lord_house in {6, 8, 12}:
        results["career_promise"] = "unstable"
        results["confidence_boost"] -= 5
        results["fired_patterns"].append(
            f"10L_dusthana: 10th lord ({tenth_lord}) in H{tenth_lord_house} (challenges)")

    # Mars-Jupiter conjunction = administrative yoga
    if mars_house == jupiter_house:
        results["confidence_boost"] += 8
        results["fired_patterns"].append(
            "mars_jupiter_conjunct: Administrative leadership potential")

    # Mars exalted in Capricorn (sign 10) = executive energy
    if chart.planets["Mars"]["sign"] == 10:
        results["confidence_boost"] += 6
        results["fired_patterns"].append(
            "mars_exalted_capricorn: Executive ambition and competitive drive")

    return results




# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR (Career)
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """Structural assessment of career type/quality."""
    results = {
        "career_type": "unknown",  # government, business, corporate, spiritual
        "stability": "unknown",    # stable, unstable, mixed
        "leadership_potential": False,
        "fired_outcomes": [],
    }

    tenth_sign = ((chart.asc_sign + 9 - 1) % 12) + 1
    tenth_lord = SIGN_LORDS[tenth_sign]
    tenth_lord_house = chart.planets[tenth_lord]["house"]
    tenth_house_occupants = [n for n, d in chart.planets.items() if d["house"] == 10]

    # Sun in 10th = executive/government
    if "Sun" in tenth_house_occupants:
        results["career_type"] = "government"
        results["leadership_potential"] = True
        results["fired_outcomes"].append("sun_10th: Executive/government leadership")

    # Saturn in 10th = government/populist
    if "Saturn" in tenth_house_occupants:
        results["career_type"] = "government"
        results["stability"] = "stable"
        results["fired_outcomes"].append("saturn_10th: Disciplined rise, government/labor")

    # Jupiter in 10th = ethical leadership
    if "Jupiter" in tenth_house_occupants:
        results["career_type"] = "consulting"
        results["leadership_potential"] = True
        results["fired_outcomes"].append("jupiter_10th: Ethical leadership, advisory roles")

    # Mercury in 10th = business/commerce
    if "Mercury" in tenth_house_occupants:
        results["career_type"] = "business"
        results["fired_outcomes"].append("mercury_10th: Commerce, law, administration")

    # 10th lord in 7th = business/public fame
    if tenth_lord_house == 7:
        results["career_type"] = "business"
        results["stability"] = "stable"
        results["leadership_potential"] = True
        results["fired_outcomes"].append("10L_7th: Business acumen, public fame")

    # 10th lord in 8th = unstable/research
    if tenth_lord_house == 8:
        results["stability"] = "unstable"
        results["fired_outcomes"].append("10L_8th: Career breaks, research/esoteric expertise")

    # Mars exalted = corporate executive
    if chart.planets["Mars"]["sign"] == 10:
        results["career_type"] = "corporate"
        results["leadership_potential"] = True
        results["fired_outcomes"].append("mars_capricorn: Corporate executive energy")

    # Default stability from 10th lord placement
    if results["stability"] == "unknown":
        if tenth_lord_house in BENEFIC_HOUSES:
            results["stability"] = "stable"
        elif tenth_lord_house in MALEFIC_HOUSES:
            results["stability"] = "unstable"

    return results



# ═══════════════════════════════════════════════════════════════
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE
# ═══════════════════════════════════════════════════════════════

class CareerWindowResult:
    """Result of evaluating a single time window for career events."""

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
        """Compute score using career calibration weights."""
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




def scan_career_windows(chart: ChartState, start_age=18, end_age=65):
    """
    Scan through life for career event windows.
    Returns sorted list of CareerWindowResult.
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

            # LAYER 2: TRANSIT (midpoint + boundaries)
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
            result = CareerWindowResult()
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
    # Modi: 17 Sep 1950, 11:00, Vadnagar → PM on 26 May 2014
    # Sachin: 24 Apr 1973, 16:25, Mumbai → Debut 15 Nov 1989
    TEST_CASES = [
        ("Modi (PM 2014)", datetime(1950, 9, 17, 11, 0), 23.7833, 72.6333,
         datetime(2014, 5, 26)),
        ("Sachin (Debut 1989)", datetime(1973, 4, 24, 16, 25), 19.076, 72.8777,
         datetime(1989, 11, 15)),
        ("Dhoni (Captain 2007)", datetime(1981, 7, 7, 11, 15), 23.3441, 85.3096,
         datetime(2007, 9, 24)),
    ]

    print("=" * 70)
    print("  CAREER ENGINE VALIDATION")
    print("=" * 70)

    for name, birth_dt, lat, lon, event_date in TEST_CASES:
        chart = ChartState(birth_dt, lat, lon)
        event_age = (event_date - birth_dt).days / 365.25

        windows = scan_career_windows(chart,
            start_age=max(15, event_age - 5),
            end_age=min(70, event_age + 5))

        matched_rank = -1
        for i, w in enumerate(windows):
            if w.period_start <= event_date <= w.period_end:
                matched_rank = i + 1
                break

        in_top5 = matched_rank > 0 and matched_rank <= 5
        score = windows[matched_rank - 1].total_score if matched_rank > 0 else 0
        md_ad = (f"{windows[matched_rank-1].md_lord}-{windows[matched_rank-1].ad_lord}"
                 if matched_rank > 0 else "MISS")

        rank_s = f"#{matched_rank}" if matched_rank > 0 else "MISS"
        top5_s = "Y" if in_top5 else "N"
        print(f"  {name:<25} age={event_age:.1f}  rank={rank_s:<5} "
              f"top5={top5_s}  score={score:.1f}  {md_ad}")

    print()
    print("  Done.")
