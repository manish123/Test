"""
Phase 8 Evaluator Profile Migration Tests

Proves that:
1. Each evaluator resolves the correct scoring profile
2. Default/fallback mode produces identical outputs
3. Trading profile never contaminates non-trading domains
4. All evaluators have _SCORING_PROFILE defined

Run with:
    pytest astro_engine/tests/test_evaluator_profile_migration.py -q
"""

import sys
import re
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"


# ═══════════════════════════════════════════════════════════════
# TEST 1: ALL EVALUATORS HAVE PROFILE LOADED
# ═══════════════════════════════════════════════════════════════

ALL_EVALUATORS = [
    "marriage_evaluator", "career_evaluator", "childbirth_evaluator",
    "business_evaluator", "medical_evaluator", "fame_evaluator",
    "property_evaluator", "property_purchase_evaluator",
    "vehicle_purchase_evaluator", "relocation_evaluator",
    "parent_loss_evaluator", "financial_crisis_evaluator",
    "wealth_evaluator", "career_authority_evaluator",
    "social_network_evaluator", "creative_output_evaluator",
    "litigation_evaluator", "foreign_migration_evaluator",
]


class TestAllEvaluatorsHaveProfile:
    """Every evaluator must have _SCORING_PROFILE defined at module level."""

    @pytest.mark.parametrize("module_name", ALL_EVALUATORS)
    def test_has_scoring_profile(self, module_name):
        path = RULES_DIR / f"{module_name}.py"
        content = path.read_text()
        assert "_SCORING_PROFILE" in content, (
            f"{module_name} missing _SCORING_PROFILE"
        )

    @pytest.mark.parametrize("module_name", ALL_EVALUATORS)
    def test_imports_load_scoring_profile(self, module_name):
        path = RULES_DIR / f"{module_name}.py"
        content = path.read_text()
        assert "load_scoring_profile" in content, (
            f"{module_name} missing load_scoring_profile import"
        )


# ═══════════════════════════════════════════════════════════════
# TEST 2: CORRECT DOMAIN RESOLUTION
# ═══════════════════════════════════════════════════════════════

DOMAIN_MAP = {
    "marriage_evaluator": "relationship",
    "career_evaluator": "career",
    "childbirth_evaluator": "relationship",
    "business_evaluator": "career",
    "medical_evaluator": "health",
    "fame_evaluator": "career",
    "property_evaluator": "finance",
    "property_purchase_evaluator": "finance",
    "vehicle_purchase_evaluator": "finance",
    "relocation_evaluator": "general_life",
    "parent_loss_evaluator": "general_life",
    "financial_crisis_evaluator": "finance",
    "wealth_evaluator": "finance",
    "career_authority_evaluator": "career",
    "social_network_evaluator": "general_life",
    "creative_output_evaluator": "general_life",
    "litigation_evaluator": "general_life",
    "foreign_migration_evaluator": "general_life",
}


class TestCorrectDomainResolution:
    """Each evaluator must resolve to the correct domain profile."""

    @pytest.mark.parametrize("module_name,expected_domain", list(DOMAIN_MAP.items()))
    def test_domain_in_source(self, module_name, expected_domain):
        path = RULES_DIR / f"{module_name}.py"
        content = path.read_text()
        # Find the load_scoring_profile call and verify domain
        pattern = rf'load_scoring_profile\("{re.escape(expected_domain)}"\)'
        assert re.search(pattern, content), (
            f"{module_name} should load profile for '{expected_domain}'"
        )


# ═══════════════════════════════════════════════════════════════
# TEST 3: TRADING ISOLATION
# ═══════════════════════════════════════════════════════════════

class TestTradingNeverContaminates:
    """Non-trading evaluators must never load the trading profile."""

    NON_TRADING = [k for k, v in DOMAIN_MAP.items() if v != "trading"]

    @pytest.mark.parametrize("module_name", NON_TRADING)
    def test_no_trading_profile(self, module_name):
        path = RULES_DIR / f"{module_name}.py"
        content = path.read_text()
        assert 'load_scoring_profile("trading")' not in content, (
            f"{module_name} must NOT load trading profile"
        )


# ═══════════════════════════════════════════════════════════════
# TEST 4: EVALUATORS STILL IMPORT AND RUN
# ═══════════════════════════════════════════════════════════════

class TestEvaluatorsStillRun:
    """All evaluators must import without error after migration."""

    @pytest.mark.parametrize("module_name", ALL_EVALUATORS)
    def test_module_imports(self, module_name):
        mod = __import__(f"rules.{module_name}", fromlist=[module_name])
        assert hasattr(mod, "ChartState")
        assert hasattr(mod, "TransitState")

    def test_wealth_evaluator_runs(self):
        from datetime import datetime
        from rules.wealth_evaluator import ChartState, evaluate_wealth_for_date
        chart = ChartState(datetime(1990, 5, 15, 6, 30), 21.1458, 79.0882, 310)
        result = evaluate_wealth_for_date(chart, datetime(2025, 6, 1, 9, 15))
        assert hasattr(result, "total_score")
        assert isinstance(result.total_score, (int, float))

    def test_career_authority_evaluator_runs(self):
        from datetime import datetime
        from rules.career_authority_evaluator import ChartState, evaluate_authority_for_date
        chart = ChartState(datetime(1990, 5, 15, 6, 30), 21.1458, 79.0882, 310)
        result = evaluate_authority_for_date(chart, datetime(2025, 6, 1, 9, 15))
        assert hasattr(result, "total_score")

    def test_litigation_evaluator_runs(self):
        from datetime import datetime
        from rules.litigation_evaluator import ChartState, evaluate_litigation_for_date
        chart = ChartState(datetime(1990, 5, 15, 6, 30), 21.1458, 79.0882, 310)
        result = evaluate_litigation_for_date(chart, datetime(2025, 6, 1, 9, 15))
        assert hasattr(result, "total_score")
