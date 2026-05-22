MOVABLE_SIGNS = {1, 4, 7, 10}
FIXED_SIGNS = {2, 5, 8, 11}
DUAL_SIGNS = {3, 6, 9, 12}


def _house_offset(base_sign, offset):
    return ((base_sign - 1 + offset) % 12) + 1


def get_badhaka_house(asc_sign):
    if asc_sign in MOVABLE_SIGNS:
        return 11
    if asc_sign in FIXED_SIGNS:
        return 9
    if asc_sign in DUAL_SIGNS:
        return 7
    return 7


def get_badhakesh(lagna_sign, sign_lords):
    badhaka_house = get_badhaka_house(lagna_sign)
    badhaka_sign = _house_offset(lagna_sign, badhaka_house - 1)
    return sign_lords[badhaka_sign]


def is_badhakesh_active(badhakesh, aspects, target_houses):
    return any(h in aspects.get(badhakesh, []) for h in target_houses)
