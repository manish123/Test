MOVABLE = {1, 4, 7, 10}
FIXED = {2, 5, 8, 11}
DUAL = {3, 6, 9, 12}


def _adjacent(sign):
    return {((sign - 2) % 12) + 1, (sign % 12) + 1}


def get_rasi_drishti(sign):
    if sign in MOVABLE:
        return sorted(FIXED - _adjacent(sign))
    if sign in FIXED:
        return sorted(MOVABLE - _adjacent(sign))
    return sorted(DUAL - {sign})


def sign_aspects(sign, target_sign):
    return target_sign in get_rasi_drishti(sign)
