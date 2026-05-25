"""
Social Network Dynamics Evaluator — 5-Layer Sequential Engine
Domain: Social Networks, Alliances, Patronage, Betrayal, Influence

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
    NATURAL_BENEFICS, NATURAL_MALEFICS,
    BaseChartState, BaseTransitState,
    load_calibration,
)

RULES_DIR = Path(__file__).resolve().parent / "domains" / "general_life" / "social_network_dynamics"

SOCIAL_KARAKAS = {"Venus", "Mercury", "Moon", "Jupiter", "Rahu"}
SOCIAL_HOUSES = {3, 7, 11}  # communication, partnerships, networks

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
        self.eleventh_sign = ((self.asc_sign + 10 - 1) % 12) + 1
        self.eleventh_lord = SIGN_LORDS[self.eleventh_sign]
        self.third_sign = ((self.asc_sign + 2 - 1) % 12) + 1
        self.third_lord = SIGN_LORDS[self.third_sign]
        self.seventh_sign = ((self.asc_sign + 6 - 1) % 12) + 1
        self.seventh_lord = SIGN_LORDS[self.seventh_sign]
        self.janma_nak_index = int((self.moon_lon % 360) / 13.3333333333) % 27


class TransitState(BaseTransitState):
    pass


def evaluate_dasha_layer(chart: ChartState, transit: TransitState):
    """Evaluate social network transit triggers."""
    fired = []

    # Jupiter conjunct natal Mercury (friendship expansion)
    jup_lon = transit.positions.get("Jupiter", 0)
    merc_natal = chart.birth_positions.get("Mercury", 0)
    diff = abs((jup_lon - merc_natal) % 360)
    diff = min(diff, 360 - diff)
    if diff <= 10:
        fired.append(("transit_jupiter_conjunct_mercury_friendships", 35,
                      [f"Jupiter conjunct natal Mercury ({diff:.1f}° orb) — social expansion"]))

    # Jupiter/Venus in 11th from lagna (network house)
    jup_house = transit.planet_houses_from_lagna.get("Jupiter", 0)
    venus_house = transit.planet_houses_from_lagna.get("Venus", 0)
    if jup_house == 11:
        fired.append(("transit_benefic_11th_network", 28,
                      ["Jupiter in 11th — network expansion and gains through friends"]))
    if venus_house == 11:
        fired.append(("transit_benefic_11th_network", 22,
                      ["Venus in 11th — social pleasures and alliance support"]))

    # Saturn/Rahu in 11th (challenging social dynamics)
    sat_house = transit.planet_houses_from_lagna.get("Saturn", 0)
    rahu_house = transit.planet_houses_from_lagna.get("Rahu", 0)
    if sat_house == 11:
        fired.append(("transit_malefic_11th_restriction", -15,
                      ["Saturn in 11th — social restrictions, delayed gains"]))
    if rahu_house == 11:
        fired.append(("transit_rahu_11th_obsessive_networking", 20,
                      ["Rahu in 11th — obsessive networking, unconventional alliances"]))

    return fired


def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    return evaluate_dasha_layer(chart, transit)


def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """Evaluate Anga Gochara fast triggers for social events."""
    fired = []
    janma_idx = chart.janma_nak_index

    moon_lon = transit.positions.get("Moon", 0)
    moon_nak_idx = int((moon_lon % 360) / 13.3333333333) % 27
    moon_offset = (moon_nak_idx - janma_idx) % 27 + 1

    # Mitra Tara (8th) — alliance formation
    if moon_offset == 8:
        fired.append(("fast_trigger_moon_mitra_tara_alliance", 28,
                      ["Moon on Mitra Tara (8th star) — alliance/friendship trigger"]))

    # Param Mitra Tara (9th) — elite contact
    if moon_offset == 9:
        fired.append(("fast_trigger_moon_param_mitra_tara_elite", 30,
                      ["Moon on Param Mitra Tara (9th star) — elite contact trigger"]))

    # Left hand (16-18) — quarrels/betrayal
    if moon_offset in [16, 17, 18]:
        fired.append(("fast_trigger_moon_16_to_18_nakshatra_betrayal", -20,
                      [f"Moon in {moon_offset}th nakshatra (left hand) — social quarrel trigger"]))

    # Mars 3rd-8th — social conflict
    mars_lon = transit.positions.get("Mars", 0)
    mars_nak_idx = int((mars_lon % 360) / 13.3333333333) % 27
    mars_offset = (mars_nak_idx - janma_idx) % 27 + 1
    if mars_offset in range(3, 9):
        fired.append(("fast_trigger_mars_3_to_8_social_conflict", -15,
                      [f"Mars in {mars_offset}th nakshatra (feet) — social friction"]))

    return fired


def evaluate_classical_layer(chart: ChartState):
    """Evaluate structural social network patterns."""
    results = {"social_promise": "normal", "confidence_boost": 0, "fired_patterns": []}

    eleventh_lord_house = chart.planets[chart.eleventh_lord]["house"]
    mercury_house = chart.planets["Mercury"]["house"]
    venus_house = chart.planets["Venus"]["house"]
    jupiter_house = chart.planets["Jupiter"]["house"]
    sun_house = chart.planets["Sun"]["house"]
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)

    # Sun in 11th — network leadership
    if sun_house == 11:
        results["social_promise"] = "strong"
        results["confidence_boost"] += 12
        results["fired_patterns"].append("sun_11th: Network leadership archetype")

    # Mercury in 10th — social approval
    if mercury_house == 10:
        results["confidence_boost"] += 10
        results["fired_patterns"].append("mercury_10th: Widespread social approval")

    # Jupiter in 11th — expansive networks
    if jupiter_house == 11:
        results["social_promise"] = "strong"
        results["confidence_boost"] += 12
        results["fired_patterns"].append("jupiter_11th: Expansive social networks")

    # Venus in 11th — pleasurable alliances
    if venus_house == 11:
        results["confidence_boost"] += 8
        results["fired_patterns"].append("venus_11th: Pleasurable social alliances")

    # Jupiter conjunct Rahu — Guru Chandal (distorted alliances)
    if jupiter_house == rahu_house and jupiter_house > 0:
        results["confidence_boost"] -= 8
        results["fired_patterns"].append("guru_chandal: Distorted/manipulative alliances")

    # 11th lord in benefic house
    if eleventh_lord_house in {1, 2, 4, 5, 7, 9, 11}:
        results["confidence_boost"] += 8
        results["fired_patterns"].append(f"11L_benefic: 11th lord in H{eleventh_lord_house}")

    return results


def evaluate_outcome_layer(chart: ChartState):
    """Classify social network type."""
    results = {"network_type": "general", "stability": "moderate", "fired_outcomes": []}

    sun_house = chart.planets["Sun"]["house"]
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    venus_house = chart.planets["Venus"]["house"]

    if sun_house == 11:
        results["network_type"] = "leadership_network"
        results["fired_outcomes"].append("sun_11th: Leadership-driven network")
    elif venus_house == 11:
        results["network_type"] = "pleasure_network"
        results["fired_outcomes"].append("venus_11th: Pleasure/arts-driven network")
    elif rahu_house == 11:
        results["network_type"] = "unconventional_network"
        results["stability"] = "volatile"
        results["fired_outcomes"].append("rahu_11th: Unconventional/taboo network")

    return results


class SocialWindowResult:
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


def evaluate_social_for_date(chart: ChartState, eval_date: datetime):
    transit = TransitState(eval_date, chart)
    result = SocialWindowResult()
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
    print(f"Lagna: {SIGN_NAMES[chart.asc_sign]} | 11L: {chart.eleventh_lord}")
    classical = evaluate_classical_layer(chart)
    print(f"Social promise: {classical['social_promise']} (+{classical['confidence_boost']})")
    for p in classical["fired_patterns"]: print(f"  ✓ {p}")
    r = evaluate_social_for_date(chart, datetime(2026, 5, 25, 9, 15))
    print(f"\n2026-05-25: score={r.total_score:.1f}, {r.likelihood}")
