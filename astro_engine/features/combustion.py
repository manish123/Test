COMBUSTION_THRESHOLDS = {
    "Moon": 12,
    "Mars": 17,
    "Mercury": 14,
    "Jupiter": 11,
    "Venus": 10,
    "Saturn": 15,
}

RETROGRADE_THRESHOLDS = {
    "Mercury": 12,
    "Venus": 8,
}


def angular_distance(a, b):
    diff = abs((a - b) % 360)
    return min(diff, 360 - diff)


def is_combust(planet_name, planet_lon, sun_lon, retrograde=False):
    if planet_name in ["Sun", "Rahu", "Ketu"]:
        return False

    threshold = RETROGRADE_THRESHOLDS.get(planet_name, COMBUSTION_THRESHOLDS.get(planet_name)) if retrograde else COMBUSTION_THRESHOLDS.get(planet_name)
    if threshold is None:
        return False

    return angular_distance(planet_lon, sun_lon) <= threshold


def apply_combustion(planet_name, multiplier, planet_lon, sun_lon, retrograde=False):
    threshold = RETROGRADE_THRESHOLDS.get(planet_name, COMBUSTION_THRESHOLDS.get(planet_name)) if retrograde else COMBUSTION_THRESHOLDS.get(planet_name)
    if threshold is None or planet_name in ["Sun", "Rahu", "Ketu"]:
        return multiplier, False

    distance = angular_distance(planet_lon, sun_lon)
    if distance > threshold:
        return multiplier, False

    intensity = max(0.0, min(1.0, (threshold - distance) / max(threshold, 1e-6)))
    damp_factor = 1.0 - (0.65 * intensity)
    return round(multiplier * damp_factor, 4), True
