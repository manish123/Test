"""
Career Authority & Institutional Power Evaluator — 5-Layer Sequential Engine
Domain: Career Authority, Executive Power, Government Positions

Post-refactor pattern: imports from evaluator_base.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from features.dignity import SIGN_LORDS, get_sign
from features.nakshatra import get_nakshatra

from rules.evaluator_base import (
    IST_OFFSET, ist_to_utc, get_jd,
    SIGN_NAMES, NAKSHATRA_LORDS,
    NATURAL_BENEFICS, NATURAL_MALEFICS, BENEFIC_HOUSES, MALEFIC_HOUSES,
    BaseChartState, BaseTransitState,
    load_calibration,
)

RULES_DIR = Path(__file__).resolve().parent / "domains" / "career" / "career_authority_and_institutional_power"

AUTHORITY_KARAKAS = {"Sun", "Saturn", "Jupiter", "Mars", "Rahu"}
AUTHORITY_HOUSES = {1, 3, 6, 9, 10, 11}

CALIBRATION = load_calibration(
    RULES_DIR / "calibration_overlay.json",
    fallback_defaults={
        "layer_weights": {"dasha_weight": 0.35, "transit_weight": 0.30, "fast_trigger_weight": 0.20, "classical_weight": 0.15},
        "likelihood_thresholds": {"very_high": 55, "high": 40, "moderate": 25, "low": 15},
    },
)


class ChartState(BaseChartState):
    def __init__(self, birth_dt, lat, lon, alt=0):
        super().__init__(birth_dt, lat, lon, alt)
        self.tenth_sign = ((self.asc_sign + 9 - 1) % 12) + 1
        self.tenth_lord = SIGN_LORDS[self.tenth_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.eleventh_sign = ((self.asc_sign + 10 - 1) % 12) + 1
        self.eleventh_lord = SIGN_LORDS[self.eleventh_sign]
        self.janma_nak_index = int((self.moon_lon % 360) / 13.3333333333) % 27


class TransitState(BaseTransitState):
    pass


def evaluate_dasha_layer(chart: ChartState, transit: TransitState):
    """Evaluate career authority transit/dasha rules."""
    fired = []

    # 10th lord in upachaya from lagna
    tenth_lord_transit_sign = transit.planet_signs.get(chart.tenth_lord)
    if tenth_lord_transit_sign:
        tenth_lord_house = chart.get_house_from_sign(tenth_lord_transit_sign)
        if tenth_lord_house in [3, 6, 10, 11]:
            fired.append(("transit_10th_lord_upachaya_promotion", 35,
                          [f"Transit 10th lord ({chart.tenth_lord}) in upachaya H{tenth_lord_house}"]))

    # Jupiter/Sun in 10th house
    jup_house = transit.planet_houses_from_lagna.get("Jupiter", 0)
    sun_house = transit.planet_houses_from_lagna.get("Sun", 0)
    if jup_house == 10:
        fired.append(("transit_auspicious_10th_house_recognition", 30,
                      ["Transit Jupiter in 10th house (institutional recognition)"]))
    if sun_house == 10:
        fired.append(("transit_auspicious_10th_house_recognition", 25,
                      ["Transit Sun in 10th house (executive visibility)"]))

    # Saturn in 10th (restructuring/authority)
    sat_house = transit.planet_houses_from_lagna.get("Saturn", 0)
    if sat_house == 10:
        fired.append(("saturn_transit_10th_authority", 28,
                      ["Transit Saturn in 10th (career restructuring/authority)"]))

    return fired


def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    return evaluate_dasha_layer(chart, transit)


def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """Evaluate Anga Gochara fast triggers for career authority."""
    fired = []
    janma_idx = chart.janma_nak_index

    # Moon on Karma Tara (10th nakshatra)
    moon_lon = transit.positions.get("Moon", 0)
    moon_nak_idx = int((moon_lon % 360) / 13.3333333333) % 27
    moon_offset = (moon_nak_idx - janma_idx) % 27 + 1

    if moon_offset == 10:
        fired.append(("fast_trigger_moon_karma_tara_role_change", 28,
                      ["Moon on Karma Tara (10th star) — role change trigger"]))

    # Moon on Abhishek Tara (28th = 1st nakshatra, wraps)
    if moon_offset == 1:  # 28th from 27 wraps to 1
        fired.append(("fast_trigger_moon_abhishek_tara_promotion", 30,
                      ["Moon on Abhishek Tara — promotion/honors trigger"]))

    # Mars in 9th/10th/11th nakshatra (chest — success)
    mars_lon = transit.positions.get("Mars", 0)
    mars_nak_idx = int((mars_lon % 360) / 13.3333333333) % 27
    mars_offset = (mars_nak_idx - janma_idx) % 27 + 1

    if mars_offset in [9, 10, 11]:
        fired.append(("fast_trigger_mars_anga_gochara_success", 25,
                      [f"Mars in {mars_offset}th nakshatra (chest — executive success)"]))

    return fired


def evaluate_classical_layer(chart: ChartState):
    """Evaluate structural authority patterns."""
    results = {"authority_promise": "normal", "confidence_boost": 0, "fired_patterns": []}

    tenth_lord_house = chart.planets[chart.tenth_lord]["house"]
    sun_house = chart.planets["Sun"]["house"]
    saturn_house = chart.planets["Saturn"]["house"]
    jupiter_house = chart.planets["Jupiter"]["house"]
    ninth_lord_house = chart.planets[chart.ninth_lord]["house"]

    # Sun in 10th
    if sun_house == 10:
        results["authority_promise"] = "strong"
        results["confidence_boost"] += 15
        results["fired_patterns"].append("sun_10th: Executive power archetype")

    # Saturn in 10th
    if saturn_house == 10:
        results["authority_promise"] = "strong"
        results["confidence_boost"] += 12
        results["fired_patterns"].append("saturn_10th: Bureaucratic authority archetype")

    # 9th/10th lords conjunct (Dharma-Karma)
    if ninth_lord_house == tenth_lord_house:
        results["confidence_boost"] += 15
        results["fired_patterns"].append(
            f"dharma_karma_yoga: 9L+10L conjunct in H{ninth_lord_house}")

    # 10th lord in kendra
    if tenth_lord_house in {1, 4, 7, 10}:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(f"10L_kendra: 10th lord in H{tenth_lord_house}")

    # Jupiter in 1st (Hamsa yoga potential)
    if jupiter_house == 1:
        results["confidence_boost"] += 8
        results["fired_patterns"].append("jupiter_1st: Wisdom-based leadership")

    # Malefics in 3rd and 6th (army chief pattern)
    malefics_3 = [n for n, d in chart.planets.items() if d["house"] == 3 and n in NATURAL_MALEFICS]
    malefics_6 = [n for n, d in chart.planets.items() if d["house"] == 6 and n in NATURAL_MALEFICS]
    if malefics_3 and malefics_6:
        results["confidence_boost"] += 12
        results["fired_patterns"].append(f"malefics_3_6: Command position ({malefics_3} in 3rd, {malefics_6} in 6th)")

    return results


def evaluate_outcome_layer(chart: ChartState):
    """Classify authority type."""
    results = {"authority_type": "general", "stability": "unknown", "fired_outcomes": []}

    sun_house = chart.planets["Sun"]["house"]
    saturn_house = chart.planets["Saturn"]["house"]
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)

    if sun_house == 10:
        results["authority_type"] = "executive"
        results["fired_outcomes"].append("sun_10th: Executive/government leadership")
    elif saturn_house == 10:
        results["authority_type"] = "bureaucratic"
        results["stability"] = "stable"
        results["fired_outcomes"].append("saturn_10th: Bureaucratic/populist authority")
    elif rahu_house == 10:
        results["authority_type"] = "controversial"
        results["fired_outcomes"].append("rahu_10th: Controversial/ambitious authority")

    if results["stability"] == "unknown":
        tenth_h = chart.planets[chart.tenth_lord]["house"]
        results["stability"] = "stable" if tenth_h in BENEFIC_HOUSES else "unstable"

    return results


class AuthorityWindowResult:
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
        fast_score = sum(s for _, s, _ in self.fast_trigger_fired)
        classical_boost = self.classical.get("confidence_boost", 0)
        lw = CALIBRATION.get("layer_weights", {})
        self.total_score = (
            dasha_score * lw.get("dasha_weight", 0.35) +
            dasha_score * lw.get("transit_weight", 0.30) +
            fast_score * lw.get("fast_trigger_weight", 0.20) +
            classical_boost * lw.get("classical_weight", 0.15)
        )
        if fast_score > 20: self.timing_band = "exact"
        elif dasha_score > 25: self.timing_band = "narrow"
        lt = CALIBRATION.get("likelihood_thresholds", {})
        if self.total_score >= lt.get("very_high", 55): self.likelihood = "VERY_HIGH"
        elif self.total_score >= lt.get("high", 40): self.likelihood = "HIGH"
        elif self.total_score >= lt.get("moderate", 25): self.likelihood = "MODERATE"
        elif self.total_score >= lt.get("low", 15): self.likelihood = "LOW"
        else: self.likelihood = "VERY_LOW"


def evaluate_authority_for_date(chart: ChartState, eval_date: datetime):
    transit = TransitState(eval_date, chart)
    result = AuthorityWindowResult()
    result.eval_date = eval_date
    result.dasha_fired = evaluate_dasha_layer(chart, transit)
    result.transit_fired = evaluate_transit_layer(chart, transit)
    result.fast_trigger_fired = evaluate_fast_trigger_layer(chart, transit)
    result.classical = evaluate_classical_layer(chart)
    result.outcome = evaluate_outcome_layer(chart)
    result.compute_composite_score()
    return result


if __name__ == "__main__":
    BIRTH_DT = datetime(1975, 7, 22, 18, 15)
    LAT, LON, ALT = 21.2094, 81.4285, 297
    chart = ChartState(BIRTH_DT, LAT, LON, ALT)
    print(f"Lagna: {SIGN_NAMES[chart.asc_sign]} | 10L: {chart.tenth_lord}")
    classical = evaluate_classical_layer(chart)
    print(f"Authority promise: {classical['authority_promise']} (+{classical['confidence_boost']})")
    for p in classical["fired_patterns"]: print(f"  ✓ {p}")
    r = evaluate_authority_for_date(chart, datetime(2026, 5, 25, 9, 15))
    print(f"\n2026-05-25: score={r.total_score:.1f}, {r.likelihood}, {r.timing_band}")
