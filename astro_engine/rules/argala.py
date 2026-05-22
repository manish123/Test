def _house_offset(base_house, offset):
    return ((base_house - 1 + offset) % 12) + 1


def compute_argala_score(reference_house, occupied_houses):
    argala = 0
    virodha = 0

    argala_houses = [
        _house_offset(reference_house, 1),
        _house_offset(reference_house, 3),
        _house_offset(reference_house, 10),
        _house_offset(reference_house, 4),
    ]
    virodha_houses = [
        _house_offset(reference_house, -1),
        _house_offset(reference_house, -3),
        _house_offset(reference_house, -10),
        _house_offset(reference_house, -4),
    ]

    for house in argala_houses:
        if house in occupied_houses:
            argala += 1

    for house in virodha_houses:
        if house in occupied_houses:
            virodha += 1

    return argala - virodha


def compute_reverse_argala(node_house, occupied_houses):
    reverse_argala_houses = [
        _house_offset(node_house, -1),
        _house_offset(node_house, -3),
        _house_offset(node_house, -10),
    ]
    reverse_virodha_houses = [
        _house_offset(node_house, 1),
        _house_offset(node_house, 3),
        _house_offset(node_house, 10),
    ]

    argala_points = sum(1 for h in reverse_argala_houses if h in occupied_houses)
    virodha_points = sum(1 for h in reverse_virodha_houses if h in occupied_houses)
    return argala_points - virodha_points
