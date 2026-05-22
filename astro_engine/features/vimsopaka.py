from features.dignity import EXALTATION, DEBILITATION, SIGN_LORDS, _relationship_tier
from features.divisional import get_d2_sign, get_d3_sign, get_d7_sign, get_d9_sign, get_d10_sign, get_d12_sign, get_d60_sign


VARGA_WEIGHTS = {
    "D1": 3.0,
    "D2": 1.5,
    "D3": 1.5,
    "D7": 1.0,
    "D9": 2.5,
    "D10": 2.0,
    "D12": 1.5,
    "D60": 3.0,
}


DIGNITY_SCORES = {
    "own": 20,
    "exalted": 20,
    "great_friend": 17,
    "friend": 15,
    "neutral": 10,
    "enemy": 7,
    "bitter_enemy": 6,
    "debilitated": 5,
}


def normalize_dignity(dignity):
    aliases = {
        "moolatrikona": "own",
        "mt": "own",
        "exalt": "exalted",
    }
    d = aliases.get(dignity, dignity)
    return d if d in DIGNITY_SCORES else "neutral"


def _dignity_from_sign(planet_name, sign):
    if EXALTATION.get(planet_name) == sign:
        return "exalted"
    if DEBILITATION.get(planet_name) == sign:
        return "debilitated"
    if SIGN_LORDS.get(sign) == planet_name:
        return "own"
    return _relationship_tier(planet_name, SIGN_LORDS.get(sign))


def get_varga_dignity(planet, varga):
    if varga == "D1":
        return normalize_dignity(planet.get("status", "neutral"))
    if varga == "D2":
        return _dignity_from_sign(planet["name"], get_d2_sign(planet["longitude"]))
    if varga == "D3":
        return _dignity_from_sign(planet["name"], get_d3_sign(planet["longitude"]))
    if varga == "D7":
        return _dignity_from_sign(planet["name"], get_d7_sign(planet["longitude"]))
    if varga == "D9":
        return _dignity_from_sign(planet["name"], get_d9_sign(planet["longitude"]))
    if varga == "D10":
        return _dignity_from_sign(planet["name"], get_d10_sign(planet["longitude"]))
    if varga == "D12":
        return _dignity_from_sign(planet["name"], get_d12_sign(planet["longitude"]))
    if varga == "D60":
        return _dignity_from_sign(planet["name"], get_d60_sign(planet["longitude"]))
    return "neutral"


def compute_vimsopaka(planet):
    total = 0.0
    total_weight = 0.0

    for varga, weight in VARGA_WEIGHTS.items():
        dignity = get_varga_dignity(planet, varga)
        score = DIGNITY_SCORES[normalize_dignity(dignity)]
        total += weight * score
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(total / total_weight, 2)


def calculate_vimsopaka(planet_varga_positions):
    total = 0.0
    total_weight = 0.0
    for varga, dignity in planet_varga_positions.items():
        weight = VARGA_WEIGHTS.get(varga, 0.5)
        score = DIGNITY_SCORES[normalize_dignity(dignity)]
        total += weight * score
        total_weight += weight
    if total_weight == 0:
        return 0.0
    return round(total / total_weight, 2)
