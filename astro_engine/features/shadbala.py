STATUS_STHANA_POINTS = {
    "exalted": 60.0,
    "own": 50.0,
    "great_friend": 45.0,
    "friend": 40.0,
    "neutral": 30.0,
    "enemy": 20.0,
    "bitter_enemy": 15.0,
    "debilitated": 10.0,
}

DIG_BALA_STRONG_HOUSE = {
    "Sun": 10,
    "Mars": 10,
    "Moon": 4,
    "Venus": 4,
    "Jupiter": 1,
    "Mercury": 1,
    "Saturn": 7,
}

DAY_STRONG_PLANETS = {"Sun", "Jupiter", "Venus"}
NIGHT_STRONG_PLANETS = {"Moon", "Mars", "Saturn"}

NAISARGIKA_BALA_POINTS = {
    "Sun": 60.0,
    "Moon": 51.0,
    "Venus": 43.0,
    "Jupiter": 34.0,
    "Mercury": 26.0,
    "Mars": 17.0,
    "Saturn": 9.0,
    "Rahu": 15.0,
    "Ketu": 15.0,
}

BENEFIC_PLANETS = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFIC_PLANETS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


def _house_distance(a, b):
    diff = abs(a - b) % 12
    return min(diff, 12 - diff)


def _clamp_points(value, minimum=0.0, maximum=60.0):
    return max(minimum, min(maximum, float(value)))


def sthana_bala_points(planet):
    status = planet.get("status", "neutral")
    points = STATUS_STHANA_POINTS.get(status, STATUS_STHANA_POINTS["neutral"])

    if planet.get("is_kendra"):
        points += 5.0

    return _clamp_points(points)


def dig_bala_points(planet):
    name = planet.get("name")
    house = planet.get("house")
    if house is None or name not in DIG_BALA_STRONG_HOUSE:
        return 30.0

    strongest_house = DIG_BALA_STRONG_HOUSE[name]
    distance = _house_distance(house, strongest_house)
    return _clamp_points(60.0 - (distance * 10.0))


def naisargika_bala_points(planet):
    return _clamp_points(NAISARGIKA_BALA_POINTS.get(planet.get("name"), 30.0))


def cheshta_bala_points(planet):
    points = 30.0

    if planet.get("retrograde"):
        points += 15.0

    if planet.get("combust"):
        points -= 10.0

    return _clamp_points(points)


def drik_bala_points(planet, chart):
    name = planet.get("name")
    aspects = chart.get("aspects", {})

    benefic_total = 0.0
    malefic_total = 0.0

    for source, targets in aspects.items():
        if source == name:
            continue
        strength = float(targets.get(name, 0.0))
        if strength <= 0:
            continue

        if source in BENEFIC_PLANETS:
            benefic_total += strength
        elif source in MALEFIC_PLANETS:
            malefic_total += strength

    score = 30.0 + ((benefic_total - malefic_total) * 20.0)
    return _clamp_points(score)


def kala_bala_points(planet, chart):
    name = planet.get("name")
    dt = chart.get("datetime")
    if dt is None or name == "Mercury":
        return 30.0

    is_day = 6 <= dt.hour < 18

    if name in DAY_STRONG_PLANETS:
        return 45.0 if is_day else 25.0
    if name in NIGHT_STRONG_PLANETS:
        return 45.0 if not is_day else 25.0

    return 30.0


def compute_shadbala(planet, chart):
    sthana = sthana_bala_points(planet)
    dig = dig_bala_points(planet)
    kala = kala_bala_points(planet, chart)
    naisargika = naisargika_bala_points(planet)
    cheshta = cheshta_bala_points(planet)
    drik = drik_bala_points(planet, chart)

    total = round(sthana + dig + kala + naisargika + cheshta + drik, 2)
    normalized = total / 360.0
    multiplier = round(max(0.75, min(1.25, 0.75 + (normalized * 0.5))), 4)

    return {
        "sthana_bala": round(sthana, 2),
        "dig_bala": round(dig, 2),
        "kala_bala": round(kala, 2),
        "naisargika_bala": round(naisargika, 2),
        "cheshta_bala": round(cheshta, 2),
        "drik_bala": round(drik, 2),
        "total": total,
        "normalized": round(normalized, 4),
        "multiplier": multiplier,
    }
