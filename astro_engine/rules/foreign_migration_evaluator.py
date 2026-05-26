"""
Foreign Migration & Settlement Evaluator — 5-Layer Sequential Engine
Domain: Foreign residence, immigration, overseas career, permanent settlement

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
    NATURAL_BENEFICS, NATURAL_MALEFICS,
    BaseChartState, BaseTransitState,
    load_calibration,
    load_scoring_profile,
)

RULES_DIR = Path(__file__).resolve().parent / "domains" / "relocation" / "foreign_migration_and_settlement"

MIGRATION_KARAKAS = {"Rahu", "Ketu", "Moon", "Saturn", "Jupiter"}
MIGRATION_HOUSES = {4, 7, 9, 12}  # home, foreign lands, long journeys, loss/abroad

CALIBRATION = load_calibration(
    RULES_DIR / "calibration_overlay.json",
    fallback_defaults={
        "layer_weights": {"dasha_weight": 0.35, "transit_weight": 0.30, "fast_trigger_weight": 0.20, "classical_weight": 0.15},
        "likelihood_thresholds": {"very_high": 55, "high": 40, "moderate": 25, "low": 15},
    },
)

# ── Scoring profile (v3.0.0) ──────────────────────────────────
_SCORING_PROFILE = load_scoring_profile("general_life")
if _SCORING_PROFILE:
    # Override calibration thresholds/weights with profile values
    if "likelihood_thresholds" in _SCORING_PROFILE.get("thresholds", {}).__class__.__name__ == "NoneType" or True:
        _profile_thresholds = _SCORING_PROFILE.get("thresholds")
        if _profile_thresholds:
            CALIBRATION["likelihood_thresholds"] = _profile_thresholds
        _profile_weights = _SCORING_PROFILE.get("layer_weights")
        if _profile_weights:
            CALIBRATION["layer_weights"] = _profile_weights



class ChartState(BaseChartState):
    def __init__(self, birth_dt, lat, lon, alt=0):
        super().__init__(birth_dt, lat, lon, alt)
        self.fourth_sign = ((self.asc_sign + 3 - 1) % 12) + 1
        self.fourth_lord = SIGN_LORDS[self.fourth_sign]
        self.seventh_sign = ((self.asc_sign + 6 - 1) % 12) + 1
        self.seventh_lord = SIGN_LORDS[self.seventh_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.twelfth_sign = ((self.asc_sign + 11 - 1) % 12) + 1
        self.twelfth_lord = SIGN_LORDS[self.twelfth_sign]
        self.janma_nak_index = int((self.moon_lon % 360) / 13.3333333333) % 27


class TransitState(BaseTransitState):
    pass


def evaluate_dasha_layer(chart: ChartState, transit: TransitState):
    """Evaluate migration transit triggers."""
    fired = []

    # Rahu in 9th or 12th from lagna (foreign lands)
    rahu_house = transit.planet_houses_from_lagna.get("Rahu", 0)
    if rahu_house in [9, 12]:
        fired.append(("transit_rahu_9_12_foreign", 35,
                      [f"Rahu in H{rahu_house} — foreign settlement activation"]))

    # Jupiter in 9th or 12th (expansion abroad)
    jup_house = transit.planet_houses_from_lagna.get("Jupiter", 0)
    if jup_house in [9, 12]:
        fired.append(("transit_jupiter_9_12_abroad", 28,
                      [f"Jupiter in H{jup_house} — overseas expansion"]))

    # Saturn in 4th from Moon (displacement from home)
    sat_house_moon = transit.planet_houses_from_moon.get("Saturn", 0)
    if sat_house_moon == 4:
        fired.append(("transit_saturn_4th_moon_displacement", 25,
                      ["Saturn 4th from Moon — displacement from homeland"]))

    # 12th lord transiting 9th or 12th
    twelfth_lord_house = transit.planet_houses_from_lagna.get(chart.twelfth_lord, 0)
    if twelfth_lord_house in [9, 12]:
        fired.append(("transit_12L_in_9_12_abroad", 22,
                      [f"12th lord ({chart.twelfth_lord}) in H{twelfth_lord_house} — abroad activation"]))

    return fired


def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    return evaluate_dasha_layer(chart, transit)


def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """Evaluate fast triggers for migration events."""
    fired = []
    janma_idx = chart.janma_nak_index

    # Moon in 19th-24th nakshatra (feet — movement/travel)
    moon_lon = transit.positions.get("Moon", 0)
    moon_nak_idx = int((moon_lon % 360) / 13.3333333333) % 27
    moon_offset = (moon_nak_idx - janma_idx) % 27 + 1

    if moon_offset in range(19, 25):
        fired.append(("fast_trigger_moon_feet_travel", 22,
                      [f"Moon in {moon_offset}th nakshatra (feet — movement/migration)"]))

    # Mars in 12th-14th nakshatra (belly — deep change)
    mars_lon = transit.positions.get("Mars", 0)
    mars_nak_idx = int((mars_lon % 360) / 13.3333333333) % 27
    mars_offset = (mars_nak_idx - janma_idx) % 27 + 1

    if mars_offset in [12, 13, 14]:
        fired.append(("fast_trigger_mars_belly_relocation", 20,
                      [f"Mars in {mars_offset}th nakshatra (belly — deep life change)"]))

    # Desha Tara (27th) — homeland connection/disconnection
    if moon_offset == 27:
        fired.append(("fast_trigger_moon_desha_tara", 25,
                      ["Moon on Desha Tara (27th) — homeland axis activated"]))

    return fired


def evaluate_classical_layer(chart: ChartState):
    """Evaluate structural migration patterns."""
    results = {"migration_promise": "normal", "confidence_boost": 0, "fired_patterns": []}

    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    ketu_house = chart.planets.get("Ketu", {}).get("house", 0)
    fourth_lord_house = chart.planets[chart.fourth_lord]["house"]
    twelfth_lord_house = chart.planets[chart.twelfth_lord]["house"]
    ninth_lord_house = chart.planets[chart.ninth_lord]["house"]
    moon_house = chart.planets["Moon"]["house"]

    # Rahu in 4th or 12th (foreign connection to home/abroad)
    if rahu_house in [4, 12]:
        results["migration_promise"] = "strong"
        results["confidence_boost"] += 15
        results["fired_patterns"].append(f"rahu_H{rahu_house}: Strong foreign settlement archetype")

    # 4th lord in 12th (home in foreign land)
    if fourth_lord_house == 12:
        results["migration_promise"] = "strong"
        results["confidence_boost"] += 12
        results["fired_patterns"].append("4L_in_12th: Home established in foreign land")

    # 12th lord in 9th (abroad through fortune/dharma)
    if twelfth_lord_house == 9:
        results["confidence_boost"] += 10
        results["fired_patterns"].append("12L_in_9th: Foreign settlement through fortune")

    # Moon in 12th (emotional pull to foreign lands)
    if moon_house == 12:
        results["confidence_boost"] += 8
        results["fired_patterns"].append("moon_12th: Emotional connection to foreign lands")

    # 9th lord in 12th (dharma fulfilled abroad)
    if ninth_lord_house == 12:
        results["confidence_boost"] += 10
        results["fired_patterns"].append("9L_in_12th: Life purpose fulfilled abroad")

    return results


def evaluate_outcome_layer(chart: ChartState):
    """Classify migration type."""
    results = {"migration_type": "general", "permanence": "unknown", "fired_outcomes": []}

    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    fourth_lord_house = chart.planets[chart.fourth_lord]["house"]

    if rahu_house in [4, 9, 12]:
        results["migration_type"] = "permanent_settlement"
        results["permanence"] = "permanent"
        results["fired_outcomes"].append(f"rahu_H{rahu_house}: Permanent foreign settlement")
    elif fourth_lord_house == 12:
        results["migration_type"] = "career_migration"
        results["permanence"] = "long_term"
        results["fired_outcomes"].append("4L_12th: Career-driven long-term migration")
    else:
        results["permanence"] = "temporary"

    return results


class MigrationWindowResult:
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


def evaluate_migration_for_date(chart: ChartState, eval_date: datetime):
    transit = TransitState(eval_date, chart)
    result = MigrationWindowResult()
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
    print(f"Lagna: {SIGN_NAMES[chart.asc_sign]} | 4L: {chart.fourth_lord} | 12L: {chart.twelfth_lord} | Rahu: H{chart.planets.get('Rahu',{}).get('house','?')}")
    classical = evaluate_classical_layer(chart)
    print(f"Migration promise: {classical['migration_promise']} (+{classical['confidence_boost']})")
    for p in classical["fired_patterns"]: print(f"  ✓ {p}")
    outcome = evaluate_outcome_layer(chart)
    print(f"Type: {outcome['migration_type']} | Permanence: {outcome['permanence']}")
    r = evaluate_migration_for_date(chart, datetime(2026, 5, 25, 9, 15))
    print(f"\n2026-05-25: score={r.total_score:.1f}, {r.likelihood}")
