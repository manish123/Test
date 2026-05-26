"""
Tests for the Timing API Adapter.

Verifies determinism, contract compliance, token budgets, and no contamination.
"""

import sys
from pathlib import Path
from datetime import datetime
from copy import deepcopy

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BIRTH_A = {"date": datetime(1975, 7, 22, 18, 15), "lat": 21.2094, "lon": 81.4285}
BIRTH_B = {"date": datetime(1983, 11, 30, 21, 20), "lat": 23.1186, "lon": 83.1960, "alt": 594}
EVAL = datetime(2025, 6, 1, 9, 15)


class TestTimingContextDeterminism:
    def test_same_input_same_output(self):
        from orchestration.timing_api_adapter import build_timing_context
        r1 = build_timing_context(BIRTH_A, eval_date=EVAL)
        r2 = build_timing_context(BIRTH_A, eval_date=EVAL)
        r1.pop("_routing", None); r2.pop("_routing", None)
        assert r1 == r2

    def test_different_subjects_differ(self):
        from orchestration.timing_api_adapter import build_timing_context
        r1 = build_timing_context(BIRTH_A, eval_date=EVAL)
        r2 = build_timing_context(BIRTH_B, eval_date=EVAL)
        assert r1.get("lifecycle") != r2.get("lifecycle") or r1.get("identity") != r2.get("identity")


class TestTimingContextContract:
    @pytest.fixture
    def result(self):
        from orchestration.timing_api_adapter import build_timing_context
        return build_timing_context(BIRTH_A, eval_date=EVAL)

    def test_has_lifecycle(self, result):
        assert "lifecycle" in result
        lc = result["lifecycle"]
        assert "phase" in lc
        assert "stability" in lc
        assert "direction" in lc

    def test_has_coherence(self, result):
        assert "coherence" in result
        assert "score" in result["coherence"]

    def test_has_routing(self, result):
        assert "_routing" in result
        assert result["_routing"]["target"] == "timing_context"

    def test_lifecycle_populated(self, result):
        assert result["lifecycle"]["phase"] != "unknown"
        assert result["lifecycle"]["direction"] != "unknown"


class TestTimingTokenBudget:
    def test_within_budget(self):
        from orchestration.timing_api_adapter import build_timing_context
        from orchestration.token_budget import estimate_tokens
        result = build_timing_context(BIRTH_A, eval_date=EVAL)
        tokens = estimate_tokens(result)
        assert tokens <= 440  # 400 + 10% tolerance


class TestPredictionContext:
    def test_deterministic(self):
        from orchestration.timing_api_adapter import build_prediction_context
        r1 = build_prediction_context(BIRTH_A, eval_date=EVAL)
        r2 = build_prediction_context(BIRTH_A, eval_date=EVAL)
        r1.pop("_routing", None); r2.pop("_routing", None)
        assert r1 == r2

    def test_has_narratives(self):
        from orchestration.timing_api_adapter import build_prediction_context
        result = build_prediction_context(BIRTH_A, eval_date=EVAL)
        assert "top_narratives" in result

    def test_has_identity(self):
        from orchestration.timing_api_adapter import build_prediction_context
        result = build_prediction_context(BIRTH_A, eval_date=EVAL)
        assert "identity" in result

    def test_within_budget(self):
        from orchestration.timing_api_adapter import build_prediction_context
        from orchestration.token_budget import estimate_tokens
        result = build_prediction_context(BIRTH_A, eval_date=EVAL)
        tokens = estimate_tokens(result)
        assert tokens <= 275  # 250 + 10% tolerance

    def test_routing_target(self):
        from orchestration.timing_api_adapter import build_prediction_context
        result = build_prediction_context(BIRTH_A, eval_date=EVAL)
        assert result["_routing"]["target"] == "prediction_context"


class TestWeeklyInjection:
    def test_produces_string(self):
        from orchestration.timing_api_adapter import build_weekly_prediction_injection
        result = build_weekly_prediction_injection(BIRTH_A, eval_date=EVAL)
        assert isinstance(result, str)
        assert len(result) > 30

    def test_contains_phase(self):
        from orchestration.timing_api_adapter import build_weekly_prediction_injection
        result = build_weekly_prediction_injection(BIRTH_A, eval_date=EVAL)
        assert "Life Phase:" in result

    def test_deterministic(self):
        from orchestration.timing_api_adapter import build_weekly_prediction_injection
        r1 = build_weekly_prediction_injection(BIRTH_A, eval_date=EVAL)
        r2 = build_weekly_prediction_injection(BIRTH_A, eval_date=EVAL)
        assert r1 == r2


class TestNoMutation:
    def test_timing_no_mutation(self):
        from orchestration.timing_api_adapter import build_timing_context
        original = deepcopy(BIRTH_A)
        build_timing_context(BIRTH_A, eval_date=EVAL)
        assert BIRTH_A == original

    def test_prediction_no_mutation(self):
        from orchestration.timing_api_adapter import build_prediction_context
        original = deepcopy(BIRTH_B)
        build_prediction_context(BIRTH_B, eval_date=EVAL)
        assert BIRTH_B == original


class TestNoContamination:
    def test_scoring_unchanged(self):
        from rules.event_engine import evaluate_event
        from orchestration.timing_api_adapter import build_timing_context
        chart_data = {"planets": [{"name": "Jupiter", "multiplier": 1.5, "vimsopaka": 10, "status": "exalted"}],
                      "strong_houses": [2, 11], "dasha": "Jupiter"}
        score_before = evaluate_event("finance", chart_data, {"strength": 1.0})
        build_timing_context(BIRTH_A, eval_date=EVAL)
        score_after = evaluate_event("finance", chart_data, {"strength": 1.0})
        assert score_before == score_after
