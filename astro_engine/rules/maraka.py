def identify_maraka_houses():
    return [2, 7]


def _relative_sign(base_sign, offset):
    return ((base_sign - 1 + offset) % 12) + 1


def identify_maraka_lords(sign_lords, lagna_sign):
    second_sign = _relative_sign(lagna_sign, 1)
    seventh_sign = _relative_sign(lagna_sign, 6)
    return {sign_lords[second_sign], sign_lords[seventh_sign]}


def secondary_maraka_planets(planets, sign_lords, lagna_sign):
    eighth_sign = _relative_sign(lagna_sign, 7)
    eighth_lord = sign_lords[eighth_sign]
    house_occupants = {p["name"] for p in planets if p.get("house") in identify_maraka_houses()}
    return {
        "eighth_lord": eighth_lord,
        "maraka_house_occupants": house_occupants,
    }


def maraka_score(planets, sign_lords=None, lagna_sign=None):
    maraka_houses = identify_maraka_houses()
    maraka_planets = [p for p in planets if p.get("house") in maraka_houses]
    if not maraka_planets:
        return 0

    severe = any(p["name"] in ["Rahu", "Ketu", "Saturn", "Mars"] for p in maraka_planets)
    score = 40 if severe else 20

    if sign_lords and lagna_sign:
        secondary = secondary_maraka_planets(planets, sign_lords, lagna_sign)
        active_secondary = secondary["eighth_lord"] in secondary["maraka_house_occupants"]
        if active_secondary:
            score += 10

    return score


def maraka_trigger_risk(md_lord, ad_lord, maraka_lords, age_years, longevity_bracket, planet_in_8th=False):
    risk = 0

    if md_lord in maraka_lords:
        risk += 15

    if ad_lord in maraka_lords:
        risk += 25

    if planet_in_8th:
        risk += 20

    if risk >= 50:
        return risk, "critical"
    if risk > 0:
        return risk, "warning"
    return 0, None
