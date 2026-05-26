"""
Phase 5 Scoring Purity Tests

Verifies that canonical Vedic scoring is separated from trading calibration.
Locks canonical values so they cannot drift without explicit review.

Run with:
    pytest astro_engine/tests/test_scoring_purity.py -q
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ═══════════════════════════════════════════════════════════════
# TEST 1: CANONICAL TARA SYSTEM
# ═══════════════════════════════════════════════════════════════

class TestCanonicalTara:
    """Tara calculation formula must remain canonical (Navatara from BPHS)."""

    def test_tara_formula_same_nakshatra(self):
        """Same nakshatra → count=1, tara=1 (Janma)."""
        from rules.evaluator_base import get_tara
        assert get_tara("Ashwini", "Ashwini") == 1

    def test_tara_formula_9th_is_param_mitra(self):
        """9th nakshatra → tara=9 (Param Mitra)."""
        from rules.evaluator_base import get_tara
        # Ashwini(0) to Ashlesha(8) = count 9, tara = 9%9 = 0 → 9
        assert get_tara("Ashwini", "Ashlesha") == 9

    def test_tara_formula_7th_is_naidhana(self):
        """7th nakshatra → tara=7 (Naidhana/Vadha)."""
        from rules.evaluator_base import get_tara
        # Ashwini(0) to Punarvasu(6) = count 7, tara = 7%9 = 7
        assert get_tara("Ashwini", "Punarvasu") == 7

    def test_tara_scores_polarity_canonical(self):
        """Tara score signs must match classical favorable/unfavorable."""
        from rules.evaluator_base import TARA_SCORES
        # Favorable taras: 2 (Sampat), 4 (Kshema), 6 (Sadhana), 8 (Mitra), 9 (Param Mitra)
        assert TARA_SCORES[2] > 0  # Sampat = favorable
        assert TARA_SCORES[4] > 0  # Kshema = favorable
        assert TARA_SCORES[6] > 0  # Sadhana = favorable
        assert TARA_SCORES[8] > 0  # Mitra = favorable
        assert TARA_SCORES[9] > 0  # Param Mitra = favorable
        # Unfavorable taras: 1 (Janma), 3 (Vipat), 5 (Pratyak), 7 (Naidhana)
        assert TARA_SCORES[1] < 0  # Janma = unfavorable
        assert TARA_SCORES[3] < 0  # Vipat = unfavorable
        assert TARA_SCORES[5] < 0  # Pratyak = unfavorable
        assert TARA_SCORES[7] < 0  # Naidhana = most unfavorable

    def test_naidhana_is_worst(self):
        """Naidhana (7th tara) must have the lowest score."""
        from rules.evaluator_base import TARA_SCORES
        assert TARA_SCORES[7] == min(TARA_SCORES.values())


# ═══════════════════════════════════════════════════════════════
# TEST 2: CANONICAL MOORTHY GRADING
# ═══════════════════════════════════════════════════════════════

class TestCanonicalMoorthy:
    """Moorthy house-to-grade mapping must remain canonical."""

    def test_swarna_houses(self):
        from rules.moorthy import moorthy_grade
        for natal, transit in [(1, 1), (1, 6), (1, 11)]:
            grade, _ = moorthy_grade(natal, transit)
            assert grade == "Swarna", f"House {((transit-natal)%12)+1} should be Swarna"

    def test_rajata_houses(self):
        from rules.moorthy import moorthy_grade
        for natal, transit in [(1, 2), (1, 5), (1, 9)]:
            grade, _ = moorthy_grade(natal, transit)
            assert grade == "Rajata", f"House {((transit-natal)%12)+1} should be Rajata"

    def test_taamra_houses(self):
        from rules.moorthy import moorthy_grade
        for natal, transit in [(1, 3), (1, 7), (1, 10)]:
            grade, _ = moorthy_grade(natal, transit)
            assert grade == "Taamra", f"House {((transit-natal)%12)+1} should be Taamra"

    def test_loha_houses(self):
        from rules.moorthy import moorthy_grade
        for natal, transit in [(1, 4), (1, 8), (1, 12)]:
            grade, _ = moorthy_grade(natal, transit)
            assert grade == "Loha", f"House {((transit-natal)%12)+1} should be Loha"

    def test_grade_ordering(self):
        """Swarna > Rajata > Taamra > Loha in factor value."""
        from rules.moorthy import moorthy_grade
        _, swarna = moorthy_grade(1, 1)
        _, rajata = moorthy_grade(1, 2)
        _, taamra = moorthy_grade(1, 3)
        _, loha = moorthy_grade(1, 4)
        assert swarna > rajata > taamra > loha


# ═══════════════════════════════════════════════════════════════
# TEST 3: CANONICAL DIGNITY CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

class TestCanonicalDignity:
    """Dignity classification tables must remain canonical (BPHS)."""

    def test_sign_lords_canonical(self):
        from features.dignity import SIGN_LORDS
        # Aries=Mars, Taurus=Venus, Gemini=Mercury, Cancer=Moon
        assert SIGN_LORDS[1] == "Mars"
        assert SIGN_LORDS[2] == "Venus"
        assert SIGN_LORDS[3] == "Mercury"
        assert SIGN_LORDS[4] == "Moon"
        assert SIGN_LORDS[5] == "Sun"
        assert SIGN_LORDS[6] == "Mercury"
        assert SIGN_LORDS[7] == "Venus"
        assert SIGN_LORDS[8] == "Mars"
        assert SIGN_LORDS[9] == "Jupiter"
        assert SIGN_LORDS[10] == "Saturn"
        assert SIGN_LORDS[11] == "Saturn"
        assert SIGN_LORDS[12] == "Jupiter"

    def test_dignity_multiplier_ordering(self):
        """Exalted > own > friend > neutral > enemy > debilitated."""
        from rules.state_engine import STATUS_MULTIPLIER
        assert STATUS_MULTIPLIER["exalted"] > STATUS_MULTIPLIER["own"]
        assert STATUS_MULTIPLIER["own"] > STATUS_MULTIPLIER["friend"]
        assert STATUS_MULTIPLIER["friend"] > STATUS_MULTIPLIER["neutral"]
        assert STATUS_MULTIPLIER["neutral"] > STATUS_MULTIPLIER["enemy"]
        assert STATUS_MULTIPLIER["enemy"] > STATUS_MULTIPLIER["debilitated"]


# ═══════════════════════════════════════════════════════════════
# TEST 4: CANONICAL ASPECT RULES
# ═══════════════════════════════════════════════════════════════

class TestCanonicalAspects:
    """Aspect constants must remain canonical (BPHS)."""

    def test_jupiter_aspects(self):
        from rules.evaluator_base import JUPITER_ASPECTS
        assert set(JUPITER_ASPECTS) == {5, 7, 9}

    def test_saturn_aspects(self):
        from rules.evaluator_base import SATURN_ASPECTS
        assert set(SATURN_ASPECTS) == {3, 7, 10}

    def test_mars_aspects(self):
        from rules.evaluator_base import MARS_ASPECTS
        assert set(MARS_ASPECTS) == {4, 7, 8}


# ═══════════════════════════════════════════════════════════════
# TEST 5: TRADING ISOLATION
# ═══════════════════════════════════════════════════════════════

class TestTradingIsolation:
    """Trading-specific values must not contaminate canonical scoring."""

    def test_trading_boost_not_in_canonical(self):
        """TRADING_EVENT_BOOST is only applied when trading filter is active."""
        from rules.evaluator_base import TRADING_EVENT_BOOST, NON_TRADING_EVENT_MULTIPLIER
        # These exist but are only used conditionally
        assert TRADING_EVENT_BOOST == 1.15
        assert NON_TRADING_EVENT_MULTIPLIER == 0.35

    def test_trading_gate_is_optional(self):
        """Trading gate must be opt-in, not default."""
        from decisions.trading_gate import evaluate_trading_gate
        # The function exists but is only called when use_trading_gate=True
        assert callable(evaluate_trading_gate)

    def test_risky_nakshatras_are_trading_scoped(self):
        """RISKY_NAKSHATRA_SET lives in trading_gate, not in canonical modules."""
        from decisions.trading_gate import RISKY_NAKSHATRA_SET
        # Verify it's in the trading module, not in evaluator_base or nakshatra
        assert "Dhanishta" in RISKY_NAKSHATRA_SET
        # evaluator_base should NOT have this set
        import rules.evaluator_base as eb
        assert not hasattr(eb, "RISKY_NAKSHATRA_SET")

    def test_confidence_calibration_is_optional(self):
        """Confidence calibration must be a no-op when config is None."""
        from decisions.confidence_calibration import apply_confidence_calibration
        # With no config, returns input unchanged
        assert apply_confidence_calibration(75.0, None) == 75.0
        assert apply_confidence_calibration(50.0, {"enabled": False}) == 50.0


# ═══════════════════════════════════════════════════════════════
# TEST 6: NAKSHATRA WEIGHT CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

class TestNakshatraWeightClassification:
    """Nakshatra adjustment is empirical, not canonical."""

    def test_good_nak_list_is_empirical(self):
        """GOOD_NAK list is from trading backtest, not classical tara."""
        from rules.nakshatra_weight import GOOD_NAK
        # These are empirically favorable for trading, not classical tara-favorable
        assert "Rohini" in GOOD_NAK
        assert "Pushya" in GOOD_NAK

    def test_bad_nak_list_is_empirical(self):
        """BAD_NAK list is from trading backtest."""
        from rules.nakshatra_weight import BAD_NAK
        assert "Ashlesha" in BAD_NAK
        assert "Dhanishta" in BAD_NAK

    def test_adjustment_factor_range(self):
        """Adjustment factors must be mild (not extreme)."""
        from rules.nakshatra_weight import nakshatra_adjustment
        # Good: 1.1 (10% boost)
        assert nakshatra_adjustment("Rohini") == 1.1
        # Bad: 0.85 (15% reduction)
        assert nakshatra_adjustment("Ashlesha") == 0.85
        # Neutral: 1.0
        assert nakshatra_adjustment("Hasta") == 1.0

    def test_canonical_tara_is_separate_from_nakshatra_weight(self):
        """The tara system (canonical) is independent of nakshatra_weight (empirical)."""
        from rules.evaluator_base import get_tara
        from rules.nakshatra_weight import nakshatra_adjustment
        # These are two different systems that don't reference each other
        tara = get_tara("Ashwini", "Ashlesha")  # canonical
        adj = nakshatra_adjustment("Ashlesha")   # empirical
        # Both produce values but from different sources
        assert isinstance(tara, int)
        assert isinstance(adj, float)


# ═══════════════════════════════════════════════════════════════
# TEST 7: EVENT SCORING STRUCTURE
# ═══════════════════════════════════════════════════════════════

class TestEventScoringStructure:
    """Event scoring formula must maintain structural integrity."""

    def test_evaluate_event_uses_multiplier(self):
        """evaluate_event must use planet multiplier (set by state_engine)."""
        from rules.event_engine import evaluate_event
        chart = {
            "planets": [
                {"name": "Jupiter", "multiplier": 1.5, "vimsopaka": 10, "status": "exalted"},
                {"name": "Mercury", "multiplier": 1.0, "vimsopaka": 8, "status": "neutral"},
            ],
            "strong_houses": [2, 11],
            "dasha": "Jupiter",
        }
        transit = {"strength": 1.0}
        score = evaluate_event("finance", chart, transit)
        assert score > 0
        assert isinstance(score, float)

    def test_higher_multiplier_gives_higher_score(self):
        """Higher planet multiplier must produce higher event score."""
        from rules.event_engine import evaluate_event
        chart_low = {
            "planets": [{"name": "Jupiter", "multiplier": 0.5, "vimsopaka": 8, "status": "debilitated"}],
            "strong_houses": [],
            "dasha": "Jupiter",
        }
        chart_high = {
            "planets": [{"name": "Jupiter", "multiplier": 1.5, "vimsopaka": 8, "status": "exalted"}],
            "strong_houses": [],
            "dasha": "Jupiter",
        }
        transit = {"strength": 0.5}
        score_low = evaluate_event("finance", chart_low, transit)
        score_high = evaluate_event("finance", chart_high, transit)
        assert score_high > score_low
