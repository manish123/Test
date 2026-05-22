"""
Decision Pipeline Stage (Layer D orchestration) — FULL PARITY VERSION

Consumes rule_pipeline output dict, produces decision dict identical to _run_single().
Replicates ALL logic from _run_single() lines 580-720:
- Full confidence formula with all 7 adjustments
- Yogini factor × sandhi multiplier
- Chara sandhi × 0.9
- Tara confidence boost (score * 3)
- Rulebook confidence adjustment (delta * 0.6)
- Kakshya +10 bonus
- Final yogini factor application
- Confidence calibration
- Decision generation with override rules
- Trading gate integration (optional)
"""

import math

from decisions.confidence import confidence_score
from decisions.confidence_calibration import apply_confidence_calibration
from decisions.decision_engine import generate_decision
from decisions.normalization import normalize_event_scores, normalize_top_events
from decisions.priority import rank_events
from decisions.trading_gate import evaluate_trading_gate, evaluate_asset_timeline_events, TRADING_FOCUSED_EVENTS

from features.transit import check_event_transit
from features.ashtakavarga import focal_sign_strength
from features.dignity import SIGN_LORDS
from features.chara_dasha import get_chara_dasha_sequence
from features.yogini import yogini_cross_validation

from rules.event_engine import EVENT_MAP
from rules.kakshya import kakshya_trigger


def run_decisions(rule_output: dict, config: dict = None) -> dict:
    """
    Execute Layer D: produce final trading decision from rule interpretations.
    FULL PARITY with _run_single().

    Args:
        rule_output: dict from run_rules() (full parity version)
        config: optional dict with trading_gate settings, calibration, etc.

    Returns:
        dict matching _run_single()["decision"] structure exactly
    """
    config = config or {}
    use_trading_gate = config.get("use_trading_gate", False)
    trading_gate_profile = config.get("trading_gate_profile", "strict")
    confidence_calibration_config = config.get("confidence_calibration", None)
    use_asset_timeline_events = config.get("use_asset_timeline_events", False)

    # Extract from rule output
    planets = rule_output["planets"]
    event_scores = rule_output["event_scores"]
    top_events = rule_output["top_events"]
    yoga_info = rule_output["yoga"]
    risk = rule_output["risk_final"]
    tara_score = rule_output["tara_score"]
    rulebook_action = rule_output["rulebook_action"]
    rulebook_confidence_delta = rule_output["rulebook_confidence_delta"]
    kakshya = rule_output["kakshya"]
    yogini = rule_output["yogini"]
    yogini_factor = rule_output["yogini_factor"]
    chara_current = rule_output["chara_current"]
    promise_label = rule_output["promise_label"]
    focal_11 = rule_output["focal_11"]
    transit_strength = rule_output["transit_strength"]
    ashtakavarga = rule_output["ashtakavarga"]
    av_risk = rule_output["av_risk"]
    asc_sign = rule_output["asc_sign"]
    dasha = rule_output["dasha"]
    antardasha = rule_output["antardasha"]
    vedha_blocked = rule_output["vedha_blocked"]
    chandrabala_count = rule_output["chandrabala_count"]
    chandrabala_eighth = rule_output["chandrabala_eighth"]
    kakshya_cluster = rule_output["kakshya_cluster"]
    sbc_analysis = rule_output["sbc_analysis"]
    sbc_malefic_karma_vedha = rule_output["sbc_malefic_karma_vedha"]
    sbc_malefic_janma_vedha = rule_output["sbc_malefic_janma_vedha"]
    sbc_malefic_vedha_count = rule_output["sbc_malefic_vedha_count"]
    panchang = rule_output["panchang"]
    moon_nak = next(p["nakshatra"] for p in planets if p["name"] == "Moon")
    natal_moon_sign = rule_output["natal_moon_sign"]

    # ── Normalize and rank ────────────────────────────────────────────────────
    normalized_event_scores = normalize_event_scores(event_scores)
    top_events_ranked = rank_events(event_scores)
    top_events_normalized = normalize_top_events(top_events_ranked, normalized_event_scores)
    top_event_name, top_event_score = top_events_ranked[0]

    # ── Confidence components ─────────────────────────────────────────────────
    event_strength = min(80, top_event_score * 0.5)
    yoga_component = max(0, min(25, yoga_info.get("score", 0) + 5))
    top_event_planets = EVENT_MAP.get(top_event_name, {}).get("planets", [])
    top_event_houses = EVENT_MAP.get(top_event_name, {}).get("houses", [])

    jupiter_house = next(p["house"] for p in planets if p["name"] == "Jupiter")
    saturn_house = next(p["house"] for p in planets if p["name"] == "Saturn")
    double_transit_strength = check_event_transit(jupiter_house, saturn_house, top_event_houses)

    # Dasha lord gate
    second_sign = (asc_sign % 12) + 1
    tenth_sign = ((asc_sign + 8 - 1) % 12) + 1
    eleventh_sign = ((asc_sign + 9 - 1) % 12) + 1
    dasha_lords_2_10_11 = {SIGN_LORDS[second_sign], SIGN_LORDS[tenth_sign], SIGN_LORDS[eleventh_sign]}
    dasha_lord_gate = dasha in dasha_lords_2_10_11 or antardasha in dasha_lords_2_10_11

    # Vargottama proxy
    dasha_planets = [p for p in planets if p["name"] in {dasha, antardasha}]
    vargottama_dasha_proxy = any(p.get("vimsopaka", 0) >= 16 for p in dasha_planets)

    # Dasha component
    dasha_component = 20 if dasha in top_event_planets else 12
    if antardasha in top_event_planets:
        dasha_component += 5
    if yogini.get("yd") in top_event_planets:
        dasha_component += 4
    if chara_current.get("lord") in top_event_planets:
        dasha_component += 6
    dasha_component = min(35, dasha_component)

    # ── Base confidence ───────────────────────────────────────────────────────
    confidence = confidence_score(
        {
            "event_strength": event_strength,
            "yoga": yoga_component,
            "dasha": dasha_component,
            "promise": promise_label,
            "kakshya_active": kakshya.get("active", False),
        },
        penalties={"risk": risk},
    )

    # ── Adjustment 1: Yogini factor × sandhi multiplier ───────────────────────
    confidence = round(max(0.0, min(100.0, confidence * yogini_factor * yogini.get("sandhi_confidence_multiplier", 1.0))), 2)

    # ── Adjustment 2: Chara sandhi ────────────────────────────────────────────
    if chara_current.get("sandhi_active"):
        confidence = round(max(0.0, min(100.0, confidence * 0.9)), 2)

    # ── Adjustment 3: Tara confidence boost ───────────────────────────────────
    tara_confidence_boost = tara_score * 3

    # ── Adjustment 4: Rulebook confidence delta ───────────────────────────────
    rulebook_confidence_adj = round(rulebook_confidence_delta * 0.6, 1)

    confidence = round(max(0.0, min(100.0, confidence + tara_confidence_boost + rulebook_confidence_adj)), 2)

    # ── Adjustment 5: Kakshya bonus ───────────────────────────────────────────
    if kakshya.get("active", False):
        confidence = round(max(0.0, min(100.0, confidence + 10)), 2)

    # ── Adjustment 6: Final yogini factor ─────────────────────────────────────
    confidence = round(max(0.0, min(100.0, confidence * yogini_factor)), 2)

    # ── Adjustment 7: Calibration ─────────────────────────────────────────────
    confidence_calibrated = round(
        max(0.0, min(100.0, apply_confidence_calibration(confidence, confidence_calibration_config))),
        2,
    )

    # ── Conflict flag ─────────────────────────────────────────────────────────
    conflict_flag = tara_score > 7 and rulebook_action == "DO NOT TRADE"

    # ── Generate decision ─────────────────────────────────────────────────────
    decision = generate_decision(top_events_ranked, risk, confidence_calibrated, av_vulnerability=av_risk)
    decision["confidence_raw"] = confidence
    decision["confidence_calibrated"] = confidence_calibrated

    # ── Override rules ────────────────────────────────────────────────────────
    if conflict_flag:
        decision["action"] = "LOW SIZE / TEST TRADE"
        decision["phase"] = "TARA_RULEBOOK_CONFLICT"
    elif tara_score > 7 and confidence_calibrated > 60 and risk < 40:
        decision["action"] = "AGGRESSIVE"
        decision["phase"] = "FINAL_FRAMEWORK_AGGRESSIVE"
    elif tara_score < 0 and confidence_calibrated < 20 and risk > 80:
        decision["action"] = "AVOID"
        decision["phase"] = "FINAL_FRAMEWORK_AVOID"

    # ── Trading gate (optional) ───────────────────────────────────────────────
    if use_trading_gate:
        # Build BAV values for asset signals
        saturn_sign = next(p["sign"] for p in planets if p["name"] == "Saturn")
        sun_sign_now = next(p["sign"] for p in planets if p["name"] == "Sun")
        venus_sign_now = next(p["sign"] for p in planets if p["name"] == "Venus")
        mars_sign_now = next(p["sign"] for p in planets if p["name"] == "Mars")
        mercury_sign_now = next(p["sign"] for p in planets if p["name"] == "Mercury")

        sun_bav = ashtakavarga["bav"].get("Sun", [0] * 12)[sun_sign_now - 1]
        sun_sav = ashtakavarga.get("sav_sodhya", [0] * 12)[sun_sign_now - 1]
        venus_sav = ashtakavarga.get("sav_sodhya", [0] * 12)[venus_sign_now - 1]
        mercury_bav = ashtakavarga["bav"].get("Mercury", [0] * 12)[mercury_sign_now - 1]
        mercury_sav = ashtakavarga.get("sav_sodhya", [0] * 12)[mercury_sign_now - 1]
        saturn_bav = ashtakavarga["bav"].get("Saturn", [0] * 12)[saturn_sign - 1]

        # Venus kakshya
        venus_lon = next(p["longitude"] for p in planets if p["name"] == "Venus")
        venus_bav_bindus = {
            lord: (ashtakavarga["bav"].get(lord, [0] * 12) or [0] * 12)[venus_sign_now - 1]
            for lord in ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
        }
        venus_bav_bindus["Ascendant"] = 1
        venus_kakshya_active = kakshya_trigger(venus_lon, venus_bav_bindus).get("active", False)

        # Mars/Saturn house from natal
        from astronomy.utils import normalize_lon
        # We need natal mars sign — compute from birth_data
        natal_mars_sign = int(normalize_lon(rule_output.get("_natal_positions", {}).get("Mars", 0)) // 30) + 1 if rule_output.get("_natal_positions") else 1
        mars_house_from_natal = ((mars_sign_now - natal_mars_sign) % 12) + 1
        saturn_house_from_natal_moon = ((saturn_sign - natal_moon_sign) % 12) + 1

        trading_context = {
            "top_event_name": top_event_name,
            "top_event_score": top_event_score,
            "top_event_planets": top_event_planets,
            "moon_nakshatra": moon_nak,
            "dasha": dasha,
            "antardasha": antardasha,
            "promise_label": promise_label,
            "tara_score": tara_score,
            "vedha_blocked": vedha_blocked,
            "kakshya_active": kakshya.get("active", False),
            "kakshya_cluster": kakshya_cluster,
            "panchang_score": panchang.get("score", 0),
            "focal_11": focal_11,
            "transit_strength": transit_strength,
            "double_transit_strength": double_transit_strength,
            "dasha_lord_gate": dasha_lord_gate,
            "vargottama_dasha_proxy": vargottama_dasha_proxy,
            "confidence": confidence_calibrated,
            "confidence_raw": confidence,
            "risk": risk,
            "tara_remainder": rule_output["tara_remainder"],
            "chandrabala_count": chandrabala_count,
            "chandrabala_eighth": chandrabala_eighth,
            "sbc_malefic_karma_vedha": sbc_malefic_karma_vedha,
            "sbc_malefic_janma_vedha": sbc_malefic_janma_vedha,
            "sbc_malefic_vedha_count": sbc_malefic_vedha_count,
            "sbc_analysis": sbc_analysis,
            "sun_bav": sun_bav,
            "sun_sav": sun_sav,
            "venus_kakshya_active": venus_kakshya_active,
            "venus_sav": venus_sav,
            "mars_house_from_natal": mars_house_from_natal,
            "mercury_bav": mercury_bav,
            "mercury_sav": mercury_sav,
            "saturn_house_from_natal_moon": saturn_house_from_natal_moon,
            "saturn_bav": saturn_bav,
            "trading_gate_profile": trading_gate_profile,
        }

        trading_gate = evaluate_trading_gate(trading_context)
        if trading_gate["overall_status"] == "BLOCK":
            decision["action"] = "AVOID"
            decision["phase"] = "TRADING_GATE_BLOCK"
        elif trading_gate["overall_status"] == "CAUTION" and decision["action"] in {
            "GO FULL", "AGGRESSIVE", "CONTROLLED AGGRESSION",
        }:
            decision["action"] = "LOW SIZE / WAIT"
            decision["phase"] = "TRADING_GATE_CAUTION"

        # Adaptive lite plus calibration
        trading_gate_profile_lc = str(trading_gate_profile or "").strip().lower()
        adaptive_lite_plus_enabled = trading_gate_profile_lc in {
            "adaptive_lite_plus", "adaptive_plus", "adaptive_profile_22071975_plus",
        }
        calibration = {
            "adaptive_lite_plus_enabled": adaptive_lite_plus_enabled,
            "risky_nakshatra_penalty": bool(
                (trading_gate.get("adaptive_overrides") or {}).get("risky_nakshatra_penalty", False)
            ),
            "chandrabala_eighth": bool(trading_gate.get("chandrabala_eighth", False)),
            "focal_11_sav_band": trading_gate.get("focal_11_sav_band"),
            "position_multiplier": 1.0,
            "confidence_before_calibration": decision.get("confidence"),
            "risk_before_calibration": decision.get("risk"),
            "applied": [],
        }
        if adaptive_lite_plus_enabled:
            position_multiplier = 1.0
            if calibration["chandrabala_eighth"]:
                decision["action"] = "AVOID"
                decision["phase"] = "CALIBRATION_CHANDRABALA_8TH"
                calibration["applied"].append("chandrabala_8th_hard_block")
                position_multiplier = 0.0
            elif calibration["risky_nakshatra_penalty"] and decision["action"] != "AVOID":
                decision["action"] = "LOW SIZE / WAIT"
                decision["phase"] = "CALIBRATION_RISKY_NAKSHATRA"
                calibration["applied"].append("risky_nakshatra_size_cap")
                position_multiplier = min(position_multiplier, 0.75)

            if (
                calibration["focal_11_sav_band"] == "<20"
                and decision["action"] in {"MODERATE", "LOW SIZE / TEST TRADE"}
            ):
                decision["action"] = "LOW SIZE / WAIT"
                decision["phase"] = "CALIBRATION_LOW_SAV_11"
                calibration["applied"].append("low_sav11_execution_cap")
                position_multiplier = min(position_multiplier, 0.9)

            confidence_now = float(decision.get("confidence") or 0.0)
            risk_now = float(decision.get("risk") or 0.0)
            confidence_post = round(max(0.0, min(100.0, confidence_now * position_multiplier)), 2)
            risk_uplift = round((1.0 - position_multiplier) * 8.0, 2)
            risk_post = round(max(0.0, min(100.0, risk_now + risk_uplift)), 2)

            decision["confidence"] = confidence_post
            decision["risk"] = risk_post
            decision["position_multiplier"] = round(position_multiplier, 2)

            calibration["position_multiplier"] = round(position_multiplier, 2)
            calibration["confidence_after_calibration"] = confidence_post
            calibration["risk_after_calibration"] = risk_post

        decision["calibration"] = calibration
        decision["trading_gate"] = trading_gate
    else:
        decision["trading_gate"] = {
            "enabled": False,
            "overall_status": "DISABLED",
            "score": None,
            "suggested_action": None,
            "levels": {},
        }

    # Asset events
    if use_asset_timeline_events and use_trading_gate:
        decision["asset_events"] = evaluate_asset_timeline_events(trading_context)
    else:
        decision["asset_events"] = []

    return decision
