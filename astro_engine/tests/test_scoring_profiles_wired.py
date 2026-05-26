"""
Phase 7 Scoring Profiles Wired Tests

Proves that:
1. load_scoring_profile() resolves each domain correctly
2. Fallback mode (no profile) produces identical outputs to current behavior
3. Profile-parameterized confidence_score() matches hardcoded when defaults used
4. Each domain resolves to its own profile
5. Canonical values remain unchanged with profiles active

Run with:
    pytest astro_engine/tests/test_scoring_profiles_wired.py -q
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ═══════════════════════════════════════════════════════════════
# TEST 1: PROFILE LOADING
# ═══════════════════════════════════════════════════════════════

class TestProfileLoading:
    """load_scoring_profile() must resolve each domain correctly."""

    @pytest.mark.parametrize("domain", [
        "trading", "general_life", "career", "relationship",
        "health", "spirituality", "finance",
    ])
    def test_profile_loads_for_domain(self, domain):
        from rules.evaluator_base import load_scoring_profile
        profile = load_scoring_profile(domain)
        assert profile is not None, f"Profile for '{domain}' should load"
        assert profile["domain"] == domain
        assert profile["version"] == "3.0.0"

    def test_unknown_domain_falls_back_to_general_life(self):
        from rules.evaluator_base import load_scoring_profile
        profile = load_scoring_profile("unknown_domain_xyz")
        # Should fall back to general_life
        assert profile is not None
        assert profile["domain"] == "general_life"

    def test_profile_has_required_sections(self):
        from rules.evaluator_base import load_scoring_profile
        profile = load_scoring_profile("trading")
        assert "confidence" in profile
        assert "thresholds" in profile
        assert "layer_weights" in profile
        assert "trading_gate" in profile
        assert "nakshatra_adjustment" in profile


# ═══════════════════════════════════════════════════════════════
# TEST 2: CONFIDENCE BACKWARD COMPATIBILITY
# ═══════════════════════════════════════════════════════════════

class TestConfidenceBackwardCompat:
    """confidence_score() with no profile must produce identical results."""

    def test_no_profile_same_as_before(self):
        from decisions.confidence import confidence_score
        data = {"event_strength": 50, "yoga": 10, "dasha": 20, "promise": "moderate", "kakshya_active": True}
        penalties = {"risk": 60}
        # Without profile_params (None) = hardcoded defaults
        score_no_profile = confidence_score(data, penalties, profile_params=None)
        # With explicit hardcoded values
        score_explicit = confidence_score(data, penalties, profile_params={
            "risk_penalty_factor": 0.15,
            "risk_penalty_cap": 40,
            "high_risk_threshold": 120,
            "high_risk_extra": 10,
            "weak_promise_multiplier": 0.6,
            "kakshya_inactive_multiplier": 0.7,
        })
        assert score_no_profile == score_explicit

    def test_weak_promise_penalty(self):
        from decisions.confidence import confidence_score
        data = {"event_strength": 50, "yoga": 10, "dasha": 20, "promise": "weak", "kakshya_active": True}
        score = confidence_score(data, {"risk": 30})
        # With weak promise, score should be reduced
        data_normal = dict(data, promise="moderate")
        score_normal = confidence_score(data_normal, {"risk": 30})
        assert score < score_normal

    def test_kakshya_inactive_penalty(self):
        from decisions.confidence import confidence_score
        data = {"event_strength": 50, "yoga": 10, "dasha": 20, "promise": "moderate", "kakshya_active": False}
        score_inactive = confidence_score(data, {"risk": 30})
        data_active = dict(data, kakshya_active=True)
        score_active = confidence_score(data_active, {"risk": 30})
        assert score_inactive < score_active


# ═══════════════════════════════════════════════════════════════
# TEST 3: PROFILE PARAMS CHANGE BEHAVIOR
# ═══════════════════════════════════════════════════════════════

class TestProfileParamsEffect:
    """Profile params must actually change confidence when different from defaults."""

    def test_lower_risk_factor_gives_higher_confidence(self):
        from decisions.confidence import confidence_score
        data = {"event_strength": 50, "yoga": 10, "dasha": 20, "promise": "moderate", "kakshya_active": True}
        penalties = {"risk": 80}

        # Trading profile: factor=0.15
        score_trading = confidence_score(data, penalties, profile_params={
            "risk_penalty_factor": 0.15, "risk_penalty_cap": 40,
            "high_risk_threshold": 120, "high_risk_extra": 10,
            "weak_promise_multiplier": 0.6, "kakshya_inactive_multiplier": 0.7,
        })
        # Spirituality profile: factor=0.08 (less punitive)
        score_spiritual = confidence_score(data, penalties, profile_params={
            "risk_penalty_factor": 0.08, "risk_penalty_cap": 25,
            "high_risk_threshold": 150, "high_risk_extra": 0,
            "weak_promise_multiplier": 0.8, "kakshya_inactive_multiplier": 0.9,
        })
        assert score_spiritual > score_trading

    def test_get_profile_confidence_params(self):
        from rules.evaluator_base import load_scoring_profile, get_profile_confidence_params
        profile = load_scoring_profile("trading")
        params = get_profile_confidence_params(profile)
        assert params is not None
        assert params["risk_penalty_factor"] == 0.15
        assert params["risk_penalty_cap"] == 40

    def test_none_profile_gives_none_params(self):
        from rules.evaluator_base import get_profile_confidence_params
        params = get_profile_confidence_params(None)
        assert params is None


# ═══════════════════════════════════════════════════════════════
# TEST 4: DOMAIN ISOLATION
# ═══════════════════════════════════════════════════════════════

class TestDomainIsolation:
    """Each domain must resolve to its own distinct profile."""

    def test_trading_has_gate_enabled(self):
        from rules.evaluator_base import load_scoring_profile
        p = load_scoring_profile("trading")
        assert p["trading_gate"]["enabled"] is True

    def test_non_trading_domains_have_gate_disabled(self):
        from rules.evaluator_base import load_scoring_profile
        for domain in ["general_life", "career", "relationship", "health", "spirituality", "finance"]:
            p = load_scoring_profile(domain)
            assert p["trading_gate"]["enabled"] is False, f"{domain} should have gate disabled"

    def test_trading_has_nakshatra_lists(self):
        from rules.evaluator_base import load_scoring_profile
        p = load_scoring_profile("trading")
        assert len(p["nakshatra_adjustment"]["good"]) > 0
        assert len(p["nakshatra_adjustment"]["bad"]) > 0

    def test_non_trading_has_empty_nakshatra_lists(self):
        from rules.evaluator_base import load_scoring_profile
        for domain in ["general_life", "career", "relationship", "health", "spirituality", "finance"]:
            p = load_scoring_profile(domain)
            assert p["nakshatra_adjustment"]["good"] == [], f"{domain} should have empty good list"
            assert p["nakshatra_adjustment"]["bad"] == [], f"{domain} should have empty bad list"

    def test_each_domain_has_unique_risk_factor(self):
        from rules.evaluator_base import load_scoring_profile
        factors = {}
        for domain in ["trading", "general_life", "relationship", "spirituality", "health"]:
            p = load_scoring_profile(domain)
            factors[domain] = p["confidence"]["risk_penalty"]["factor"]
        # At least some should differ
        unique_values = set(factors.values())
        assert len(unique_values) >= 3, f"Expected diverse risk factors, got {factors}"


# ═══════════════════════════════════════════════════════════════
# TEST 5: CANONICAL UNCHANGED WITH PROFILES
# ═══════════════════════════════════════════════════════════════

class TestCanonicalUnchangedWithProfiles:
    """Loading profiles must not alter canonical scoring functions."""

    def test_tara_unchanged_after_profile_load(self):
        from rules.evaluator_base import load_scoring_profile, get_tara
        # Load a profile (triggers import of yaml, caching, etc.)
        load_scoring_profile("trading")
        load_scoring_profile("spirituality")
        # Canonical tara must still work identically
        assert get_tara("Ashwini", "Bharani") == 2
        assert get_tara("Ashwini", "Ashlesha") == 9

    def test_moorthy_unchanged_after_profile_load(self):
        from rules.evaluator_base import load_scoring_profile
        from rules.moorthy import moorthy_grade
        load_scoring_profile("health")
        grade, factor = moorthy_grade(1, 6)
        assert grade == "Swarna"
        assert factor == 1.2

    def test_evaluate_event_unchanged_after_profile_load(self):
        from rules.evaluator_base import load_scoring_profile
        from rules.event_engine import evaluate_event
        load_scoring_profile("finance")
        chart = {
            "planets": [{"name": "Jupiter", "multiplier": 1.5, "vimsopaka": 10, "status": "exalted"}],
            "strong_houses": [2, 11],
            "dasha": "Jupiter",
        }
        transit = {"strength": 1.0}
        score = evaluate_event("finance", chart, transit)
        assert score > 0
        # Run again to prove determinism
        assert evaluate_event("finance", chart, transit) == score
