FATHER_SON_EXEMPTIONS = {("Sun", "Saturn"), ("Saturn", "Sun"), ("Moon", "Mercury"), ("Mercury", "Moon")}


def is_vedha_blocked(transit_house, vedha_house, planets_by_house, transit_planet=None, blocker_planet=None):
    occupants = planets_by_house.get(vedha_house, [])
    if not occupants:
        return False

    if transit_planet and blocker_planet and (transit_planet, blocker_planet) in FATHER_SON_EXEMPTIONS:
        return False

    if blocker_planet and blocker_planet in occupants:
        return False

    return True
