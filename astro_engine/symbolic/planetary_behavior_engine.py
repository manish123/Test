"""
Planetary Behavior Engine — Model planets as behavioral/economic operating systems.

Combines planetary behavior profiles to derive leadership style, economic behavior,
risk behavior, and psychological operating system.
"""

from symbolic.registry_loader import get_planetary_behaviors, get_planetary_behavior


def build_behavioral_profile(chart_state):
    """
    Build a composite behavioral profile from the chart's planetary placements.

    Returns dict with: behavioral_profile, leadership_signature, economic_style,
                       volatility_signature, psychological_os
    """
    planets = chart_state.planets
    behaviors = get_planetary_behaviors()
    if not behaviors:
        return {"behavioral_profile": {}, "leadership_signature": {}}

    # Identify dominant planets (in kendra/trikona, exalted, or lagna lord)
    dominant_planets = []
    for name, data in planets.items():
        if name in ("Rahu", "Ketu"):
            continue
        weight = 1.0
        if data["house"] in (1, 4, 7, 10):  # Kendra
            weight += 1.0
        if data["house"] in (5, 9):  # Trikona
            weight += 0.8
        if data.get("status") == "exalted":
            weight += 1.5
        elif data.get("status") == "own":
            weight += 0.8
        if name == chart_state.lagna_lord:
            weight += 1.0
        dominant_planets.append((name, weight, data))

    dominant_planets.sort(key=lambda x: x[1], reverse=True)
    top_3 = dominant_planets[:3]

    # Build composite from top 3 planets
    leadership_traits = []
    economic_traits = []
    risk_traits = []
    failure_modes = []
    time_horizons = []

    for planet_name, weight, _ in top_3:
        behavior = get_planetary_behavior(planet_name)
        if not behavior:
            continue
        leadership_traits.extend(behavior.get("leadership_behavior", []))
        economic_traits.extend(behavior.get("economic_behavior", []))
        risk_traits.extend(behavior.get("risk_behavior", []))
        failure_modes.extend(behavior.get("failure_behavior", []))
        time_horizons.append(behavior.get("time_horizon", ""))

    return {
        "behavioral_profile": {
            "dominant_planets": [(p[0], round(p[1], 2)) for p in top_3],
            "core_intelligence": [
                get_planetary_behavior(p[0]).get("core_intelligence", "")
                for p in top_3 if get_planetary_behavior(p[0])
            ],
        },
        "leadership_signature": {
            "traits": leadership_traits[:4],
            "primary_planet": top_3[0][0] if top_3 else "unknown",
        },
        "economic_style": {
            "traits": economic_traits[:4],
            "wealth_behavior": [
                get_planetary_behavior(top_3[0][0]).get("wealth_behavior", [""])[0]
            ] if top_3 else [],
        },
        "volatility_signature": {
            "risk_traits": risk_traits[:3],
            "time_horizons": time_horizons[:3],
        },
        "psychological_os": {
            "primary": get_planetary_behavior(top_3[0][0]).get("psychological_signature", [""])[0] if top_3 else "",
            "shadow": get_planetary_behavior(top_3[0][0]).get("shadow_expression", [""])[0] if top_3 else "",
            "failure_modes": failure_modes[:3],
        },
    }
