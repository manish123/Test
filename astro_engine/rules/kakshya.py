KAKSHYA_LORDS = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Ascendant"]


def get_kakshya_index(longitude):
    degree_in_sign = longitude % 30
    return int(degree_in_sign / 3.75)


def get_kakshya_lord(longitude):
    idx = max(0, min(7, get_kakshya_index(longitude)))
    return KAKSHYA_LORDS[idx]


def kakshya_trigger(transit_longitude, bav_bindus_by_lord):
    lord = get_kakshya_lord(transit_longitude)
    bindu = bav_bindus_by_lord.get(lord, 0)
    return {
        "lord": lord,
        "active": bindu >= 1,
        "window_days": "5-10" if bindu >= 1 else None,
    }


def detect_kakshya_cluster(planets, ashtakavarga):
    bav = (ashtakavarga or {}).get("bav") or {}
    tracked_planets = [
        p
        for p in (planets or [])
        if p.get("name") in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    ]

    inactive = []
    active = []
    for p in tracked_planets:
        sign = int(p.get("sign", 0))
        if sign < 1 or sign > 12:
            continue

        bav_bindus_by_lord = {}
        for lord in KAKSHYA_LORDS:
            if lord == "Ascendant":
                bav_bindus_by_lord[lord] = 1
            else:
                bav_bindus_by_lord[lord] = (bav.get(lord, [0] * 12) or [0] * 12)[sign - 1]

        trigger = kakshya_trigger(p.get("longitude", 0), bav_bindus_by_lord)
        item = {
            "planet": p.get("name"),
            "sign": sign,
            "kakshya_lord": trigger.get("lord"),
            "active": bool(trigger.get("active")),
        }
        if trigger.get("active"):
            active.append(item)
        else:
            inactive.append(item)

    inactive_count = len(inactive)
    if inactive_count >= 4:
        level = "SEVERE"
        risk_points = 20
    elif inactive_count >= 3:
        level = "ELEVATED"
        risk_points = 12
    elif inactive_count >= 2:
        level = "MILD"
        risk_points = 6
    else:
        level = "LOW"
        risk_points = 0

    return {
        "tracked_planets": len(tracked_planets),
        "inactive_count": inactive_count,
        "active_count": len(active),
        "level": level,
        "risk_points": risk_points,
        "caution": inactive_count >= 3,
        "block_entry": inactive_count >= 4,
        "inactive_planets": inactive,
        "active_planets": active,
    }
