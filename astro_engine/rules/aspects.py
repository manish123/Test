def _offset_house(house, offset):
    return ((house - 1 + offset) % 12) + 1


def _angular_distance(a, b):
    diff = abs((a - b) % 360)
    return min(diff, 360 - diff)


def _aspect_weight_by_orb(orb):
    if orb <= 10:
        return 1.0
    if orb <= 20:
        return 0.5
    return 0.25


def _aspect_house_offsets(planet_name):
    offsets = {6}
    if planet_name == "Mars":
        offsets.update({3, 7})
    elif planet_name == "Jupiter":
        offsets.update({4, 8})
    elif planet_name == "Saturn":
        offsets.update({2, 9})
    return offsets


def graha_aspect_houses(planet_name, source_house):
    if source_house is None:
        return set()

    return {_offset_house(source_house, off) for off in _aspect_house_offsets(planet_name)}


def _aspect_strength(source_lon, target_lon, house_offset):
    exact_aspect_lon = (source_lon + (house_offset * 30)) % 360
    orb = _angular_distance(exact_aspect_lon, target_lon)
    return _aspect_weight_by_orb(orb)


def build_graha_aspects(planets):
    by_house = {}
    for p in planets:
        h = p.get("house")
        if h is None:
            continue
        by_house.setdefault(h, []).append(p)

    aspect_map = {}
    for source in planets:
        source_name = source.get("name")
        source_house = source.get("house")
        source_lon = source.get("longitude")
        if not source_name or source_house is None:
            continue

        target_strengths = {}
        for house_offset in _aspect_house_offsets(source_name):
            target_house = _offset_house(source_house, house_offset)
            for target in by_house.get(target_house, []):
                target_name = target.get("name")
                if not target_name or target_name == source_name:
                    continue
                strength = _aspect_strength(source_lon, target.get("longitude", 0.0), house_offset)
                prev = target_strengths.get(target_name, 0.0)
                target_strengths[target_name] = max(prev, strength)

        aspect_map[source_name] = target_strengths

    return aspect_map
