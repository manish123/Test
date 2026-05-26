"""
Rule Pipeline Stage (Layer C orchestration) — FULL PARITY VERSION

Consumes FeatureResult, produces RuleResult.
Replicates ALL logic from _run_single() lines 280-530:
- State engine processing
- Dual reference event scoring (lagna 50% + moon 50%)
- Tara scoring (get_tara, calculate_score, get_trade_decision)
- Nakshatra adjustment
- Moorthy grading
- Node yogakaraka bonus
- Argala scoring
- SBC vedha analysis
- Panchang adverse risk
- Full risk context with all modifiers
- Governance filtering
- Trading event filter

This must produce IDENTICAL event_scores, risk_context, and top_events
to _run_single() for the same inputs.
"""

import math
from contracts.feature_result import FeatureResult
from contracts.rule_result import RuleResult, YogaResult

from features.dignity import SIGN_LORDS
from features.nakshatra import get_nakshatra, nakshatra_list
from features.houses import detect_strong_houses
from features.ashtakavarga import focal_sign_strength, micro_transit_overlay, bav_risk
from features.transit import check_event_transit, event_orb_degree
from features.time_decay import time_decay_probability
from features.divisional import classify_vimsopaka_promise
from features.yogini import yogini_cross_validation, get_current_yogini
from features.chara_dasha import get_chara_dasha_sequence, get_current_chara_dasha
from features.panchang import compute_panchang_score

from rules.state_engine import process_chart_states
from rules.event_engine import evaluate_event, EVENT_MAP
from rules.yoga_engine import evaluate_yogas
from rules.governance import apply_event_governance
from rules.nakshatra_weight import nakshatra_adjustment
from rules.moorthy import moorthy_grade
from rules.sbc import evaluate_sbc_vedha
from rules.vedha import is_vedha_blocked
from rules.badhakesh import is_badhakesh_active, get_badhakesh
from rules.rasi_drishti import get_rasi_drishti
from rules.kakshya import kakshya_trigger, detect_kakshya_cluster
from rules.longevity import estimate_jaimini_longevity
from rules.maraka import identify_maraka_lords
from rules.personality_engine import build_personality_profile
from rules.argala import compute_argala_score
from rules.arudha import compute_arudha_pada

# ── Shared tara scoring (Phase 1 refactor — was duplicated from main.py) ──────
from rules.evaluator_base import (
    TARA_SCORES, PLANET_WEIGHTS,
    PANCHANG_RISK_WEIGHT, TRADING_EVENT_BOOST, NON_TRADING_EVENT_MULTIPLIER,
    get_tara as _get_tara_base,
    calculate_tara_score as _calculate_tara_score_base,
    get_trade_decision as _get_trade_decision_base,
    load_scoring_profile, get_profile_confidence_params,
)

from features.rahu_ketu import (
    detect_kala_sarpa,
    get_node_aspect_houses,
    node_yogakaraka,
    reverse_argala_points,
)

from decisions.risk_engine import build_risk_context, calculate_risk
from decisions.trading_gate import TRADING_FOCUSED_EVENTS

from astronomy.utils import normalize_lon

# Local aliases preserve the private-prefixed names used throughout this file
def _get_tara(janma, transit):
    return _get_tara_base(janma, transit)

def _calculate_tara_score(janma_nak, pdata):
    return _calculate_tara_score_base(janma_nak, pdata)

def _get_trade_decision(pdata):
    return _get_trade_decision_base(pdata)


# ═══════════════════════════════════════════════════════════════
# MAIN RULE PIPELINE
# ═══════════════════════════════════════════════════════════════

def run_rules(feature: FeatureResult, birth_data: dict, eval_date, config: dict = None) -> dict:
    """
    Execute Layer C: apply interpretive rules to derived features.
    FULL PARITY with _run_single().

    Returns a dict (not frozen RuleResult) for maximum compatibility during migration.
    Contains all fields needed by decision_pipeline for full parity.
    """
    config = config or {}
    governance_profile = config.get("governance_profile", "professional")
    allow_adult_insights = config.get("allow_adult_insights", False)
    use_trading_event_filter = config.get("use_trading_event_filter", False)
    use_nakshatra_rulebook_bias = config.get("use_nakshatra_rulebook_bias", False)

    # ── Scoring profile (Phase 9) ────────────────────────────────────────────
    # Resolve which domain profile to use. Trading path uses trading.yaml;
    # all other paths use general_life (or a domain-specific profile if specified).
    _scoring_domain = config.get("scoring_domain", "trading" if use_trading_event_filter else "general_life")
    _scoring_profile = load_scoring_profile(_scoring_domain)
    _use_nakshatra_overlay = bool(
        _scoring_profile
        and _scoring_profile.get("nakshatra_adjustment", {}).get("source") != "canonical_tara_only"
    )

    # ── Convert PlanetFeatures to mutable dicts ───────────────────────────────
    planets = []
    for pf in feature.planets:
        planets.append({
            "name": pf.name, "longitude": pf.longitude, "latitude": pf.latitude,
            "sign": pf.sign, "nakshatra": pf.nakshatra, "status": pf.status,
            "dispositor": pf.dispositor, "retrograde": pf.retrograde,
            "house": pf.house, "rashi_house": pf.rashi_house,
            "operational_house": pf.operational_house, "is_kendra": pf.is_kendra,
            "vimsopaka": pf.vimsopaka, "multiplier": 1.0,
        })

    # ── Process chart states (combustion, retro, graha yuddha) ────────────────
    by_house = {}
    for p in planets:
        by_house.setdefault(p["house"], []).append(p["name"])
    conjunctions = {
        p["name"]: [x for x in by_house.get(p["house"], []) if x != p["name"]]
        for p in planets
    }
    planets = process_chart_states(planets, {"conjunctions": conjunctions, "datetime": eval_date})

    from features.vimsopaka import compute_vimsopaka
    for p in planets:
        p["vimsopaka"] = compute_vimsopaka(p)

    # ── Core references ───────────────────────────────────────────────────────
    asc_sign = feature.asc_sign
    natal_moon_sign = feature.natal_moon_sign
    dasha = feature.dasha.md
    antardasha = feature.dasha.ad

    jupiter_house = next(p["house"] for p in planets if p["name"] == "Jupiter")
    saturn_house = next(p["house"] for p in planets if p["name"] == "Saturn")
    jupiter_lon = next(p["longitude"] for p in planets if p["name"] == "Jupiter")
    saturn_lon = next(p["longitude"] for p in planets if p["name"] == "Saturn")
    jupiter_sign = next(p["sign"] for p in planets if p["name"] == "Jupiter")
    saturn_sign = next(p["sign"] for p in planets if p["name"] == "Saturn")

    # ── Ashtakavarga ──────────────────────────────────────────────────────────
    ashtakavarga = {
        "bav": feature.ashtakavarga.bav,
        "sav_raw": feature.ashtakavarga.sav_raw,
        "sav_trikona": feature.ashtakavarga.sav_trikona,
        "sav_sodhya": feature.ashtakavarga.sav_sodhya,
    }
    av_overlay = micro_transit_overlay(ashtakavarga, jupiter_sign, saturn_sign)

    def _target_lons(reference_sign, target_houses):
        lons = []
        for h in target_houses:
            sign = ((reference_sign + h - 2) % 12) + 1
            lons.append(((sign - 1) * 30) + 15)
        return lons

    # ── Dual reference event scoring (lagna 50% + moon 50%) ───────────────────
    all_target_houses = sorted({h for cfg in EVENT_MAP.values() for h in cfg.get("houses", [])})
    transit_strength = check_event_transit(jupiter_house, saturn_house, all_target_houses) * av_overlay
    transit_orb = event_orb_degree(jupiter_lon, saturn_lon, _target_lons(asc_sign, all_target_houses))
    transit_decay = time_decay_probability(transit_orb, applying=True) / 100

    def _score_events(reference_sign):
        reference_planets = []
        for p in planets:
            rp = dict(p)
            rp["house"] = int((((p["sign"] - reference_sign) % 12) + 1))
            reference_planets.append(rp)

        ref_jupiter_house = next(p["house"] for p in reference_planets if p["name"] == "Jupiter")
        ref_saturn_house = next(p["house"] for p in reference_planets if p["name"] == "Saturn")
        ref_strong_houses = detect_strong_houses(reference_planets)
        ref_chart = {"planets": reference_planets, "strong_houses": ref_strong_houses, "dasha": dasha}

        ref_scores = {}
        for event_name, event_config in EVENT_MAP.items():
            target_houses = event_config.get("houses", [])
            ref_transit_strength = check_event_transit(ref_jupiter_house, ref_saturn_house, target_houses) * av_overlay
            ref_target_lons = _target_lons(reference_sign, target_houses)
            ref_transit_orb = event_orb_degree(jupiter_lon, saturn_lon, ref_target_lons)
            ref_transit_decay = time_decay_probability(ref_transit_orb, applying=True) / 100
            ref_transit = {"strength": ref_transit_strength * ref_transit_decay}
            ref_scores[event_name] = evaluate_event(event_name, ref_chart, ref_transit)

        ref_yoga = evaluate_yogas(reference_planets, reference_sign, SIGN_LORDS, dasha, [ref_jupiter_house, ref_saturn_house])
        for event_name in ref_scores:
            ref_scores[event_name] += ref_yoga["score"]
            if ref_yoga["bhanga"]:
                ref_scores[event_name] *= 0.3
        return ref_scores, ref_yoga

    lagna_scores, lagna_yoga = _score_events(asc_sign)
    moon_scores, moon_yoga = _score_events(natal_moon_sign)

    event_scores = {k: lagna_scores[k] * 0.5 + moon_scores.get(k, 0) * 0.5 for k in lagna_scores}

    yoga_info = {
        "mahapurusha": list(set(lagna_yoga.get("mahapurusha", []) + moon_yoga.get("mahapurusha", []))),
        "dainya": lagna_yoga.get("dainya") or moon_yoga.get("dainya"),
        "dhana": lagna_yoga.get("dhana") or moon_yoga.get("dhana"),
        "bhanga": lagna_yoga.get("bhanga") or moon_yoga.get("bhanga"),
        "score": (lagna_yoga.get("score", 0) + moon_yoga.get("score", 0)) * 0.5,
    }

    # ── Tara scoring ──────────────────────────────────────────────────────────
    janma_nak = feature.janma_nakshatra
    navatara_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    tara_pdata = {
        name: {"nakshatra": next(p["nakshatra"] for p in planets if p["name"] == name)}
        for name in navatara_planets
    }
    tara_raw_score = _calculate_tara_score(janma_nak, tara_pdata)
    tara_score = max(min(tara_raw_score, 10), -10)

    if use_nakshatra_rulebook_bias:
        rulebook_action, rulebook_reason = _get_trade_decision(tara_pdata)
    else:
        rulebook_action, rulebook_reason = "DISABLED", "Nakshatra rulebook bias disabled"

    moon_nak = next(p["nakshatra"] for p in planets if p["name"] == "Moon")
    tara_remainder = _get_tara(janma_nak, moon_nak)

    # ── Nakshatra adjustment ──────────────────────────────────────────────────
    # Only apply empirical GOOD/BAD nakshatra overlay when the scoring profile
    # has nakshatra lists (trading). Non-trading profiles use canonical tara only.
    if _use_nakshatra_overlay:
        factor = nakshatra_adjustment(moon_nak)
    else:
        factor = 1.0  # No empirical overlay for non-trading paths
    for event_name in event_scores:
        event_scores[event_name] *= factor

    # ── Argala + Rahu yogakaraka ──────────────────────────────────────────────
    occupied_houses = [p["house"] for p in planets]
    argala_raw = compute_argala_score(11, occupied_houses)
    rahu_house = next((p["house"] for p in planets if p["name"] == "Rahu"), None)
    if rahu_house is not None:
        argala_raw += reverse_argala_points(rahu_house, occupied_houses)

    # ── Panchang ──────────────────────────────────────────────────────────────
    planets_by_house = {}
    for p in planets:
        planets_by_house.setdefault(p["house"], []).append(p["name"])

    tara_index = (nakshatra_list.index(moon_nak) % 9) + 1
    sun_lon = next(p["longitude"] for p in planets if p["name"] == "Sun")
    moon_lon = next(p["longitude"] for p in planets if p["name"] == "Moon")
    panchang = compute_panchang_score(moon_lon, sun_lon, tara_index, date_obj=eval_date)

    # ── SBC Vedha ─────────────────────────────────────────────────────────────
    retrograde_flags_dict = {p["name"]: p.get("retrograde", False) for p in planets}
    sbc_analysis = evaluate_sbc_vedha(
        planets, janma_nak=janma_nak, tithi=panchang.get("tithi", 1),
        retrograde_flags=retrograde_flags_dict,
    )
    sbc_zones = sbc_analysis.get("zones", {})
    sbc_karma = sbc_zones.get("karma", {})
    sbc_janma = sbc_zones.get("janma", {})
    sbc_malefic_karma_vedha = bool(sbc_karma.get("malefic_vedha", False))
    sbc_malefic_janma_vedha = bool(sbc_janma.get("malefic_vedha", False))
    sbc_malefic_vedha_count = int(sbc_analysis.get("malefic_vedha_count", 0))

    # ── Vedha ─────────────────────────────────────────────────────────────────
    vedha_blocked = is_vedha_blocked(11, 3, planets_by_house, transit_planet="Jupiter")

    # ── Badhakesh ─────────────────────────────────────────────────────────────
    planet_aspects = {
        p["name"]: [int((((aspect_sign - asc_sign) % 12) + 1)) for aspect_sign in get_rasi_drishti(p["sign"])]
        for p in planets
    }
    badhakesh = get_badhakesh(asc_sign, SIGN_LORDS)
    badhakesh_flag = is_badhakesh_active(badhakesh, planet_aspects, [11])

    # ── Longevity / Maraka ────────────────────────────────────────────────────
    asc_lord = SIGN_LORDS[asc_sign]
    asc_lord_sign = next((p["sign"] for p in planets if p["name"] == asc_lord), asc_sign)
    eighth_sign = ((asc_sign + 7 - 1) % 12) + 1
    eighth_lord = SIGN_LORDS[eighth_sign]
    eighth_lord_sign = next((p["sign"] for p in planets if p["name"] == eighth_lord), eighth_sign)
    hora_lagna_sign = ((asc_sign - 1 + (eval_date.hour // 2)) % 12) + 1
    longevity = estimate_jaimini_longevity(asc_lord_sign, eighth_lord_sign, natal_moon_sign, saturn_sign, asc_sign, hora_lagna_sign)

    age_years = eval_date.year - birth_data["date"].year
    maraka_lords = identify_maraka_lords(SIGN_LORDS, asc_sign)
    md_lord_house = next((p["house"] for p in planets if p["name"] == dasha), 0)
    ad_lord_house = next((p["house"] for p in planets if p["name"] == antardasha), 0)
    av_risk = bav_risk(ashtakavarga, planets)

    # ── Risk context ──────────────────────────────────────────────────────────
    risk_context = build_risk_context(
        planets, moon_sign=natal_moon_sign, saturn_sign=saturn_sign,
        sign_lords=SIGN_LORDS, lagna_sign=asc_sign,
        dasha_sandhi=feature.dasha.sandhi_active, av_vulnerability=av_risk,
        maraka_trigger_data={
            "md_lord": dasha, "ad_lord": antardasha, "maraka_lords": maraka_lords,
            "age_years": age_years, "longevity_bracket": longevity["age_bracket"],
            "planet_in_8th": md_lord_house == 8 or ad_lord_house == 8,
        },
    )
    if moon_nak in ["Mrigashira", "Ardra", "Ashlesha", "Jyeshtha", "Dhanishta"]:
        risk_context["tara_risk"] = 20
    if badhakesh_flag:
        risk_context["badhakesh"] = 20
    if vedha_blocked:
        risk_context["gochar_vedha"] = 15
    if panchang["score"] < -15 or (panchang["tithi"] in [4, 9, 14] and panchang["yoga"] in [6, 9, 10, 17]):
        risk_context["panchang_adverse"] = 20 * PANCHANG_RISK_WEIGHT
    risk_context["sbc_vedha"] = 10 if sbc_malefic_karma_vedha else 6 if sbc_malefic_janma_vedha else 0

    # ── Kala Sarpa ────────────────────────────────────────────────────────────
    rahu_lon = next((p["longitude"] for p in planets if p["name"] == "Rahu"), None)
    ketu_lon = (rahu_lon + 180) % 360 if rahu_lon is not None else None
    physical_lons = [p["longitude"] for p in planets if p["name"] in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]]
    kala_sarpa, kala_sarpa_type = (False, None)
    if rahu_lon is not None and ketu_lon is not None:
        kala_sarpa, kala_sarpa_type = detect_kala_sarpa(rahu_lon, ketu_lon, physical_lons)
        if kala_sarpa:
            risk_context["node_crisis"] += 15

    # ── Node yogakaraka bonus ─────────────────────────────────────────────────
    if rahu_house is not None and node_yogakaraka(rahu_house, get_node_aspect_houses(rahu_house)):
        for name in event_scores:
            event_scores[name] += 10

    # ── Risk calculation ──────────────────────────────────────────────────────
    raw_risk_score = calculate_risk(risk_context)
    # Apply tara adjustment to raw risk
    risk_after_tara = round(max(0.0, min(150.0, raw_risk_score - (tara_score * 3))), 2)

    # Apply rulebook delta
    rulebook_risk_delta = 0
    rulebook_confidence_delta = 0
    if rulebook_action == "DO NOT TRADE":
        rulebook_risk_delta = 40
        rulebook_confidence_delta = -30
    elif rulebook_action == "TRADE HEAVILY":
        rulebook_risk_delta = -15
        rulebook_confidence_delta = 25

    risk_after_rulebook = round(max(0.0, min(150.0, risk_after_tara + rulebook_risk_delta)), 2)
    raw_risk = risk_after_rulebook
    # Sqrt normalization
    risk_final = round(math.sqrt(min(raw_risk, 100.0)) * 10, 2)

    # ── Moorthy (AFTER risk, before governance) ───────────────────────────────
    transit_moon_sign = next(p["sign"] for p in planets if p["name"] == "Moon")
    moorthy_name, moorthy_fac = moorthy_grade(natal_moon_sign, transit_moon_sign)
    for event_name in event_scores:
        event_scores[event_name] *= moorthy_fac

    # ── Chandrabala ───────────────────────────────────────────────────────────
    moon_sign_now = next(p["sign"] for p in planets if p["name"] == "Moon")
    chandrabala_count = ((moon_sign_now - natal_moon_sign) % 12) + 1
    chandrabala_eighth = chandrabala_count == 8

    # ── Kakshya ───────────────────────────────────────────────────────────────
    moon_sign_idx = moon_sign_now - 1
    bav_bindus = {
        lord: (ashtakavarga["bav"].get(lord, [0] * 12) or [0] * 12)[moon_sign_idx]
        for lord in ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
    }
    bav_bindus["Ascendant"] = 1
    kakshya = kakshya_trigger(moon_lon, bav_bindus)
    kakshya_cluster = detect_kakshya_cluster(planets, ashtakavarga)

    # ── Yogini ────────────────────────────────────────────────────────────────
    # Need natal moon lon from feature
    natal_moon_lon = None
    # We can compute from natal positions stored in AstronomyResult
    # For now, use the janma nakshatra index * 13.33 as approximation
    # Actually, we stored it in feature pipeline — let's use birth_data directly
    from astronomy.engine_base import get_planet_positions
    import swisseph as swe
    from datetime import timedelta
    birth_utc = birth_data["date"] - timedelta(hours=5, minutes=30)
    birth_jd = swe.julday(birth_utc.year, birth_utc.month, birth_utc.day, birth_utc.hour + birth_utc.minute/60.0)
    natal_positions = get_planet_positions(birth_jd)
    natal_moon_lon = natal_positions["Moon"]

    yogini = get_current_yogini(birth_data["date"], eval_date, natal_moon_lon)
    yogini_factor = yogini_cross_validation(bool(dasha), bool(yogini.get("yd")))

    # ── Chara Dasha ───────────────────────────────────────────────────────────
    chara_current = get_current_chara_dasha(birth_data["date"], eval_date, asc_sign, planets)

    # ── Promise ───────────────────────────────────────────────────────────────
    focal_11 = focal_sign_strength(ashtakavarga, ((asc_sign + 9 - 1) % 12) + 1)
    avg_vims = sum(p["vimsopaka"] for p in planets) / max(len(planets), 1)
    promise_label, promise_strength = classify_vimsopaka_promise(avg_vims)

    # ── Governance ────────────────────────────────────────────────────────────
    event_scores, governance = apply_event_governance(
        event_scores, profile=governance_profile,
        context={"yoga_score": yoga_info.get("score", 0), "transit_strength": transit_strength,
                 "tara_score": tara_score, "age_years": age_years},
        allow_adult_insights=allow_adult_insights,
    )

    # ── Trading event filter ──────────────────────────────────────────────────
    # Only active when explicitly enabled AND the scoring profile is trading.
    if use_trading_event_filter:
        _boost = TRADING_EVENT_BOOST
        _damp = NON_TRADING_EVENT_MULTIPLIER
        if _scoring_profile and _scoring_profile.get("event_filter", {}).get("enabled"):
            _boost = _scoring_profile["event_filter"].get("trading_event_boost", TRADING_EVENT_BOOST)
            _damp = _scoring_profile["event_filter"].get("non_trading_event_multiplier", NON_TRADING_EVENT_MULTIPLIER)
        event_scores = {
            event_name: (
                score * _boost
                if event_name.lower() in TRADING_FOCUSED_EVENTS
                else score * _damp
            )
            for event_name, score in event_scores.items()
        }

    # ── Personality ───────────────────────────────────────────────────────────
    personality_profile = build_personality_profile(planets, asc_sign, birth_data=birth_data)

    # ── Top events ────────────────────────────────────────────────────────────
    top_events = sorted(event_scores.items(), key=lambda x: x[1], reverse=True)[:2]

    # ── Return full context needed by decision_pipeline ───────────────────────
    return {
        "planets": planets,
        "event_scores": event_scores,
        "top_events": top_events,
        "yoga": yoga_info,
        "risk_context": risk_context,
        "risk_final": risk_final,
        "raw_risk": raw_risk,
        "tara_score": tara_score,
        "tara_raw_score": tara_raw_score,
        "tara_remainder": tara_remainder,
        "rulebook_action": rulebook_action,
        "rulebook_reason": rulebook_reason,
        "rulebook_risk_delta": rulebook_risk_delta,
        "rulebook_confidence_delta": rulebook_confidence_delta,
        "nakshatra_factor": factor,
        "moorthy_grade": moorthy_name,
        "moorthy_factor": moorthy_fac,
        "kala_sarpa": kala_sarpa,
        "kala_sarpa_type": kala_sarpa_type,
        "vedha_blocked": vedha_blocked,
        "badhakesh_active": badhakesh_flag,
        "sbc_analysis": sbc_analysis,
        "sbc_malefic_karma_vedha": sbc_malefic_karma_vedha,
        "sbc_malefic_janma_vedha": sbc_malefic_janma_vedha,
        "sbc_malefic_vedha_count": sbc_malefic_vedha_count,
        "kakshya": kakshya,
        "kakshya_cluster": kakshya_cluster,
        "panchang": panchang,
        "chandrabala_count": chandrabala_count,
        "chandrabala_eighth": chandrabala_eighth,
        "yogini": yogini,
        "yogini_factor": yogini_factor,
        "chara_current": chara_current,
        "promise_label": promise_label,
        "focal_11": focal_11,
        "transit_strength": transit_strength,
        "governance": governance,
        "personality_profile": personality_profile,
        "longevity": longevity,
        "ashtakavarga": ashtakavarga,
        "av_risk": av_risk,
        "asc_sign": asc_sign,
        "natal_moon_sign": natal_moon_sign,
        "dasha": dasha,
        "antardasha": antardasha,
    }
