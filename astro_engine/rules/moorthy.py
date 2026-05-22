def moorthy_grade(natal_moon_sign, transit_moon_sign):
    house_count = ((transit_moon_sign - natal_moon_sign) % 12) + 1

    if house_count in [1, 6, 11]:
        return "Swarna", 1.2
    if house_count in [2, 5, 9]:
        return "Rajata", 1.1
    if house_count in [3, 7, 10]:
        return "Taamra", 0.9
    return "Loha", 0.7
