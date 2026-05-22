def get_jagradadi_multiplier(status):
    if status in ["exalted", "own"]:
        return 1.0
    if status in ["great_friend", "friend"]:
        return 0.75
    if status == "neutral":
        return 0.5
    if status in ["enemy", "bitter_enemy", "debilitated"]:
        return 0.25  # Turiya state — weakened but not zeroed out
    return 0.5


def get_lajjitadi_state(planet, chart):
    house = planet.get("house")
    conjunctions = chart.get("conjunctions", {})
    conjoined = conjunctions.get(planet["name"], [])

    if house == 5 and any(p in conjoined for p in ["Rahu", "Ketu", "Sun", "Saturn", "Mars"]):
        return "lajjita"
    if "Sun" in conjoined:
        return "kshobhita"
    if any(p in conjoined for p in ["Jupiter", "Venus"]):
        return "mudita"
    if planet.get("sign") in [4, 8, 12] and not any(p in conjoined for p in ["Jupiter", "Venus", "Moon"]):
        return "trishita"
    if planet.get("status") in ["exalted", "own"]:
        return "garvita"
    if planet.get("status") in ["enemy", "debilitated"] or "Saturn" in conjoined:
        return "kshudita"
    return "normal"
