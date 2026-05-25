"""
Litigation & Legal Disputes Evaluator — 5-Layer Sequential Engine
Domain: Lawsuits, Legal Conflicts, Imprisonment, Regulatory Pressure

Post-refactor pattern: imports from evaluator_base.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from features.dignity import SIGN_LORDS, get_sign
from features.nakshatra import get_nakshatra

from rules.evaluator_base import (
    SIGN_NAMES, NAKSHATRA_LORDS,
    NATURAL_BENEFICS, NATURAL_MALEFICS, MALEFIC_HOUSES,
    BaseChartState, BaseTransitState,
    load_calibration,
)

RULES_DIR = Path(__file__).resolve().parent / "domains" / "general_life" / "litigation_and_legal_disputes"

LITIGATION_KARAKAS = {"Mars", "Saturn", "Rahu", "Ketu"}
LITIGATION_HOUSES = {6, 7, 8, 12}  # enemies, disputes, crisis, imprisonment

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
        self.sixth_sign = ((self.asc_sign + 5 - 1) % 12) + 1
        self.sixth_lord = SIGN_LORDS[self.sixth_sign]
        self.seventh_sign = ((self.asc_sign + 6 - 1) % 12) + 1
        self.seventh_lord = SIGN_LORDS[self.seventh_sign]
        self.eighth_sign = ((self.asc_sign + 7 - 1) % 12) + 1
        self.eighth_lord = SIGN_LORDS[self.eighth_sign]
        self.twelfth_sign = ((self.asc_sign + 11 - 1) % 12) + 1
        self.twelfth_lord = SIGN_LORDS[self.twelfth_sign]
        self.janma_nak_index = int((self.moon_lon % 360) / 13.3333333333) % 27


class TransitState(BaseTransitState):
    pass


def evaluate_dasha_layer(chart: ChartState, transit: TransitState):
    """Evaluate litigation transit triggers."""
    fired = []

    # Mars in 6th/8th/12th from lagna (conflict houses)
    mars_house = transit.planet_houses_from_lagna.get("Mars", 0)
    if mars_house in [6, 8, 12]:
        fired.append(("transit_mars_dusthana_conflict", 30,
                      [f"Mars in H{mars_house} — legal conflict activation"]))

    # Saturn in 6th or 8th (prolonged disputes)
    sat_house = transit.planet_houses_from_lagna.get("Saturn", 0)
    if sat_house in [6, 8]:
        fired.append(("transit_saturn_6_8_prolonged_dispute", 28,
                      [f"Saturn in H{sat_house} — prolonged legal pressure"]))

    # Rahu in 6th (enemy amplification) or 12th (imprisonment risk)
    rahu_house = transit.planet_houses_from_lagna.get("Rahu", 0)
    if rahu_house == 6:
        fired.append(("transit_rahu_6th_enemy_amplification", 25,
                      ["Rahu in 6th — amplified enemies/litigation"]))
    elif rahu_house == 12:
        fired.append(("transit_rahu_12th_confinement_risk", 32,
                      ["Rahu in 12th — confinement/imprisonment risk"]))

    # 6th lord in 7th or 7th lord in 6th (dispute with partner/opponent)
    sixth_lord_house = transit.planet_houses_from_lagna.get(chart.sixth_lord, 0)
    if sixth_lord_house == 7:
        fired.append(("transit_6L_in_7th_opponent_clash", 22,
                      [f"6th lord ({chart.sixth_lord}) transiting 7th — opponent clash"]))

    return fired


def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    return evaluate_dasha_layer(chart, transit)


def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """Evaluate fast triggers for legal events."""
    fired = []
    janma_idx = chart.janma_nak_index

    # Moon in 16th-18th nakshatra (left hand — quarrels)
    moon_lon = transit.positions.get("Moon", 0)
    moon_nak_idx = int((moon_lon % 360) / 13.3333333333) % 27
    moon_offset = (moon_nak_idx - janma_idx) % 27 + 1

    if moon_offset in [16, 17, 18]:
        fired.append(("fast_trigger_moon_left_hand_quarrel", 22,
                      [f"Moon in {moon_offset}th nakshatra (left hand — legal quarrel)"]))

    # Mars in 3rd-8th (feet — active conflict)
    mars_lon = transit.positions.get("Mars", 0)
    mars_nak_idx = int((mars_lon % 360) / 13.3333333333) % 27
    mars_offset = (mars_nak_idx - janma_idx) % 27 + 1

    if mars_offset in range(3, 9):
        fired.append(("fast_trigger_mars_feet_conflict", 20,
                      [f"Mars in {mars_offset}th nakshatra (feet — active legal conflict)"]))

    # Saturn on Sanghatika (16th star — structural crisis)
    sat_lon = transit.positions.get("Saturn", 0)
    sat_nak_idx = int((sat_lon % 360) / 13.3333333333) % 27
    sat_offset = (sat_nak_idx - janma_idx) % 27 + 1

    if sat_offset == 16:
        fired.append(("fast_trigger_saturn_sanghatika_legal_crisis", 30,
                      ["Saturn on Sanghatika (16th star) — structural legal crisis"]))

    return fired


def evaluate_classical_layer(chart: ChartState):
    """Evaluate structural litigation patterns."""
    results = {"litigation_risk": "low", "confidence_boost": 0, "fired_patterns": []}

    sixth_lord_house = chart.planets[chart.sixth_lord]["house"]
    seventh_lord_house = chart.planets[chart.seventh_lord]["house"]
    mars_house = chart.planets["Mars"]["house"]
    saturn_house = chart.planets["Saturn"]["house"]
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)

    # Mars in 6th (fighter, wins disputes)
    if mars_house == 6:
        results["litigation_risk"] = "moderate"
        results["confidence_boost"] += 10
        results["fired_patterns"].append("mars_6th: Fighter archetype — wins disputes")

    # Saturn in 6th (prolonged but eventual victory)
    if saturn_house == 6:
        results["confidence_boost"] += 8
        results["fired_patterns"].append("saturn_6th: Prolonged disputes, eventual victory")

    # Rahu in 6th (amplified enemies but can win unconventionally)
    if rahu_house == 6:
        results["litigation_risk"] = "high"
        results["confidence_boost"] += 5
        results["fired_patterns"].append("rahu_6th: Amplified enemies, unconventional victory")

    # 6th lord in 7th or 7th lord in 6th (chronic disputes)
    if sixth_lord_house == 7 or seventh_lord_house == 6:
        results["litigation_risk"] = "high"
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            f"6L_7L_exchange: 6L in H{sixth_lord_house}, 7L in H{seventh_lord_house} — chronic disputes")

    # Mars + Saturn conjunction (legal grinding)
    if mars_house == saturn_house:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(f"mars_saturn_conjunct_H{mars_house}: Legal grinding pattern")

    return results


def evaluate_outcome_layer(chart: ChartState):
    """Classify litigation outcome type."""
    results = {"dispute_type": "general", "outcome_tendency": "unknown", "fired_outcomes": []}

    mars_house = chart.planets["Mars"]["house"]
    jupiter_house = chart.planets["Jupiter"]["house"]
    sixth_lord_house = chart.planets[chart.sixth_lord]["house"]

    # Mars in 6th = victory tendency
    if mars_house == 6:
        results["outcome_tendency"] = "victory"
        results["fired_outcomes"].append("mars_6th: Strong victory tendency in disputes")
    # Jupiter aspecting 6th = protection
    elif jupiter_house in [2, 6, 10]:  # Jupiter aspects 6th from these
        results["outcome_tendency"] = "settlement"
        results["fired_outcomes"].append("jupiter_aspects_6th: Settlement/protection tendency")
    # 6th lord in dusthana = enemies self-destruct
    elif sixth_lord_house in [6, 8, 12]:
        results["outcome_tendency"] = "vipreet_victory"
        results["fired_outcomes"].append(f"6L_in_dusthana_H{sixth_lord_house}: Enemies self-destruct (Vipreet)")

    return results


class LitigationWindowResult:
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


def evaluate_litigation_for_date(chart: ChartState, eval_date: datetime):
    transit = TransitState(eval_date, chart)
    result = LitigationWindowResult()
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
    print(f"Lagna: {SIGN_NAMES[chart.asc_sign]} | 6L: {chart.sixth_lord} | 7L: {chart.seventh_lord}")
    classical = evaluate_classical_layer(chart)
    print(f"Litigation risk: {classical['litigation_risk']} (+{classical['confidence_boost']})")
    for p in classical["fired_patterns"]: print(f"  ✓ {p}")
    outcome = evaluate_outcome_layer(chart)
    print(f"Outcome tendency: {outcome['outcome_tendency']}")
    r = evaluate_litigation_for_date(chart, datetime(2026, 5, 25, 9, 15))
    print(f"\n2026-05-25: score={r.total_score:.1f}, {r.likelihood}, {r.timing_band}")
