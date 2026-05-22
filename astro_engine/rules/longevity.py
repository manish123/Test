def _category_from_pair(a_sign, b_sign):
    movable = {1, 4, 7, 10}
    fixed = {2, 5, 8, 11}
    dual = {3, 6, 9, 12}

    def _t(sign):
        if sign in movable:
            return "mov"
        if sign in fixed:
            return "fix"
        return "dual"

    ta = _t(a_sign)
    tb = _t(b_sign)

    if (ta == "mov" and tb == "mov") or (ta == "fix" and tb == "dual") or (ta == "dual" and tb == "fix"):
        return "long"
    if (ta == "mov" and tb == "fix") or (ta == "fix" and tb == "mov") or (ta == "dual" and tb == "dual"):
        return "medium"
    return "short"


def _mode(values):
    counts = {k: values.count(k) for k in set(values)}
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[0][0]


def estimate_jaimini_longevity(asc_lord_sign, eighth_lord_sign, moon_sign, saturn_sign, asc_sign, hora_lagna_sign):
    pair_1 = _category_from_pair(asc_lord_sign, eighth_lord_sign)
    pair_2 = _category_from_pair(moon_sign, saturn_sign)
    pair_3 = _category_from_pair(asc_sign, hora_lagna_sign)

    final = _mode([pair_1, pair_2, pair_3])
    bracket = {
        "short": (0, 36),
        "medium": (36, 72),
        "long": (72, 120),
    }[final]

    return {
        "pair_1": pair_1,
        "pair_2": pair_2,
        "pair_3": pair_3,
        "final": final,
        "age_bracket": bracket,
    }
