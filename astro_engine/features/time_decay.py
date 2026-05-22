def time_decay_probability(orb_degree, applying=True):
    if orb_degree > 12:
        return 0.0

    base = max(0.0, 100 - (orb_degree * 8.33))
    if applying:
        return round(base, 2)
    return round(base * 0.5, 2)
