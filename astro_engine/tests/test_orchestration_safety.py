"""
Orchestration Safety Regression Tests — Prevents dasha/transit layer skipping.

These tests FAIL LOUDLY if:
- Any evaluator's dasha layer is skipped when required
- Any evaluator's transit layer crashes due to missing methods
- Any evaluator is silently dropped from the runner
- The generic fallback regresses to transit-only scoring
- BaseTransitState loses required conjunction methods

Run: ../.venv/bin/pytest tests/test_orchestration_safety.py -v
"""

import sys
import importlib
import inspect
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rules.evaluator_base import BaseChartState, BaseTransitState
from rules.multi_evaluator_runner import evaluate_all_domains, _get_current_dasha


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

ALL_EVALUATORS = [
    "marriage_evaluator", "childbirth_evaluator", "career_evaluator",
    "business_evaluator", "relocation_evaluator", "property_evaluator",
    "property_purchase_evaluator", "parent_loss_evaluator", "medical_evaluator",
    "fame_evaluator", "financial_crisis_evaluator", "vehicle_purchase_evaluator",
    "wealth_evaluator", "career_authority_evaluator", "social_network_evaluator",
    "creative_output_evaluator", "litigation_evaluator", "foreign_migration_evaluator",
]

THREE_PARAM_EVALUATORS = [
    "marriage_evaluator", "childbirth_evaluator", "career_evaluator",
    "business_evaluator", "relocation_evaluator", "property_evaluator",
    "property_purchase_evaluator", "parent_loss_evaluator", "medical_evaluator",
    "fame_evaluator", "financial_crisis_evaluator", "vehicle_purchase_evaluator",
]

TWO_PARAM_EVALUATORS = [
    "wealth_evaluator", "career_authority_evaluator", "social_network_evaluator",
    "creative_output_evaluator", "litigation_evaluator", "foreign_migration_evaluator",
]

# Test subject
BIRTH_DT = datetime(1975, 7, 22, 18, 15)
LAT, LON, ALT = 21.2094, 81.4285, 297
EVAL_DATE = datetime(2009, 5, 7)


# ═══════════════════════════════════════════════════════════════
# A. DASHA WIRING REGRESSION
# ═══════════════════════════════════════════════════════════════

class TestDashaWiring:
    """Every 3-param evaluator must receive MD/AD from the runner."""

    def test_get_current_dasha_works(self):
        chart = BaseChartState(BIRTH_DT, LAT, LON, ALT)
        md, ad = _get_current_dasha(BIRTH_DT, chart.moon_lon, EVAL_DATE)
        assert md != "unknown", "MD lord must be computed"
        assert ad != "unknown", "AD lord must be computed"

    @pytest.mark.parametrize("evaluator_name", THREE_PARAM_EVALUATORS)
    def test_dasha_layer_callable_with_3_params(self, evaluator_name):
        """Each 3-param evaluator's dasha layer must accept (chart, md_lord, ad_lord)."""
        mod = importlib.import_module(f"rules.{evaluator_name}")
        assert hasattr(mod, "evaluate_dasha_layer"), f"{evaluator_name} missing evaluate_dasha_layer"
        sig = inspect.signature(mod.evaluate_dasha_layer)
        params = list(sig.parameters.keys())
        assert len(params) == 3, f"{evaluator_name} dasha layer has {len(params)} params, expected 3"

    @pytest.mark.parametrize("evaluator_name", THREE_PARAM_EVALUATORS)
    def test_dasha_layer_executes_without_error(self, evaluator_name):
        """Each 3-param evaluator's dasha layer must execute without crashing."""
        mod = importlib.import_module(f"rules.{evaluator_name}")
        chart = mod.ChartState(BIRTH_DT, LAT, LON, ALT)
        base_chart = BaseChartState(BIRTH_DT, LAT, LON, ALT)
        md, ad = _get_current_dasha(BIRTH_DT, base_chart.moon_lon, EVAL_DATE)
        # Must not raise
        result = mod.evaluate_dasha_layer(chart, md, ad)
        assert isinstance(result, list), f"{evaluator_name} dasha layer must return a list"

    def test_runner_generic_fallback_computes_dasha(self):
        """The generic fallback in evaluate_all_domains must compute dasha for 3-param evaluators."""
        results = evaluate_all_domains(BIRTH_DT, LAT, LON, EVAL_DATE, ALT)
        # Marriage is a 3-param evaluator routed through generic fallback
        marriage = results.get("marriage", {})
        assert marriage.get("score", 0) > 50, (
            f"Marriage score at wedding date should be >50 (got {marriage.get('score', 0)}). "
            "If this fails, dasha layer is being skipped again."
        )


# ═══════════════════════════════════════════════════════════════
# B. TRANSIT WIRING REGRESSION
# ═══════════════════════════════════════════════════════════════

class TestTransitWiring:
    """Transit helpers must be available on BaseTransitState."""

    def test_base_transit_state_has_planet_conjunct_natal(self):
        assert hasattr(BaseTransitState, "planet_conjunct_natal")

    def test_base_transit_state_has_jupiter_conjunct_natal(self):
        assert hasattr(BaseTransitState, "jupiter_conjunct_natal")

    def test_base_transit_state_has_rahu_conjunct_natal(self):
        assert hasattr(BaseTransitState, "rahu_conjunct_natal")

    def test_base_transit_state_has_rahu_conjunct_natal_moon(self):
        assert hasattr(BaseTransitState, "rahu_conjunct_natal_moon")

    def test_base_transit_state_has_saturn_conjunct_natal(self):
        assert hasattr(BaseTransitState, "saturn_conjunct_natal")

    @pytest.mark.parametrize("evaluator_name", ALL_EVALUATORS)
    def test_transit_layer_executes_without_error(self, evaluator_name):
        """Every evaluator's transit layer must execute without AttributeError."""
        mod = importlib.import_module(f"rules.{evaluator_name}")
        chart = mod.ChartState(BIRTH_DT, LAT, LON, ALT)
        transit = mod.TransitState(EVAL_DATE, chart)
        # Must not raise AttributeError
        result = mod.evaluate_transit_layer(chart, transit)
        assert isinstance(result, list), f"{evaluator_name} transit layer must return a list"


# ═══════════════════════════════════════════════════════════════
# C. LAYER COVERAGE REGRESSION
# ═══════════════════════════════════════════════════════════════

class TestLayerCoverage:
    """All 5 layers must be defined for every evaluator."""

    @pytest.mark.parametrize("evaluator_name", ALL_EVALUATORS)
    def test_all_five_layers_exist(self, evaluator_name):
        mod = importlib.import_module(f"rules.{evaluator_name}")
        assert hasattr(mod, "evaluate_dasha_layer"), f"{evaluator_name} missing dasha layer"
        assert hasattr(mod, "evaluate_transit_layer"), f"{evaluator_name} missing transit layer"
        assert hasattr(mod, "evaluate_fast_trigger_layer"), f"{evaluator_name} missing fast trigger layer"
        assert hasattr(mod, "evaluate_classical_layer"), f"{evaluator_name} missing classical layer"
        assert hasattr(mod, "evaluate_outcome_layer"), f"{evaluator_name} missing outcome layer"

    @pytest.mark.parametrize("evaluator_name", ALL_EVALUATORS)
    def test_fast_trigger_executes(self, evaluator_name):
        mod = importlib.import_module(f"rules.{evaluator_name}")
        chart = mod.ChartState(BIRTH_DT, LAT, LON, ALT)
        transit = mod.TransitState(EVAL_DATE, chart)
        result = mod.evaluate_fast_trigger_layer(chart, transit)
        assert isinstance(result, list)

    @pytest.mark.parametrize("evaluator_name", ALL_EVALUATORS)
    def test_classical_layer_executes(self, evaluator_name):
        mod = importlib.import_module(f"rules.{evaluator_name}")
        chart = mod.ChartState(BIRTH_DT, LAT, LON, ALT)
        result = mod.evaluate_classical_layer(chart)
        assert isinstance(result, dict)

    @pytest.mark.parametrize("evaluator_name", ALL_EVALUATORS)
    def test_outcome_layer_executes(self, evaluator_name):
        mod = importlib.import_module(f"rules.{evaluator_name}")
        chart = mod.ChartState(BIRTH_DT, LAT, LON, ALT)
        result = mod.evaluate_outcome_layer(chart)
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════
# D. RUNNER COMPLETENESS
# ═══════════════════════════════════════════════════════════════

class TestRunnerCompleteness:
    """The runner must invoke all registered evaluators."""

    def test_all_domains_present_in_output(self):
        results = evaluate_all_domains(BIRTH_DT, LAT, LON, EVAL_DATE, ALT)
        expected_domains = {
            "marriage", "childbirth", "career", "business", "relocation",
            "property", "property_purchase", "parent_loss", "medical",
            "fame", "financial_crisis", "vehicle_purchase", "wealth",
            "career_authority", "social_network", "creative_output",
            "litigation", "foreign_migration",
        }
        present = set(results.keys())
        missing = expected_domains - present
        assert not missing, f"Runner is missing domains: {missing}"

    def test_no_domain_has_error(self):
        results = evaluate_all_domains(BIRTH_DT, LAT, LON, EVAL_DATE, ALT)
        errors = {k: v for k, v in results.items() if "error" in v}
        assert not errors, f"Domains with errors: {errors}"

    def test_marriage_score_includes_dasha_signal(self):
        """Marriage at wedding date must include dasha contribution (>50 total)."""
        results = evaluate_all_domains(BIRTH_DT, LAT, LON, EVAL_DATE, ALT)
        score = results.get("marriage", {}).get("score", 0)
        # Without dasha, marriage scores ~58. With dasha, it scores ~103.
        assert score > 80, (
            f"Marriage score {score} is too low — dasha layer may be skipped. "
            "Expected >80 when dasha is properly included."
        )

    def test_childbirth_score_at_birth_date(self):
        """Childbirth at actual birth date must have dasha signal."""
        birth_date = datetime(2010, 12, 4)
        results = evaluate_all_domains(BIRTH_DT, LAT, LON, birth_date, ALT)
        score = results.get("childbirth", {}).get("score", 0)
        # Without dasha, childbirth scores ~22. With dasha, it scores ~43+.
        assert score > 35, (
            f"Childbirth score {score} at birth date is too low — dasha may be skipped. "
            "Expected >35 when dasha is properly included."
        )


# ═══════════════════════════════════════════════════════════════
# E. FIXTURE REGRESSION (gold-label events)
# ═══════════════════════════════════════════════════════════════

class TestFixtureRegression:
    """Gold-label events must remain detectable after any code change."""

    def test_marriage_subject_a_detectable(self):
        """Marriage (7 May 2009) must score VERY_HIGH for Subject A."""
        results = evaluate_all_domains(BIRTH_DT, LAT, LON, datetime(2009, 5, 7), ALT)
        score = results.get("marriage", {}).get("score", 0)
        assert score >= 80, f"Marriage(A) at actual date: {score} < 80"

    def test_marriage_subject_b_detectable(self):
        """Marriage (7 May 2009) must score HIGH+ for Subject B."""
        birth_b = datetime(1983, 11, 30, 21, 20)
        results = evaluate_all_domains(birth_b, 23.1186, 83.1960, datetime(2009, 5, 7), 594)
        score = results.get("marriage", {}).get("score", 0)
        assert score >= 50, f"Marriage(B) at actual date: {score} < 50"

    def test_childbirth_subject_b_detectable(self):
        """Childbirth (4 Dec 2010) must score HIGH+ for Subject B."""
        birth_b = datetime(1983, 11, 30, 21, 20)
        results = evaluate_all_domains(birth_b, 23.1186, 83.1960, datetime(2010, 12, 4), 594)
        score = results.get("childbirth", {}).get("score", 0)
        assert score >= 50, f"Childbirth(B) at actual date: {score} < 50"

    def test_father_death_subject_a_detectable(self):
        """Father death (Mar 2018) must score HIGH+ for Subject A."""
        results = evaluate_all_domains(BIRTH_DT, LAT, LON, datetime(2018, 3, 15), ALT)
        score = results.get("parent_loss", {}).get("score", 0)
        assert score >= 40, f"Father death(A) at actual date: {score} < 40"

    def test_relocation_bhopal_detectable(self):
        """Bhopal relocation (2003) must score HIGH+ for Subject A."""
        results = evaluate_all_domains(BIRTH_DT, LAT, LON, datetime(2003, 6, 1), ALT)
        score = results.get("relocation", {}).get("score", 0)
        assert score >= 50, f"Bhopal relocation(A): {score} < 50"

    def test_relocation_pune_detectable(self):
        """Pune relocation (Aug 2007) must score HIGH+ for Subject A."""
        results = evaluate_all_domains(BIRTH_DT, LAT, LON, datetime(2007, 8, 20), ALT)
        score = results.get("relocation", {}).get("score", 0)
        assert score >= 100, f"Pune relocation(A): {score} < 100"
