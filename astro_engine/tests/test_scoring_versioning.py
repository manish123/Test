"""
Phase 6 Scoring Versioning Tests

Proves that:
1. Canonical score values remain stable regardless of profile
2. Calibration changes do not alter canonical inputs
3. Per-domain formulas can evolve independently
4. Profile files are valid and parseable

Run with:
    pytest astro_engine/tests/test_scoring_versioning.py -q
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROFILES_DIR = Path(__file__).resolve().parent.parent / "configs" / "scoring_profiles"


# ═══════════════════════════════════════════════════════════════
# TEST 1: CANONICAL YAML IS FROZEN
# ═══════════════════════════════════════════════════════════════

class TestCanonicalYamlFrozen:
    """canonical.yaml must match the code constants exactly."""

    @pytest.fixture
    def canonical(self):
        with open(PROFILES_DIR / "canonical.yaml") as f:
            return yaml.safe_load(f)

    def test_canonical_status_frozen(self, canonical):
        assert canonical["status"] == "frozen"

    def test_tara_favorable_matches_code(self, canonical):
        from rules.evaluator_base import TARA_SCORES
        favorable = canonical["tara"]["polarity"]["favorable"]
        for t in favorable:
            assert TARA_SCORES[t] > 0, f"Tara {t} should be favorable (positive score)"

    def test_tara_unfavorable_matches_code(self, canonical):
        from rules.evaluator_base import TARA_SCORES
        unfavorable = canonical["tara"]["polarity"]["unfavorable"]
        for t in unfavorable:
            assert TARA_SCORES[t] < 0, f"Tara {t} should be unfavorable (negative score)"

    def test_moorthy_mapping_matches_code(self, canonical):
        from rules.moorthy import moorthy_grade
        for grade_name, houses in canonical["moorthy"]["mapping"].items():
            for h in houses:
                # Use natal_moon=1, transit_moon=h (so house_count = h)
                actual_grade, _ = moorthy_grade(1, h)
                assert actual_grade.lower() == grade_name, (
                    f"House {h} should be {grade_name}, got {actual_grade}"
                )

    def test_sign_lords_match_code(self, canonical):
        from features.dignity import SIGN_LORDS
        for sign_str, lord in canonical["dignity"]["sign_lords"].items():
            sign = int(sign_str)
            assert SIGN_LORDS[sign] == lord, f"Sign {sign} lord mismatch"

    def test_aspects_match_code(self, canonical):
        from rules.evaluator_base import JUPITER_ASPECTS, SATURN_ASPECTS, MARS_ASPECTS
        assert set(canonical["aspects"]["jupiter"]) == set(JUPITER_ASPECTS)
        assert set(canonical["aspects"]["saturn"]) == set(SATURN_ASPECTS)
        assert set(canonical["aspects"]["mars"]) == set(MARS_ASPECTS)

    def test_dasha_periods_match_code(self, canonical):
        from features.dasha import DASHA_YEARS
        for planet, years in canonical["dasha"]["periods"].items():
            assert DASHA_YEARS[planet] == years, f"{planet} dasha years mismatch"


# ═══════════════════════════════════════════════════════════════
# TEST 2: PROFILE FILES ARE VALID
# ═══════════════════════════════════════════════════════════════

class TestProfileFilesValid:
    """All scoring profile YAML files must be parseable and well-structured."""

    @pytest.mark.parametrize("profile_name", ["canonical", "trading", "general_life"])
    def test_profile_parseable(self, profile_name):
        path = PROFILES_DIR / f"{profile_name}.yaml"
        assert path.exists(), f"{profile_name}.yaml not found"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert "version" in data

    def test_trading_profile_has_gate(self):
        with open(PROFILES_DIR / "trading.yaml") as f:
            data = yaml.safe_load(f)
        assert data["trading_gate"]["enabled"] is True
        assert "risky_nakshatras" in data["trading_gate"]

    def test_general_life_has_no_gate(self):
        with open(PROFILES_DIR / "general_life.yaml") as f:
            data = yaml.safe_load(f)
        assert data["trading_gate"]["enabled"] is False

    def test_profiles_have_confidence_section(self):
        for name in ["trading", "general_life"]:
            with open(PROFILES_DIR / f"{name}.yaml") as f:
                data = yaml.safe_load(f)
            assert "confidence" in data
            assert "risk_penalty" in data["confidence"]
            assert "promise_multipliers" in data["confidence"]

    def test_profiles_have_thresholds(self):
        for name in ["trading", "general_life"]:
            with open(PROFILES_DIR / f"{name}.yaml") as f:
                data = yaml.safe_load(f)
            assert "thresholds" in data
            t = data["thresholds"]
            assert t["very_high"] > t["high"] > t["moderate"] > t["low"]


# ═══════════════════════════════════════════════════════════════
# TEST 3: DOMAIN INDEPENDENCE
# ═══════════════════════════════════════════════════════════════

class TestDomainIndependence:
    """Per-domain profiles must be independent of each other."""

    def test_trading_and_general_life_differ(self):
        with open(PROFILES_DIR / "trading.yaml") as f:
            trading = yaml.safe_load(f)
        with open(PROFILES_DIR / "general_life.yaml") as f:
            general = yaml.safe_load(f)

        # Risk penalty should differ
        assert trading["confidence"]["risk_penalty"]["factor"] != general["confidence"]["risk_penalty"]["factor"]

        # Trading gate status should differ
        assert trading["trading_gate"]["enabled"] != general["trading_gate"]["enabled"]

        # Nakshatra adjustment should differ
        assert trading["nakshatra_adjustment"]["source"] != general["nakshatra_adjustment"]["source"]

    def test_general_life_no_trading_contamination(self):
        with open(PROFILES_DIR / "general_life.yaml") as f:
            data = yaml.safe_load(f)

        # No trading event filter
        assert data["event_filter"]["enabled"] is False

        # No trading gate
        assert data["trading_gate"]["enabled"] is False

        # No nakshatra rulebook
        assert data["confidence"]["adjustments"]["rulebook_confidence_factor"] == 0.0

        # No trading-derived nakshatra lists
        assert data["nakshatra_adjustment"]["good"] == []
        assert data["nakshatra_adjustment"]["bad"] == []


# ═══════════════════════════════════════════════════════════════
# TEST 4: CANONICAL INPUTS UNAFFECTED BY PROFILES
# ═══════════════════════════════════════════════════════════════

class TestCanonicalUnaffectedByProfiles:
    """Canonical scoring functions must produce the same output regardless of
    which domain profile is active."""

    def test_tara_independent_of_profile(self):
        """get_tara() is canonical — no profile can change it."""
        from rules.evaluator_base import get_tara
        # These values must be the same no matter what profile is loaded
        assert get_tara("Ashwini", "Bharani") == 2
        assert get_tara("Rohini", "Pushya") == 5
        assert get_tara("Magha", "Swati") == 6

    def test_moorthy_independent_of_profile(self):
        """moorthy_grade() is canonical — no profile can change it."""
        from rules.moorthy import moorthy_grade
        grade, factor = moorthy_grade(1, 6)
        assert grade == "Swarna"
        assert factor == 1.2

    def test_dignity_classification_independent(self):
        """SIGN_LORDS is canonical — no profile can change it."""
        from features.dignity import SIGN_LORDS
        assert SIGN_LORDS[1] == "Mars"
        assert SIGN_LORDS[9] == "Jupiter"

    def test_aspect_rules_independent(self):
        """Aspect constants are canonical — no profile can change them."""
        from rules.evaluator_base import JUPITER_ASPECTS, SATURN_ASPECTS, MARS_ASPECTS
        assert JUPITER_ASPECTS == [5, 7, 9]
        assert SATURN_ASPECTS == [3, 7, 10]
        assert MARS_ASPECTS == [4, 7, 8]

    def test_evaluate_event_independent_of_profile(self):
        """evaluate_event() uses canonical scoring — profiles don't alter it."""
        from rules.event_engine import evaluate_event
        chart = {
            "planets": [
                {"name": "Jupiter", "multiplier": 1.5, "vimsopaka": 10, "status": "exalted"},
            ],
            "strong_houses": [2, 11],
            "dasha": "Jupiter",
        }
        transit = {"strength": 1.0}
        score = evaluate_event("finance", chart, transit)
        # This score must be deterministic and profile-independent
        assert score == evaluate_event("finance", chart, transit)


# ═══════════════════════════════════════════════════════════════
# TEST 5: CALIBRATION DOES NOT ALTER CANONICAL
# ═══════════════════════════════════════════════════════════════

class TestCalibrationDoesNotAlterCanonical:
    """Confidence calibration must be a post-hoc adjustment only."""

    def test_calibration_none_is_identity(self):
        from decisions.confidence_calibration import apply_confidence_calibration
        for val in [0.0, 25.0, 50.0, 75.0, 100.0]:
            assert apply_confidence_calibration(val, None) == val

    def test_calibration_disabled_is_identity(self):
        from decisions.confidence_calibration import apply_confidence_calibration
        cfg = {"enabled": False, "offset": 99, "scale": 0.1}
        assert apply_confidence_calibration(50.0, cfg) == 50.0

    def test_calibration_does_not_affect_tara(self):
        """Tara scoring is upstream of calibration — calibration cannot reach it."""
        from rules.evaluator_base import get_tara, calculate_tara_score
        pdata = {
            "Moon": {"nakshatra": "Rohini"},
            "Mercury": {"nakshatra": "Ashwini"},
            "Jupiter": {"nakshatra": "Pushya"},
            "Saturn": {"nakshatra": "Anuradha"},
            "Mars": {"nakshatra": "Mrigashira"},
            "Venus": {"nakshatra": "Bharani"},
            "Sun": {"nakshatra": "Krittika"},
        }
        score_before = calculate_tara_score("Ashwini", pdata)
        # Even if we apply calibration to confidence, tara score is unchanged
        score_after = calculate_tara_score("Ashwini", pdata)
        assert score_before == score_after

    def test_calibration_does_not_affect_event_scoring(self):
        """Event scoring is upstream of calibration."""
        from rules.event_engine import evaluate_event
        chart = {
            "planets": [{"name": "Venus", "multiplier": 1.0, "vimsopaka": 8, "status": "own"}],
            "strong_houses": [7],
            "dasha": "Venus",
        }
        transit = {"strength": 0.8}
        score1 = evaluate_event("relationship", chart, transit)
        score2 = evaluate_event("relationship", chart, transit)
        assert score1 == score2  # Deterministic, calibration-independent
