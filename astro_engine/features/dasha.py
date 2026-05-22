from datetime import timedelta


NAKSHATRA_SIZE = 13.3333333333


DASHA_SEQUENCE = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]

DASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}


def get_current_dasha(birth_year, current_year):
    age = current_year - birth_year

    cumulative = 0

    for planet in DASHA_SEQUENCE:
        cumulative += DASHA_YEARS[planet]

        if age <= cumulative:
            return planet

    return "Mercury"


def _next_lord(current_lord):
    idx = DASHA_SEQUENCE.index(current_lord)
    return DASHA_SEQUENCE[(idx + 1) % len(DASHA_SEQUENCE)]


def _years_to_days(years):
    return years * 365.2425


def _starting_lord_from_moon(moon_longitude):
    nak_index = int((moon_longitude % 360) / NAKSHATRA_SIZE)
    return DASHA_SEQUENCE[nak_index % len(DASHA_SEQUENCE)]


def _starting_lord_balance_years(moon_longitude, lord):
    position_in_nak = (moon_longitude % 360) % NAKSHATRA_SIZE
    remaining_fraction = max(0.0, (NAKSHATRA_SIZE - position_in_nak) / NAKSHATRA_SIZE)
    return DASHA_YEARS[lord] * remaining_fraction


def _generate_md_periods(birth_dt, moon_longitude, years=150):
    periods = []

    start_lord = _starting_lord_from_moon(moon_longitude)
    first_years = _starting_lord_balance_years(moon_longitude, start_lord)
    current_start = birth_dt
    current_lord = start_lord
    consumed = 0.0
    first = True

    while consumed < years:
        span_years = first_years if first else DASHA_YEARS[current_lord]
        first = False

        current_end = current_start + timedelta(days=_years_to_days(span_years))
        periods.append(
            {
                "lord": current_lord,
                "start": current_start,
                "end": current_end,
                "years": span_years,
            }
        )

        consumed += span_years
        current_start = current_end
        current_lord = _next_lord(current_lord)

    return periods


def _generate_ad_periods(md_period):
    ad_periods = []
    md_lord = md_period["lord"]
    md_start = md_period["start"]
    md_years = md_period["years"]

    idx = DASHA_SEQUENCE.index(md_lord)
    ordered_lords = DASHA_SEQUENCE[idx:] + DASHA_SEQUENCE[:idx]

    cursor = md_start
    for ad_lord in ordered_lords:
        ad_years = (md_years * DASHA_YEARS[ad_lord]) / 120.0
        ad_end = cursor + timedelta(days=_years_to_days(ad_years))
        ad_periods.append(
            {
                "lord": ad_lord,
                "start": cursor,
                "end": ad_end,
                "years": ad_years,
            }
        )
        cursor = ad_end

    if ad_periods:
        ad_periods[-1]["end"] = md_period["end"]

    return ad_periods


def get_current_vimshottari(birth_dt, current_dt, moon_longitude):
    md_periods = _generate_md_periods(birth_dt, moon_longitude)
    md = next((p for p in md_periods if p["start"] <= current_dt < p["end"]), md_periods[-1])

    ad_periods = _generate_ad_periods(md)
    ad = next((p for p in ad_periods if p["start"] <= current_dt < p["end"]), ad_periods[-1])

    elapsed_days = (current_dt - md["start"]).days
    remaining_days = (md["end"] - current_dt).days
    sandhi_active = elapsed_days <= 183 or remaining_days <= 183

    return {
        "md": md["lord"],
        "ad": ad["lord"],
        "md_start": md["start"],
        "md_end": md["end"],
        "ad_start": ad["start"],
        "ad_end": ad["end"],
        "sandhi_active": sandhi_active,
        "sandhi_risk": 25 if sandhi_active else 0,
        "sandhi_confidence_multiplier": 0.6 if sandhi_active else 1.0,
    }
