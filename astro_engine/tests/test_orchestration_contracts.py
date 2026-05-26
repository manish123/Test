"""
Phase 11A Orchestration Contract Tests
"""
import sys
from pathlib import Path
from datetime import datetime
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TEST_BIRTH = datetime(1975, 7, 22, 18, 15)
TEST_LAT, TEST_LON, TEST_ALT = 21.2094, 81.4285, 297


@pytest.fixture
def coherent_state():
    from rules.evaluator_base import BaseChartState
    from symbolic.coherent_state_builder import build_coherent_state
    chart = BaseChartState(TEST_BIRTH, TEST_LAT, TEST_LON, TEST_ALT)
    return build_coherent_state(chart, eval_date=datetime(2025, 6, 1))


class TestContracts:
    def test_all_contracts_defined(self):
        from orchestration.context_contracts import list_contracts
        contracts = list_contracts()
        assert "minimal_context" in contracts
        assert "personality_context" in contracts
        assert "timing_context" in contracts
        assert "career_context" in contracts
        assert "prediction_context" in contracts
        assert "relationship_context" in contracts
        assert "full_symbolic_context" in contracts

    def test_contracts_have_budgets(self):
        from orchestration.context_contracts import CONTRACTS
        for name, contract in CONTRACTS.items():
            assert "token_budget" in contract
            assert contract["token_budget"] > 0


class TestTokenBudget:
    def test_estimate_tokens(self):
        from orchestration.token_budget import estimate_tokens
        payload = {"key": "value", "list": [1, 2, 3]}
        tokens = estimate_tokens(payload)
        assert tokens > 0 and tokens < 50

    def test_enforce_budget_within(self):
        from orchestration.token_budget import enforce_budget
        payload = {"a": "short"}
        result = enforce_budget(payload, 1000)
        assert result == payload  # No pruning needed

    def test_budget_utilization(self):
        from orchestration.token_budget import compute_budget_utilization
        result = compute_budget_utilization({"key": "val"}, 100)
        assert result["within_budget"] is True
        assert result["utilization"] <= 1.0


class TestContextRouter:
    @pytest.mark.parametrize("target", [
        "minimal_context", "personality_context", "timing_context",
        "career_context", "prediction_context", "relationship_context",
    ])
    def test_routing_produces_payload(self, coherent_state, target):
        from orchestration.context_router import route_context
        result = route_context(coherent_state, target)
        assert isinstance(result, dict)
        assert "_routing" in result
        assert result["_routing"]["target"] == target

    def test_routing_deterministic(self, coherent_state):
        from orchestration.context_router import route_context
        r1 = route_context(coherent_state, "personality_context")
        r2 = route_context(coherent_state, "personality_context")
        assert r1 == r2

    @pytest.mark.parametrize("target", [
        "minimal_context", "personality_context", "timing_context",
        "career_context", "prediction_context",
    ])
    def test_routing_within_budget(self, coherent_state, target):
        from orchestration.context_router import route_context
        from orchestration.context_contracts import get_token_budget
        result = route_context(coherent_state, target)
        budget = get_token_budget(target)
        tokens = result["_routing"]["tokens_used"]
        assert tokens <= budget * 1.1  # Allow 10% tolerance


class TestPromptSections:
    def test_section_order(self):
        from orchestration.prompt_sections import get_section_order
        order = get_section_order()
        assert order[0] == "identity"
        assert order[1] == "behavioral_core"
        assert order[2] == "lifecycle_state"

    def test_required_sections(self):
        from orchestration.prompt_sections import get_required_sections
        required = get_required_sections()
        assert "identity" in required
        assert "behavioral_core" in required
        assert "lifecycle_state" in required

    def test_section_budget_allocation(self):
        from orchestration.prompt_sections import compute_section_budget
        allocation = compute_section_budget(600)
        assert allocation["identity"] == 80
        assert allocation["behavioral_core"] == 120
        assert sum(allocation.values()) <= 600


class TestPayloadBuilder:
    def test_build_payload(self, coherent_state):
        from orchestration.payload_builder import build_payload
        result = build_payload(coherent_state, "personality_context")
        assert "payload" in result
        assert "sections" in result
        assert "budget_utilization" in result
        assert result["target"] == "personality_context"

    def test_build_all_payloads(self, coherent_state):
        from orchestration.payload_builder import build_all_payloads
        results = build_all_payloads(coherent_state)
        assert len(results) == 7  # All contracts
        for target, result in results.items():
            assert "payload" in result

    def test_payload_deterministic(self, coherent_state):
        from orchestration.payload_builder import build_payload
        r1 = build_payload(coherent_state, "career_context")
        r2 = build_payload(coherent_state, "career_context")
        assert r1["payload"] == r2["payload"]


class TestNoContamination:
    def test_scoring_unchanged(self):
        from rules.event_engine import evaluate_event
        from orchestration.payload_builder import build_all_payloads
        chart_data = {"planets": [{"name": "Jupiter", "multiplier": 1.5, "vimsopaka": 10, "status": "exalted"}],
                      "strong_houses": [2, 11], "dasha": "Jupiter"}
        score_before = evaluate_event("finance", chart_data, {"strength": 1.0})
        # Run orchestration
        from rules.evaluator_base import BaseChartState
        from symbolic.coherent_state_builder import build_coherent_state
        c = BaseChartState(TEST_BIRTH, TEST_LAT, TEST_LON, TEST_ALT)
        state = build_coherent_state(c, datetime(2025, 6, 1))
        build_all_payloads(state)
        score_after = evaluate_event("finance", chart_data, {"strength": 1.0})
        assert score_before == score_after
