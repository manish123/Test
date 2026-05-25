"""
Creative Output & Expression Evaluator — 5-Layer Sequential Engine
Domain: Creativity, Artistic Expression, Intellectual Output, Performance

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
)

RULES_DIR = Path(__file__).resolve().parent / "domains" / "general_life" / "creative_output_and_expression"

CREATIVE_KARAKAS = {"Venus", "Mercury", "Moon", "Rahu", "Ketu"}
CREATIVE_HOUSES = {3, 5, 9, 12}  # communication, creativity, inspiration, imagination

CALIBRATION = load_calibration(
    RULES_DIR / "calibration_overlay.json",
    fallback_defaults={
        "layer_weights": {"dasha_weight": 0.30, "transit_weight": 0.30, "fast_trigger_weight": 0.20, "classical_weight": 0.20},
        "likelihood_thresholds": {"very_high": 55, "high": 40, "moderate": 25, "low": 15},
    },
)


class ChartState(BaseChartState):
    def __init__(self, birth_dt, lat, lon, alt=0):
        super().__init__(birth_dt, lat, lon, alt)
        self.third_sign = ((self.asc_sign + 2 - 1) % 12) + 1
        self.third_lord = SIGN_LORDS[self.third_sign]
        self.fifth_sign = ((self.asc_sign + 4 - 1) % 12) + 1
        self.fifth_lord = SIGN_LORDS[self.fifth_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.twelfth_sign = ((self.asc_sign + 11 - 1) % 12) + 1
        self.twelfth_lord = SIGN_LORDS[self.twelfth_sign]
        self.janma_nak_index = int((self.moon_lon % 360) / 13.3333333333) % 27


class TransitState(BaseTransitState):
    pass


def evaluate_dasha_layer(chart: ChartState, transit: TransitState):
    """Evaluate creative output transit triggers."""
    fired = []

    # Venus in 5th from lagna (creative house)
    venus_house = transit.planet_houses_from_lagna.get("Venus", 0)
    if venus_house == 5:
        fired.append(("transit_venus_5th_creative", 30,
                      ["Venus in 5th — creative expression peak"]))

    # Mercury in 3rd or 5th (communication/creativity)
    merc_house = transit.planet_houses_from_lagna.get("Mercury", 0)
    if merc_house in [3, 5]:
        fired.append(("transit_mercury_3_5_expression", 25,
                      [f"Mercury in H{merc_house} — intellectual/creative output"]))

    # Jupiter in 5th or 9th (inspiration/wisdom)
    jup_house = transit.planet_houses_from_lagna.get("Jupiter", 0)
    if jup_house in [5, 9]:
        fired.append(("transit_jupiter_5_9_inspiration", 28,
                      [f"Jupiter in H{jup_house} — creative inspiration/expansion"]))

    # Moon in 5th (emotional creativity)
    moon_house = transit.planet_houses_from_lagna.get("Moon", 0)
    if moon_house == 5:
        fired.append(("transit_moon_5th_emotional_art", 20,
                      ["Moon in 5th — emotional creative surge"]))

    return fired


def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    return evaluate_dasha_layer(chart, transit)


def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """Evaluate Anga Gochara fast triggers for creative events."""
    fired = []
    janma_idx = chart.janma_nak_index

    moon_lon = transit.positions.get("Moon", 0)
    moon_nak_idx = int((moon_lon % 360) / 13.3333333333) % 27
    moon_offset = (moon_nak_idx - janma_idx) % 27 + 1

    # Moon in 4th-6th nakshatra (face — expression)
    if moon_offset in [4, 5, 6]:
        fired.append(("fast_trigger_moon_face_expression", 25,
                      [f"Moon in {moon_offset}th nakshatra (face — creative expression)"]))

    # Venus transit through 5th lord's nakshatra
    venus_lon = transit.positions.get("Venus", 0)
    venus_nak_idx = int((venus_lon % 360) / 13.3333333333) % 27
    venus_offset = (venus_nak_idx - janma_idx) % 27 + 1
    if venus_offset in [4, 5, 6]:
        fired.append(("fast_trigger_venus_face_art", 28,
                      [f"Venus in {venus_offset}th nakshatra (face — artistic output)"]))

    # Mercury in 9th-10th (eyes — vision/insight)
    merc_lon = transit.positions.get("Mercury", 0)
    merc_nak_idx = int((merc_lon % 360) / 13.3333333333) % 27
    merc_offset = (merc_nak_idx - janma_idx) % 27 + 1
    if merc_offset in [9, 10]:
        fired.append(("fast_trigger_mercury_eyes_insight", 22,
                      [f"Mercury in {merc_offset}th nakshatra (eyes — intellectual vision)"]))

    return fired


def evaluate_classical_layer(chart: ChartState):
    """Evaluate structural creative patterns."""
    results = {"creative_promise": "normal", "confidence_boost": 0, "fired_patterns": []}

    venus_house = chart.planets["Venus"]["house"]
    mercury_house = chart.planets["Mercury"]["house"]
    fifth_lord_house = chart.planets[chart.fifth_lord]["house"]
    moon_house = chart.planets["Moon"]["house"]

    # Venus in 5th — artistic genius
    if venus_house == 5:
        results["creative_promise"] = "exceptional"
        results["confidence_boost"] += 15
        results["fired_patterns"].append("venus_5th: Artistic genius archetype")

    # Mercury in 3rd — communication mastery
    if mercury_house == 3:
        results["confidence_boost"] += 10
        results["fired_patterns"].append("mercury_3rd: Communication/writing mastery")

    # 5th lord in kendra/trikona
    if fifth_lord_house in {1, 4, 5, 7, 9, 10}:
        results["confidence_boost"] += 8
        results["fired_patterns"].append(f"5L_strong: 5th lord ({chart.fifth_lord}) in H{fifth_lord_house}")

    # Moon in 5th — emotional creativity
    if moon_house == 5:
        results["confidence_boost"] += 10
        results["fired_patterns"].append("moon_5th: Emotional/intuitive creativity")

    # Venus + Mercury conjunction (artistic intellect)
    if venus_house == mercury_house:
        results["confidence_boost"] += 12
        results["fired_patterns"].append("venus_mercury_conjunct: Artistic intellect combination")

    return results


def evaluate_outcome_layer(chart: ChartState):
    """Classify creative output type."""
    results = {"creative_type": "general", "medium": "unknown", "fired_outcomes": []}

    venus_house = chart.planets["Venus"]["house"]
    mercury_house = chart.planets["Mercury"]["house"]
    moon_house = chart.planets["Moon"]["house"]

    if venus_house in [3, 5]:
        results["creative_type"] = "artistic"
        results["medium"] = "visual_performing"
        results["fired_outcomes"].append("venus_creative_house: Visual/performing arts")
    elif mercury_house in [3, 5]:
        results["creative_type"] = "intellectual"
        results["medium"] = "writing_communication"
        results["fired_outcomes"].append("mercury_creative_house: Writing/intellectual output")
    elif moon_house in [5, 12]:
        results["creative_type"] = "intuitive"
        results["medium"] = "music_poetry"
        results["fired_outcomes"].append("moon_creative_house: Music/poetry/intuitive arts")

    return results


class CreativeWindowResult:
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
            dasha_score * lw.get("dasha_weight", 0.30) +
            dasha_score * lw.get("transit_weight", 0.30) +
            fast_score * lw.get("fast_trigger_weight", 0.20) +
            classical_boost * lw.get("classical_weight", 0.20)
        )
        if fast_score > 20: self.timing_band = "exact"
        elif dasha_score > 25: self.timing_band = "narrow"
        lt = CALIBRATION.get("likelihood_thresholds", {})
        if self.total_score >= lt.get("very_high", 55): self.likelihood = "VERY_HIGH"
        elif self.total_score >= lt.get("high", 40): self.likelihood = "HIGH"
        elif self.total_score >= lt.get("moderate", 25): self.likelihood = "MODERATE"
        elif self.total_score >= lt.get("low", 15): self.likelihood = "LOW"
        else: self.likelihood = "VERY_LOW"


def evaluate_creative_for_date(chart: ChartState, eval_date: datetime):
    transit = TransitState(eval_date, chart)
    result = CreativeWindowResult()
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
    print(f"Lagna: {SIGN_NAMES[chart.asc_sign]} | 5L: {chart.fifth_lord} | Venus H{chart.planets['Venus']['house']}")
    classical = evaluate_classical_layer(chart)
    print(f"Creative promise: {classical['creative_promise']} (+{classical['confidence_boost']})")
    for p in classical["fired_patterns"]: print(f"  ✓ {p}")
    r = evaluate_creative_for_date(chart, datetime(2026, 5, 25, 9, 15))
    print(f"\n2026-05-25: score={r.total_score:.1f}, {r.likelihood}")
