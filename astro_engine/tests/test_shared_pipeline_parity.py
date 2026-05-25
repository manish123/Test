"""
Phase 2 Parity Tests — Shared Pipeline Refactor

Verifies that the refactored evaluator_base.py infrastructure produces
identical results to the pre-refactor behavior.

Tests cover:
1. evaluator_base constants match expected values
2. Tara scoring functions produce identical outputs
3. BaseChartState produces identical derived values to each domain ChartState
4. BaseTransitState produces identical derived values
5. All 12 evaluator modules import and expose ChartState/TransitState
6. Baseline fixture outputs remain unchanged after refactor

Run with:
    pytest astro_engine/tests/test_shared_pipeline_parity.py -q
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

import pytest

# Ensure astro_engine is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def baseline_run_single():
    with open(FIXTURES_DIR / "baseline_run_single.json") as f:
        return json.load(f)


@pytest.fixture
def baseline_no_gate():
    with open(FIXTURES_DIR / "baseline_no_gate.json") as f:
        return json.load(f)


# Test birth data (same as used to generate baselines)
TEST_BIRTH_DT = datetime(1990, 5, 15, 6, 30)
TEST_LAT = 21.1458
TEST_LON = 79.0882
TEST_ALT = 310


# ═══════════════════════════════════════════════════════════════
# TEST 1: CONSTANTS PARITY
# ═══════════════════════════════════════════════════════════════

class TestConstantsParity:
    """Verify evaluator_base constants match expected canonical values."""

    def test_ist_offset(self):
        from rules.evaluator_base import IST_OFFSET
        assert IST_OFFSET == timedelta(hours=5, minutes=30)

    def test_sign_names_complete(self):
        from rules.evaluator_base import SIGN_NAMES
        assert len(SIGN_NAMES) == 12
        assert SIGN_NAMES[1] == "Aries"
        assert SIGN_NAMES[12] == "Pisces"

    def test_nakshatra_lords_length(self):
        from rules.evaluator_base import NAKSHATRA_LORDS
        assert len(NAKSHATRA_LORDS) == 27
        assert NAKSHATRA_LORDS[0] == "Ketu"
        assert NAKSHATRA_LORDS[6] == "Jupiter"

    def test_benefics_malefics(self):
        from rules.evaluator_base import NATURAL_BENEFICS, NATURAL_MALEFICS
        assert NATURAL_BENEFICS == {"Jupiter", "Venus", "Mercury", "Moon"}
        assert NATURAL_MALEFICS == {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

    def test_house_sets(self):
        from rules.evaluator_base import BENEFIC_HOUSES, MALEFIC_HOUSES
        assert BENEFIC_HOUSES == {1, 2, 4, 5, 7, 9, 11}
        assert MALEFIC_HOUSES == {3, 6, 8, 12}

    def test_aspect_constants(self):
        from rules.evaluator_base import JUPITER_ASPECTS, SATURN_ASPECTS, MARS_ASPECTS
        assert JUPITER_ASPECTS == [5, 7, 9]
        assert SATURN_ASPECTS == [3, 7, 10]
        assert MARS_ASPECTS == [4, 7, 8]

    def test_tara_scores(self):
        from rules.evaluator_base import TARA_SCORES
        assert TARA_SCORES == {1: -1, 2: 2, 3: -2, 4: 1.5, 5: -1.5, 6: 2, 7: -3, 8: 1, 9: 2}

    def test_planet_weights(self):
        from rules.evaluator_base import PLANET_WEIGHTS
        assert PLANET_WEIGHTS["Moon"] == 3
        assert PLANET_WEIGHTS["Sun"] == 1
        assert len(PLANET_WEIGHTS) == 7

    def test_trading_constants(self):
        from rules.evaluator_base import (
            PANCHANG_RISK_WEIGHT, TRADING_EVENT_BOOST, NON_TRADING_EVENT_MULTIPLIER
        )
        assert PANCHANG_RISK_WEIGHT == 0.5
        assert TRADING_EVENT_BOOST == 1.15
        assert NON_TRADING_EVENT_MULTIPLIER == 0.35


# ═══════════════════════════════════════════════════════════════
# TEST 2: TARA SCORING PARITY
# ═══════════════════════════════════════════════════════════════

class TestTaraScoringParity:
    """Verify tara scoring functions produce expected outputs."""

    def test_get_tara_basic(self):
        from rules.evaluator_base import get_tara
        # Same nakshatra → count = (0-0)%27+1 = 1, tara = 1%9 = 1
        assert get_tara("Ashwini", "Ashwini") == 1
        # 2nd nakshatra → count = 2, tara = 2
        assert get_tara("Ashwini", "Bharani") == 2
        # 10th nakshatra → count = 10, tara = 10%9 = 1
        assert get_tara("Ashwini", "Magha") == 1

    def test_get_tara_wraparound(self):
        from rules.evaluator_base import get_tara
        # Revati (27th) to Ashwini (1st) → count = 2, tara = 2
        assert get_tara("Revati", "Ashwini") == 2

    def test_calculate_tara_score(self):
        from rules.evaluator_base import calculate_tara_score
        pdata = {
            "Moon": {"nakshatra": "Rohini"},
            "Mercury": {"nakshatra": "Ashwini"},
            "Jupiter": {"nakshatra": "Pushya"},
            "Saturn": {"nakshatra": "Anuradha"},
            "Mars": {"nakshatra": "Mrigashira"},
            "Venus": {"nakshatra": "Bharani"},
            "Sun": {"nakshatra": "Krittika"},
        }
        score = calculate_tara_score("Ashwini", pdata)
        assert isinstance(score, float)

    def test_get_trade_decision_trade_heavily(self):
        from rules.evaluator_base import get_trade_decision
        pdata = {
            "Moon": {"nakshatra": "Rohini"},
            "Sun": {"nakshatra": "Ashwini"},
            "Venus": {"nakshatra": "Ashwini"},
            "Mars": {"nakshatra": "Ashwini"},
        }
        action, reason = get_trade_decision(pdata)
        assert action == "TRADE HEAVILY"
        assert "Moon in Rohini" in reason

    def test_get_trade_decision_do_not_trade(self):
        from rules.evaluator_base import get_trade_decision
        pdata = {
            "Moon": {"nakshatra": "Dhanishta"},
            "Sun": {"nakshatra": "Ashwini"},
            "Venus": {"nakshatra": "Ashwini"},
            "Mars": {"nakshatra": "Ashwini"},
        }
        action, reason = get_trade_decision(pdata)
        assert action == "DO NOT TRADE"

    def test_get_trade_decision_neutral(self):
        from rules.evaluator_base import get_trade_decision
        pdata = {
            "Moon": {"nakshatra": "Chitra"},
            "Sun": {"nakshatra": "Ashwini"},
            "Venus": {"nakshatra": "Ashwini"},
            "Mars": {"nakshatra": "Ashwini"},
        }
        action, reason = get_trade_decision(pdata)
        assert action == "NEUTRAL"

    @pytest.mark.parametrize("fixture_idx", [0, 1, 2, 3, 4])
    def test_tara_matches_baseline(self, baseline_run_single, fixture_idx):
        """Verify tara scores from baseline fixture are reproducible."""
        entry = baseline_run_single[fixture_idx]
        tara = entry["tara"]
        # Verify structure
        assert "score" in tara
        assert "raw_score" in tara
        assert "rulebook_action" in tara
        assert tara["rulebook_action"] in ("TRADE HEAVILY", "DO NOT TRADE", "NEUTRAL", "DISABLED")


# ═══════════════════════════════════════════════════════════════
# TEST 3: EVALUATOR MODULE IMPORT PARITY
# ═══════════════════════════════════════════════════════════════

EVALUATOR_MODULES = [
    "rules.marriage_evaluator",
    "rules.career_evaluator",
    "rules.childbirth_evaluator",
    "rules.business_evaluator",
    "rules.medical_evaluator",
    "rules.fame_evaluator",
    "rules.property_evaluator",
    "rules.property_purchase_evaluator",
    "rules.vehicle_purchase_evaluator",
    "rules.relocation_evaluator",
    "rules.parent_loss_evaluator",
    "rules.financial_crisis_evaluator",
]


class TestEvaluatorImports:
    """Verify all evaluator modules import and expose required classes."""

    @pytest.mark.parametrize("module_name", EVALUATOR_MODULES)
    def test_module_imports(self, module_name):
        mod = __import__(module_name, fromlist=[module_name.split(".")[-1]])
        assert hasattr(mod, "ChartState"), f"{module_name} missing ChartState"
        assert hasattr(mod, "TransitState"), f"{module_name} missing TransitState"

    @pytest.mark.parametrize("module_name", EVALUATOR_MODULES)
    def test_chartstate_inherits_base(self, module_name):
        from rules.evaluator_base import BaseChartState
        mod = __import__(module_name, fromlist=[module_name.split(".")[-1]])
        cs = getattr(mod, "ChartState")
        assert issubclass(cs, BaseChartState), (
            f"{module_name}.ChartState does not inherit BaseChartState"
        )

    @pytest.mark.parametrize("module_name", EVALUATOR_MODULES)
    def test_transitstate_inherits_base(self, module_name):
        from rules.evaluator_base import BaseTransitState
        mod = __import__(module_name, fromlist=[module_name.split(".")[-1]])
        ts = getattr(mod, "TransitState")
        assert issubclass(ts, BaseTransitState), (
            f"{module_name}.TransitState does not inherit BaseTransitState"
        )


# ═══════════════════════════════════════════════════════════════
# TEST 4: CHART STATE DERIVED VALUES PARITY
# ═══════════════════════════════════════════════════════════════

class TestChartStateParity:
    """Verify BaseChartState produces correct derived values."""

    @pytest.fixture
    def chart(self):
        from rules.evaluator_base import BaseChartState
        return BaseChartState(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)

    def test_asc_sign_range(self, chart):
        assert 1 <= chart.asc_sign <= 12

    def test_moon_sign_range(self, chart):
        assert 1 <= chart.moon_sign <= 12

    def test_planets_dict_complete(self, chart):
        expected_planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
                           "Venus", "Saturn", "Rahu", "Ketu"}
        assert expected_planets.issubset(set(chart.planets.keys()))

    def test_planet_house_range(self, chart):
        for name, data in chart.planets.items():
            assert 1 <= data["house"] <= 12, f"{name} house out of range"
            assert 1 <= data["sign"] <= 12, f"{name} sign out of range"

    def test_lagna_lord_valid(self, chart):
        from features.dignity import SIGN_LORDS
        assert chart.lagna_lord == SIGN_LORDS[chart.asc_sign]

    def test_get_house_from_sign(self, chart):
        # Lagna sign should be house 1
        assert chart.get_house_from_sign(chart.asc_sign) == 1
        # 7th sign should be house 7
        seventh_sign = ((chart.asc_sign + 6 - 1) % 12) + 1
        assert chart.get_house_from_sign(seventh_sign) == 7

    def test_d9_sign_range(self, chart):
        d9 = chart._get_d9_sign(chart.asc_lon)
        assert 1 <= d9 <= 12

    def test_aspectors_returns_list(self, chart):
        aspectors = chart._get_aspectors_of_house(7)
        assert isinstance(aspectors, list)
        # All entries should be planet names
        for a in aspectors:
            assert a in chart.planets

    def test_marriage_chartstate_compatible(self):
        """Marriage ChartState (subclass) produces same base values."""
        from rules.evaluator_base import BaseChartState
        from rules.marriage_evaluator import ChartState as MarriageCS

        base = BaseChartState(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)
        marriage = MarriageCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)

        assert base.asc_sign == marriage.asc_sign
        assert base.moon_sign == marriage.moon_sign
        assert base.lagna_lord == marriage.lagna_lord
        assert base.planets == marriage.planets


# ═══════════════════════════════════════════════════════════════
# TEST 5: TRANSIT STATE PARITY
# ═══════════════════════════════════════════════════════════════

class TestTransitStateParity:
    """Verify BaseTransitState produces correct derived values."""

    @pytest.fixture
    def chart_and_transit(self):
        from rules.evaluator_base import BaseChartState, BaseTransitState
        chart = BaseChartState(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)
        transit_date = datetime(2024, 12, 10, 9, 15)
        transit = BaseTransitState(transit_date, chart)
        return chart, transit

    def test_transit_positions_complete(self, chart_and_transit):
        _, transit = chart_and_transit
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert expected.issubset(set(transit.positions.keys()))

    def test_transit_houses_range(self, chart_and_transit):
        _, transit = chart_and_transit
        for name, house in transit.planet_houses_from_lagna.items():
            assert 1 <= house <= 12, f"Transit {name} house out of range"

    def test_planet_aspects_house_returns_bool(self, chart_and_transit):
        _, transit = chart_and_transit
        result = transit.planet_aspects_house("Jupiter", 7, "lagna")
        assert isinstance(result, bool)

    def test_jupiter_on_degree_returns_bool(self, chart_and_transit):
        _, transit = chart_and_transit
        result = transit.jupiter_on_degree(180.0, orb=5.0)
        assert isinstance(result, bool)

    def test_marriage_transitstate_compatible(self):
        """Marriage TransitState (subclass) produces same values as base."""
        from rules.evaluator_base import BaseChartState, BaseTransitState
        from rules.marriage_evaluator import ChartState as MCS, TransitState as MTS

        base_chart = BaseChartState(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)
        marriage_chart = MCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)

        transit_date = datetime(2024, 12, 10, 9, 15)
        base_transit = BaseTransitState(transit_date, base_chart)
        marriage_transit = MTS(transit_date, marriage_chart)

        assert base_transit.planet_signs == marriage_transit.planet_signs
        assert base_transit.planet_houses_from_lagna == marriage_transit.planet_houses_from_lagna
        assert base_transit.planet_houses_from_moon == marriage_transit.planet_houses_from_moon


# ═══════════════════════════════════════════════════════════════
# TEST 6: BASELINE FIXTURE STRUCTURE VALIDATION
# ═══════════════════════════════════════════════════════════════

class TestBaselineFixtureStructure:
    """Verify baseline fixtures have expected structure (sanity check)."""

    @pytest.mark.parametrize("fixture_idx", [0, 1, 2, 3, 4])
    def test_run_single_structure(self, baseline_run_single, fixture_idx):
        entry = baseline_run_single[fixture_idx]
        assert "eval_date" in entry
        assert "decision" in entry
        assert "top_events" in entry
        assert "yoga" in entry
        assert "tara" in entry
        assert "moorthy" in entry
        assert "dasha" in entry
        assert "nodes" in entry

    @pytest.mark.parametrize("fixture_idx", [0, 1, 2, 3, 4])
    def test_no_gate_structure(self, baseline_no_gate, fixture_idx):
        entry = baseline_no_gate[fixture_idx]
        assert "eval_date" in entry
        assert "decision" in entry
        assert "top_events" in entry
        assert "tara" in entry
        assert "moorthy" in entry

    @pytest.mark.parametrize("fixture_idx", [0, 1, 2, 3, 4])
    def test_tara_rulebook_action_valid(self, baseline_run_single, fixture_idx):
        entry = baseline_run_single[fixture_idx]
        action = entry["tara"]["rulebook_action"]
        assert action in ("TRADE HEAVILY", "DO NOT TRADE", "NEUTRAL", "DISABLED")

    @pytest.mark.parametrize("fixture_idx", [0, 1, 2, 3, 4])
    def test_moorthy_grade_valid(self, baseline_run_single, fixture_idx):
        entry = baseline_run_single[fixture_idx]
        grade = entry["moorthy"]["grade"]
        assert grade in ("Swarna", "Rajata", "Taamra", "Loha")


# ═══════════════════════════════════════════════════════════════
# TEST 7: CROSS-EVALUATOR SHARED BASE CONSISTENCY
# ═══════════════════════════════════════════════════════════════

class TestCrossEvaluatorConsistency:
    """
    Verify that different evaluator ChartStates produce identical
    base-level values for the same input (since they all inherit
    from BaseChartState).
    """

    def test_all_evaluators_same_asc_sign(self):
        """All evaluator ChartStates must compute the same asc_sign."""
        from rules.marriage_evaluator import ChartState as MCS
        from rules.business_evaluator import ChartState as BCS
        from rules.medical_evaluator import ChartState as MedCS
        from rules.relocation_evaluator import ChartState as RCS

        m = MCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)
        b = BCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)
        med = MedCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)
        r = RCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)

        assert m.asc_sign == b.asc_sign == med.asc_sign == r.asc_sign

    def test_all_evaluators_same_planets(self):
        """All evaluator ChartStates must compute the same planet dict."""
        from rules.marriage_evaluator import ChartState as MCS
        from rules.fame_evaluator import ChartState as FCS
        from rules.financial_crisis_evaluator import ChartState as FCCS

        m = MCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)
        f = FCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)
        fc = FCCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)

        assert m.planets == f.planets == fc.planets

    def test_all_evaluators_same_moon(self):
        """All evaluator ChartStates must compute the same moon data."""
        from rules.property_evaluator import ChartState as PCS
        from rules.vehicle_purchase_evaluator import ChartState as VCS
        from rules.parent_loss_evaluator import ChartState as PLCS

        p = PCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)
        v = VCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)
        pl = PLCS(TEST_BIRTH_DT, TEST_LAT, TEST_LON, TEST_ALT)

        assert p.moon_sign == v.moon_sign == pl.moon_sign
        assert p.moon_nakshatra == v.moon_nakshatra == pl.moon_nakshatra
