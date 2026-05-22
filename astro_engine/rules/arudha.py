def _count_signs(start_sign, end_sign):
    return ((end_sign - start_sign) % 12) + 1


def _forward_sign(start_sign, count):
    return ((start_sign - 1 + count) % 12) + 1


def compute_arudha_pada(house_sign, lord_sign):
    distance = _count_signs(house_sign, lord_sign)
    pada = _forward_sign(lord_sign, distance - 1)

    if pada == house_sign:
        return _forward_sign(house_sign, 9)

    seventh = _forward_sign(house_sign, 6)
    if pada == seventh:
        return _forward_sign(house_sign, 3)

    return pada
