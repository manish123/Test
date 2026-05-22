#!/usr/bin/env python3
"""
Astro Engine — Isolation Test

Verifies that the 4-layer architecture runs correctly in isolation.
Run from this directory: python3 run_test.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime


def test_layer_a():
    """Layer A — Astronomy: raw ephemeris positions."""
    from astronomy.engine_base import get_planet_positions, get_retrograde_flags, get_house_cusps
    import swisseph as swe

    jd = swe.julday(2026, 5, 22, 3.75)  # 9:15 IST = 3:45 UTC
    positions = get_planet_positions(jd)
    retro = get_retrograde_flags(jd)
    cusps = get_house_cusps(jd, 21.19, 81.38)

    assert "Moon" in positions, "Moon position missing"
    assert "Sun" in positions, "Sun position missing"
    assert 0 <= positions["Moon"] < 360, f"Moon longitude out of range: {positions['Moon']}"
    assert "ascendant" in cusps, "Ascendant missing from cusps"
    assert len(cusps["houses"]) == 12, f"Expected 12 houses, got {len(cusps['houses'])}"

    print(f"  Moon: {positions['Moon']:.4f}°  Sun: {positions['Sun']:.4f}°")
    print(f"  Ascendant: {cusps['ascendant']:.4f}°")
    print(f"  Retrogrades: {[k for k, v in retro.items() if v]}")
    return True


def test_layer_b():
    """Layer B — Features: derived astrology facts."""
    from features.dignity import get_planet_status, get_sign, SIGN_LORDS
    from features.nakshatra import get_nakshatra
    from features.dasha import get_current_vimshottari
    from features.ashtakavarga import compute_ashtakavarga

    # Mars in Capricorn (sign 10) should be exalted
    assert get_planet_status("Mars", 275.0) == "exalted", "Mars at 275° should be exalted (Capricorn)"

    # Moon at 45° → sign 2 (Taurus) → exalted
    assert get_planet_status("Moon", 45.0) == "exalted", "Moon at 45° should be exalted (Taurus)"

    # Nakshatra test
    nak = get_nakshatra(110.0)
    assert nak is not None, "Nakshatra should not be None"

    # Dasha test
    birth_dt = datetime(1975, 7, 22, 18, 15)
    current_dt = datetime(2026, 5, 22, 9, 15)
    moon_lon = 110.0
    vim = get_current_vimshottari(birth_dt, current_dt, moon_lon)
    assert "md" in vim and "ad" in vim, "Dasha should have md and ad"

    # Ashtakavarga test
    planet_signs = {"Sun": 2, "Moon": 4, "Mars": 10, "Mercury": 3, "Jupiter": 3, "Venus": 1, "Saturn": 11}
    av = compute_ashtakavarga(planet_signs, asc_sign=3)
    assert "bav" in av and "sav_sodhya" in av, "Ashtakavarga missing expected keys"

    print(f"  Mars@275° = {get_planet_status('Mars', 275.0)}")
    print(f"  Nakshatra@110° = {nak}")
    print(f"  Dasha: {vim['md']}/{vim['ad']}")
    return True


def test_layer_c():
    """Layer C — Rules: interpretive logic."""
    from rules.event_engine import evaluate_event, EVENT_MAP
    from rules.yoga_engine import evaluate_yogas
    from rules.moorthy import moorthy_grade
    from rules.nakshatra_weight import nakshatra_adjustment

    # Moorthy grade test
    grade, factor = moorthy_grade(4, 4)  # same sign = Swarna
    assert grade == "Swarna", f"Expected Swarna, got {grade}"
    assert factor == 1.2, f"Expected 1.2, got {factor}"

    # Nakshatra weight test
    assert nakshatra_adjustment("Rohini") == 1.1, "Rohini should be good nakshatra (1.1)"
    assert nakshatra_adjustment("Ardra") == 0.85, "Ardra should be bad nakshatra (0.85)"

    # Event evaluation test
    test_planets = [
        {"name": "Jupiter", "sign": 3, "house": 11, "multiplier": 1.5, "vimsopaka": 14, "status": "own", "is_kendra": False},
        {"name": "Mercury", "sign": 2, "house": 2, "multiplier": 1.2, "vimsopaka": 12, "status": "friend", "is_kendra": False},
        {"name": "Venus", "sign": 1, "house": 11, "multiplier": 1.0, "vimsopaka": 10, "status": "neutral", "is_kendra": False},
    ]
    chart = {"planets": test_planets, "strong_houses": [11, 2], "dasha": "Jupiter"}
    transit = {"strength": 0.8}
    score = evaluate_event("finance", chart, transit)
    assert score > 0, f"Finance event score should be positive, got {score}"

    print(f"  Moorthy(4,4) = {grade} ({factor})")
    print(f"  Finance event score = {score}")
    return True


def test_layer_d():
    """Layer D — Decisions: scoring and action."""
    from decisions.decision_engine import generate_decision
    from decisions.confidence import confidence_score
    from decisions.confidence_calibration import apply_confidence_calibration

    # Confidence test
    conf = confidence_score(
        {"event_strength": 60, "yoga": 20, "dasha": 25, "promise": "strong", "kakshya_active": True},
        penalties={"risk": 30},
    )
    assert 0 <= conf <= 100, f"Confidence out of range: {conf}"

    # Calibration passthrough
    assert apply_confidence_calibration(75.0) == 75.0, "Passthrough should return same value"

    # Calibration with config
    cal = apply_confidence_calibration(75.0, {"enabled": True, "scale": 0.9, "offset": -5})
    assert cal == 62.5, f"Expected 62.5, got {cal}"

    # Decision test
    top_events = [("business", 150.0), ("finance", 120.0)]
    decision = generate_decision(top_events, risk=30.0, confidence=75.0)
    assert "action" in decision, "Decision should have action"
    assert decision["action"] in {"GO FULL", "CONTROLLED AGGRESSION", "MODERATE", "LOW SIZE / WAIT", "AVOID", "SURVIVE"}

    print(f"  Confidence = {conf}")
    print(f"  Calibration(75, scale=0.9, offset=-5) = {cal}")
    print(f"  Decision: {decision['action']} (conf={decision['confidence']}, risk={decision['risk']})")
    return True


def test_contracts():
    """Contracts — immutable typed boundaries."""
    from contracts import AstronomyResult, FeatureResult, RuleResult, DecisionResult
    from contracts.engine_snapshot import create_snapshot

    # Immutability
    ar = AstronomyResult(jd=2461182.66, ayanamsa="FAGAN_BRADLEY", lat=21.19, lon=81.38)
    try:
        ar.jd = 999
        assert False, "Should not allow mutation"
    except Exception:
        pass  # FrozenInstanceError — correct

    # Snapshot
    birth = {"date": datetime(1975, 7, 22, 18, 15), "lat": 21.19, "lon": 81.38}
    snap = create_snapshot(eval_date=datetime(2026, 5, 22, 9, 15), birth_data=birth, mode="C", stages_completed=4)
    assert snap.engine_version == "2.0.0", f"Expected 2.0.0, got {snap.engine_version}"
    assert snap.pipeline_stages_completed == 4

    print(f"  AstronomyResult: frozen ✓")
    print(f"  EngineSnapshot: v{snap.engine_version}, stages={snap.pipeline_stages_completed}")
    return True


def test_pipeline():
    """Pipeline — full A→B→C→D execution."""
    from pipeline import run_astronomy, run_features, run_rules, run_decisions

    birth = {"date": datetime(1975, 7, 22, 18, 15), "lat": 21.19, "lon": 81.38}
    date = datetime(2026, 5, 22, 9, 15)

    astro = run_astronomy(date, birth)
    assert astro.jd > 0, "JD should be positive"

    features = run_features(astro, birth, date)
    assert features.asc_sign >= 1 and features.asc_sign <= 12

    rules = run_rules(features, birth, date)
    assert len(rules.top_events) > 0, "Should have at least one top event"

    decision = run_decisions(rules)
    assert decision.action in {"GO FULL", "CONTROLLED AGGRESSION", "MODERATE", "LOW SIZE / WAIT", "AVOID", "SURVIVE"}

    print(f"  [A] Moon={astro.positions['Moon']:.2f}°")
    print(f"  [B] Asc={features.asc_sign}, Dasha={features.dasha.md}/{features.dasha.ad}")
    print(f"  [C] Top={rules.top_events[0][0]}, Risk={rules.risk_score:.1f}")
    print(f"  [D] Action={decision.action}, Conf={decision.confidence}, Risk={decision.risk}")
    return True


def test_legacy_api():
    """Legacy API — _run_single still works."""
    from main import _run_single

    birth = {"date": datetime(1975, 7, 22, 18, 15), "lat": 21.19, "lon": 81.38}
    date = datetime(2026, 5, 22, 9, 15)

    result = _run_single(date=date, birth_data=birth, use_trading_gate=True)
    assert "decision" in result, "Legacy result should have 'decision' key"
    assert "top_events" in result, "Legacy result should have 'top_events' key"
    assert result["decision"]["action"] is not None

    print(f"  Action: {result['decision']['action']}")
    print(f"  Confidence: {result['decision']['confidence']}")
    print(f"  Top event: {result['top_events'][0][0]}")
    return True


if __name__ == "__main__":
    tests = [
        ("Layer A — Astronomy", test_layer_a),
        ("Layer B — Features", test_layer_b),
        ("Layer C — Rules", test_layer_c),
        ("Layer D — Decisions", test_layer_d),
        ("Contracts", test_contracts),
        ("Pipeline (A→B→C→D)", test_pipeline),
        ("Legacy API", test_legacy_api),
    ]

    print("=" * 60)
    print("ASTRO ENGINE — 4-LAYER ARCHITECTURE ISOLATION TEST")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"[TEST] {name}")
        try:
            result = test_fn()
            if result:
                print(f"  ✓ PASSED\n")
                passed += 1
            else:
                print(f"  ✗ FAILED\n")
                failed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
