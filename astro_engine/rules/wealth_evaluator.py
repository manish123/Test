"""
Wealth Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow.
Domain: Wealth, Financial Gain & Accumulation

Post-refactor pattern: imports shared infrastructure from evaluator_base.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from features.dasha import get_current_vimshottari, _generate_md_periods, _generate_ad_periods
from features.dignity import SIGN_LORDS, get_sign
from features.nakshatra import get_nakshatra, nakshatra_list

# ── Shared infrastructure ─────────────────────────────────────
from rules.evaluator_base import (
    IST_OFFSET, ist_to_utc, get_jd,
    SIGN_NAMES, NAKSHATRA_LORDS,
    NATURAL_BENEFICS, NATURAL_MALEFICS, BENEFIC_HOUSES, MALEFIC_HOUSES,
    JUPITER_ASPECTS, SATURN_ASPECTS, MARS_ASPECTS,
    BaseChartState, BaseTransitState,
    load_calibration,
)

# ═══════════════════════════════════════════════════════════════
# DOMAIN-SPECIFIC CONSTANTS
# ═══════════════════════════════════════════════════════════════
RULES_DIR = Path(__file__).resolve().parent / "domains" / "finance" / "wealth_financial_gain_and_accumulation"

# Wealth karakas: Jupiter=expansion, Venus=luxury, Mercury=commerce, Moon=nourishment
WEALTH_KARAKAS = {"Jupiter", "Venus", "Mercury", "Moon", "Rahu"}
# Key wealth houses: 2=savings, 5=speculation, 8=inheritance, 9=fortune, 11=gains
WEALTH_HOUSES = {2, 5, 8, 9, 11}

# ═══════════════════════════════════════════════════════════════
# CALIBRATION
# ═══════════════════════════════════════════════════════════════
CALIBRATION = load_calibration(
    RULES_DIR / "calibration_overlay.json",
    fallback_defaults={
        "layer_weights": {
            "dasha_weight": 0.30,
            "transit_weight": 0.35,
            "fast_trigger_weight": 0.20,
            "classical_weight": 0.15,
        },
        "likelihood_thresholds": {
            "very_high": 55, "high": 40, "moderate": 25, "low": 15,
        },
    },
)


# ═══════════════════════════════════════════════════════════════
# CHART STATE (thin subclass)
# ═══════════════════════════════════════════════════════════════

class ChartState(BaseChartState):
    """Wealth-domain chart state with finance-specific house lords."""

    def __init__(self, birth_dt, lat, lon, alt=0):
        super().__init__(birth_dt, lat, lon, alt)

        # Wealth-relevant house lords
        self.second_sign = ((self.asc_sign + 1 - 1) % 12) + 1
        self.second_lord = SIGN_LORDS[self.second_sign]
        self.fifth_sign = ((self.asc_sign + 4 - 1) % 12) + 1
        self.fifth_lord = SIGN_LORDS[self.fifth_sign]
        self.eighth_sign = ((self.asc_sign + 7 - 1) % 12) + 1
        self.eighth_lord = SIGN_LORDS[self.eighth_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.tenth_sign = ((self.asc_sign + 9 - 1) % 12) + 1
        self.tenth_lord = SIGN_LORDS[self.tenth_sign]
        self.eleventh_sign = ((self.asc_sign + 10 - 1) % 12) + 1
        self.eleventh_lord = SIGN_LORDS[self.eleventh_sign]

        # Moon dispositor
        self.moon_lord = SIGN_LORDS[self.moon_sign]

        # Janma Nakshatra index
        self.janma_nak_index = int((self.moon_lon % 360) / 13.3333333333) % 27
        self.janma_nakshatra_lord = NAKSHATRA_LORDS[self.janma_nak_index]


# ═══════════════════════════════════════════════════════════════
# TRANSIT STATE (pass-through)
# ═══════════════════════════════════════════════════════════════

class TransitState(BaseTransitState):
    """Wealth-domain transit state."""
    pass


# ═══════════════════════════════════════════════════════════════
# LAYER 1: DASHA EVALUATOR (Wealth-specific)
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate wealth dasha/transit rules.
    Uses transit positions relative to Moon sign (Gochara from Moon).
    """
    fired = []

    # Jupiter in 2nd or 11th from Moon
    jup_house_from_moon = transit.planet_houses_from_moon.get("Jupiter", 0)
    if jup_house_from_moon in [2, 11]:
        fired.append(("transit_jupiter_2_11_from_moon_wealth", 45,
                      [f"Transit Jupiter in {jup_house_from_moon}th from Moon (wealth window)"]))

    # Mercury in 2/4/8/11 from Moon
    merc_house_from_moon = transit.planet_houses_from_moon.get("Mercury", 0)
    if merc_house_from_moon in [2, 4, 8, 11]:
        fired.append(("transit_mercury_2_4_8_11_from_moon_wealth", 25,
                      [f"Transit Mercury in {merc_house_from_moon}th from Moon (commercial gain)"]))

    # Venus in 2/8/9 from Moon
    venus_house_from_moon = transit.planet_houses_from_moon.get("Venus", 0)
    if venus_house_from_moon in [2, 8, 9]:
        fired.append(("transit_venus_2_8_9_from_moon_wealth", 28,
                      [f"Transit Venus in {venus_house_from_moon}th from Moon (prosperity)"]))

    # Rahu in 10th from Moon
    rahu_house_from_moon = transit.planet_houses_from_moon.get("Rahu", 0)
    if rahu_house_from_moon == 10:
        fired.append(("transit_rahu_10_from_moon_wealth", 35,
                      [f"Transit Rahu in 10th from Moon (ambitious gains)"]))

    # Jupiter conjunct natal Sun (within 10 degrees)
    jup_lon = transit.positions.get("Jupiter", 0)
    sun_natal_lon = chart.birth_positions.get("Sun", 0)
    diff = abs((jup_lon - sun_natal_lon) % 360)
    diff = min(diff, 360 - diff)
    if diff <= 10:
        fired.append(("transit_jupiter_on_natal_sun_wealth", 38,
                      [f"Transit Jupiter conjunct natal Sun ({diff:.1f}° orb)"]))

    return fired


# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR (same as dasha for this domain)
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """Transit layer — same rules as dasha for wealth (Gochara-based domain)."""
    return evaluate_dasha_layer(chart, transit)


# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate Anga Gochara fast triggers for wealth.
    Moon/Mars/Mercury in specific Nakshatras from birth star.
    """
    fired = []
    janma_idx = chart.janma_nak_index

    # Moon in 9th/10th nakshatra (eyes — gain of wealth)
    moon_lon = transit.positions.get("Moon", 0)
    moon_nak_idx = int((moon_lon % 360) / 13.3333333333) % 27
    moon_offset = (moon_nak_idx - janma_idx) % 27 + 1

    if moon_offset in [9, 10]:
        fired.append(("fast_trigger_moon_9_10_nakshatra_wealth", 30,
                      [f"Moon in {moon_offset}th nakshatra from birth star (eyes — wealth gain)"]))

    if moon_offset in [25, 26, 27]:
        fired.append(("fast_trigger_moon_25_to_27_nakshatra_acquisition", 28,
                      [f"Moon in {moon_offset}th nakshatra from birth star (right hand — acquisition)"]))

    # Mars in 16th/17th nakshatra (head — gains)
    mars_lon = transit.positions.get("Mars", 0)
    mars_nak_idx = int((mars_lon % 360) / 13.3333333333) % 27
    mars_offset = (mars_nak_idx - janma_idx) % 27 + 1

    if mars_offset in [16, 17]:
        fired.append(("fast_trigger_mars_16_17_nakshatra_gains", 25,
                      [f"Mars in {mars_offset}th nakshatra from birth star (head — aggressive gains)"]))

    # Mercury in 4th-6th nakshatra (face — financial gain)
    merc_lon = transit.positions.get("Mercury", 0)
    merc_nak_idx = int((merc_lon % 360) / 13.3333333333) % 27
    merc_offset = (merc_nak_idx - janma_idx) % 27 + 1

    if merc_offset in [4, 5, 6]:
        fired.append(("fast_trigger_mercury_4_to_6_nakshatra_financial_gain", 22,
                      [f"Mercury in {merc_offset}th nakshatra from birth star (face — income)"]))

    if merc_offset in [13, 14, 15, 16, 17]:
        fired.append(("fast_trigger_mercury_13_to_17_nakshatra_wealth_spike", 28,
                      [f"Mercury in {merc_offset}th nakshatra from birth star (belly — wealth spike)"]))

    return fired


# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """Evaluate structural Dhana Yogas in the natal chart."""
    results = {
        "wealth_promise": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    second_lord_house = chart.planets[chart.second_lord]["house"]
    eleventh_lord_house = chart.planets[chart.eleventh_lord]["house"]
    fifth_lord_house = chart.planets[chart.fifth_lord]["house"]
    ninth_lord_house = chart.planets[chart.ninth_lord]["house"]
    tenth_lord_house = chart.planets[chart.tenth_lord]["house"]
    jupiter_house = chart.planets["Jupiter"]["house"]
    venus_house = chart.planets["Venus"]["house"]
    moon_house = chart.planets["Moon"]["house"]

    # Dhana Yoga: 2nd/11th lord exchange
    if second_lord_house == 11 and eleventh_lord_house == 2:
        results["wealth_promise"] = "exceptional"
        results["confidence_boost"] += 20
        results["fired_patterns"].append(
            f"dhana_yoga_2_11_exchange: {chart.second_lord} (2L) in 11th, {chart.eleventh_lord} (11L) in 2nd")

    # 2nd and 11th lords conjunct in kendra/trikona
    if second_lord_house == eleventh_lord_house and second_lord_house in {1, 4, 5, 7, 9, 10}:
        results["wealth_promise"] = "strong"
        results["confidence_boost"] += 15
        results["fired_patterns"].append(
            f"dhana_yoga_2_11_conjunct: Both in H{second_lord_house}")

    # Jupiter in 11th
    if jupiter_house == 11:
        results["confidence_boost"] += 10
        results["fired_patterns"].append("jupiter_11th: Jupiter in house of gains")

    # Venus in 9th (fortune)
    if venus_house == 9:
        results["confidence_boost"] += 8
        results["fired_patterns"].append("venus_9th: Venus in house of fortune")

    # 9th + 10th lords conjunct (Raja-Dhana)
    if ninth_lord_house == tenth_lord_house:
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            f"raja_dhana: 9L ({chart.ninth_lord}) + 10L ({chart.tenth_lord}) conjunct in H{ninth_lord_house}")

    # 5th/8th exchange (speculative)
    eighth_lord_house = chart.planets[chart.eighth_lord]["house"]
    if fifth_lord_house == 8 and eighth_lord_house == 5:
        results["wealth_promise"] = "speculative"
        results["confidence_boost"] += 15
        results["fired_patterns"].append("5_8_exchange: Speculative wealth archetype")

    # Benefics in upachaya from Moon
    upachaya_from_moon = set()
    for name in ["Jupiter", "Venus", "Mercury"]:
        p_sign = chart.planets[name]["sign"]
        h_from_moon = ((p_sign - chart.moon_sign) % 12) + 1
        if h_from_moon in [3, 6, 10, 11]:
            upachaya_from_moon.add(name)
    if len(upachaya_from_moon) == 3:
        results["wealth_promise"] = "strong"
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            f"lunar_upachaya_affluence: All benefics in upachaya from Moon")

    return results


# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """Classify the type of wealth the native is likely to accumulate."""
    results = {
        "wealth_type": "general",
        "stability": "unknown",
        "fired_outcomes": [],
    }

    moon_house = chart.planets["Moon"]["house"]
    mars_house = chart.planets["Mars"]["house"]
    eighth_lord_house = chart.planets[chart.eighth_lord]["house"]

    # Chandra-Mangala in 11th → network wealth
    if moon_house == 11 and mars_house == 11:
        results["wealth_type"] = "network_based"
        results["stability"] = "dynamic"
        results["fired_outcomes"].append("chandra_mangala_11th: Network-based wealth")

    # Chandra-Mangala in 5th → speculative/creative
    if moon_house == 5 and mars_house == 5:
        results["wealth_type"] = "speculative"
        results["stability"] = "volatile"
        results["fired_outcomes"].append("chandra_mangala_5th: Creative/speculative wealth")

    # 8th lord in 6th → hidden wealth
    if eighth_lord_house == 6:
        results["wealth_type"] = "hidden"
        results["stability"] = "stable"
        results["fired_outcomes"].append("8L_in_6th: Hidden wealth from confidential deals")

    # Jupiter in 11th + Moon in 2nd + Venus in 9th → luxury
    jup_h = chart.planets["Jupiter"]["house"]
    venus_h = chart.planets["Venus"]["house"]
    if jup_h == 11 and moon_house == 2 and venus_h == 9:
        results["wealth_type"] = "luxury"
        results["stability"] = "stable"
        results["fired_outcomes"].append("benefic_triad: Luxury lifestyle archetype")

    # Default stability from 2nd/11th lord placement
    if results["stability"] == "unknown":
        second_h = chart.planets[chart.second_lord]["house"]
        eleventh_h = chart.planets[chart.eleventh_lord]["house"]
        if second_h in BENEFIC_HOUSES and eleventh_h in BENEFIC_HOUSES:
            results["stability"] = "stable"
        elif second_h in MALEFIC_HOUSES or eleventh_h in MALEFIC_HOUSES:
            results["stability"] = "unstable"
        else:
            results["stability"] = "moderate"

    return results


# ═══════════════════════════════════════════════════════════════
# COMPOSITE SCORER
# ═══════════════════════════════════════════════════════════════

class WealthWindowResult:
    """Result of evaluating a single time window for wealth events."""

    def __init__(self):
        self.eval_date = None
        self.dasha_fired = []
        self.transit_fired = []
        self.fast_trigger_fired = []
        self.classical = {}
        self.outcome = {}
        self.total_score = 0
        self.timing_band = "broad"
        self.likelihood = "low"

    def compute_composite_score(self):
        dasha_score = sum(s for _, s, _ in self.dasha_fired)
        transit_score = sum(s for _, s, _ in self.transit_fired)
        fast_score = sum(s for _, s, _ in self.fast_trigger_fired)
        classical_boost = self.classical.get("confidence_boost", 0)

        lw = CALIBRATION.get("layer_weights", {})
        self.total_score = (
            dasha_score * lw.get("dasha_weight", 0.30) +
            transit_score * lw.get("transit_weight", 0.35) +
            fast_score * lw.get("fast_trigger_weight", 0.20) +
            classical_boost * lw.get("classical_weight", 0.15)
        )

        if fast_score > 20:
            self.timing_band = "exact"
        elif transit_score > 25:
            self.timing_band = "narrow"
        else:
            self.timing_band = "broad"

        lt = CALIBRATION.get("likelihood_thresholds", {})
        if self.total_score >= lt.get("very_high", 55):
            self.likelihood = "VERY_HIGH"
        elif self.total_score >= lt.get("high", 40):
            self.likelihood = "HIGH"
        elif self.total_score >= lt.get("moderate", 25):
            self.likelihood = "MODERATE"
        elif self.total_score >= lt.get("low", 15):
            self.likelihood = "LOW"
        else:
            self.likelihood = "VERY_LOW"


# ═══════════════════════════════════════════════════════════════
# SINGLE-DATE EVALUATOR
# ═══════════════════════════════════════════════════════════════

def evaluate_wealth_for_date(chart: ChartState, eval_date: datetime):
    """
    Run the full 5-layer wealth evaluation for a specific date.
    Returns a WealthWindowResult.
    """
    transit = TransitState(eval_date, chart)

    result = WealthWindowResult()
    result.eval_date = eval_date
    result.dasha_fired = evaluate_dasha_layer(chart, transit)
    result.transit_fired = evaluate_transit_layer(chart, transit)
    result.fast_trigger_fired = evaluate_fast_trigger_layer(chart, transit)
    result.classical = evaluate_classical_layer(chart)
    result.outcome = evaluate_outcome_layer(chart)
    result.compute_composite_score()

    return result


# ═══════════════════════════════════════════════════════════════
# MAIN — TEST EXECUTION
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Base subject: 22 July 1975, 18:15 IST, Bhilai
    BIRTH_DT = datetime(1975, 7, 22, 18, 15)
    LAT, LON, ALT = 21.2094, 81.4285, 297

    print("=" * 70)
    print("  WEALTH EVALUATOR — Base Subject (22 Jul 1975, 18:15, Bhilai)")
    print("=" * 70)

    chart = ChartState(BIRTH_DT, LAT, LON, ALT)

    print(f"\n  Lagna: {SIGN_NAMES[chart.asc_sign]} | Moon: {SIGN_NAMES[chart.moon_sign]}")
    print(f"  2L: {chart.second_lord} (H{chart.planets[chart.second_lord]['house']})")
    print(f"  11L: {chart.eleventh_lord} (H{chart.planets[chart.eleventh_lord]['house']})")
    print(f"  Jupiter: H{chart.planets['Jupiter']['house']} | Venus: H{chart.planets['Venus']['house']}")

    # Classical assessment
    classical = evaluate_classical_layer(chart)
    print(f"\n  Classical Promise: {classical['wealth_promise']} (boost: +{classical['confidence_boost']})")
    for p in classical["fired_patterns"]:
        print(f"    ✓ {p}")

    # Outcome classification
    outcome = evaluate_outcome_layer(chart)
    print(f"\n  Wealth Type: {outcome['wealth_type']} | Stability: {outcome['stability']}")
    for o in outcome["fired_outcomes"]:
        print(f"    ✓ {o}")

    # Evaluate current date
    print(f"\n  ── Current Period Evaluation ──")
    eval_dates = [
        datetime(2025, 6, 1, 9, 15),
        datetime(2025, 9, 1, 9, 15),
        datetime(2026, 1, 1, 9, 15),
        datetime(2026, 5, 25, 9, 15),
    ]

    print(f"\n  {'Date':<14} {'Score':<8} {'Band':<8} {'Likelihood':<12} {'Triggers'}")
    print(f"  {'─'*14} {'─'*8} {'─'*8} {'─'*12} {'─'*30}")

    for dt in eval_dates:
        r = evaluate_wealth_for_date(chart, dt)
        triggers = len(r.dasha_fired) + len(r.fast_trigger_fired)
        top_rules = [rid for rid, _, _ in (r.dasha_fired + r.fast_trigger_fired)[:3]]
        print(f"  {dt.strftime('%Y-%m-%d'):<14} {r.total_score:<8.1f} {r.timing_band:<8} "
              f"{r.likelihood:<12} {triggers} fired")
        for rid in top_rules:
            print(f"    → {rid}")

    print("\n  Done.")
