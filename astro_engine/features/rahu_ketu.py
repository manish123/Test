NODE_DIGNITY = {
    "Rahu": {
        "exalt": 2,
        "moolatrikona": 3,
        "own": 11,
    },
    "Ketu": {
        "exalt": 8,
        "moolatrikona": 9,
        "own": 8,
    },
}


def _house_offset(base_house, offset):
    return ((base_house - 1 + offset) % 12) + 1


def get_node_aspect_houses(house):
    return [((house + 4 - 1) % 12) + 1, ((house + 6 - 1) % 12) + 1, ((house + 8 - 1) % 12) + 1]


def get_node_dignity(node_name, sign):
    cfg = NODE_DIGNITY.get(node_name, {})
    if sign == cfg.get("exalt"):
        return "exalted", 1.5
    if sign == cfg.get("moolatrikona"):
        return "moolatrikona", 1.25
    if sign == cfg.get("own"):
        return "own", 1.15
    return "neutral", 1.0


def proxy_node_strength(proxy_lord_multiplier, node_name, node_sign):
    _, node_factor = get_node_dignity(node_name, node_sign)
    return round(proxy_lord_multiplier * node_factor, 2)


def node_crisis_score(node_house):
    if node_house in [1, 7, 8, 12]:
        return 50
    if node_house in [3, 6, 10, 11]:
        return -30
    return 0


def reverse_argala_points(node_house, occupied_houses):
    node_argala = [_house_offset(node_house, -1), _house_offset(node_house, -3), _house_offset(node_house, -10)]
    node_virodha = [_house_offset(node_house, -11), _house_offset(node_house, -9), _house_offset(node_house, -2)]
    argala = sum(1 for h in node_argala if h in occupied_houses)
    virodha = sum(1 for h in node_virodha if h in occupied_houses)
    return argala - virodha


def rahu_chara_karaka_degree(rahu_longitude):
    return 30 - (rahu_longitude % 30)


def resolve_co_lordship(sign, planets):
    if sign == 11:
        lords = ["Saturn", "Rahu"]
    elif sign == 8:
        lords = ["Mars", "Ketu"]
    else:
        return None

    by_name = {p["name"]: p for p in planets}
    p1 = by_name.get(lords[0])
    p2 = by_name.get(lords[1])

    if p1 and p2:
        if p1.get("status") == "exalted" and p2.get("status") != "exalted":
            return lords[0]
        if p2.get("status") == "exalted" and p1.get("status") != "exalted":
            return lords[1]
        return lords[0] if p1.get("house", 0) <= p2.get("house", 0) else lords[1]

    return lords[0] if p1 else lords[1]


def node_yogakaraka(node_house, aspecting_houses):
    in_kendra = node_house in [1, 4, 7, 10]
    in_trikona = node_house in [1, 5, 9]
    if in_kendra and any(h in [1, 5, 9] for h in aspecting_houses):
        return True
    if in_trikona and any(h in [1, 4, 7, 10] for h in aspecting_houses):
        return True
    return False


def detect_kala_sarpa(rahu_lon, ketu_lon, planet_longitudes):
    start = rahu_lon % 360
    end = ketu_lon % 360

    def _between(a, b, x):
        if a <= b:
            return a <= x <= b
        return x >= a or x <= b

    between_direct = all(_between(start, end, lon % 360) for lon in planet_longitudes)
    between_reverse = all(_between(end, start, lon % 360) for lon in planet_longitudes)

    if between_direct:
        return True, "anuloma"
    if between_reverse:
        return True, "viloma"
    return False, None
