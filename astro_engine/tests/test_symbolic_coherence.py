"""
Phase 10B Symbolic Coherence Tests
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


@pytest.fixture
def coherent_state(chart):
    from symbolic.coherent_state_builder import build_coherent_state
    return build_coherent_state(chart, eval_date=datetime(2025, 6, 1))


class TestCoherenceDeterminism:
    def test_coherent_state_deterministic(self, chart):
        from symbolic.coherent_state_builder import build_coherent_state
        r1 = build_coherent_state(chart, datetime(2025, 6, 1))
        r2 = build_coherent_state(chart, datetime(2025, 6, 1))
        assert r1["semantic_coherence_score"] == r2["semantic_coherence_score"]
        assert r1["core_identity"] == r2["core_identity"]

    def test_coherence_score_in_range(self, coherent_state):
        assert 0.0 <= coherent_state["semantic_coherence_score"] <= 1.0


class TestArchetypePruning:
    def test_core_identity_populated(self, coherent_state):
        ci = coherent_state["core_identity"]
        assert ci["primary"] != "undetermined"
        assert ci["fusion_type"] in ("single", "complementary_dual", "tension_dual", "parallel_dual")

    def test_pruning_stable(self, chart):
        from symbolic.coherent_state_builder import build_coherent_state
        r1 = build_coherent_state(chart, datetime(2025, 6, 1))
        r2 = build_coherent_state(chart, datetime(2025, 6, 1))
        assert r1["dominant_archetypes"] == r2["dominant_archetypes"]
        assert r1["suppressed_archetypes"] == r2["suppressed_archetypes"]


class TestSemanticCompression:
    def test_compression_reduces(self, coherent_state):
        stats = coherent_state.get("_compression_stats", {})
        assert stats.get("original_items", 0) >= stats.get("compressed_items", 0)

    def test_behavioral_core_compact(self, coherent_state):
        bc = coherent_state["behavioral_core"]
        for key in ("leadership", "risk", "economic"):
            assert len(bc.get(key, [])) <= 4


class TestNarrativeRanking:
    def test_narratives_ranked(self, coherent_state):
        narr = coherent_state["top_causal_narratives"]
        if len(narr) >= 2:
            assert narr[0].get("rank_score", 0) >= narr[1].get("rank_score", 0)

    def test_narrative_stats(self, coherent_state):
        stats = coherent_state["_narrative_stats"]
        assert stats["kept"] <= stats["total"]


class TestPromptPayload:
    def test_prompt_context_compact(self, coherent_state):
        ctx = coherent_state["prompt_ready_context"]
        tokens = ctx.get("_meta", {}).get("estimated_tokens", 9999)
        assert tokens < 600  # Must be compact

    def test_minimal_context_ultra_compact(self, coherent_state):
        import json
        mini = coherent_state["_minimal_context"]
        mini_str = json.dumps(mini)
        assert len(mini_str) < 300  # Ultra compact

    def test_prompt_has_required_sections(self, coherent_state):
        ctx = coherent_state["prompt_ready_context"]
        for key in ("identity", "behavioral_core", "lifecycle", "coherence"):
            assert key in ctx


class TestNoContamination:
    def test_evaluator_unchanged(self, chart):
        from symbolic.coherent_state_builder import build_coherent_state
        planets_before = dict(chart.planets)
        build_coherent_state(chart, datetime(2025, 6, 1))
        assert chart.planets == planets_before

    def test_scoring_unchanged(self):
        from rules.event_engine import evaluate_event
        from symbolic.coherent_state_builder import build_coherent_state
        chart_data = {"planets": [{"name": "Jupiter", "multiplier": 1.5, "vimsopaka": 10, "status": "exalted"}],
                      "strong_houses": [2, 11], "dasha": "Jupiter"}
        score_before = evaluate_event("finance", chart_data, {"strength": 1.0})
        # Import and run symbolic layer
        from rules.evaluator_base import BaseChartState
        c = BaseChartState(TEST_BIRTH, TEST_LAT, TEST_LON, TEST_ALT)
        build_coherent_state(c, datetime(2025, 6, 1))
        score_after = evaluate_event("finance", chart_data, {"strength": 1.0})
        assert score_before == score_after
