PLANET_OFFSET_RULES = {
    "Sun": [1, 2, 4, 7, 8, 9, 10, 11],
    "Moon": [1, 3, 6, 7, 10, 11],
    "Mars": [3, 6, 10, 11],
    "Mercury": [2, 4, 6, 8, 10, 11],
    "Jupiter": [2, 5, 6, 9, 11],
    "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
    "Saturn": [3, 6, 11],
}

TRIKONA_GROUPS = [(1, 5, 9), (2, 6, 10), (3, 7, 11), (4, 8, 12)]
EKADHIPATYA_PAIRS = [(1, 8), (2, 7), (3, 6), (9, 12), (10, 11)]
MALEFICS = {"Mars", "Saturn"}
CONTRIBUTORS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Ascendant"]


def _normalize_sign(sign):
    return ((sign - 1) % 12) + 1


def _relative_house(from_sign, to_sign):
    return ((to_sign - from_sign) % 12) + 1


def compute_bav_for_planet(planet_name, contributor_signs):
    bav = [0] * 12

    valid_contributors = [name for name, sign in contributor_signs.items() if sign is not None]
    if not valid_contributors:
        return bav

    # Use the PLANET's own offset rules (not the contributor's rules).
    # Each contributor casts a bindu to a target sign if the relative house
    # from that contributor's sign to the target sign is in the PLANET's rules.
    planet_offsets = PLANET_OFFSET_RULES.get(planet_name, [])

    for target in range(1, 13):
        points = 0
        for contributor in valid_contributors:
            ref_sign = contributor_signs[contributor]
            rel = _relative_house(ref_sign, target)
            if rel in planet_offsets:
                points += 1
        bav[target - 1] = points

    return bav


def compute_bav_matrix(planet_signs, asc_sign=None):
    contributor_signs = {name: planet_signs.get(name) for name in CONTRIBUTORS if name != "Ascendant"}
    contributor_signs["Ascendant"] = asc_sign

    matrix = {}
    for planet in PLANET_OFFSET_RULES:
        matrix[planet] = compute_bav_for_planet(planet, contributor_signs)
    return matrix


def compute_sav(bav_matrix):
    sav = [0] * 12
    for row in bav_matrix.values():
        for idx, value in enumerate(row):
            sav[idx] += value
    return sav


def apply_trikona_shodhana(sav):
    reduced = sav[:]
    for a, b, c in TRIKONA_GROUPS:
        triad_values = [reduced[a - 1], reduced[b - 1], reduced[c - 1]]
        if 0 in triad_values:
            continue
        deduction = min(triad_values)
        reduced[a - 1] -= deduction
        reduced[b - 1] -= deduction
        reduced[c - 1] -= deduction
    return reduced


def apply_ekadhipatya_shodhana(sav):
    reduced = sav[:]
    for a, b in EKADHIPATYA_PAIRS:
        deduction = min(reduced[a - 1], reduced[b - 1])
        reduced[a - 1] -= deduction
        reduced[b - 1] -= deduction
    return reduced


def compute_ashtakavarga(planet_signs, asc_sign=None):
    bav = compute_bav_matrix(planet_signs, asc_sign=asc_sign)
    sav_raw = compute_sav(bav)
    sav_trikona = apply_trikona_shodhana(sav_raw)
    sav_sodhya = apply_ekadhipatya_shodhana(sav_trikona)
    return {
        "bav": bav,
        "sav_raw": sav_raw,
        "sav_trikona": sav_trikona,
        "sav_sodhya": sav_sodhya,
    }


def sav_status(score):
    if score > 28:
        return "expansion", 1.5
    if score >= 25:
        return "neutral", 1.0
    return "contraction", 0.5


def focal_sign_strength(ashtakavarga_data, sign):
    score = ashtakavarga_data["sav_sodhya"][_normalize_sign(sign) - 1]
    status, mult = sav_status(score)
    return {
        "score": score,
        "status": status,
        "multiplier": mult,
    }


def micro_transit_overlay(ashtakavarga_data, jupiter_sign, saturn_sign):
    j_score = ashtakavarga_data["sav_sodhya"][_normalize_sign(jupiter_sign) - 1]
    s_score = ashtakavarga_data["sav_sodhya"][_normalize_sign(saturn_sign) - 1]

    enhance = 1.5 if j_score > 28 else 1.0
    obstacle = 1.5 if s_score < 25 else 1.0
    return round(enhance / obstacle, 2)


def bav_risk(ashtakavarga_data, planets):
    risk = 0
    sav = ashtakavarga_data["sav_sodhya"]

    for planet in planets:
        name = planet["name"]
        if name not in MALEFICS:
            continue

        house_sign = planet.get("sign")
        if not house_sign:
            continue

        sign_idx = _normalize_sign(house_sign) - 1
        planet_bav = ashtakavarga_data["bav"].get(name, [0] * 12)

        if sav[sign_idx] < 25 and planet_bav[sign_idx] < 1:
            risk += 40

    return risk
