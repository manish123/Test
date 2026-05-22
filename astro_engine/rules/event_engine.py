from rules.multi_planet import weighted_planet_score


EVENT_MAP = {
    "finance": {
        "houses": [2, 11],
        "planets": ["Jupiter", "Mercury", "Venus"],
    },
    "property": {
        "houses": [4],
        "planets": ["Mars", "Venus"],
    },
    "relationship": {
        "houses": [7],
        "planets": ["Venus"],
    },
    "legal": {
        "houses": [6],
        "planets": ["Mars", "Saturn"],
    },
    "career": {
        "houses": [10],
        "planets": ["Sun", "Saturn"],
    },
    "job": {
        "houses": [6, 10],
        "planets": ["Sun", "Saturn", "Mercury"],
    },
    "business": {
        "houses": [2, 7, 10, 11],
        "planets": ["Mercury", "Jupiter", "Mars"],
    },
    "authority": {
        "houses": [9, 10],
        "planets": ["Sun", "Jupiter", "Saturn"],
    },
    "retirement": {
        "houses": [4, 8, 12],
        "planets": ["Saturn", "Sun", "Ketu"],
    },
    "achievement": {
        "houses": [9, 10, 11],
        "planets": ["Sun", "Jupiter", "Mercury"],
    },
    "loss": {
        "houses": [12],
        "planets": ["Saturn", "Ketu"],
    },
    "inheritance": {
        "houses": [2, 8, 11],
        "planets": ["Jupiter", "Saturn", "Ketu"],
    },
    "bankruptcy": {
        "houses": [2, 8, 12],
        "planets": ["Saturn", "Rahu", "Ketu"],
    },
    "health": {
        "houses": [1, 6, 8],
        "planets": ["Sun", "Mars", "Saturn"],
    },
    "health_scare": {
        "houses": [6, 8, 12],
        "planets": ["Sun", "Saturn", "Mars"],
    },
    "accident": {
        "houses": [6, 8, 12],
        "planets": ["Mars", "Saturn", "Rahu"],
    },
    "hospitalization": {
        "houses": [6, 8, 12],
        "planets": ["Saturn", "Ketu", "Moon"],
    },
    "surgery": {
        "houses": [6, 8],
        "planets": ["Mars", "Saturn", "Ketu"],
    },
    "education": {
        "houses": [4, 5, 9],
        "planets": ["Jupiter", "Mercury", "Moon"],
    },
    "studies": {
        "houses": [4, 5],
        "planets": ["Mercury", "Moon", "Jupiter"],
    },
    "examination": {
        "houses": [4, 5, 9],
        "planets": ["Mercury", "Jupiter", "Moon"],
    },
    "children": {
        "houses": [5, 9],
        "planets": ["Jupiter", "Sun", "Venus"],
    },
    "child_birth": {
        "houses": [2, 5, 11],
        "planets": ["Jupiter", "Venus", "Moon"],
    },
    "grandchildren": {
        "houses": [5, 9, 11],
        "planets": ["Jupiter", "Moon", "Sun"],
    },
    "spiritual": {
        "houses": [9, 12],
        "planets": ["Jupiter", "Ketu", "Moon"],
    },
    "travel_foreign": {
        "houses": [3, 9, 12],
        "planets": ["Mercury", "Rahu", "Moon"],
    },
    "relocation": {
        "houses": [3, 4, 12],
        "planets": ["Moon", "Mercury", "Rahu"],
    },
    "citizenship": {
        "houses": [9, 10, 11, 12],
        "planets": ["Sun", "Rahu", "Saturn"],
    },
    "marriage": {
        "houses": [2, 7, 11],
        "planets": ["Venus", "Jupiter", "Moon"],
    },
    "divorce": {
        "houses": [6, 7, 8, 12],
        "planets": ["Venus", "Saturn", "Mars"],
    },
    "extra_marital": {
        "houses": [5, 7, 12],
        "planets": ["Venus", "Rahu", "Moon"],
    },
    "parents_death": {
        "houses": [4, 8, 9],
        "planets": ["Saturn", "Sun", "Ketu"],
    },
    "sibling_death": {
        "houses": [3, 8, 11],
        "planets": ["Mars", "Saturn", "Rahu"],
    },
    "spouse_bereavement": {
        "houses": [7, 8, 12],
        "planets": ["Saturn", "Ketu", "Venus"],
    },
    "litigation": {
        "houses": [6, 7, 8],
        "planets": ["Mars", "Saturn", "Rahu"],
    },
    "criminal_record": {
        "houses": [6, 8, 12],
        "planets": ["Saturn", "Mars", "Rahu"],
    },
    "behavior_risk": {
        "houses": [3, 6, 8],
        "planets": ["Mars", "Rahu", "Saturn"],
    },
    "behavior_discipline": {
        "houses": [1, 6, 10],
        "planets": ["Saturn", "Sun", "Mercury"],
    },
    "addiction_recovery": {
        "houses": [6, 8, 12],
        "planets": ["Jupiter", "Moon", "Saturn"],
    },
    "creative_milestone": {
        "houses": [3, 5, 11],
        "planets": ["Venus", "Mercury", "Moon"],
    },
    "belief_shift": {
        "houses": [5, 9, 12],
        "planets": ["Jupiter", "Ketu", "Moon"],
    },
}


def evaluate_event(event_name, chart, transit):
    config = EVENT_MAP[event_name]

    score = 0

    for p in config["planets"]:
        for planet in chart["planets"]:
            if planet["name"] == p:
                score += planet["multiplier"] * 25
                score += planet["vimsopaka"] * 2

                if planet["status"] == "exalted":
                    score += 15

                if planet["status"] == "debilitated":
                    score -= 10

    score += weighted_planet_score(event_name, chart["planets"])

    for h in config["houses"]:
        if h in chart["strong_houses"]:
            score += 20

    score += transit["strength"] * 30

    return round(score, 2)
