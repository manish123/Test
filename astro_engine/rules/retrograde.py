def apply_retrograde(planet):
    if not planet["retrograde"]:
        return planet["multiplier"]

    if planet["status"] == "debilitated":
        # Retrograde debilitated = neechabhanga-like effect, treat as neutral
        return 1.0

    if planet["status"] == "exalted":
        # Retrograde exalted = reduced strength (not zeroed — planet still exists)
        return planet["multiplier"] * 0.75

    return planet["multiplier"] * 1.2
