MULTI_PLANET_WEIGHTS = {
    "finance": {"Jupiter": 0.40, "Mercury": 0.30, "Venus": 0.20, "Moon": 0.10},
    "property": {"Mars": 0.60, "Venus": 0.40},
    "career": {"Sun": 0.45, "Saturn": 0.35, "Mercury": 0.20},
    "job": {"Sun": 0.35, "Saturn": 0.30, "Mercury": 0.20, "Moon": 0.15},
    "business": {"Mercury": 0.35, "Jupiter": 0.30, "Mars": 0.20, "Venus": 0.15},
    "authority": {"Sun": 0.45, "Jupiter": 0.30, "Saturn": 0.25},
    "retirement": {"Saturn": 0.45, "Sun": 0.30, "Ketu": 0.25},
    "achievement": {"Sun": 0.40, "Jupiter": 0.35, "Mercury": 0.25},
    "health": {"Sun": 0.35, "Mars": 0.35, "Saturn": 0.30},
    "health_scare": {"Sun": 0.30, "Saturn": 0.40, "Mars": 0.30},
    "accident": {"Mars": 0.40, "Saturn": 0.30, "Rahu": 0.30},
    "hospitalization": {"Saturn": 0.35, "Ketu": 0.35, "Moon": 0.30},
    "surgery": {"Mars": 0.45, "Saturn": 0.30, "Ketu": 0.25},
    "inheritance": {"Jupiter": 0.40, "Saturn": 0.35, "Ketu": 0.25},
    "bankruptcy": {"Saturn": 0.40, "Rahu": 0.35, "Ketu": 0.25},
    "education": {"Jupiter": 0.40, "Mercury": 0.35, "Moon": 0.25},
    "studies": {"Mercury": 0.40, "Moon": 0.30, "Jupiter": 0.30},
    "examination": {"Mercury": 0.45, "Jupiter": 0.35, "Moon": 0.20},
    "children": {"Jupiter": 0.45, "Sun": 0.30, "Venus": 0.25},
    "child_birth": {"Jupiter": 0.40, "Venus": 0.35, "Moon": 0.25},
    "grandchildren": {"Jupiter": 0.45, "Moon": 0.30, "Sun": 0.25},
    "spiritual": {"Jupiter": 0.40, "Moon": 0.30, "Ketu": 0.30},
    "belief_shift": {"Jupiter": 0.40, "Ketu": 0.35, "Moon": 0.25},
    "creative_milestone": {"Venus": 0.40, "Mercury": 0.35, "Moon": 0.25},
    "travel_foreign": {"Mercury": 0.35, "Rahu": 0.35, "Moon": 0.30},
    "relocation": {"Moon": 0.40, "Mercury": 0.30, "Rahu": 0.30},
    "citizenship": {"Sun": 0.35, "Rahu": 0.35, "Saturn": 0.30},
    "relationship": {"Venus": 0.50, "Jupiter": 0.30, "Moon": 0.20},
    "marriage": {"Venus": 0.40, "Jupiter": 0.35, "Moon": 0.25},
    "divorce": {"Venus": 0.35, "Saturn": 0.35, "Mars": 0.30},
    "extra_marital": {"Venus": 0.35, "Rahu": 0.35, "Moon": 0.30},
    "parents_death": {"Saturn": 0.40, "Sun": 0.30, "Ketu": 0.30},
    "sibling_death": {"Mars": 0.35, "Saturn": 0.35, "Rahu": 0.30},
    "spouse_bereavement": {"Saturn": 0.40, "Ketu": 0.30, "Venus": 0.30},
    "legal": {"Mars": 0.40, "Saturn": 0.35, "Mercury": 0.25},
    "litigation": {"Mars": 0.35, "Saturn": 0.35, "Rahu": 0.30},
    "criminal_record": {"Saturn": 0.40, "Mars": 0.30, "Rahu": 0.30},
    "behavior_risk": {"Mars": 0.35, "Rahu": 0.35, "Saturn": 0.30},
    "behavior_discipline": {"Saturn": 0.40, "Sun": 0.30, "Mercury": 0.30},
    "addiction_recovery": {"Jupiter": 0.40, "Moon": 0.30, "Saturn": 0.30},
    "loss": {"Saturn": 0.45, "Ketu": 0.35, "Moon": 0.20},
}


def weighted_planet_score(event_name, planets):
    weights = MULTI_PLANET_WEIGHTS.get(event_name, {})
    if not weights:
        return 0.0

    by_name = {planet["name"]: planet for planet in planets}
    score = 0.0
    for name, weight in weights.items():
        p = by_name.get(name)
        if not p:
            continue
        score += (p.get("multiplier", 1.0) * 25 + p.get("vimsopaka", 0) * 2) * weight
    return round(score, 2)
