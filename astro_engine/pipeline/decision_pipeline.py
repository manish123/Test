"""
Decision Pipeline Stage (Layer D orchestration)

Consumes RuleResult, produces DecisionResult.
Applies scoring, confidence, risk normalization, trading gate, and final action.
Does not know ephemeris math. Only consumes structured outputs from layers 1-3.
"""

import math

from contracts.rule_result import RuleResult
from contracts.decision_result import DecisionResult, TradingGateResult

from decisions.confidence import confidence_score
from decisions.confidence_calibration import apply_confidence_calibration
from decisions.decision_engine import generate_decision
from decisions.normalization import normalize_event_scores, normalize_top_events
from decisions.trading_gate import evaluate_trading_gate, evaluate_asset_timeline_events, TRADING_FOCUSED_EVENTS


def run_decisions(rule: RuleResult, config: dict = None) -> DecisionResult:
    """
    Execute Layer D: produce final trading decision from rule interpretations.

    Args:
        rule: RuleResult from rule pipeline
        config: optional dict with trading_gate settings, calibration, etc.

    Returns:
        DecisionResult (frozen dataclass)
    """
    config = config or {}
    use_trading_gate = config.get("use_trading_gate", False)
    trading_gate_profile = config.get("trading_gate_profile", "strict")
    confidence_calibration_config = config.get("confidence_calibration", None)
    use_trading_event_filter = config.get("use_trading_event_filter", False)
    use_asset_timeline_events = config.get("use_asset_timeline_events", False)

    event_scores = dict(rule.event_scores)

    # Trading event filter
    if use_trading_event_filter:
        event_scores = {
            name: (score * 1.15 if name.lower() in TRADING_FOCUSED_EVENTS else score * 0.35)
            for name, score in event_scores.items()
        }

    # Normalize and rank
    normalized = normalize_event_scores(event_scores)
    top_events = sorted(event_scores.items(), key=lambda x: x[1], reverse=True)[:2]
    top_events_normalized = normalize_top_events(top_events, normalized)

    if not top_events:
        return DecisionResult(action="AVOID", phase="NO_EVENTS")

    top_event_name, top_event_score = top_events[0]
    top_event_planets = []
    from rules.event_engine import EVENT_MAP
    if top_event_name in EVENT_MAP:
        top_event_planets = EVENT_MAP[top_event_name].get("planets", [])

    # Risk normalization (sqrt transform)
    raw_risk = rule.risk_score
    risk = round(math.sqrt(min(raw_risk, 100.0)) * 10, 2)

    # Confidence computation
    event_strength = min(80, top_event_score * 0.5)
    yoga_component = max(0, min(25, rule.yoga.score + 5))
    dasha_component = 12  # simplified — full version in main.py

    conf = confidence_score(
        {"event_strength": event_strength, "yoga": yoga_component, "dasha": dasha_component,
         "promise": "moderate", "kakshya_active": True},
        penalties={"risk": risk},
    )
    confidence_calibrated = apply_confidence_calibration(conf, confidence_calibration_config)

    # Generate decision
    decision = generate_decision(top_events, risk, confidence_calibrated,
                                 av_vulnerability=rule.risk_context.get("av_vulnerability", 0))

    # Trading gate
    trading_gate_result = TradingGateResult(enabled=False, overall_status="DISABLED")
    asset_events = []

    if use_trading_gate:
        # Build trading context for gate evaluation
        trading_context = {
            "top_event_name": top_event_name,
            "top_event_score": top_event_score,
            "top_event_planets": top_event_planets,
            "moon_nakshatra": "",
            "dasha": "",
            "antardasha": "",
            "promise_label": "moderate",
            "tara_score": rule.tara_score,
            "vedha_blocked": rule.vedha_blocked,
            "kakshya_active": rule.kakshya.get("active", False),
            "kakshya_cluster": rule.kakshya_cluster,
            "panchang_score": 0,
            "focal_11": 0,
            "transit_strength": 0,
            "double_transit_strength": 0,
            "dasha_lord_gate": False,
            "vargottama_dasha_proxy": False,
            "confidence": confidence_calibrated,
            "confidence_raw": conf,
            "risk": risk,
            "tara_remainder": rule.tara_remainder,
            "chandrabala_count": 0,
            "chandrabala_eighth": False,
            "sbc_malefic_karma_vedha": False,
            "sbc_malefic_janma_vedha": False,
            "sbc_malefic_vedha_count": 0,
            "sbc_analysis": rule.sbc_analysis,
            "trading_gate_profile": trading_gate_profile,
        }
        gate = evaluate_trading_gate(trading_context)
        trading_gate_result = TradingGateResult(
            enabled=True,
            overall_status=gate.get("overall_status", "DISABLED"),
            score=gate.get("score"),
            suggested_action=gate.get("suggested_action"),
            profile=trading_gate_profile,
            levels=gate.get("levels", {}),
            no_trade_triggers=gate.get("no_trade_triggers", []),
        )

        if gate["overall_status"] == "BLOCK":
            decision["action"] = "AVOID"
            decision["phase"] = "TRADING_GATE_BLOCK"

    if use_asset_timeline_events:
        asset_events = evaluate_asset_timeline_events({
            "sun_bav": 0, "sun_sav": 0, "venus_kakshya_active": False,
            "venus_sav": 0, "mars_house_from_natal": 0, "mercury_bav": 0,
            "mercury_sav": 0, "saturn_house_from_natal_moon": 0, "saturn_bav": 0,
            "sbc_malefic_karma_vedha": False,
        })

    return DecisionResult(
        action=decision.get("action", "AVOID"),
        phase=decision.get("phase", "NORMAL"),
        confidence=confidence_calibrated,
        confidence_raw=conf,
        risk=risk,
        top_event=top_event_name,
        top_event_score=top_event_score,
        position_multiplier=decision.get("position_multiplier", 1.0),
        trading_gate=trading_gate_result,
        asset_events=asset_events,
        calibration=None,
    )
