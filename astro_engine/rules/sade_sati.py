def sade_sati_phase(moon_sign, saturn_sign):
    diff = (saturn_sign - moon_sign) % 12

    if diff == 11:
        return "rising", 20
    elif diff == 0:
        return "peak", 40
    elif diff == 1:
        return "setting", 25
    elif diff == 7:
        return "ashtama", 50

    return "none", 0
