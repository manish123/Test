from features.dignity import SIGN_LORDS
from datetime import timedelta


def _count_distance(start_sign, end_sign):
    return ((end_sign - start_sign) % 12) + 1


def _resolve_colord(sign, planets):
    if sign == 11:
        primary, secondary = "Saturn", "Rahu"
    elif sign == 8:
        primary, secondary = "Mars", "Ketu"
    else:
        return SIGN_LORDS[sign]

    by_name = {p["name"]: p for p in planets}
    p1 = by_name.get(primary)
    p2 = by_name.get(secondary)

    if p1 and p2:
        if p1.get("status") == "exalted" and p2.get("status") != "exalted":
            return primary
        if p2.get("status") == "exalted" and p1.get("status") != "exalted":
            return secondary
        if p1.get("house", 0) <= p2.get("house", 0):
            return primary
        return secondary

    return primary if p1 else secondary


def get_chara_dasha_direction(ninth_sign):
    return 1 if ninth_sign % 2 == 1 else -1


def get_chara_dasha_sequence(asc_sign, planets):
    ninth_sign = ((asc_sign + 7 - 1) % 12) + 1
    direction = get_chara_dasha_direction(ninth_sign)

    sequence = []
    sign = asc_sign
    for _ in range(12):
        lord = _resolve_colord(sign, planets)
        lord_sign = next((p["sign"] for p in planets if p["name"] == lord), sign)
        duration = max(1, _count_distance(sign, lord_sign) - 1)
        sequence.append({"sign": sign, "lord": lord, "years": duration})
        sign = ((sign - 1 + direction) % 12) + 1

    return sequence


def _years_to_days(years):
    return years * 365.2425


def get_current_chara_dasha(birth_dt, current_dt, asc_sign, planets):
    sequence = get_chara_dasha_sequence(asc_sign, planets)
    periods = []

    cursor = birth_dt
    for item in sequence:
        end = cursor + timedelta(days=_years_to_days(item["years"]))
        periods.append(
            {
                "sign": item["sign"],
                "lord": item["lord"],
                "years": item["years"],
                "start": cursor,
                "end": end,
            }
        )
        cursor = end

    current = next((p for p in periods if p["start"] <= current_dt < p["end"]), periods[-1])
    elapsed_days = (current_dt - current["start"]).days
    remaining_days = (current["end"] - current_dt).days
    sandhi_active = elapsed_days <= 90 or remaining_days <= 90

    return {
        "sign": current["sign"],
        "lord": current["lord"],
        "start": current["start"],
        "end": current["end"],
        "years": current["years"],
        "sandhi_active": sandhi_active,
    }
