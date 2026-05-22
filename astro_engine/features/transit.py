def house_distance(a, b):
    return (b - a) % 12


def _angular_distance(a, b):
    diff = abs((a - b) % 360)
    return min(diff, 360 - diff)


def _aspect_offsets_degrees(planet_name):
    if planet_name == "Jupiter":
        return [0, 120, 180, 240]
    if planet_name == "Saturn":
        return [0, 60, 180, 270]
    return [0, 180]


def _min_aspect_orb(planet_name, planet_lon, target_lons):
    if not target_lons:
        return 180.0

    offsets = _aspect_offsets_degrees(planet_name)
    aspect_points = [((planet_lon + off) % 360) for off in offsets]
    return min(_angular_distance(ap, tl) for ap in aspect_points for tl in target_lons)


def check_double_transit(jupiter_house, saturn_house, target_house):
    jupiter_dist = house_distance(jupiter_house, target_house)
    saturn_dist = house_distance(saturn_house, target_house)

    jupiter_ok = jupiter_dist in [0, 4, 6, 8]
    saturn_ok = saturn_dist in [0, 2, 6, 9]

    if jupiter_ok and saturn_ok:
        return 1.0

    if jupiter_ok or saturn_ok:
        return 0.5

    return 0.0


def check_event_transit(jupiter_house, saturn_house, target_houses):
    if not target_houses:
        return 0.0

    strengths = [check_double_transit(jupiter_house, saturn_house, h) for h in target_houses]
    return max(strengths) if strengths else 0.0


def event_orb_degree(jupiter_lon, saturn_lon, target_lons):
    j_orb = _min_aspect_orb("Jupiter", jupiter_lon, target_lons)
    s_orb = _min_aspect_orb("Saturn", saturn_lon, target_lons)
    return min(j_orb, s_orb)
