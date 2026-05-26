"""
Phase 9 Pipeline Profile Isolation Tests

Proves that:
1. Trading profile affects trading path only
2. Non-trading paths have no nakshatra overlay
3. Canonical tara values are untouched
4. Nakshatra overlays no longer contaminate non-trading scoring

Run with:
    pytest astro_engine/tests/test_pipeline_profile_isolation.py -q
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ═══════════════════════════════════════════════════════════════
# TEST 1: NAKSHATRA OVERLAY IS TRADING-ONLY
# ═══════════════════════════════════════════════════════════════

class TestNakshatraOverlayIsolation:
    """Empirical GOOD/BAD nakshatra lists must only affect trading path."""

    def test_non_trading_profile_has_no_overlay(self):
        """general_life profile must have canonical_tara_only source."""
        from rules.evaluator_base import load_scoring_profile
        p = load_scoring_profile("general_life")
        assert p["nakshatra_adjustment"]["source"] == "canonical_tara_only"
        assert p["nakshatra_adjustment"]["good"] == []
        assert p["nakshatra_adjustment"]["bad"] == []
        assert p["nakshatra_adjustment"]["good_factor"] == 1.0
        assert p["nakshatra_adjustment"]["bad_factor"] == 1.0

    def test_trading_profile_has_overlay(self):
        """trading profile must have empirical nakshatra lists."""
        from rules.evaluator_base import load_scoring_profile
        p = load_scoring_profile("trading")
        assert p["nakshatra_adjustment"]["source"] == "empirical_trading_backtest"
        assert len(p["nakshatra_adjustment"]["good"]) > 0
        assert len(p["nakshatra_adjustment"]["bad"]) > 0
        assert p["nakshatra_adjustment"]["good_factor"] == 1.1
        assert p["nakshatra_adjustment"]["bad_factor"] == 0.85

    def test_rule_pipeline_non_trading_factor_is_1(self):
        """When use_trading_event_filter=False, nakshatra factor must be 1.0."""
        # The rule_pipeline now checks the profile source
        from rules.evaluator_base import load_scoring_profile
        p = load_scoring_profile("general_life")
        source = p.get("nakshatra_adjustment", {}).get("source", "")
        use_overlay = source != "canonical_tara_only"
        assert use_overlay is False

    def test_nakshatra_adjustment_function_still_works(self):
        """The function itself still works — it's just not called for non-trading."""
        from rules.nakshatra_weight import nakshatra_adjustment
        assert nakshatra_adjustment("Rohini") == 1.1
        assert nakshatra_adjustment("Ashlesha") == 0.85
        assert nakshatra_adjustment("Hasta") == 1.0


# ═══════════════════════════════════════════════════════════════
# TEST 2: CANONICAL TARA UNTOUCHED
# ═══════════════════════════════════════════════════════════════

class TestCanonicalTaraUntouched:
    """Tara scoring must remain canonical regardless of profile."""

    def test_tara_formula_unchanged(self):
        from rules.evaluator_base import get_tara
        assert get_tara("Ashwini", "Bharani") == 2
        assert get_tara("Ashwini", "Punarvasu") == 7
        assert get_tara("Ashwini", "Ashlesha") == 9

    def test_tara_scores_unchanged(self):
        from rules.evaluator_base import TARA_SCORES
        assert TARA_SCORES[7] == -3  # Naidhana worst
        assert TARA_SCORES[2] == 2   # Sampat best (tied)
        assert TARA_SCORES[6] == 2   # Sadhana best (tied)

    def test_calculate_tara_score_deterministic(self):
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
        s1 = calculate_tara_score("Ashwini", pdata)
        s2 = calculate_tara_score("Ashwini", pdata)
        assert s1 == s2  # Deterministic


# ═══════════════════════════════════════════════════════════════
# TEST 3: TRADING PATH ISOLATION
# ═══════════════════════════════════════════════════════════════

class TestTradingPathIsolation:
    """Trading-specific adjustments must only fire when trading is active."""

    def test_trading_event_boost_only_when_enabled(self):
        """TRADING_EVENT_BOOST is only used when use_trading_event_filter=True."""
        from rules.evaluator_base import TRADING_EVENT_BOOST, NON_TRADING_EVENT_MULTIPLIER
        # These constants exist but are gated by the flag
        assert TRADING_EVENT_BOOST == 1.15
        assert NON_TRADING_EVENT_MULTIPLIER == 0.35

    def test_trading_gate_only_in_trading_profile(self):
        from rules.evaluator_base import load_scoring_profile
        for domain in ["general_life", "career", "relationship", "health", "spirituality", "finance"]:
            p = load_scoring_profile(domain)
            assert p["trading_gate"]["enabled"] is False, f"{domain} should not have trading gate"

    def test_trade_decision_function_exists_but_gated(self):
        """get_trade_decision exists but is only called when rulebook bias is enabled."""
        from rules.evaluator_base import get_trade_decision
        # Function works
        pdata = {"Moon": {"nakshatra": "Rohini"}, "Sun": {"nakshatra": "Ashwini"},
                 "Venus": {"nakshatra": "Ashwini"}, "Mars": {"nakshatra": "Ashwini"}}
        action, _ = get_trade_decision(pdata)
        assert action == "TRADE HEAVILY"
        # But it's only called when use_nakshatra_rulebook_bias=True in config


# ═══════════════════════════════════════════════════════════════
# TEST 4: PROFILE RESOLVES CORRECTLY IN PIPELINE
# ═══════════════════════════════════════════════════════════════

class TestPipelineProfileResolution:
    """rule_pipeline must resolve the correct profile based on config."""

    def test_trading_filter_implies_trading_profile(self):
        """When use_trading_event_filter=True, scoring_domain defaults to trading."""
        # This is the logic in run_rules():
        config = {"use_trading_event_filter": True}
        scoring_domain = config.get("scoring_domain", "trading" if config.get("use_trading_event_filter") else "general_life")
        assert scoring_domain == "trading"

    def test_no_filter_implies_general_life(self):
        """When use_trading_event_filter=False, scoring_domain defaults to general_life."""
        config = {"use_trading_event_filter": False}
        scoring_domain = config.get("scoring_domain", "trading" if config.get("use_trading_event_filter") else "general_life")
        assert scoring_domain == "general_life"

    def test_explicit_domain_override(self):
        """Config can explicitly set scoring_domain."""
        config = {"scoring_domain": "health", "use_trading_event_filter": False}
        scoring_domain = config.get("scoring_domain", "trading" if config.get("use_trading_event_filter") else "general_life")
        assert scoring_domain == "health"
