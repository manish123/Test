"""
Tests for the Career API Adapter.
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


class TestCareerContextDeterminism:
    def test_same_input_same_output(self):
        from orchestration.career_api_adapter import build_career_context
        r1 = build_career_context(BIRTH_A, eval_date=EVAL)
        r2 = build_career_context(BIRTH_A, eval_date=EVAL)
        r1.pop("_routing", None); r2.pop("_routing", None)
        assert r1 == r2

    def test_different_subjects_differ(self):
        from orchestration.career_api_adapter import build_career_context
        r1 = build_career_context(BIRTH_A, eval_date=EVAL)
        r2 = build_career_context(BIRTH_B, eval_date=EVAL)
        assert r1 != r2


class TestCareerContextContract:
    @pytest.fixture
    def result(self):
        from orchestration.career_api_adapter import build_career_context
        return build_career_context(BIRTH_A, eval_date=EVAL)

    def test_has_identity(self, result):
        assert "identity" in result
        assert "primary_archetype" in result["identity"]
        assert result["identity"]["primary_archetype"] != "undetermined"

    def test_has_lifecycle(self, result):
        assert "lifecycle" in result
        assert result["lifecycle"]["phase"] != "unknown"

    def test_has_routing(self, result):
        assert "_routing" in result
        assert result["_routing"]["target"] == "career_context"

    def test_within_budget(self, result):
        from orchestration.token_budget import estimate_tokens
        tokens = estimate_tokens(result)
        assert tokens <= 550  # 500 + 10% tolerance


class TestBusinessContext:
    @pytest.fixture
    def result(self):
        from orchestration.career_api_adapter import build_business_context
        return build_business_context(BIRTH_A, eval_date=EVAL)

    def test_has_business_section(self, result):
        assert "business" in result

    def test_has_scaling_style(self, result):
        biz = result["business"]
        assert "scaling_style" in biz
        assert isinstance(biz["scaling_style"], list)

    def test_has_collapse_vectors(self, result):
        biz = result["business"]
        assert "collapse_vectors" in biz

    def test_has_wealth_behavior(self, result):
        biz = result["business"]
        assert "wealth_behavior" in biz

    def test_within_budget(self, result):
        from orchestration.token_budget import estimate_tokens
        tokens = estimate_tokens(result)
        assert tokens <= 605  # 550 + 10% tolerance

    def test_deterministic(self):
        from orchestration.career_api_adapter import build_business_context
        r1 = build_business_context(BIRTH_A, eval_date=EVAL)
        r2 = build_business_context(BIRTH_A, eval_date=EVAL)
        r1.pop("_routing", None); r2.pop("_routing", None)
        assert r1 == r2


class TestCareerPromptInjection:
    def test_produces_string(self):
        from orchestration.career_api_adapter import build_career_prompt_injection
        result = build_career_prompt_injection(BIRTH_A, eval_date=EVAL)
        assert isinstance(result, str)
        assert len(result) > 50

    def test_contains_archetype(self):
        from orchestration.career_api_adapter import build_career_prompt_injection
        result = build_career_prompt_injection(BIRTH_A, eval_date=EVAL)
        assert "Archetype:" in result

    def test_contains_career_phase(self):
        from orchestration.career_api_adapter import build_career_prompt_injection
        result = build_career_prompt_injection(BIRTH_A, eval_date=EVAL)
        assert "Career Phase:" in result

    def test_deterministic(self):
        from orchestration.career_api_adapter import build_career_prompt_injection
        r1 = build_career_prompt_injection(BIRTH_A, eval_date=EVAL)
        r2 = build_career_prompt_injection(BIRTH_A, eval_date=EVAL)
        assert r1 == r2


class TestNoMutation:
    def test_career_no_mutation(self):
        from orchestration.career_api_adapter import build_career_context
        original = deepcopy(BIRTH_A)
        build_career_context(BIRTH_A, eval_date=EVAL)
        assert BIRTH_A == original

    def test_business_no_mutation(self):
        from orchestration.career_api_adapter import build_business_context
        original = deepcopy(BIRTH_B)
        build_business_context(BIRTH_B, eval_date=EVAL)
        assert BIRTH_B == original


class TestNoContamination:
    def test_scoring_unchanged(self):
        from rules.event_engine import evaluate_event
        from orchestration.career_api_adapter import build_business_context
        chart_data = {"planets": [{"name": "Jupiter", "multiplier": 1.5, "vimsopaka": 10, "status": "exalted"}],
                      "strong_houses": [2, 11], "dasha": "Jupiter"}
        score_before = evaluate_event("finance", chart_data, {"strength": 1.0})
        build_business_context(BIRTH_A, eval_date=EVAL)
        score_after = evaluate_event("finance", chart_data, {"strength": 1.0})
        assert score_before == score_after
