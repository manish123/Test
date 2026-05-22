from features.dignity import EXALTATION, SIGN_LORDS


def is_in_kendra(planet_name, chart):
    p = chart.get(planet_name)
    if not p:
        return False

    house = p.get("house")
    if house in [1, 4, 7, 10]:
        return True

    moon_house = chart.get("moon_house")
    if not moon_house:
        return False

    moon_kendras = {((moon_house - 1 + step) % 12) + 1 for step in [0, 3, 6, 9]}
    return house in moon_kendras


def get_exaltation_lord(planet_name):
    exalt_sign = EXALTATION.get(planet_name)
    if not exalt_sign:
        return None
    return SIGN_LORDS.get(exalt_sign)


def is_aspected_by(planet, aspecting_planet_name, chart):
    aspects = chart.get("aspects", {})
    target_name = planet.get("name")

    aspect_strength = aspects.get(aspecting_planet_name, {}).get(target_name, 0.0)
    if aspect_strength >= 0.5:
        return True

    source = chart.get(aspecting_planet_name)
    if not source:
        return False

    return source.get("house") == planet.get("house")


def check_neechabhanga(planet, chart):
    if planet["status"] != "debilitated":
        return False

    dispositor = planet.get("dispositor")
    if not dispositor:
        return False

    if is_in_kendra(dispositor, chart):
        return True

    exalt_lord = get_exaltation_lord(planet["name"])
    if exalt_lord and is_in_kendra(exalt_lord, chart):
        return True

    if is_aspected_by(planet, dispositor, chart):
        return True

    return False
