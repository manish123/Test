"""
Relationship Symbolic Conditions (Layer C1)

Detects NEUTRAL marriage/relationship signals from planetary state.
No judgment about whether marriage "will happen" — only whether
marriage-related conditions are active.

Output format:
{
    "condition": "seventh_house_activated",
    "strength": 0.82,
    "source": "7th lord in MD"
}

These are consumed by:
- rules/domains/relationship/marriage/marriage_policy.py (meaning)
- rules/domains/relationship/marriage/marriage_timing.py (when)
"""

from typing import List, Dict, Any


# ═══════════════════════════════════════════════════════════════
# A. DASHA-BASED CONDITIONS (broad window)
# ═══════════════════════════════════════════════════════════════

def detect_dasha_marriage_conditions(
    dasha_md: str,
    dasha_ad: str,
    seventh_lord: str,
    second_lord: str,
    planets_in_7th: List[str],
    planets_aspecting_7th: List[str],
    seventh_lord_dispositor: str,
    d9_seventh_house_planets: List[str] = None,
    d9_lagna_lord: str = None,
    darakaraka: str = None,
) -> List[Dict[str, Any]]:
    """
    Detect dasha-based marriage indicators.

    Returns list of neutral conditions with strength scores.
    Each condition is probabilistic, not deterministic.
    """
    conditions = []
    d9_seventh_house_planets = d9_seventh_house_planets or []

    # 1. 7th lord running MD or AD
    if dasha_md == seventh_lord:
        conditions.append({
            "condition": "seventh_lord_mahadasha",
            "strength": 0.85,
            "source": f"7th lord ({seventh_lord}) running Mahadasha",
            "category": "dasha",
        })
    if dasha_ad == seventh_lord:
        conditions.append({
            "condition": "seventh_lord_antardasha",
            "strength": 0.75,
            "source": f"7th lord ({seventh_lord}) running Antardasha",
            "category": "dasha",
        })

    # 2. Planets placed in 7th house running MD/AD
    if dasha_md in planets_in_7th:
        conditions.append({
            "condition": "planet_in_7th_mahadasha",
            "strength": 0.70,
            "source": f"{dasha_md} (placed in 7th) running MD",
            "category": "dasha",
        })
    if dasha_ad in planets_in_7th:
        conditions.append({
            "condition": "planet_in_7th_antardasha",
            "strength": 0.60,
            "source": f"{dasha_ad} (placed in 7th) running AD",
            "category": "dasha",
        })

    # 3. Planets aspecting 7th house/lord running MD/AD
    if dasha_md in planets_aspecting_7th:
        conditions.append({
            "condition": "planet_aspecting_7th_mahadasha",
            "strength": 0.55,
            "source": f"{dasha_md} (aspecting 7th) running MD",
            "category": "dasha",
        })
    if dasha_ad in planets_aspecting_7th:
        conditions.append({
            "condition": "planet_aspecting_7th_antardasha",
            "strength": 0.45,
            "source": f"{dasha_ad} (aspecting 7th) running AD",
            "category": "dasha",
        })

    # 4. Dispositor of 7th lord running MD/AD
    if seventh_lord_dispositor and dasha_md == seventh_lord_dispositor:
        conditions.append({
            "condition": "seventh_lord_dispositor_mahadasha",
            "strength": 0.50,
            "source": f"Dispositor of 7th lord ({seventh_lord_dispositor}) running MD",
            "category": "dasha",
        })

    # 5. Venus/Jupiter MD/AD combinations
    if dasha_md == "Venus":
        conditions.append({
            "condition": "venus_mahadasha",
            "strength": 0.65,
            "source": "Venus (natural marriage catalyst) running MD",
            "category": "dasha",
        })
    if dasha_md == "Jupiter":
        conditions.append({
            "condition": "jupiter_mahadasha",
            "strength": 0.55,
            "source": "Jupiter (marriage significator for women) running MD",
            "category": "dasha",
        })

    # 6. Venus MD + 7th lord AD (prime combination)
    if dasha_md == "Venus" and dasha_ad == seventh_lord:
        conditions.append({
            "condition": "venus_md_seventh_lord_ad",
            "strength": 0.90,
            "source": f"Venus MD + 7th lord ({seventh_lord}) AD — prime marriage combination",
            "category": "dasha",
        })
    # Jupiter MD + Venus AD
    if dasha_md == "Jupiter" and dasha_ad == "Venus":
        conditions.append({
            "condition": "jupiter_md_venus_ad",
            "strength": 0.80,
            "source": "Jupiter MD + Venus AD — strong marriage period",
            "category": "dasha",
        })

    # 7. 2nd house lord activation (family formation)
    if dasha_md == second_lord:
        conditions.append({
            "condition": "second_lord_mahadasha",
            "strength": 0.50,
            "source": f"2nd lord ({second_lord}) running MD — family formation active",
            "category": "dasha",
        })
    if dasha_ad == second_lord:
        conditions.append({
            "condition": "second_lord_antardasha",
            "strength": 0.45,
            "source": f"2nd lord ({second_lord}) running AD — family formation active",
            "category": "dasha",
        })

    # 8. D9 (Navamsa) activation
    if dasha_md in d9_seventh_house_planets:
        conditions.append({
            "condition": "d9_seventh_house_planet_md",
            "strength": 0.70,
            "source": f"{dasha_md} (in D9 7th house) running MD — Navamsa marriage activation",
            "category": "dasha_d9",
        })
    if d9_lagna_lord and dasha_md == d9_lagna_lord:
        conditions.append({
            "condition": "d9_lagna_lord_md",
            "strength": 0.65,
            "source": f"D9 Lagna lord ({d9_lagna_lord}) running MD",
            "category": "dasha_d9",
        })
    if darakaraka and (dasha_md == darakaraka or dasha_ad == darakaraka):
        conditions.append({
            "condition": "darakaraka_dasha",
            "strength": 0.70,
            "source": f"Darakaraka ({darakaraka}) running {'MD' if dasha_md == darakaraka else 'AD'}",
            "category": "dasha_d9",
        })

    return conditions


# ═══════════════════════════════════════════════════════════════
# B. TRANSIT-BASED CONDITIONS (window refinement)
# ═══════════════════════════════════════════════════════════════

def detect_transit_marriage_conditions(
    jupiter_house: int,
    saturn_house: int,
    jupiter_sign: int,
    saturn_sign: int,
    seventh_house: int = 7,
    seventh_lord_sign: int = None,
    lagna_lord_sign: int = None,
    venus_sign: int = None,
    d9_lagna_sign: int = None,
    asc_sign: int = 1,
) -> List[Dict[str, Any]]:
    """
    Detect transit-based marriage indicators (Jupiter/Saturn slow transits).

    These create the broad activation window (months).
    """
    conditions = []

    # Compute 7th house sign from ascendant
    seventh_sign = ((asc_sign + 6 - 1) % 12) + 1

    # 1. Jupiter transiting 7th house
    if jupiter_house == 7:
        conditions.append({
            "condition": "jupiter_transit_7th_house",
            "strength": 0.80,
            "source": "Transit Jupiter in 7th house — relationship expansion",
            "category": "transit",
        })

    # 2. Jupiter transiting over 7th lord
    if seventh_lord_sign and jupiter_sign == seventh_lord_sign:
        conditions.append({
            "condition": "jupiter_transit_over_7th_lord",
            "strength": 0.75,
            "source": "Transit Jupiter conjunct 7th lord — partnership activation",
            "category": "transit",
        })

    # 3. Jupiter transiting over Venus
    if venus_sign and jupiter_sign == venus_sign:
        conditions.append({
            "condition": "jupiter_transit_over_venus",
            "strength": 0.65,
            "source": "Transit Jupiter conjunct Venus — love expansion",
            "category": "transit",
        })

    # 4. Jupiter transiting D9 Lagna
    if d9_lagna_sign and jupiter_sign == d9_lagna_sign:
        conditions.append({
            "condition": "jupiter_transit_d9_lagna",
            "strength": 0.70,
            "source": "Transit Jupiter on Navamsa Lagna — D9 marriage activation",
            "category": "transit_d9",
        })

    # 5. Double Transit Method (most powerful)
    # Saturn transiting/aspecting 7th house AND Jupiter transiting/aspecting 7th lord (or vice versa)
    saturn_aspects_7th = saturn_house == 7 or _saturn_aspects_house(saturn_house, 7)
    jupiter_aspects_7th = jupiter_house == 7 or _jupiter_aspects_house(jupiter_house, 7)

    saturn_on_lagna_lord = (lagna_lord_sign and saturn_sign == lagna_lord_sign)
    jupiter_on_7th_lord = (seventh_lord_sign and jupiter_sign == seventh_lord_sign)

    if saturn_aspects_7th and jupiter_on_7th_lord:
        conditions.append({
            "condition": "double_transit_marriage",
            "strength": 0.90,
            "source": "Saturn on 7th + Jupiter on 7th lord — DOUBLE TRANSIT (strongest trigger)",
            "category": "transit_double",
        })
    elif jupiter_aspects_7th and saturn_on_lagna_lord:
        conditions.append({
            "condition": "double_transit_marriage_reverse",
            "strength": 0.85,
            "source": "Jupiter on 7th + Saturn on Lagna lord — DOUBLE TRANSIT (reverse)",
            "category": "transit_double",
        })
    elif saturn_aspects_7th or jupiter_aspects_7th:
        conditions.append({
            "condition": "single_transit_7th",
            "strength": 0.50,
            "source": f"{'Saturn' if saturn_aspects_7th else 'Jupiter'} activating 7th house (single transit)",
            "category": "transit",
        })

    return conditions


# ═══════════════════════════════════════════════════════════════
# C. FAST TRIGGER CONDITIONS (exact timing)
# ═══════════════════════════════════════════════════════════════

def detect_fast_trigger_conditions(
    moon_house: int,
    mars_house: int,
    venus_house: int = None,
    lagna_lord_house: int = None,
    moon_sign: int = None,
    seventh_lord_sign: int = None,
    ninth_lord_sign: int = None,
) -> List[Dict[str, Any]]:
    """
    Detect fast-moving planet triggers that narrow the window to days/weeks.

    Moon transit → within 72 days
    Mars transit → within 2 months
    Venus/Lagna lord transit → immediate trigger
    """
    conditions = []

    # Moon transiting 7th or 9th house
    if moon_house == 7:
        conditions.append({
            "condition": "moon_transit_7th",
            "strength": 0.60,
            "source": "Moon transiting 7th house — marriage possible within 72 days",
            "category": "fast_trigger",
            "timing_window_days": 72,
        })
    if moon_house == 9:
        conditions.append({
            "condition": "moon_transit_9th",
            "strength": 0.50,
            "source": "Moon transiting 9th house — auspicious timing within 72 days",
            "category": "fast_trigger",
            "timing_window_days": 72,
        })

    # Mars transiting 7th or 9th house
    if mars_house == 7:
        conditions.append({
            "condition": "mars_transit_7th",
            "strength": 0.55,
            "source": "Mars transiting 7th house — marriage possible within 2 months",
            "category": "fast_trigger",
            "timing_window_days": 60,
        })
    if mars_house == 9:
        conditions.append({
            "condition": "mars_transit_9th",
            "strength": 0.45,
            "source": "Mars transiting 9th house — event within 2 months",
            "category": "fast_trigger",
            "timing_window_days": 60,
        })

    # Lagna lord transiting 7th house
    if lagna_lord_house == 7:
        conditions.append({
            "condition": "lagna_lord_transit_7th",
            "strength": 0.65,
            "source": "Lagna lord transiting 7th house — personal-partnership axis activated",
            "category": "fast_trigger",
            "timing_window_days": 30,
        })

    # Venus transiting 7th
    if venus_house == 7:
        conditions.append({
            "condition": "venus_transit_7th",
            "strength": 0.55,
            "source": "Venus transiting 7th house — love/partnership window",
            "category": "fast_trigger",
            "timing_window_days": 30,
        })

    return conditions


# ═══════════════════════════════════════════════════════════════
# D. MATHEMATICAL LONGITUDE POINTS
# ═══════════════════════════════════════════════════════════════

def compute_marriage_sensitive_points(
    lagna_lord_longitude: float,
    seventh_lord_longitude: float,
    janma_nakshatra_lord_longitude: float = None,
) -> List[Dict[str, Any]]:
    """
    Compute mathematical sensitive points for marriage timing.

    When transit Jupiter crosses these points (or their trines/opposition),
    marriage is highly likely.
    """
    points = []

    # Point 1: Lagna lord + 7th lord longitudes
    sum_1 = (lagna_lord_longitude + seventh_lord_longitude) % 360
    points.append({
        "point_name": "lagna_7th_lord_sum",
        "longitude": round(sum_1, 2),
        "trine_1": round((sum_1 + 120) % 360, 2),
        "trine_2": round((sum_1 + 240) % 360, 2),
        "opposition": round((sum_1 + 180) % 360, 2),
        "description": "Sum of Lagna lord + 7th lord longitudes",
    })

    # Point 2: Janma Nakshatra lord + 7th lord (if available)
    if janma_nakshatra_lord_longitude is not None:
        sum_2 = (janma_nakshatra_lord_longitude + seventh_lord_longitude) % 360
        points.append({
            "point_name": "janma_nak_lord_7th_lord_sum",
            "longitude": round(sum_2, 2),
            "trine_1": round((sum_2 + 120) % 360, 2),
            "trine_2": round((sum_2 + 240) % 360, 2),
            "opposition": round((sum_2 + 180) % 360, 2),
            "description": "Sum of Janma Nakshatra lord + 7th lord longitudes",
        })

    return points


def check_jupiter_on_sensitive_points(
    jupiter_longitude: float,
    sensitive_points: List[Dict[str, Any]],
    orb_degrees: float = 5.0,
) -> List[Dict[str, Any]]:
    """
    Check if transit Jupiter is within orb of any marriage-sensitive points.
    """
    hits = []
    for point in sensitive_points:
        for target_key in ["longitude", "trine_1", "trine_2", "opposition"]:
            target = point[target_key]
            distance = abs((jupiter_longitude - target + 180) % 360 - 180)
            if distance <= orb_degrees:
                hits.append({
                    "condition": "jupiter_on_sensitive_point",
                    "strength": round(1.0 - (distance / orb_degrees) * 0.3, 2),
                    "source": f"Jupiter at {jupiter_longitude:.1f}° within {distance:.1f}° of {point['point_name']} ({target_key}={target:.1f}°)",
                    "category": "mathematical",
                    "point": point["point_name"],
                    "aspect_type": target_key,
                    "orb": round(distance, 2),
                })
    return hits


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _saturn_aspects_house(saturn_house, target_house):
    """Saturn aspects: 3rd, 7th, 10th from its position."""
    offsets = [2, 6, 9]  # 3rd, 7th, 10th (0-indexed offsets)
    aspected = [((saturn_house - 1 + off) % 12) + 1 for off in offsets]
    return target_house in aspected


def _jupiter_aspects_house(jupiter_house, target_house):
    """Jupiter aspects: 5th, 7th, 9th from its position."""
    offsets = [4, 6, 8]  # 5th, 7th, 9th (0-indexed offsets)
    aspected = [((jupiter_house - 1 + off) % 12) + 1 for off in offsets]
    return target_house in aspected


# ═══════════════════════════════════════════════════════════════
# COMPOSITE: BUILD ALL MARRIAGE CONDITIONS
# ═══════════════════════════════════════════════════════════════

def build_marriage_conditions(
    dasha_md: str,
    dasha_ad: str,
    seventh_lord: str,
    second_lord: str,
    planets_in_7th: List[str],
    planets_aspecting_7th: List[str],
    seventh_lord_dispositor: str,
    jupiter_house: int,
    saturn_house: int,
    jupiter_sign: int,
    saturn_sign: int,
    moon_house: int,
    mars_house: int,
    asc_sign: int = 1,
    seventh_lord_sign: int = None,
    lagna_lord_sign: int = None,
    venus_sign: int = None,
    venus_house: int = None,
    lagna_lord_house: int = None,
    d9_lagna_sign: int = None,
    d9_seventh_house_planets: List[str] = None,
    d9_lagna_lord: str = None,
    darakaraka: str = None,
    lagna_lord_longitude: float = None,
    seventh_lord_longitude: float = None,
    jupiter_longitude: float = None,
    janma_nakshatra_lord_longitude: float = None,
) -> Dict[str, Any]:
    """
    Build complete marriage condition assessment.

    Returns:
        dict with:
            "dasha_conditions": list of dasha-based indicators
            "transit_conditions": list of transit-based indicators
            "fast_triggers": list of fast-moving planet triggers
            "sensitive_points": mathematical longitude points
            "jupiter_point_hits": Jupiter on sensitive points
            "total_strength": composite score (0-1)
            "signal_level": NO_SIGNAL | WEAK | MODERATE | STRONG | VERY_STRONG
    """
    # A. Dasha conditions
    dasha_conditions = detect_dasha_marriage_conditions(
        dasha_md=dasha_md, dasha_ad=dasha_ad,
        seventh_lord=seventh_lord, second_lord=second_lord,
        planets_in_7th=planets_in_7th, planets_aspecting_7th=planets_aspecting_7th,
        seventh_lord_dispositor=seventh_lord_dispositor,
        d9_seventh_house_planets=d9_seventh_house_planets,
        d9_lagna_lord=d9_lagna_lord, darakaraka=darakaraka,
    )

    # B. Transit conditions
    transit_conditions = detect_transit_marriage_conditions(
        jupiter_house=jupiter_house, saturn_house=saturn_house,
        jupiter_sign=jupiter_sign, saturn_sign=saturn_sign,
        seventh_lord_sign=seventh_lord_sign, lagna_lord_sign=lagna_lord_sign,
        venus_sign=venus_sign, d9_lagna_sign=d9_lagna_sign,
        asc_sign=asc_sign,
    )

    # C. Fast triggers
    fast_triggers = detect_fast_trigger_conditions(
        moon_house=moon_house, mars_house=mars_house,
        venus_house=venus_house, lagna_lord_house=lagna_lord_house,
    )

    # D. Mathematical points
    sensitive_points = []
    jupiter_point_hits = []
    if lagna_lord_longitude is not None and seventh_lord_longitude is not None:
        sensitive_points = compute_marriage_sensitive_points(
            lagna_lord_longitude=lagna_lord_longitude,
            seventh_lord_longitude=seventh_lord_longitude,
            janma_nakshatra_lord_longitude=janma_nakshatra_lord_longitude,
        )
        if jupiter_longitude is not None:
            jupiter_point_hits = check_jupiter_on_sensitive_points(
                jupiter_longitude=jupiter_longitude,
                sensitive_points=sensitive_points,
            )

    # Composite strength
    all_conditions = dasha_conditions + transit_conditions + fast_triggers + jupiter_point_hits
    if not all_conditions:
        total_strength = 0.0
    else:
        # Use max strength as primary, with count as secondary boost
        max_strength = max(c["strength"] for c in all_conditions)
        count_boost = min(0.15, len(all_conditions) * 0.02)  # up to +0.15 for many signals
        total_strength = min(1.0, max_strength + count_boost)

    # Signal level classification
    if total_strength >= 0.85:
        signal_level = "VERY_STRONG"
    elif total_strength >= 0.70:
        signal_level = "STRONG"
    elif total_strength >= 0.50:
        signal_level = "MODERATE"
    elif total_strength >= 0.30:
        signal_level = "WEAK"
    else:
        signal_level = "NO_SIGNAL"

    return {
        "dasha_conditions": dasha_conditions,
        "transit_conditions": transit_conditions,
        "fast_triggers": fast_triggers,
        "sensitive_points": sensitive_points,
        "jupiter_point_hits": jupiter_point_hits,
        "total_conditions": len(all_conditions),
        "total_strength": round(total_strength, 3),
        "signal_level": signal_level,
    }
