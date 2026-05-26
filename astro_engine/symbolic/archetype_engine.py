"""
Archetype Engine — Determine dominant and secondary symbolic archetypes.

Consumes chart state + evaluator outputs. Produces archetype rankings.
Does NOT modify scoring or evaluator outputs.
"""

from symbolic.registry_loader import get_business_archetypes


def determine_archetypes(chart_state, evaluator_outputs=None):
    """
    Determine dominant and secondary archetypes for a chart.

    Parameters
    ----------
    chart_state : BaseChartState or subclass
        Natal chart with planets, houses, signs.
    evaluator_outputs : dict, optional
        Results from domain evaluators (for context weighting).

    Returns
    -------
    dict with: dominant_archetypes, secondary_archetypes, archetype_confidence,
               fusion_patterns, symbolic_identity_profile
    """
    archetypes = get_business_archetypes()
    if not archetypes:
        return {"dominant_archetypes": [], "secondary_archetypes": [], "archetype_confidence": {}}

    scored = []
    for arch in archetypes:
        score = _score_archetype(arch, chart_state)
        scored.append((arch["archetype_id"], arch["name"], score, arch.get("confidence", 0.5)))

    scored.sort(key=lambda x: x[2], reverse=True)

    dominant = scored[:2] if len(scored) >= 2 else scored
    secondary = scored[2:4] if len(scored) >= 4 else []

    return {
        "dominant_archetypes": [
            {"id": s[0], "name": s[1], "match_score": round(s[2], 2), "source_confidence": s[3]}
            for s in dominant
        ],
        "secondary_archetypes": [
            {"id": s[0], "name": s[1], "match_score": round(s[2], 2), "source_confidence": s[3]}
            for s in secondary
        ],
        "archetype_confidence": {s[0]: round(s[2] * s[3], 3) for s in scored if s[2] > 0},
        "fusion_patterns": _detect_fusion(dominant, secondary),
        "symbolic_identity_profile": _build_identity(dominant, chart_state),
    }


def _score_archetype(archetype, chart_state):
    """Score how well a chart matches an archetype based on planetary/house drivers."""
    score = 0.0
    planets = chart_state.planets

    # Check planetary drivers
    for driver in archetype.get("planetary_drivers", []):
        for planet_name, data in planets.items():
            if planet_name in driver:
                # Planet exists in chart — base match
                score += 1.0
                # Exalted driver = stronger match
                if "exalted" in driver.lower() and data.get("status") == "exalted":
                    score += 2.0
                # Check house alignment
                for house_driver in archetype.get("house_drivers", []):
                    if "10th" in house_driver and data["house"] == 10:
                        score += 1.5
                    elif "11th" in house_driver and data["house"] == 11:
                        score += 1.5
                    elif "5th" in house_driver and data["house"] == 5:
                        score += 1.5
                    elif "6th" in house_driver and data["house"] == 6:
                        score += 1.0
                    elif "3rd" in house_driver and data["house"] == 3:
                        score += 1.0
                    elif "7th" in house_driver and data["house"] == 7:
                        score += 1.0

    # Check amplification factors
    for amp in archetype.get("amplification_factors", []):
        if "Saturn" in amp:
            sat_status = planets.get("Saturn", {}).get("status", "")
            if sat_status in ("exalted", "own"):
                score += 1.0

    return score


def _detect_fusion(dominant, secondary):
    """Detect if dominant archetypes create a fusion pattern."""
    if len(dominant) < 2:
        return []
    return [{"primary": dominant[0][0], "secondary": dominant[1][0], "fusion_type": "dual_archetype"}]


def _build_identity(dominant, chart_state):
    """Build a symbolic identity summary."""
    if not dominant:
        return {"summary": "undetermined"}
    return {
        "primary_archetype": dominant[0][1] if dominant else "unknown",
        "asc_sign": chart_state.asc_sign,
        "moon_sign": chart_state.moon_sign,
    }
