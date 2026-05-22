TRADING_FOCUSED_EVENTS = {
    "finance",
    "business",
    "career",
    "job",
    "gain",
    "loss",
    "legal",
}

NO_TRADE_TARA_REMAINDERS = {3, 5, 7}
FAVORABLE_TARA_REMAINDERS = {2, 4, 6, 8, 9}
RISKY_NAKSHATRA_SET = {
    "Dhanishta",
    "Ashlesha",
    "Ashwini",
    "Mrigashira",
    "Jyeshtha",
}

ASSET_SIGNIFICATOR_MAP = {
    "gold_authority": {"Sun", "Jupiter"},
    "silver_luxury_agri": {"Venus"},
    "energy_copper_metals": {"Mars"},
    "banking_tech_trade": {"Mercury"},
    "petroleum_iron_steel": {"Saturn", "Rahu"},
}


_STATUS_SCORE = {
    "PASS": 2,
    "WARN": 1,
    "FAIL": 0,
}


def _status_from_bool(flag, warn=False):
    if flag:
        return "PASS"
    return "WARN" if warn else "FAIL"


def _build_check(name, status, value, detail):
    return {
        "name": name,
        "status": status,
        "value": value,
        "detail": detail,
    }


def _aggregate_level(checks):
    statuses = [c["status"] for c in checks]
    if any(s == "FAIL" for s in statuses):
        return "FAIL"
    if any(s == "WARN" for s in statuses):
        return "WARN"
    return "PASS"


def _aggregate_score(levels):
    total = 0
    max_total = 0
    for level in levels.values():
        checks = level.get("checks", [])
        for c in checks:
            total += _STATUS_SCORE.get(c.get("status", "WARN"), 1)
            max_total += 2
    if max_total == 0:
        return 0.0
    return round((total / max_total) * 100, 2)


def _to_float(value, fallback=0.0):
    if isinstance(value, dict):
        for key in ("score", "value", "raw"):
            if key in value:
                return _to_float(value.get(key), fallback=fallback)
        return float(fallback)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _asset_bias(top_event_planets):
    event_planets = set(top_event_planets or [])
    result = []
    for asset, significators in ASSET_SIGNIFICATOR_MAP.items():
        overlap = sorted(event_planets.intersection(significators))
        if overlap:
            result.append(
                {
                    "asset": asset,
                    "matched_significators": overlap,
                    "match_strength": round(len(overlap) / max(len(significators), 1), 2),
                }
            )
    return sorted(result, key=lambda x: x["match_strength"], reverse=True)


def evaluate_asset_timeline_events(context):
    sun_bav = _to_float(context.get("sun_bav", 0), fallback=0)
    sun_sav = _to_float(context.get("sun_sav", 0), fallback=0)
    venus_kakshya_active = bool(context.get("venus_kakshya_active", False))
    venus_sav = _to_float(context.get("venus_sav", 0), fallback=0)
    mars_house_from_natal = int(_to_float(context.get("mars_house_from_natal", 0), fallback=0))
    mercury_bav = _to_float(context.get("mercury_bav", 0), fallback=0)
    mercury_sav = _to_float(context.get("mercury_sav", 0), fallback=0)
    saturn_house_from_natal_moon = int(_to_float(context.get("saturn_house_from_natal_moon", 0), fallback=0))
    saturn_bav = _to_float(context.get("saturn_bav", 0), fallback=0)
    sbc_malefic_karma_vedha = bool(context.get("sbc_malefic_karma_vedha", False))

    events = []

    gold_score = 0
    if sun_bav >= 1:
        gold_score += 40
    if sun_sav >= 28:
        gold_score += 30
    if not sbc_malefic_karma_vedha:
        gold_score += 30
    events.append(
        {
            "asset_class": "Gold / Authority Stocks",
            "primary_significator": ["Sun", "Jupiter"],
            "score": min(100, gold_score),
            "status": "FAVORABLE" if gold_score >= 70 else "NEUTRAL" if gold_score >= 45 else "UNFAVORABLE",
            "checks": {
                "sun_high_bav": sun_bav >= 1,
                "sun_high_sav": sun_sav >= 28,
                "benefic_karma_vedha_proxy": not sbc_malefic_karma_vedha,
            },
        }
    )

    silver_score = 0
    if venus_kakshya_active:
        silver_score += 45
    if venus_sav >= 28:
        silver_score += 55
    events.append(
        {
            "asset_class": "Silver / Luxury / Agri",
            "primary_significator": ["Venus"],
            "score": min(100, silver_score),
            "status": "FAVORABLE" if silver_score >= 70 else "NEUTRAL" if silver_score >= 45 else "UNFAVORABLE",
            "checks": {
                "venus_supportive_kakshya": venus_kakshya_active,
                "venus_high_sav": venus_sav >= 28,
            },
        }
    )

    energy_score = 100 if mars_house_from_natal in {3, 6, 10, 11} else 25
    events.append(
        {
            "asset_class": "Energy / Copper / Metals",
            "primary_significator": ["Mars"],
            "score": energy_score,
            "status": "FAVORABLE" if energy_score >= 70 else "UNFAVORABLE",
            "checks": {
                "mars_house_from_natal": mars_house_from_natal,
                "mars_rule_match_3_6_10_11": mars_house_from_natal in {3, 6, 10, 11},
            },
        }
    )

    banking_score = 0
    if mercury_bav >= 1:
        banking_score += 50
    if mercury_sav >= 25:
        banking_score += 50
    events.append(
        {
            "asset_class": "Banking / Tech / Trade",
            "primary_significator": ["Mercury"],
            "score": min(100, banking_score),
            "status": "FAVORABLE" if banking_score >= 70 else "NEUTRAL" if banking_score >= 45 else "UNFAVORABLE",
            "checks": {
                "mercury_high_bindu": mercury_bav >= 1,
                "mercury_supportive_sav": mercury_sav >= 25,
            },
        }
    )

    petro_score = 0
    if saturn_house_from_natal_moon in {3, 6, 11}:
        petro_score += 60
    if saturn_bav >= 1:
        petro_score += 40
    events.append(
        {
            "asset_class": "Petroleum / Iron / Steel",
            "primary_significator": ["Saturn", "Rahu"],
            "score": min(100, petro_score),
            "status": "FAVORABLE" if petro_score >= 70 else "NEUTRAL" if petro_score >= 45 else "UNFAVORABLE",
            "checks": {
                "saturn_from_moon_3_6_11": saturn_house_from_natal_moon in {3, 6, 11},
                "saturn_high_bindu": saturn_bav >= 1,
            },
        }
    )

    return sorted(events, key=lambda x: x["score"], reverse=True)


def evaluate_trading_gate(context):
    top_event_name = context.get("top_event_name")
    top_event_score = _to_float(context.get("top_event_score", 0), fallback=0)
    top_event_planets = context.get("top_event_planets") or []

    dasha = context.get("dasha")
    antardasha = context.get("antardasha")
    trading_gate_profile = str(context.get("trading_gate_profile", "strict") or "strict").strip().lower()
    surgical_profile_enabled = trading_gate_profile in {
        "adaptive_top20_surgical",
        "top20_surgical",
        "surgical",
    }
    sav_micro_profile_enabled = trading_gate_profile in {
        "adaptive_top20_sav_micro",
        "top20_sav_micro",
        "sav_micro",
    }
    adaptive_lite_plus_enabled = trading_gate_profile in {
        "adaptive_lite_plus",
        "adaptive_plus",
        "adaptive_profile_22071975_plus",
    }
    adaptive_profile_enabled = trading_gate_profile in {
        "adaptive_profile_22071975",
        "adaptive_22071975",
        "adaptive",
    } or surgical_profile_enabled or adaptive_lite_plus_enabled

    promise_label = context.get("promise_label", "")
    tara_score = _to_float(context.get("tara_score", 0), fallback=0)
    vedha_blocked = bool(context.get("vedha_blocked", False))
    kakshya_active = bool(context.get("kakshya_active", False))
    panchang_score = _to_float(context.get("panchang_score", 0), fallback=0)
    focal_11 = _to_float(context.get("focal_11", 0), fallback=0)
    transit_strength = _to_float(context.get("transit_strength", 0), fallback=0)
    confidence = _to_float(context.get("confidence", 0), fallback=0)
    risk = _to_float(context.get("risk", 0), fallback=0)
    tara_remainder = int(_to_float(context.get("tara_remainder", 0), fallback=0))
    chandrabala_count = int(_to_float(context.get("chandrabala_count", 0), fallback=0))
    chandrabala_eighth = bool(context.get("chandrabala_eighth", False))
    moon_nakshatra = str(context.get("moon_nakshatra", "") or "").strip()
    kakshya_cluster = context.get("kakshya_cluster") or {}
    kakshya_cluster_level = str(kakshya_cluster.get("level", "LOW")).upper()
    kakshya_cluster_inactive_count = int(_to_float(kakshya_cluster.get("inactive_count", 0), fallback=0))
    kakshya_cluster_block_entry = bool(kakshya_cluster.get("block_entry", False))
    sbc_analysis = context.get("sbc_analysis") or {}
    sbc_zones = sbc_analysis.get("zones") or {}
    sbc_karma_zone = sbc_zones.get("karma") or {}
    sbc_janma_zone = sbc_zones.get("janma") or {}
    sbc_sampat_zone = sbc_zones.get("sampat") or {}

    sbc_malefic_karma_vedha = bool(
        sbc_karma_zone.get("malefic_vedha", context.get("sbc_malefic_karma_vedha", False))
    )
    sbc_malefic_janma_vedha = bool(
        sbc_janma_zone.get("malefic_vedha", context.get("sbc_malefic_janma_vedha", False))
    )
    sbc_malefic_vedha_count = int(
        _to_float(
            sbc_analysis.get("malefic_vedha_count", context.get("sbc_malefic_vedha_count", 0)),
            fallback=0,
        )
    )
    sbc_benefic_karma_vedha = bool(sbc_karma_zone.get("benefic_vedha", False))
    sbc_benefic_sampat_vedha = bool(sbc_sampat_zone.get("benefic_vedha", False))
    sbc_extreme_malefic_pressure = bool(sbc_analysis.get("extreme_malefic_pressure", sbc_malefic_vedha_count >= 4))
    sbc_motion_logic = sbc_analysis.get("motion_logic") or {}
    double_transit_strength = _to_float(context.get("double_transit_strength", 0), fallback=0)
    dasha_lord_gate = bool(context.get("dasha_lord_gate", False))
    vargottama_dasha_proxy = bool(context.get("vargottama_dasha_proxy", False))

    level_1_checks = []
    is_trading_event = (top_event_name or "").lower() in TRADING_FOCUSED_EVENTS
    level_1_checks.append(
        _build_check(
            "Trading Event Relevance",
            _status_from_bool(is_trading_event, warn=True),
            top_event_name,
            "Top event should map to a trading-relevant domain.",
        )
    )

    promise_ok = promise_label != "weak"
    level_1_checks.append(
        _build_check(
            "Capacity Promise",
            _status_from_bool(promise_ok),
            promise_label,
            "Weak promise reduces trading capacity confidence.",
        )
    )

    base_strength_ok = top_event_score >= 120
    level_1_checks.append(
        _build_check(
            "Event Strength",
            _status_from_bool(base_strength_ok, warn=True),
            round(top_event_score, 2),
            "Higher event score supports conviction for trading entries.",
        )
    )

    dasha_alignment = dasha in top_event_planets or antardasha in top_event_planets
    transit_ok = transit_strength >= 1.0
    adaptive_sav_softening = (
        adaptive_profile_enabled
        and focal_11 <= 20
        and top_event_score >= 150
        and confidence >= 60
        and risk <= 45
        and transit_ok
    )
    if focal_11 >= 28:
        sav_status = "PASS"
    elif adaptive_sav_softening:
        sav_status = "WARN"
    elif focal_11 <= 20:
        sav_status = "FAIL"
    else:
        sav_status = "WARN"

    level_2_checks = [
        _build_check(
            "Dasha Alignment",
            _status_from_bool(dasha_alignment),
            {"md": dasha, "ad": antardasha},
            "MD/AD ideally aligns with top-event planets.",
        ),
        _build_check(
            "Transit Support",
            _status_from_bool(transit_ok, warn=True),
            round(transit_strength, 4),
            "Macro transit strength should be supportive.",
        ),
        _build_check(
            "SAV House-11 Gate",
            sav_status,
            round(focal_11, 2),
            "SAV >=28 supportive, <=20 restrictive.",
        ),
        _build_check(
            "Double Transit Gate",
            "PASS" if double_transit_strength >= 1.0 else "WARN" if double_transit_strength >= 0.5 else "FAIL",
            round(double_transit_strength, 2),
            "Jupiter+Saturn joint support on target houses improves macro reliability.",
        ),
        _build_check(
            "Dasha 2/10/11 Lord Gate",
            _status_from_bool(dasha_lord_gate),
            dasha_lord_gate,
            "Activation is stronger when MD/AD involves 2nd/10th/11th lords.",
        ),
        _build_check(
            "Vargottama Dasha Proxy",
            _status_from_bool(vargottama_dasha_proxy, warn=True),
            vargottama_dasha_proxy,
            "High-quality dasha proxy boosts resilience against minor transit noise.",
        ),
    ]

    tara_ok = tara_score >= 1
    tara_remainder_status = (
        "PASS"
        if tara_remainder in FAVORABLE_TARA_REMAINDERS
        else "FAIL"
        if tara_remainder in NO_TRADE_TARA_REMAINDERS
        else "WARN"
    )
    vedha_clear = not vedha_blocked
    sbc_corroborating_risk = bool(
        vedha_blocked
        or chandrabala_eighth
        or focal_11 < 20
        or not dasha_lord_gate
    )
    if adaptive_profile_enabled:
        if sbc_extreme_malefic_pressure and sbc_corroborating_risk:
            sbc_multi_malefic_status = "FAIL"
        elif sbc_malefic_vedha_count >= 2:
            sbc_multi_malefic_status = "WARN"
        else:
            sbc_multi_malefic_status = "PASS"
    else:
        sbc_multi_malefic_status = "FAIL" if sbc_extreme_malefic_pressure else "WARN" if sbc_malefic_vedha_count >= 2 else "PASS"

    if sav_micro_profile_enabled:
        adaptive_sav_checklist_relax = bool(
            focal_11 < 20
            and top_event_score >= 175
            and confidence >= 72
            and risk <= 36
            and transit_strength >= 0.65
            and dasha_alignment
            and dasha_lord_gate
            and (sbc_benefic_karma_vedha or sbc_benefic_sampat_vedha)
            and not vedha_blocked
            and kakshya_active
            and not kakshya_cluster_block_entry
            and not chandrabala_eighth
        )
        adaptive_sbc_karma_checklist_relax = False
    elif surgical_profile_enabled:
        adaptive_sav_checklist_relax = bool(
            focal_11 < 20
            and top_event_score >= 170
            and confidence >= 70
            and risk <= 38
            and transit_strength >= 0.65
            and dasha_alignment
            and dasha_lord_gate
            and (sbc_benefic_karma_vedha or sbc_benefic_sampat_vedha)
            and not vedha_blocked
            and not kakshya_cluster_block_entry
            and not chandrabala_eighth
        )
        adaptive_sbc_karma_checklist_relax = bool(
            sbc_malefic_karma_vedha
            and not sbc_extreme_malefic_pressure
            and top_event_score >= 165
            and confidence >= 68
            and risk <= 40
            and transit_strength >= 0.65
            and dasha_alignment
            and dasha_lord_gate
            and (sbc_benefic_karma_vedha or sbc_benefic_sampat_vedha)
            and not vedha_blocked
            and not chandrabala_eighth
        )
    else:
        adaptive_sav_checklist_relax = bool(
            adaptive_profile_enabled
            and focal_11 < 20
            and top_event_score >= 165
            and confidence >= 65
            and risk <= 40
            and transit_ok
            and dasha_alignment
            and not vedha_blocked
            and not chandrabala_eighth
        )
        adaptive_sbc_karma_checklist_relax = bool(
            adaptive_profile_enabled
            and sbc_malefic_karma_vedha
            and not sbc_extreme_malefic_pressure
            and top_event_score >= 155
            and confidence >= 60
            and risk <= 45
            and (sbc_benefic_karma_vedha or sbc_benefic_sampat_vedha)
            and not chandrabala_eighth
        )

    kas_points = round(
        (tara_score * 15) + panchang_score + (20 if kakshya_active else 0) + (confidence * 0.8) - (risk * 0.4),
        2,
    )

    level_3_checks = [
        _build_check(
            "Tara Bala",
            _status_from_bool(tara_ok, warn=True),
            round(tara_score, 2),
            "Positive Tara bias supports intraday quality.",
        ),
        _build_check(
            "Tara Remainder Rule",
            tara_remainder_status,
            tara_remainder,
            "Preferred remainders: 2/4/6/8/9. Avoid 3/5/7 for entries.",
        ),
        _build_check(
            "Vedha Clearance",
            _status_from_bool(vedha_clear),
            vedha_clear,
            "Blocked vedha increases timing friction.",
        ),
        _build_check(
            "SBC Malefic Vedha (Karma)",
            _status_from_bool(not sbc_malefic_karma_vedha),
            sbc_malefic_karma_vedha,
            "Malefic pressure on Karma-sensitive zone is a no-trade warning.",
        ),
        _build_check(
            "SBC Malefic Vedha (Janma)",
            _status_from_bool(not sbc_malefic_janma_vedha, warn=True),
            sbc_malefic_janma_vedha,
            "Janma sensitivity reflects personal safety/risk stress.",
        ),
        _build_check(
            "SBC Multi-Malefic Pressure",
            sbc_multi_malefic_status,
            sbc_malefic_vedha_count,
            "Multiple simultaneous malefic pressures indicate enterprise stress.",
        ),
        _build_check(
            "SBC Benefic Vedha (Karma/Sampat)",
            "PASS" if (sbc_benefic_karma_vedha or sbc_benefic_sampat_vedha) else "WARN",
            {
                "karma": sbc_benefic_karma_vedha,
                "sampat": sbc_benefic_sampat_vedha,
            },
            "Benefic vedha support on Karma/Sampat zones improves strategic entry quality.",
        ),
        _build_check(
            "SBC Motion Logic",
            "PASS" if sbc_motion_logic else "WARN",
            sbc_motion_logic,
            "Retrograde planets use left-vedha; fast-moving planets use right-vedha.",
        ),
        _build_check(
            "Kakshya Trigger",
            _status_from_bool(kakshya_active, warn=True),
            kakshya_active,
            "Active kakshya improves timing precision.",
        ),
        _build_check(
            "Kakshya Multi-Planet Cluster",
            "FAIL"
            if kakshya_cluster_level == "SEVERE"
            else "WARN"
            if kakshya_cluster_level in {"ELEVATED", "MILD"}
            else "PASS",
            {
                "level": kakshya_cluster_level,
                "inactive_count": kakshya_cluster_inactive_count,
            },
            "Concurrent non-bindu kakshya passages across multiple planets increase execution risk.",
        ),
        _build_check(
            "KAS Composite",
            "PASS" if kas_points >= 197 else "WARN",
            kas_points,
            "Composite precision score for intraday readiness.",
        ),
        _build_check(
            "Chandrabala Exit",
            _status_from_bool(not chandrabala_eighth),
            {"count": chandrabala_count, "eighth": chandrabala_eighth},
            "8th count from natal Moon is treated as an exit/avoid condition.",
        ),
    ]

    levels = {
        "level_1_identity_capacity": {
            "status": _aggregate_level(level_1_checks),
            "checks": level_1_checks,
        },
        "level_2_macro_temporal": {
            "status": _aggregate_level(level_2_checks),
            "checks": level_2_checks,
        },
        "level_3_intraday_precision": {
            "status": _aggregate_level(level_3_checks),
            "checks": level_3_checks,
        },
    }

    statuses = [v["status"] for v in levels.values()]
    no_trade_checklist = {
        "tara_no_trade": tara_remainder in NO_TRADE_TARA_REMAINDERS,
        "sav_below_20": focal_11 < 20 and not adaptive_sav_checklist_relax,
        "sbc_malefic_karma": sbc_malefic_karma_vedha and not adaptive_sbc_karma_checklist_relax,
        "kakshya_bindu_missing": not kakshya_active,
        "kakshya_cluster_severe": kakshya_cluster_block_entry,
        "chandrabala_eighth": chandrabala_eighth,
    }
    checklist_triggered = [k for k, v in no_trade_checklist.items() if v]
    level_fail_count = statuses.count("FAIL")
    surgical_level_fail_rescue = bool(
        surgical_profile_enabled
        and not checklist_triggered
        and level_fail_count >= 3
        and top_event_score >= 185
        and confidence >= 72
        and risk <= 35
        and transit_strength >= 0.65
        and dasha_alignment
        and dasha_lord_gate
        and not vedha_blocked
        and not sbc_extreme_malefic_pressure
        and (sbc_benefic_karma_vedha or sbc_benefic_sampat_vedha)
        and kakshya_active
        and not kakshya_cluster_block_entry
        and not chandrabala_eighth
    )

    if checklist_triggered:
        overall_status = "BLOCK"
        suggested_action = "AVOID"
    elif adaptive_profile_enabled and level_fail_count >= 3:
        if surgical_level_fail_rescue:
            overall_status = "CAUTION"
            suggested_action = "LOW SIZE / WAIT"
        else:
            overall_status = "BLOCK"
            suggested_action = "AVOID"
    elif not adaptive_profile_enabled and level_fail_count >= 2:
        overall_status = "BLOCK"
        suggested_action = "AVOID"
    elif "FAIL" in statuses:
        overall_status = "CAUTION"
        suggested_action = "LOW SIZE / WAIT"
    elif "WARN" in statuses:
        overall_status = "WATCH"
        suggested_action = "MODERATE"
    else:
        overall_status = "CLEAR"
        suggested_action = "CONTROLLED AGGRESSION"

    risky_nakshatra_penalty = bool(adaptive_lite_plus_enabled and moon_nakshatra in RISKY_NAKSHATRA_SET)
    if risky_nakshatra_penalty and overall_status in {"CLEAR", "WATCH", "CAUTION"}:
        overall_status = "CAUTION"
        suggested_action = "LOW SIZE / WAIT"

    if focal_11 < 20:
        focal_11_sav_band = "<20"
    elif focal_11 < 25:
        focal_11_sav_band = "20-24"
    elif focal_11 < 30:
        focal_11_sav_band = "25-29"
    else:
        focal_11_sav_band = ">=30"

    return {
        "enabled": True,
        "overall_status": overall_status,
        "score": _aggregate_score(levels),
        "suggested_action": suggested_action,
        "profile": trading_gate_profile,
        "adaptive_profile_enabled": adaptive_profile_enabled,
        "surgical_profile_enabled": surgical_profile_enabled,
        "sav_micro_profile_enabled": sav_micro_profile_enabled,
        "adaptive_lite_plus_enabled": adaptive_lite_plus_enabled,
        "adaptive_overrides": {
            "sav_below_20_relaxed": adaptive_sav_checklist_relax,
            "sbc_malefic_karma_relaxed": adaptive_sbc_karma_checklist_relax,
            "level_fail_rescue": surgical_level_fail_rescue,
            "risky_nakshatra_penalty": risky_nakshatra_penalty,
        },
        "moon_nakshatra": moon_nakshatra,
        "chandrabala_eighth": chandrabala_eighth,
        "focal_11_sav": round(focal_11, 2),
        "focal_11_sav_band": focal_11_sav_band,
        "levels": levels,
        "no_trade_checklist": no_trade_checklist,
        "no_trade_triggers": checklist_triggered,
        "asset_signals": evaluate_asset_timeline_events(context),
        "asset_event_bias": _asset_bias(top_event_planets),
        "sbc": {
            "zones": sbc_zones,
            "motion_logic": sbc_motion_logic,
            "malefic_vedha_count": sbc_malefic_vedha_count,
            "extreme_malefic_pressure": sbc_extreme_malefic_pressure,
        },
    }
