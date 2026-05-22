GOOD_NAK = ["Rohini", "Pushya", "Anuradha", "Vishakha"]
BAD_NAK = ["Mrigashira", "Ardra", "Ashlesha", "Jyeshtha", "Dhanishta"]


def nakshatra_adjustment(nakshatra):
    if nakshatra in GOOD_NAK:
        return 1.1

    if nakshatra in BAD_NAK:
        return 0.85

    return 1.0
