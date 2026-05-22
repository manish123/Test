WAR_PLANETS = {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}


def _distance(a, b):
    diff = abs((a - b) % 360)
    return min(diff, 360 - diff)


def detect_graha_yuddha(planets):
    losers = set()

    for i in range(len(planets)):
        p1 = planets[i]
        if p1["name"] not in WAR_PLANETS:
            continue

        for j in range(i + 1, len(planets)):
            p2 = planets[j]
            if p2["name"] not in WAR_PLANETS:
                continue

            if _distance(p1["longitude"], p2["longitude"]) <= 1.0:
                if "Venus" in [p1["name"], p2["name"]]:
                    loser = p2["name"] if p1["name"] == "Venus" else p1["name"]
                else:
                    lat1 = p1.get("latitude")
                    lat2 = p2.get("latitude")
                    if lat1 is not None and lat2 is not None:
                        loser = p1["name"] if lat1 < lat2 else p2["name"]
                    else:
                        loser = p1["name"] if p1["longitude"] < p2["longitude"] else p2["name"]
                losers.add(loser)

    return losers
