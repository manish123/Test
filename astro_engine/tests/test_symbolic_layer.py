"""
Phase 10A Symbolic Cognition Layer Tests

Proves:
1. Archetype determinism
2. Behavioral profile stability
3. Arbitration consistency
4. Lifecycle transition consistency
5. Symbolic state determinism
6. No evaluator contamination
7. No scoring contamination
8. Backward compatibility preserved
"""

import sys
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TEST_BIRTH = datetime(1975, 7, 22, 18, 15)
TEST_LAT, TEST_LON, TEST_ALT = 21.2094, 81.4285, 297


@pytest.fixture
def chart():
    from rules.evaluator_base import BaseChartState
    return BaseChartState(TEST_BIRTH, TEST_LAT, TEST_LON, TEST_ALT)


class TestRegistryLoading:
    def test_archetypes_load(self):
        from symbolic.registry_loader import get_business_archetypes
        data = get_business_archetypes()
        assert len(data) == 6
        assert data[0]["archetype_id"] == "biz_arch_001"

    def test_planetary_behaviors_load(self):
        from symbolic.registry_loader import get_planetary_behaviors
        data = get_planetary_behaviors()
        assert len(data) == 7

    def test_arbitration_rules_load(self):
        from symbolic.registry_loader import get_arbitration_rules
        data = get_arbitration_rules()
        assert len(data) == 6

    def test_lifecycle_transitions_load(self):
        from symbolic.registry_loader import get_lifecycle_transitions
        data = get_lifecycle_transitions()
        assert len(data) == 5

    def test_causal_narratives_load(self):
        from symbolic.registry_loader import get_causal_narratives
        data = get_causal_narratives()
        assert len(data) >= 1


class TestArchetypeDeterminism:
    def test_same_chart_same_archetypes(self, chart):
        from symbolic.archetype_engine import determine_archetypes
        r1 = determine_archetypes(chart)
        r2 = determine_archetypes(chart)
        assert r1["dominant_archetypes"] == r2["dominant_archetypes"]

    def test_archetypes_have_required_fields(self, chart):
        from symbolic.archetype_engine import determine_archetypes
        result = determine_archetypes(chart)
        for arch in result["dominant_archetypes"]:
            assert "id" in arch
            assert "name" in arch
            assert "match_score" in arch


class TestBehavioralProfile:
    def test_profile_deterministic(self, chart):
        from symbolic.planetary_behavior_engine import build_behavioral_profile
        r1 = build_behavioral_profile(chart)
        r2 = build_behavioral_profile(chart)
        assert r1 == r2

    def test_profile_has_dominant_planets(self, chart):
        from symbolic.planetary_behavior_engine import build_behavioral_profile
        result = build_behavioral_profile(chart)
        assert len(result["behavioral_profile"]["dominant_planets"]) == 3

    def test_leadership_signature_exists(self, chart):
        from symbolic.planetary_behavior_engine import build_behavioral_profile
        result = build_behavioral_profile(chart)
        assert "primary_planet" in result["leadership_signature"]


class TestArbitration:
    def test_arbitration_deterministic(self, chart):
        from symbolic.arbitration_engine import resolve_conflicts
        r1 = resolve_conflicts(chart)
        r2 = resolve_conflicts(chart)
        assert r1 == r2

    def test_arbitration_returns_required_fields(self, chart):
        from symbolic.arbitration_engine import resolve_conflicts
        result = resolve_conflicts(chart)
        assert "arbitration_results" in result
        assert "suppressed_energies" in result
        assert "amplified_energies" in result


class TestLifecycle:
    def test_lifecycle_deterministic(self, chart):
        from symbolic.lifecycle_engine import determine_lifecycle_state
        dt = datetime(2025, 6, 1)
        r1 = determine_lifecycle_state(chart, dt)
        r2 = determine_lifecycle_state(chart, dt)
        assert r1 == r2

    def test_lifecycle_age_correct(self, chart):
        from symbolic.lifecycle_engine import determine_lifecycle_state
        result = determine_lifecycle_state(chart, datetime(2025, 6, 1))
        assert 49 < result["age_years"] < 51

    def test_lifecycle_phase_for_50yo(self, chart):
        from symbolic.lifecycle_engine import determine_lifecycle_state
        result = determine_lifecycle_state(chart, datetime(2025, 6, 1))
        assert result["current_state"]["phase"] == "mastery"


class TestSymbolicState:
    def test_full_state_deterministic(self, chart):
        from symbolic.symbolic_state_engine import build_symbolic_state
        dt = datetime(2025, 6, 1)
        r1 = build_symbolic_state(chart, dt)
        r2 = build_symbolic_state(chart, dt)
        assert r1 == r2

    def test_full_state_has_all_sections(self, chart):
        from symbolic.symbolic_state_engine import build_symbolic_state
        result = build_symbolic_state(chart, datetime(2025, 6, 1))
        required = [
            "dominant_archetypes", "secondary_archetypes", "behavioral_profile",
            "leadership_signature", "risk_signature", "lifecycle_state",
            "arbitration_results", "suppression_vectors", "amplification_vectors",
            "causal_narratives", "symbolic_summary",
        ]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_symbolic_summary_populated(self, chart):
        from symbolic.symbolic_state_engine import build_symbolic_state
        result = build_symbolic_state(chart, datetime(2025, 6, 1))
        summary = result["symbolic_summary"]
        assert summary["primary_archetype"] != "undetermined"
        assert summary["lifecycle_phase"] != "unknown"
        assert summary["dominant_planet"] != "unknown"


class TestNoContamination:
    def test_evaluator_outputs_unchanged(self, chart):
        """Symbolic layer must not modify chart state."""
        from symbolic.symbolic_state_engine import build_symbolic_state
        planets_before = dict(chart.planets)
        build_symbolic_state(chart, datetime(2025, 6, 1))
        assert chart.planets == planets_before

    def test_scoring_unchanged(self):
        """Existing scoring must produce same results after symbolic import."""
        from rules.event_engine import evaluate_event
        chart_data = {
            "planets": [{"name": "Jupiter", "multiplier": 1.5, "vimsopaka": 10, "status": "exalted"}],
            "strong_houses": [2, 11],
            "dasha": "Jupiter",
        }
        transit = {"strength": 1.0}
        score = evaluate_event("finance", chart_data, transit)
        # Import symbolic layer
        from symbolic.symbolic_state_engine import build_symbolic_state
        # Score again
        score_after = evaluate_event("finance", chart_data, transit)
        assert score == score_after
