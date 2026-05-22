from astronomy.utils import normalize_lon


def get_d1_sign(longitude):
    return int(normalize_lon(longitude) // 30) + 1


def get_d2_sign(longitude):
    longitude = normalize_lon(longitude)
    d1_sign = get_d1_sign(longitude)
    degree_in_sign = longitude % 30

    odd_sign = d1_sign in [1, 3, 5, 7, 9, 11]
    if odd_sign:
        return 5 if degree_in_sign < 15 else 4
    return 4 if degree_in_sign < 15 else 5


def get_d3_sign(longitude):
    longitude = normalize_lon(longitude)
    d1_sign = get_d1_sign(longitude)
    drekkana_part = int((longitude % 30) / 10)
    return ((d1_sign + (drekkana_part * 4) - 1) % 12) + 1


def get_d7_sign(longitude):
    longitude = normalize_lon(longitude)
    d1_sign = get_d1_sign(longitude)
    part = int((longitude % 30) / (30 / 7))
    start_sign = d1_sign if d1_sign in [1, 3, 5, 7, 9, 11] else ((d1_sign + 6 - 1) % 12) + 1
    return ((start_sign + part - 1) % 12) + 1


def get_d10_sign(longitude):
    longitude = normalize_lon(longitude)
    d1_sign = get_d1_sign(longitude)
    part = int((longitude % 30) / 3)
    movable = [1, 4, 7, 10]
    fixed = [2, 5, 8, 11]

    if d1_sign in movable:
        start_sign = d1_sign
    elif d1_sign in fixed:
        start_sign = ((d1_sign + 8 - 1) % 12) + 1
    else:
        start_sign = ((d1_sign + 4 - 1) % 12) + 1

    return ((start_sign + part - 1) % 12) + 1


def get_d12_sign(longitude):
    longitude = normalize_lon(longitude)
    d1_sign = get_d1_sign(longitude)
    part = int((longitude % 30) / (30 / 12))
    return ((d1_sign + part - 1) % 12) + 1


def get_d9_sign(longitude):
    longitude = normalize_lon(longitude)
    d1_sign = get_d1_sign(longitude)
    degree_in_sign = longitude % 30
    navamsha_part = int(degree_in_sign / (30 / 9)) + 1

    if d1_sign in [1, 4, 7, 10]:
        start_sign = d1_sign
    elif d1_sign in [2, 5, 8, 11]:
        start_sign = ((d1_sign + 8 - 1) % 12) + 1
    else:
        start_sign = ((d1_sign + 4 - 1) % 12) + 1

    return ((start_sign + navamsha_part - 2) % 12) + 1


def get_d60_sign(longitude):
    longitude = normalize_lon(longitude)
    d1_sign = get_d1_sign(longitude)
    degree_in_sign = longitude % 30
    d60_multiplier = degree_in_sign * 2
    d60_remainder = d60_multiplier % 12
    return int(((d1_sign + d60_remainder - 1) % 12) + 1)


def classify_vimsopaka_promise(score):
    if score >= 15:
        return "strong", 1.0
    if score >= 10:
        return "moderate", 0.65
    if score >= 5:
        return "weak", 0.4
    return "nil", 0.0
