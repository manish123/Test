"""
Rule Pipeline Stage (Layer C orchestration)

Consumes FeatureResult, produces RuleResult.
Applies interpretive rules: state engine, yogas, events, risk, personality.
"""

from contracts.feature_result import FeatureResult
from contracts.rule_result import RuleResult, YogaResult

from features.dignity import SIGN_LORDS
from features.nakshatra import get_nakshatra
from features.houses import detect_strong_houses
from features.ashtakavarga import focal_sign_strength, micro_transit_overlay, bav_risk
from features.transit import check_event_transit, event_orb_degree
from features.time_decay import time_decay_probability

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

from features.rahu_ketu import (
    detect_kala_sarpa,
    get_node_aspect_houses,
    node_yogakaraka,
    reverse_argala_points,
)
from rules.argala import compute_argala_score

from decisions.risk_engine import build_risk_context, calculate_risk


def run_rules(feature: FeatureResult, birth_data: dict, eval_date, config: dict = None) -> RuleResult:
    """
    Execute Layer C: apply interpretive rules to derived features.

    Args:
        feature: FeatureResult from feature pipeline
        birth_data: dict (for personality engine)
        eval_date: datetime of evaluation
        config: optional dict with governance_profile, etc.

    Returns:
        RuleResult (frozen dataclass)
    """
    config = config or {}
    governance_profile = config.get("governance_profile", "professional")
    allow_adult_insights = config.get("allow_adult_insights", False)
    use_trading_event_filter = config.get("use_trading_event_filter", False)
    use_nakshatra_rulebook_bias = config.get("use_nakshatra_rulebook_bias", False)

    # Convert PlanetFeatures back to mutable dicts for state_engine processing
    planets = []
    for pf in feature.planets:
        planets.append({
            "name": pf.name,
            "longitude": pf.longitude,
            "latitude": pf.latitude,
            "sign": pf.sign,
            "nakshatra": pf.nakshatra,
            "status": pf.status,
            "dispositor": pf.dispositor,
            "retrograde": pf.retrograde,
            "house": pf.house,
            "rashi_house": pf.rashi_house,
            "operational_house": pf.operational_house,
            "is_kendra": pf.is_kendra,
            "vimsopaka": pf.vimsopaka,
            "multiplier": 1.0,
        })

    # Process chart states (combustion, retrograde interpretation, graha yuddha)
    by_house = {}
    for p in planets:
        by_house.setdefault(p["house"], []).append(p["name"])
    conjunctions = {
        p["name"]: [x for x in by_house.get(p["house"], []) if x != p["name"]]
        for p in planets
    }
    planets = process_chart_states(planets, {"conjunctions": conjunctions, "datetime": eval_date})

    # Recompute vimsopaka after state processing
    from features.vimsopaka import compute_vimsopaka
    for p in planets:
        p["vimsopaka"] = compute_vimsopaka(p)

    strong_houses = detect_strong_houses(planets)

    # --- Event scoring (dual reference: lagna 50% + moon 50%) ---
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

    # Ashtakavarga from feature
    ashtakavarga = {
        "bav": feature.ashtakavarga.bav,
        "sav_raw": feature.ashtakavarga.sav_raw,
        "sav_trikona": feature.ashtakavarga.sav_trikona,
        "sav_sodhya": feature.ashtakavarga.sav_sodhya,
    }
    av_overlay = micro_transit_overlay(ashtakavarga, jupiter_sign, saturn_sign)

    def _target_lons(reference_sign, target_houses):
        return [((((reference_sign + h - 2) % 12) + 1) - 1) * 30 + 15 for h in target_houses]

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

    yoga_info = YogaResult(
        mahapurusha=list(set(lagna_yoga.get("mahapurusha", []) + moon_yoga.get("mahapurusha", []))),
        dainya=lagna_yoga.get("dainya") or moon_yoga.get("dainya"),
        dhana=lagna_yoga.get("dhana") or moon_yoga.get("dhana"),
        bhanga=lagna_yoga.get("bhanga") or moon_yoga.get("bhanga"),
        score=(lagna_yoga.get("score", 0) + moon_yoga.get("score", 0)) * 0.5,
    )

    # --- Nakshatra adjustment ---
    moon_nak = next(p["nakshatra"] for p in planets if p["name"] == "Moon")
    factor = nakshatra_adjustment(moon_nak)
    for event_name in event_scores:
        event_scores[event_name] *= factor

    # --- Moorthy ---
    transit_moon_sign = next(p["sign"] for p in planets if p["name"] == "Moon")
    moorthy_name, moorthy_fac = moorthy_grade(natal_moon_sign, transit_moon_sign)
    for event_name in event_scores:
        event_scores[event_name] *= moorthy_fac

    # --- Tara ---
    from features.nakshatra import nakshatra_list
    janma_nak = feature.janma_nakshatra
    j_idx = nakshatra_list.index(janma_nak)
    m_idx = nakshatra_list.index(moon_nak)
    tara_count = (m_idx - j_idx) % 27 + 1
    tara_remainder = tara_count % 9
    tara_remainder = 9 if tara_remainder == 0 else tara_remainder

    # --- Kala Sarpa ---
    rahu_lon = next((p["longitude"] for p in planets if p["name"] == "Rahu"), None)
    ketu_lon = (rahu_lon + 180) % 360 if rahu_lon is not None else None
    physical_lons = [p["longitude"] for p in planets if p["name"] in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]]
    kala_sarpa, kala_sarpa_type = (False, None)
    if rahu_lon is not None and ketu_lon is not None:
        kala_sarpa, kala_sarpa_type = detect_kala_sarpa(rahu_lon, ketu_lon, physical_lons)

    # --- Vedha ---
    planets_by_house = {}
    for p in planets:
        planets_by_house.setdefault(p["house"], []).append(p["name"])
    vedha_blocked = is_vedha_blocked(11, 3, planets_by_house, transit_planet="Jupiter")

    # --- Badhakesh ---
    planet_aspects = {
        p["name"]: [int((((aspect_sign - asc_sign) % 12) + 1)) for aspect_sign in get_rasi_drishti(p["sign"])]
        for p in planets
    }
    badhakesh = get_badhakesh(asc_sign, SIGN_LORDS)
    badhakesh_active = is_badhakesh_active(badhakesh, planet_aspects, [11])

    # --- SBC ---
    from features.panchang import compute_panchang_score
    moon_lon_val = next(p["longitude"] for p in planets if p["name"] == "Moon")
    sun_lon_val = next(p["longitude"] for p in planets if p["name"] == "Sun")
    tara_index = (nakshatra_list.index(moon_nak) % 9) + 1
    panchang = compute_panchang_score(moon_lon_val, sun_lon_val, tara_index, date_obj=eval_date)

    retrograde_flags_dict = {p["name"]: p.get("retrograde", False) for p in planets}
    sbc_analysis = evaluate_sbc_vedha(
        planets, janma_nak=janma_nak, tithi=panchang.get("tithi", 1),
        retrograde_flags=retrograde_flags_dict,
    )

    # --- Kakshya ---
    kakshya_data = detect_kakshya_cluster(planets, ashtakavarga)

    # --- Governance ---
    age_years = eval_date.year - birth_data["date"].year
    all_target_houses = sorted({h for cfg in EVENT_MAP.values() for h in cfg.get("houses", [])})
    transit_strength = check_event_transit(jupiter_house, saturn_house, all_target_houses) * av_overlay

    event_scores, governance = apply_event_governance(
        event_scores, profile=governance_profile,
        context={"yoga_score": yoga_info.score, "transit_strength": transit_strength,
                 "tara_score": feature.tara_raw_score, "age_years": age_years},
        allow_adult_insights=allow_adult_insights,
    )

    # --- Personality ---
    personality_profile = build_personality_profile(planets, asc_sign, birth_data=birth_data)

    # --- Risk context ---
    vim_data = {"sandhi_active": feature.dasha.sandhi_active}
    av_risk = bav_risk(ashtakavarga, planets)
    asc_lord = SIGN_LORDS[asc_sign]
    asc_lord_sign = next((p["sign"] for p in planets if p["name"] == asc_lord), asc_sign)
    eighth_sign = ((asc_sign + 7 - 1) % 12) + 1
    eighth_lord = SIGN_LORDS[eighth_sign]
    eighth_lord_sign = next((p["sign"] for p in planets if p["name"] == eighth_lord), eighth_sign)
    hora_lagna_sign = ((asc_sign - 1 + (eval_date.hour // 2)) % 12) + 1
    longevity = estimate_jaimini_longevity(asc_lord_sign, eighth_lord_sign, natal_moon_sign, saturn_sign, asc_sign, hora_lagna_sign)
    maraka_lords = identify_maraka_lords(SIGN_LORDS, asc_sign)
    md_lord_house = next((p["house"] for p in planets if p["name"] == dasha), 0)
    ad_lord_house = next((p["house"] for p in planets if p["name"] == antardasha), 0)

    risk_context = build_risk_context(
        planets, moon_sign=natal_moon_sign, saturn_sign=saturn_sign,
        sign_lords=SIGN_LORDS, lagna_sign=asc_sign,
        dasha_sandhi=vim_data["sandhi_active"], av_vulnerability=av_risk,
        maraka_trigger_data={
            "md_lord": dasha, "ad_lord": antardasha, "maraka_lords": maraka_lords,
            "age_years": age_years, "longevity_bracket": longevity["age_bracket"],
            "planet_in_8th": md_lord_house == 8 or ad_lord_house == 8,
        },
    )

    if kala_sarpa:
        risk_context["node_crisis"] += 15
    if badhakesh_active:
        risk_context["badhakesh"] = 20
    if vedha_blocked:
        risk_context["gochar_vedha"] = 15

    # Sort events
    top_events = sorted(event_scores.items(), key=lambda x: x[1], reverse=True)[:2]

    return RuleResult(
        event_scores=event_scores,
        top_events=top_events,
        yoga=yoga_info,
        risk_context=risk_context,
        risk_score=calculate_risk(risk_context),
        nakshatra_factor=factor,
        moorthy_grade=moorthy_name,
        moorthy_factor=moorthy_fac,
        tara_score=feature.tara_raw_score,
        tara_remainder=tara_remainder,
        kala_sarpa=kala_sarpa,
        kala_sarpa_type=kala_sarpa_type,
        vedha_blocked=vedha_blocked,
        badhakesh_active=badhakesh_active,
        sbc_analysis=sbc_analysis,
        kakshya={},
        kakshya_cluster=kakshya_data,
        governance=governance,
        personality_profile=personality_profile,
        longevity=longevity,
    )
