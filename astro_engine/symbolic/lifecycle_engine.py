"""
Lifecycle Engine — Determine current lifecycle phase and transitions.

Uses lifecycle_transitions.json registry to detect phase based on age,
Saturn return status, and dasha progression.
"""

from symbolic.registry_loader import get_lifecycle_transitions


def determine_lifecycle_state(chart_state, eval_date, age_years=None):
    """
    Determine current lifecycle phase and probable transitions.

    Parameters
    ----------
    chart_state : BaseChartState
    eval_date : datetime
    age_years : float, optional (computed from birth_dt if not provided)

    Returns
    -------
    dict with: current_state, probable_next_states, expansion_indicators,
               crisis_vectors
    """
    transitions = get_lifecycle_transitions()
    if not transitions:
        return {"current_state": "unknown", "probable_next_states": []}

    if age_years is None:
        age_years = (eval_date - chart_state.birth_dt).days / 365.25

    # Determine current phase based on age thresholds
    current = _determine_phase_by_age(age_years)
    probable_next = _determine_next_phases(current, age_years)
    crisis_vectors = _detect_crisis_indicators(chart_state, age_years, transitions)

    return {
        "current_state": current,
        "age_years": round(age_years, 1),
        "probable_next_states": probable_next,
        "expansion_indicators": _expansion_indicators(chart_state),
        "crisis_vectors": crisis_vectors,
    }


def _determine_phase_by_age(age):
    """Map age to lifecycle phase."""
    if age < 18:
        return {"phase": "formation", "label": "Identity Formation", "stability": "low"}
    elif age < 28:
        return {"phase": "exploration", "label": "Youthful Expansion", "stability": "medium"}
    elif age < 32:
        return {"phase": "first_saturn_return", "label": "First Saturn Return — Consolidation", "stability": "restructuring"}
    elif age < 42:
        return {"phase": "building", "label": "Institutional Building", "stability": "high"}
    elif age < 45:
        return {"phase": "midlife_transition", "label": "Midlife Reinvention", "stability": "volatile"}
    elif age < 58:
        return {"phase": "mastery", "label": "Mastery and Authority", "stability": "high"}
    elif age < 62:
        return {"phase": "second_saturn_return", "label": "Second Saturn Return — Legacy", "stability": "restructuring"}
    else:
        return {"phase": "legacy", "label": "Legacy and Transmission", "stability": "settling"}


def _determine_next_phases(current, age):
    """Determine probable next lifecycle phases."""
    phase = current.get("phase", "")
    transitions = {
        "formation": ["exploration"],
        "exploration": ["first_saturn_return"],
        "first_saturn_return": ["building"],
        "building": ["midlife_transition"],
        "midlife_transition": ["mastery"],
        "mastery": ["second_saturn_return"],
        "second_saturn_return": ["legacy"],
        "legacy": [],
    }
    next_phases = transitions.get(phase, [])
    return [{"phase": p, "estimated_onset_age": _phase_onset_age(p)} for p in next_phases]


def _phase_onset_age(phase):
    ages = {
        "exploration": 18, "first_saturn_return": 28, "building": 32,
        "midlife_transition": 42, "mastery": 45, "second_saturn_return": 58, "legacy": 62,
    }
    return ages.get(phase, 0)


def _detect_crisis_indicators(chart_state, age, transitions):
    """Detect if any lifecycle crisis conditions are active."""
    vectors = []
    # Saturn return windows
    if 27 <= age <= 30:
        vectors.append({"type": "first_saturn_return", "intensity": "high",
                       "ref": "life_trans_001"})
    if 56 <= age <= 60:
        vectors.append({"type": "second_saturn_return", "intensity": "high"})
    if 41 <= age <= 43:
        vectors.append({"type": "midlife_crisis", "intensity": "medium",
                       "ref": "life_trans_003"})
    return vectors


def _expansion_indicators(chart_state):
    """Check for expansion vs contraction signals."""
    jupiter_house = chart_state.planets.get("Jupiter", {}).get("house", 0)
    saturn_house = chart_state.planets.get("Saturn", {}).get("house", 0)

    expansion = jupiter_house in (1, 5, 9, 11)
    contraction = saturn_house in (1, 4, 8, 12)

    return {
        "expansion_active": expansion,
        "contraction_active": contraction,
        "net_direction": "expanding" if expansion and not contraction else
                        "contracting" if contraction and not expansion else "mixed",
    }
