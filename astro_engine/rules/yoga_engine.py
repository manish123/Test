KENDRA_HOUSES = {1, 4, 7, 10}
TRIK_HOUSES = {6, 8, 12}
GOOD_HOUSES = {1, 2, 3, 4, 5, 7, 9, 10, 11}


def _planet_by_name(planets):
    return {p["name"]: p for p in planets}


def detect_mahapurusha(planets):
    active = []
    for p in planets:
        if p["name"] not in {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}:
            continue
        if p.get("status") in {"exalted", "own"} and p.get("house") in KENDRA_HOUSES:
            active.append(p["name"])
    return active


def detect_dainya_yoga(planets, sign_lords):
    by_planet = _planet_by_name(planets)

    trik_lords = [sign_lords[s] for s in [6, 8, 12]]
    good_lords = [sign_lords[s] for s in GOOD_HOUSES]

    for t_lord in trik_lords:
        p1 = by_planet.get(t_lord)
        if not p1:
            continue

        for g_lord in good_lords:
            p2 = by_planet.get(g_lord)
            if not p2:
                continue

            if sign_lords.get(p1.get("sign")) == g_lord and sign_lords.get(p2.get("sign")) == t_lord:
                return True

    return False


def detect_dhana_yoga(asc_sign, planets):
    by_planet = _planet_by_name(planets)

    if asc_sign == 5:
        sun = by_planet.get("Sun")
        mars = by_planet.get("Mars")
        jupiter = by_planet.get("Jupiter")
        if sun and mars and jupiter and sun.get("house") == 1 and mars.get("house") in {5, 7, 9} and jupiter.get("house") in {5, 7, 9}:
            return True

    if asc_sign == 4:
        moon = by_planet.get("Moon")
        mercury = by_planet.get("Mercury")
        jupiter = by_planet.get("Jupiter")
        if moon and mercury and jupiter and moon.get("house") == 1 and mercury.get("house") in {5, 7, 9} and jupiter.get("house") in {5, 7, 9}:
            return True

    return False


def is_yoga_active(yoga_planets, dasha_lord, transit_houses, yoga_houses):
    if dasha_lord in yoga_planets:
        return True
    return any(h in transit_houses for h in yoga_houses)


def detect_yoga_bhanga(planets):
    debilitated_count = sum(1 for p in planets if p.get("status") == "debilitated")
    if debilitated_count >= 5:
        return True

    moon = next((p for p in planets if p["name"] == "Moon"), None)
    if moon and moon.get("sign") == 8 and (moon.get("longitude") % 30) <= 3 and moon.get("multiplier", 1.0) < 0.8:
        return True

    sun = next((p for p in planets if p["name"] == "Sun"), None)
    mars = next((p for p in planets if p["name"] == "Mars"), None)
    saturn = next((p for p in planets if p["name"] == "Saturn"), None)
    if sun and mars and saturn and {sun.get("house"), mars.get("house"), saturn.get("house")}.issubset({3, 6, 7}):
        return True

    return False


def evaluate_yogas(planets, asc_sign, sign_lords, dasha_lord, transit_houses):
    mahapurusha = detect_mahapurusha(planets)
    dainya = detect_dainya_yoga(planets, sign_lords)
    dhana = detect_dhana_yoga(asc_sign, planets)
    bhanga = detect_yoga_bhanga(planets)

    yoga_score = 0
    if mahapurusha and is_yoga_active(mahapurusha, dasha_lord, transit_houses, [1, 4, 7, 10]):
        yoga_score += 30
    if dhana and is_yoga_active(["Sun", "Moon", "Mars", "Jupiter", "Mercury"], dasha_lord, transit_houses, [1, 2, 11]):
        yoga_score += 20
    if dainya:
        yoga_score -= 20

    return {
        "mahapurusha": mahapurusha,
        "dainya": dainya,
        "dhana": dhana,
        "bhanga": bhanga,
        "score": yoga_score,
    }
