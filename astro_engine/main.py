# Layer A — Astronomy (pure ephemeris, math, coordinates)
from astronomy.engine_base import get_planet_positions, get_planet_latitudes, get_retrograde_flags
from astronomy.birth_data import get_birth_data
from astronomy.utils import normalize_lon

# Layer B — Classical Feature Extraction (deterministic astrology transforms)
from features.dignity import SIGN_LORDS
from features.divisional import classify_vimsopaka_promise
from features.planet_builder import build_planet
from features.nakshatra import get_nakshatra, nakshatra_list
from features.houses import get_houses, get_planet_house, detect_strong_houses, get_operational_house
from features.vimsopaka import compute_vimsopaka
from features.ashtakavarga import compute_ashtakavarga, focal_sign_strength, micro_transit_overlay, bav_risk
from features.dasha import get_current_vimshottari
from features.chara_dasha import get_chara_dasha_sequence, get_current_chara_dasha
from features.yogini import yogini_cross_validation, get_current_yogini
from features.transit import check_event_transit, event_orb_degree
from features.time_decay import time_decay_probability
from features.rahu_ketu import (
    detect_kala_sarpa,
    get_node_aspect_houses,
    node_yogakaraka,
    reverse_argala_points,
)
from features.panchang import compute_panchang_score

# Layer C — Interpretive Rules (combinatorial logic, rule firing)
from rules.state_engine import process_chart_states
from rules.argala import compute_argala_score
from rules.arudha import compute_arudha_pada
from rules.rasi_drishti import get_rasi_drishti
from rules.vedha import is_vedha_blocked
from rules.sbc import evaluate_sbc_vedha
from rules.badhakesh import is_badhakesh_active, get_badhakesh
from rules.event_engine import evaluate_event, EVENT_MAP
from rules.governance import apply_event_governance
from rules.yoga_engine import evaluate_yogas
from rules.nakshatra_weight import nakshatra_adjustment
from rules.kakshya import kakshya_trigger, detect_kakshya_cluster
from rules.moorthy import moorthy_grade
from rules.longevity import estimate_jaimini_longevity
from rules.maraka import identify_maraka_lords
from rules.personality_engine import build_personality_profile

# Layer D — Scoring & Governance (final decisions, no ephemeris math)
from decisions.decision_engine import generate_decision
from decisions.trading_gate import evaluate_trading_gate, evaluate_asset_timeline_events, TRADING_FOCUSED_EVENTS
from decisions.feedback import build_mode_c_alignment_feedback
try:
    from decisions.confidence_calibration import apply_confidence_calibration
except ImportError:
    def apply_confidence_calibration(v, _):
        return v
from decisions.risk_engine import build_risk_context, calculate_risk
from decisions.confidence import confidence_score
from decisions.normalization import normalize_event_scores, normalize_top_events
from decisions.priority import rank_events
import swisseph as swe
from datetime import datetime, timedelta
import math

# ── Shared tara scoring (Phase 1 refactor) ────────────────────────────────────
from rules.evaluator_base import (
    TARA_SCORES, PLANET_WEIGHTS,
    PANCHANG_RISK_WEIGHT, TRADING_EVENT_BOOST, NON_TRADING_EVENT_MULTIPLIER,
    get_tara, calculate_tara_score, get_trade_decision,
)
# Compatibility aliases — call-sites in this file use these names
calculate_score = calculate_tara_score  # main.py used calculate_score; base uses calculate_tara_score


def ist_to_utc(dt):
    return dt - timedelta(hours=5, minutes=30)


def _moon_nakshatra_at(dt_ist):
    dt_utc = ist_to_utc(dt_ist)
    jd = swe.julday(
        dt_utc.year,
        dt_utc.month,
        dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0,
    )
    moon_lon = get_planet_positions(jd)["Moon"]
    return get_nakshatra(moon_lon)


def _refine_moon_transition(t1, t2, old_nak):
    while (t2 - t1).total_seconds() > 60:
        mid = t1 + (t2 - t1) / 2
        if _moon_nakshatra_at(mid) == old_nak:
            t1 = mid
        else:
            t2 = mid
    return t2


def _find_moon_transitions_for_day(day_dt):
    start = datetime(day_dt.year, day_dt.month, day_dt.day, 0, 0)
    end = datetime(day_dt.year, day_dt.month, day_dt.day, 23, 59)
    step = timedelta(minutes=30)

    transitions = []
    prev_nak = _moon_nakshatra_at(start)
    t = start

    while t <= end:
        curr_nak = _moon_nakshatra_at(t)
        if curr_nak != prev_nak:
            exact = _refine_moon_transition(t - step, t, prev_nak)
            transitions.append((exact, curr_nak))
            prev_nak = curr_nak
        t += step

    return transitions


def _build_day_segments(day_dt):
    transitions = _find_moon_transitions_for_day(day_dt)
    segments = []

    seg_start = datetime(day_dt.year, day_dt.month, day_dt.day, 0, 0)
    for t, _ in transitions:
        segments.append((seg_start, t))
        seg_start = t

    day_end = datetime(day_dt.year, day_dt.month, day_dt.day, 23, 59)
    segments.append((seg_start, day_end))
    return segments


def _run_single(
    date,
    birth_data,
    location_override=None,
    location_mode="birth",
    governance_profile="professional",
    # ──────────────────────────────────────────────────────────────────────────
    # DEPRECATION NOTICE (v2.0.0, 2026-05-22)
    #
    # This function is DEPRECATED. Use the pipeline path instead:
    #
    #   from pipeline import run_astronomy, run_features, run_rules, run_decisions
    #   astro    = run_astronomy(date, birth_data)
    #   features = run_features(astro, birth_data, date)
    #   rules    = run_rules(features, birth_data, date, config)
    #   decision = run_decisions(rules, config)
    #
    # Or via api_bridges:
    #   from api_bridges.timing_bridge import get_timing_data
    #   result = get_timing_data(birth_data, date, domain="trading")
    #
    # Parity verified: pipeline produces identical output (10/10 exact match).
    # This function will be removed after one release window (v2.1.0).
    # ──────────────────────────────────────────────────────────────────────────
    allow_adult_insights=False,
    use_nakshatra_rulebook_bias=False,
    use_trading_gate=False,
    use_trading_event_filter=False,
    use_asset_timeline_events=False,
    trading_gate_profile="strict",
    confidence_calibration=None,
):
    birth = birth_data

    birth_utc = ist_to_utc(birth["date"])
    birth_jd = swe.julday(
        birth_utc.year,
        birth_utc.month,
        birth_utc.day,
        birth_utc.hour + birth_utc.minute / 60.0,
    )
    birth_positions = get_planet_positions(birth_jd)

    date_utc = ist_to_utc(date)
    jd = swe.julday(
        date_utc.year,
        date_utc.month,
        date_utc.day,
        date_utc.hour + date_utc.minute / 60.0,
    )

    mode = (location_mode or "birth").lower()
    if mode == "birth":
        lat, lon = birth["lat"], birth["lon"]
    elif mode == "current":
        if not location_override:
            raise ValueError("location_override is required when location_mode='current'")
        lat, lon = location_override["lat"], location_override["lon"]
    else:
        lat = location_override["lat"] if location_override else birth["lat"]
        lon = location_override["lon"] if location_override else birth["lon"]

    raw_positions = get_planet_positions(jd)
    raw_latitudes = get_planet_latitudes(jd)
    retrograde_flags = get_retrograde_flags(jd)

    house_data = get_houses(jd, lat, lon)
    asc_sign = int(normalize_lon(house_data["ascendant"]) // 30) + 1
    natal_moon_sign = int(normalize_lon(birth_positions["Moon"]) // 30) + 1

    planets = []

    for name, lon in raw_positions.items():
        p = build_planet(name, lon, retro=retrograde_flags.get(name, False))
        p["latitude"] = raw_latitudes.get(name)
        p["nakshatra"] = get_nakshatra(lon)
        rashi_house = int((((p["sign"] - asc_sign) % 12) + 1))
        chalit_house = get_planet_house(p["longitude"], house_data["houses"])
        p["rashi_house"] = rashi_house
        p["house"] = chalit_house
        p["is_kendra"] = chalit_house in [1, 4, 7, 10]
        p["operational_house"] = get_operational_house(p["longitude"], house_data["houses"], rashi_house)
        planets.append(p)

    by_house = {}
    for p in planets:
        by_house.setdefault(p["house"], []).append(p["name"])
    conjunctions = {p["name"]: [x for x in by_house.get(p["house"], []) if x != p["name"]] for p in planets}

    planets = process_chart_states(planets, {"conjunctions": conjunctions, "datetime": date})

    for p in planets:
        p["vimsopaka"] = compute_vimsopaka(p)

    planet_signs = {p["name"]: p["sign"] for p in planets if p["name"] in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]}
    ashtakavarga = compute_ashtakavarga(planet_signs, asc_sign=asc_sign)

    strong_houses = detect_strong_houses(planets)

    vim = get_current_vimshottari(birth["date"], date, birth_positions["Moon"])
    dasha = vim["md"]
    antardasha = vim["ad"]

    jupiter_house = next(p["house"] for p in planets if p["name"] == "Jupiter")
    saturn_house = next(p["house"] for p in planets if p["name"] == "Saturn")
    jupiter_lon = next(p["longitude"] for p in planets if p["name"] == "Jupiter")
    saturn_lon = next(p["longitude"] for p in planets if p["name"] == "Saturn")
    jupiter_sign = next(p["sign"] for p in planets if p["name"] == "Jupiter")
    saturn_sign = next(p["sign"] for p in planets if p["name"] == "Saturn")

    def _target_lons(reference_sign, target_houses):
        lons = []
        for h in target_houses:
            sign = ((reference_sign + h - 2) % 12) + 1
            lons.append(((sign - 1) * 30) + 15)
        return lons

    av_overlay = micro_transit_overlay(ashtakavarga, jupiter_sign, saturn_sign)
    all_target_houses = sorted({h for cfg in EVENT_MAP.values() for h in cfg.get("houses", [])})
    transit_strength = check_event_transit(jupiter_house, saturn_house, all_target_houses) * av_overlay
    transit_orb = event_orb_degree(jupiter_lon, saturn_lon, _target_lons(asc_sign, all_target_houses))
    transit_decay = time_decay_probability(transit_orb, applying=True) / 100

    chart = {
        "planets": planets,
        "strong_houses": strong_houses,
        "dasha": dasha,
    }

    def _score_events(reference_sign):
        reference_planets = []
        for p in planets:
            rp = dict(p)
            rp["house"] = int((((p["sign"] - reference_sign) % 12) + 1))
            reference_planets.append(rp)

        ref_jupiter_house = next(p["house"] for p in reference_planets if p["name"] == "Jupiter")
        ref_saturn_house = next(p["house"] for p in reference_planets if p["name"] == "Saturn")
        ref_strong_houses = detect_strong_houses(reference_planets)

        ref_chart = {
            "planets": reference_planets,
            "strong_houses": ref_strong_houses,
            "dasha": dasha,
        }
        ref_scores = {}
        for event_name, config in EVENT_MAP.items():
            target_houses = config.get("houses", [])
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

    event_scores = {}
    for key in lagna_scores:
        event_scores[key] = lagna_scores[key] * 0.5 + moon_scores.get(key, 0) * 0.5

    yoga_info = {
        "mahapurusha": list(set(lagna_yoga.get("mahapurusha", []) + moon_yoga.get("mahapurusha", []))),
        "dainya": lagna_yoga.get("dainya") or moon_yoga.get("dainya"),
        "dhana": lagna_yoga.get("dhana") or moon_yoga.get("dhana"),
        "bhanga": lagna_yoga.get("bhanga") or moon_yoga.get("bhanga"),
        "score": (lagna_yoga.get("score", 0) + moon_yoga.get("score", 0)) * 0.5,
    }

    navatara_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    tara_pdata = {
        name: {"nakshatra": next(p["nakshatra"] for p in planets if p["name"] == name)}
        for name in navatara_planets
    }
    janma_nak = get_nakshatra(birth_positions["Moon"])
    tara_raw_score = calculate_score(janma_nak, tara_pdata)
    tara_score = max(min(tara_raw_score, 10), -10)
    if use_nakshatra_rulebook_bias:
        rulebook_action, rulebook_reason = get_trade_decision(tara_pdata)
    else:
        rulebook_action, rulebook_reason = "DISABLED", "Nakshatra rulebook bias disabled"

    moon_nak = next(p["nakshatra"] for p in planets if p["name"] == "Moon")
    tara_remainder = get_tara(janma_nak, moon_nak)

    # Nakshatra adjustment: only apply empirical GOOD/BAD overlay when trading
    # event filter is active (trading path). Non-trading paths use factor=1.0.
    if use_trading_event_filter:
        factor = nakshatra_adjustment(moon_nak)
    else:
        factor = 1.0

    for event_name in event_scores:
        event_scores[event_name] *= factor

    occupied_houses = [p["house"] for p in planets]
    argala_raw = compute_argala_score(11, occupied_houses)
    rahu_house = next((p["house"] for p in planets if p["name"] == "Rahu"), None)
    if rahu_house is not None:
        argala_raw += reverse_argala_points(rahu_house, occupied_houses)
    argala_factor = 1 if argala_raw > 0 else 0 if argala_raw == 0 else -1

    planets_by_house = {}
    for p in planets:
        planets_by_house.setdefault(p["house"], []).append(p["name"])

    tara_index = (nakshatra_list.index(moon_nak) % 9) + 1
    sun_lon = next(p["longitude"] for p in planets if p["name"] == "Sun")
    moon_lon = next(p["longitude"] for p in planets if p["name"] == "Moon")
    panchang = compute_panchang_score(moon_lon, sun_lon, tara_index, date_obj=date)

    sbc_analysis = evaluate_sbc_vedha(
        planets,
        janma_nak=janma_nak,
        tithi=panchang.get("tithi", 1),
        retrograde_flags=retrograde_flags,
    )
    sbc_zones = sbc_analysis.get("zones", {})
    sbc_karma = sbc_zones.get("karma", {})
    sbc_janma = sbc_zones.get("janma", {})
    sbc_malefic_karma_vedha = bool(sbc_karma.get("malefic_vedha", False))
    sbc_malefic_janma_vedha = bool(sbc_janma.get("malefic_vedha", False))
    sbc_malefic_vedha_count = int(sbc_analysis.get("malefic_vedha_count", 0))

    vedha_blocked = is_vedha_blocked(11, 3, planets_by_house, transit_planet="Jupiter")
    vedha_clear = 0 if vedha_blocked else 1

    planet_aspects = {
        p["name"]: [int((((aspect_sign - asc_sign) % 12) + 1)) for aspect_sign in get_rasi_drishti(p["sign"])]
        for p in planets
    }
    badhakesh = get_badhakesh(asc_sign, SIGN_LORDS)
    badhakesh_flag = is_badhakesh_active(badhakesh, planet_aspects, [11])

    asc_lord = SIGN_LORDS[asc_sign]
    asc_lord_sign = next((p["sign"] for p in planets if p["name"] == asc_lord), asc_sign)
    eighth_sign = ((asc_sign + 7 - 1) % 12) + 1
    eighth_lord = SIGN_LORDS[eighth_sign]
    eighth_lord_sign = next((p["sign"] for p in planets if p["name"] == eighth_lord), eighth_sign)
    hora_lagna_sign = ((asc_sign - 1 + (date.hour // 2)) % 12) + 1
    longevity = estimate_jaimini_longevity(
        asc_lord_sign,
        eighth_lord_sign,
        natal_moon_sign,
        saturn_sign,
        asc_sign,
        hora_lagna_sign,
    )

    age_years = date.year - birth["date"].year
    maraka_lords = identify_maraka_lords(SIGN_LORDS, asc_sign)
    md_lord_house = next((p["house"] for p in planets if p["name"] == dasha), 0)
    ad_lord_house = next((p["house"] for p in planets if p["name"] == antardasha), 0)

    av_risk = bav_risk(ashtakavarga, planets)

    risk_context = build_risk_context(
        planets,
        moon_sign=natal_moon_sign,
        saturn_sign=saturn_sign,
        sign_lords=SIGN_LORDS,
        lagna_sign=asc_sign,
        dasha_sandhi=vim["sandhi_active"],
        av_vulnerability=av_risk,
        maraka_trigger_data={
            "md_lord": dasha,
            "ad_lord": antardasha,
            "maraka_lords": maraka_lords,
            "age_years": age_years,
            "longevity_bracket": longevity["age_bracket"],
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

    rahu_lon = next((p["longitude"] for p in planets if p["name"] == "Rahu"), None)
    ketu_lon = (rahu_lon + 180) % 360 if rahu_lon is not None else None
    physical_lons = [p["longitude"] for p in planets if p["name"] in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]]
    kala_sarpa, kala_sarpa_type = (False, None)
    if rahu_lon is not None and ketu_lon is not None:
        kala_sarpa, kala_sarpa_type = detect_kala_sarpa(rahu_lon, ketu_lon, physical_lons)
        if kala_sarpa:
            risk_context["node_crisis"] += 15

    if rahu_house is not None and node_yogakaraka(rahu_house, get_node_aspect_houses(rahu_house)):
        for name in event_scores:
            event_scores[name] += 10

    risk = calculate_risk(risk_context)
    risk = round(max(0.0, min(150.0, risk - (tara_score * 3))), 2)

    rulebook_risk_delta = 0
    rulebook_confidence_delta = 0
    if rulebook_action == "DO NOT TRADE":
        rulebook_risk_delta = 40
        rulebook_confidence_delta = -30
    elif rulebook_action == "TRADE HEAVILY":
        rulebook_risk_delta = -15
        rulebook_confidence_delta = 25

    risk = round(max(0.0, min(150.0, risk + rulebook_risk_delta)), 2)
    raw_risk = risk
    risk = round(math.sqrt(min(raw_risk, 100.0)) * 10, 2)

    transit_moon_sign = next(p["sign"] for p in planets if p["name"] == "Moon")
    moorthy_name, moorthy_factor = moorthy_grade(natal_moon_sign, transit_moon_sign)
    for event_name in event_scores:
        event_scores[event_name] *= moorthy_factor

    moon_sign_now = next(p["sign"] for p in planets if p["name"] == "Moon")
    chandrabala_count = ((moon_sign_now - natal_moon_sign) % 12) + 1
    chandrabala_eighth = chandrabala_count == 8

    natal_mars_sign = int(normalize_lon(birth_positions["Mars"]) // 30) + 1
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

    mars_house_from_natal = ((mars_sign_now - natal_mars_sign) % 12) + 1
    saturn_house_from_natal_moon = ((saturn_sign - natal_moon_sign) % 12) + 1

    venus_lon = next(p["longitude"] for p in planets if p["name"] == "Venus")
    venus_bav_bindus = {
        "Saturn": ashtakavarga["bav"].get("Saturn", [0] * 12)[venus_sign_now - 1],
        "Jupiter": ashtakavarga["bav"].get("Jupiter", [0] * 12)[venus_sign_now - 1],
        "Mars": ashtakavarga["bav"].get("Mars", [0] * 12)[venus_sign_now - 1],
        "Sun": ashtakavarga["bav"].get("Sun", [0] * 12)[venus_sign_now - 1],
        "Venus": ashtakavarga["bav"].get("Venus", [0] * 12)[venus_sign_now - 1],
        "Mercury": ashtakavarga["bav"].get("Mercury", [0] * 12)[venus_sign_now - 1],
        "Moon": ashtakavarga["bav"].get("Moon", [0] * 12)[venus_sign_now - 1],
        "Ascendant": 1,
    }
    venus_kakshya_active = kakshya_trigger(venus_lon, venus_bav_bindus).get("active", False)
    bav_bindus = {
        "Saturn": ashtakavarga["bav"].get("Saturn", [0] * 12)[moon_sign_now - 1],
        "Jupiter": ashtakavarga["bav"].get("Jupiter", [0] * 12)[moon_sign_now - 1],
        "Mars": ashtakavarga["bav"].get("Mars", [0] * 12)[moon_sign_now - 1],
        "Sun": ashtakavarga["bav"].get("Sun", [0] * 12)[moon_sign_now - 1],
        "Venus": ashtakavarga["bav"].get("Venus", [0] * 12)[moon_sign_now - 1],
        "Mercury": ashtakavarga["bav"].get("Mercury", [0] * 12)[moon_sign_now - 1],
        "Moon": ashtakavarga["bav"].get("Moon", [0] * 12)[moon_sign_now - 1],
        "Ascendant": 1,
    }
    kakshya = kakshya_trigger(moon_lon, bav_bindus)
    kakshya_cluster = detect_kakshya_cluster(planets, ashtakavarga)
    yogini = get_current_yogini(birth["date"], date, birth_positions["Moon"])
    yogini_factor = yogini_cross_validation(bool(dasha), bool(yogini.get("yd")))

    focal_11 = focal_sign_strength(ashtakavarga, ((asc_sign + 9 - 1) % 12) + 1)
    avg_vims = sum(p["vimsopaka"] for p in planets) / max(len(planets), 1)
    promise_label, promise_strength = classify_vimsopaka_promise(avg_vims)

    arudha_lagna = compute_arudha_pada(asc_sign, asc_lord_sign)
    rasi_drishti = get_rasi_drishti(asc_sign)
    chara_sequence = get_chara_dasha_sequence(asc_sign, planets)
    chara_current = get_current_chara_dasha(birth["date"], date, asc_sign, planets)
    personality_profile = build_personality_profile(planets, asc_sign, birth_data=birth)
    event_scores, governance = apply_event_governance(
        event_scores,
        profile=governance_profile,
        context={
            "yoga_score": yoga_info.get("score", 0),
            "transit_strength": transit_strength,
            "tara_score": tara_score,
            "age_years": age_years,
        },
        allow_adult_insights=allow_adult_insights,
    )

    if use_trading_event_filter:
        event_scores = {
            event_name: (
                score * TRADING_EVENT_BOOST
                if event_name.lower() in TRADING_FOCUSED_EVENTS
                else score * NON_TRADING_EVENT_MULTIPLIER
            )
            for event_name, score in event_scores.items()
        }

    normalized_event_scores = normalize_event_scores(event_scores)
    top_events = rank_events(event_scores)
    top_events_normalized = normalize_top_events(top_events, normalized_event_scores)
    top_event_name, top_event_score = top_events[0]

    event_strength = min(80, top_event_score * 0.5)  # Raised cap from 60 to 80
    yoga_component = max(0, min(25, yoga_info.get("score", 0) + 5))
    top_event_planets = EVENT_MAP.get(top_event_name, {}).get("planets", [])
    top_event_houses = EVENT_MAP.get(top_event_name, {}).get("houses", [])
    double_transit_strength = check_event_transit(jupiter_house, saturn_house, top_event_houses)

    second_sign = (asc_sign % 12) + 1
    tenth_sign = ((asc_sign + 8 - 1) % 12) + 1
    eleventh_sign = ((asc_sign + 9 - 1) % 12) + 1
    dasha_lords_2_10_11 = {
        SIGN_LORDS[second_sign],
        SIGN_LORDS[tenth_sign],
        SIGN_LORDS[eleventh_sign],
    }
    dasha_lord_gate = dasha in dasha_lords_2_10_11 or antardasha in dasha_lords_2_10_11

    dasha_planets = [p for p in planets if p["name"] in {dasha, antardasha}]
    vargottama_dasha_proxy = any(p.get("vimsopaka", 0) >= 16 for p in dasha_planets)
    dasha_component = 20 if dasha in top_event_planets else 12
    if antardasha in top_event_planets:
        dasha_component += 5
    if yogini.get("yd") in top_event_planets:
        dasha_component += 4
    if chara_current.get("lord") in top_event_planets:
        dasha_component += 6
    dasha_component = min(35, dasha_component)

    confidence = confidence_score(
        {
            "event_strength": event_strength,
            "yoga": yoga_component,
            "dasha": dasha_component,
            "promise": promise_label,
            "kakshya_active": kakshya.get("active", False),
        },
        penalties={
            "risk": risk,
        },
    )
    confidence = round(max(0.0, min(100.0, confidence * yogini_factor * yogini.get("sandhi_confidence_multiplier", 1.0))), 2)
    if chara_current.get("sandhi_active"):
        confidence = round(max(0.0, min(100.0, confidence * 0.9)), 2)
    # Tara multiplier reduced from 5 to 3 — less aggressive swing (±30 instead of ±50)
    # Rulebook delta reduced from ±25/30 to ±15 — less coarse override
    tara_confidence_boost = tara_score * 3
    rulebook_confidence_adj = round(rulebook_confidence_delta * 0.6, 1)  # ±25→±15, ±30→±18
    confidence = round(max(0.0, min(100.0, confidence + tara_confidence_boost + rulebook_confidence_adj)), 2)
    if kakshya.get("active", False):
        confidence = round(max(0.0, min(100.0, confidence + 10)), 2)
    # Apply yogini factor AFTER all adjustments for consistent scaling
    confidence = round(max(0.0, min(100.0, confidence * yogini_factor)), 2)
    confidence_calibrated = round(
        max(0.0, min(100.0, apply_confidence_calibration(confidence, confidence_calibration))),
        2,
    )

    conflict_flag = tara_score > 7 and rulebook_action == "DO NOT TRADE"

    decision = generate_decision(top_events, risk, confidence_calibrated, av_vulnerability=av_risk)
    decision["confidence_raw"] = confidence
    decision["confidence_calibrated"] = confidence_calibrated
    if conflict_flag:
        decision["action"] = "LOW SIZE / TEST TRADE"
        decision["phase"] = "TARA_RULEBOOK_CONFLICT"
    elif tara_score > 7 and confidence_calibrated > 60 and risk < 40:
        decision["action"] = "AGGRESSIVE"
        decision["phase"] = "FINAL_FRAMEWORK_AGGRESSIVE"
    elif tara_score < 0 and confidence_calibrated < 20 and risk > 80:
        decision["action"] = "AVOID"
        decision["phase"] = "FINAL_FRAMEWORK_AVOID"

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
        "tara_remainder": tara_remainder,
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

    if use_trading_gate:
        trading_gate = evaluate_trading_gate(trading_context)
        if trading_gate["overall_status"] == "BLOCK":
            decision["action"] = "AVOID"
            decision["phase"] = "TRADING_GATE_BLOCK"
        elif trading_gate["overall_status"] == "CAUTION" and decision["action"] in {
            "GO FULL",
            "AGGRESSIVE",
            "CONTROLLED AGGRESSION",
        }:
            decision["action"] = "LOW SIZE / WAIT"
            decision["phase"] = "TRADING_GATE_CAUTION"

        trading_gate_profile_lc = str(trading_gate_profile or "").strip().lower()
        adaptive_lite_plus_enabled = trading_gate_profile_lc in {
            "adaptive_lite_plus",
            "adaptive_plus",
            "adaptive_profile_22071975_plus",
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
    else:
        trading_gate = {
            "enabled": False,
            "overall_status": "DISABLED",
            "score": None,
            "suggested_action": None,
            "levels": {},
        }

    asset_events = evaluate_asset_timeline_events(trading_context) if use_asset_timeline_events else []

    time_window = {
        "decay_probability": round(transit_decay, 4),
        "transit_orb": round(transit_orb, 2),
        "kakshya": kakshya,
        "kakshya_cluster": kakshya_cluster,
        "panchang_score": panchang["score"],
        "window_hint": kakshya.get("window_days") if kakshya.get("active") else "No active kakshya window",
    }

    panchang_weather = {
        "tithi": panchang["tithi"],
        "karana_status": "restrictive" if panchang["score"] < 0 else "clear",
        "yoga_quality": "dangerous" if panchang["yoga"] in [6, 9, 10, 17] else "favorable",
        "score": panchang["score"],
    }

    return {
        "planets": planets,
        "dasha": {"md": dasha, "ad": antardasha, "sandhi": vim["sandhi_active"]},
        "yogini": yogini,
        "chara_dasha": chara_sequence,
        "chara_current": chara_current,
        "promise": promise_label,
        "event_scores": event_scores,
        "event_scores_normalized": normalized_event_scores,
        "top_events": top_events,
        "top_events_normalized": top_events_normalized,
        "panchang": panchang,
        "panchang_weather": panchang_weather,
        "moorthy": {"grade": moorthy_name, "factor": moorthy_factor},
        "kakshya": kakshya,
        "time_window": time_window,
        "ashtakavarga": {
            "sav_11": focal_11,
            "overlay": av_overlay,
        },
        "yoga": yoga_info,
        "jaimini": {
            "arudha_lagna": arudha_lagna,
            "rasi_drishti": rasi_drishti,
            "longevity": longevity,
        },
        "nodes": {
            "kala_sarpa": kala_sarpa,
            "kala_sarpa_type": kala_sarpa_type,
        },
        "governance": governance,
        "tara": {
            "janma_nakshatra": janma_nak,
            "raw_score": tara_raw_score,
            "score": tara_score,
            "rulebook_action": rulebook_action,
            "rulebook_reason": rulebook_reason,
            "rulebook_risk_delta": rulebook_risk_delta,
            "rulebook_confidence_delta": rulebook_confidence_delta,
            "conflict_flag": conflict_flag,
            "panchang_risk_weight": PANCHANG_RISK_WEIGHT,
            "raw_risk": raw_risk,
        },
        "personality_profile": personality_profile,
        "risk_context": risk_context,
        "sbc_analysis": sbc_analysis,
        "kakshya_cluster": kakshya_cluster,
        "asset_events": asset_events,
        "trading_event_filter": {
            "enabled": use_trading_event_filter,
            "trading_event_boost": TRADING_EVENT_BOOST if use_trading_event_filter else None,
            "non_trading_event_multiplier": NON_TRADING_EVENT_MULTIPLIER if use_trading_event_filter else None,
            "focus_events": sorted(TRADING_FOCUSED_EVENTS) if use_trading_event_filter else [],
        },
        "trading_gate": trading_gate,
        "decision": decision,
    }


def _safe_anniversary(base_dt, year):
    try:
        return base_dt.replace(year=year)
    except ValueError:
        return base_dt.replace(year=year, day=min(base_dt.day, 28))


def run(
    mode="C",
    date=None,
    start_year=None,
    end_year=None,
    days_ahead=3,
    birth_data=None,
    location_override=None,
    location_mode="birth",
    governance_profile="professional",
    allow_adult_insights=False,
    feedback_pnl_csv=None,
    use_nakshatra_rulebook_bias=False,
    use_trading_gate=False,
    use_trading_event_filter=False,
    use_asset_timeline_events=False,
    trading_gate_profile="strict",
    confidence_calibration=None,
):
    if isinstance(mode, datetime):
        date = mode
        mode = "C"
        days_ahead = 0

    mode = (mode or "C").upper()

    if mode == "A":
        birth = birth_data or get_birth_data()
        profile_date = birth["date"]
        result = _run_single(
            profile_date,
            birth,
            location_override=location_override,
            location_mode=location_mode,
            governance_profile=governance_profile,
            allow_adult_insights=allow_adult_insights,
            use_nakshatra_rulebook_bias=use_nakshatra_rulebook_bias,
            use_trading_gate=use_trading_gate,
            use_trading_event_filter=use_trading_event_filter,
            use_asset_timeline_events=use_asset_timeline_events,
            trading_gate_profile=trading_gate_profile,
            confidence_calibration=confidence_calibration,
        )
        return {
            "mode": "A",
            "date": profile_date.isoformat(),
            "subject": {
                "birth_datetime": birth["date"].isoformat(),
                "birth_date": birth["date"].date().isoformat(),
                "birth_time": birth["date"].time().isoformat(timespec="seconds"),
                "latitude": birth["lat"],
                "longitude": birth["lon"],
            },
            "personality_profile": result["personality_profile"],
            "jaimini": result["jaimini"],
            "sun_moon_balance": result["personality_profile"].get("solar_lunar", {}),
        }

    if mode == "B":
        birth = birth_data or get_birth_data()
        base = birth["date"]
        start = start_year or base.year
        end = end_year or (base.year + 90)

        yearly = []
        for year in range(start, end + 1):
            eval_date = _safe_anniversary(base, year)
            result = _run_single(
                eval_date,
                birth,
                location_override=location_override,
                location_mode=location_mode,
                governance_profile=governance_profile,
                allow_adult_insights=allow_adult_insights,
                use_nakshatra_rulebook_bias=use_nakshatra_rulebook_bias,
                use_trading_gate=use_trading_gate,
                use_trading_event_filter=use_trading_event_filter,
                use_asset_timeline_events=use_asset_timeline_events,
                trading_gate_profile=trading_gate_profile,
                confidence_calibration=confidence_calibration,
            )
            active_risk_factors = {
                k: v
                for k, v in result.get("risk_context", {}).items()
                if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0
            }
            yearly.append(
                {
                    "year": year,
                    "date": eval_date.isoformat(),
                    "dasha": result["dasha"],
                    "promise": result.get("promise"),
                    "top_events": result["top_events"],
                    "top_events_normalized": result.get("top_events_normalized", []),
                    "event_scores": result.get("event_scores", {}),
                    "event_scores_normalized": result.get("event_scores_normalized", {}),
                    "risk": result["decision"]["risk"],
                    "confidence": result["decision"]["confidence"],
                    "action": result["decision"]["action"],
                    "decision": result.get("decision", {}),
                    "time_window": result.get("time_window", {}),
                    "panchang_weather": result.get("panchang_weather", {}),
                    "governance": result.get("governance", {}),
                    "tara": result.get("tara", {}),
                    "sbc_analysis": result.get("sbc_analysis", {}),
                    "asset_events": result.get("asset_events", []),
                    "trading_event_filter": result.get("trading_event_filter", {}),
                    "trading_gate": result.get("trading_gate", {}),
                    "yoga": result.get("yoga", {}),
                    "nodes": result.get("nodes", {}),
                    "active_risk_factors": active_risk_factors,
                }
            )

        return {
            "mode": "B",
            "subject": {
                "birth_datetime": birth["date"].isoformat(),
                "birth_date": birth["date"].date().isoformat(),
                "birth_time": birth["date"].time().isoformat(timespec="seconds"),
                "latitude": birth["lat"],
                "longitude": birth["lon"],
            },
            "range": {"start_year": start, "end_year": end},
            "timeline": yearly,
        }

    if mode == "C":
        birth = birth_data or get_birth_data()
        base_date = date or datetime.now()
        horizon_hours = max(1, int(days_ahead) * 24) if days_ahead is not None else 48
        if days_ahead == 3:
            horizon_hours = 48
        window_end = base_date + timedelta(hours=horizon_hours)
        day_count = (window_end.date() - base_date.date()).days
        periods = []

        for offset in range(day_count + 1):
            eval_date = base_date + timedelta(days=offset)
            day_segments = _build_day_segments(eval_date)
            for seg_start, seg_end in day_segments:
                if seg_end <= base_date or seg_start >= window_end:
                    continue
                effective_start = max(seg_start, base_date)
                effective_end = min(seg_end, window_end)
                result = _run_single(
                    effective_start,
                    birth,
                    location_override=location_override,
                    location_mode=location_mode,
                    governance_profile=governance_profile,
                    allow_adult_insights=allow_adult_insights,
                    use_nakshatra_rulebook_bias=use_nakshatra_rulebook_bias,
                    use_trading_gate=use_trading_gate,
                    use_trading_event_filter=use_trading_event_filter,
                    use_asset_timeline_events=use_asset_timeline_events,
                    trading_gate_profile=trading_gate_profile,
                    confidence_calibration=confidence_calibration,
                )
                periods.append(
                    {
                        "date": eval_date.date().isoformat(),
                        "start": effective_start.isoformat(),
                        "end": effective_end.isoformat(),
                        "moon_nakshatra": _moon_nakshatra_at(effective_start),
                        "top_events": result["top_events"],
                        "top_events_normalized": result.get("top_events_normalized", []),
                        "decision": result["decision"],
                        "time_window": result["time_window"],
                        "panchang_weather": result["panchang_weather"],
                        "governance": result.get("governance", {}),
                        "tara": result.get("tara", {}),
                        "sbc_analysis": result.get("sbc_analysis", {}),
                        "asset_events": result.get("asset_events", []),
                        "trading_event_filter": result.get("trading_event_filter", {}),
                        "trading_gate": result.get("trading_gate", {}),
                    }
                )

        feedback_alignment = None
        if feedback_pnl_csv:
            feedback_alignment = build_mode_c_alignment_feedback(periods, feedback_pnl_csv)

        return {
            "mode": "C",
            "base_date": base_date.isoformat(),
            "hours_ahead": horizon_hours,
            "periods": periods,
            "feedback_alignment": feedback_alignment,
        }

    raise ValueError("mode must be one of: 'A', 'B', 'C'")


if __name__ == "__main__":
    result = run(mode="C", date=datetime.now(), days_ahead=3)
    print(result)


# =============================================================================
# PIPELINE API (v2.0) — Clean 4-stage architecture
# =============================================================================
# Use run_pipeline() for new integrations. It produces typed, immutable Results
# with full snapshot traceability. The legacy run()/_ run_single() above remains
# for backward compatibility until migration is complete.

from pipeline import run_astronomy, run_features, run_rules, run_decisions
from contracts.engine_snapshot import create_snapshot
from dataclasses import asdict


def run_pipeline(
    date=None,
    birth_data=None,
    location_override=None,
    location_mode="birth",
    governance_profile="professional",
    allow_adult_insights=False,
    use_trading_gate=False,
    use_trading_event_filter=False,
    use_asset_timeline_events=False,
    trading_gate_profile="strict",
    confidence_calibration=None,
):
    """
    Pipeline-based engine execution (v2.0).

    Produces immutable Result objects at each stage with full traceability.
    This is the forward-looking API — use this for new integrations.

    Returns:
        dict with:
            "decision": DecisionResult (as dict)
            "snapshot": EngineSnapshot (as dict)
            "stages": {
                "astronomy": AstronomyResult (as dict)
                "features": FeatureResult (as dict)
                "rules": RuleResult (as dict)
            }
    """
    birth = birth_data or get_birth_data()
    eval_date = date or datetime.now()

    config = {
        "governance_profile": governance_profile,
        "allow_adult_insights": allow_adult_insights,
        "use_trading_gate": use_trading_gate,
        "use_trading_event_filter": use_trading_event_filter,
        "use_asset_timeline_events": use_asset_timeline_events,
        "trading_gate_profile": trading_gate_profile,
        "confidence_calibration": confidence_calibration,
    }

    # Stage A — Astronomy
    astro = run_astronomy(eval_date, birth, location_override, location_mode)

    # Stage B — Features
    features = run_features(astro, birth, eval_date)

    # Stage C — Rules
    rules = run_rules(features, birth, eval_date, config)

    # Stage D — Decisions
    decision = run_decisions(rules, config)

    # Snapshot
    snapshot = create_snapshot(
        eval_date=eval_date,
        birth_data=birth,
        mode="C",
        config=config,
        lat=astro.lat,
        lon=astro.lon,
        stages_completed=4,
    )

    return {
        "decision": asdict(decision),
        "snapshot": asdict(snapshot),
        "stages": {
            "astronomy": {
                "jd": astro.jd,
                "ayanamsa": astro.ayanamsa,
                "moon_lon": astro.positions.get("Moon"),
                "sun_lon": astro.positions.get("Sun"),
                "ascendant": astro.ascendant,
            },
            "features": {
                "asc_sign": features.asc_sign,
                "natal_moon_sign": features.natal_moon_sign,
                "dasha_md": features.dasha.md,
                "dasha_ad": features.dasha.ad,
                "janma_nakshatra": features.janma_nakshatra,
            },
            "rules": {
                "top_events": rules.top_events,
                "yoga_score": rules.yoga.score,
                "risk_score": rules.risk_score,
                "moorthy_grade": rules.moorthy_grade,
                "kala_sarpa": rules.kala_sarpa,
            },
        },
    }

