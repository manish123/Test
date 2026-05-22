from datetime import timedelta


YOGINI_SEQUENCE = ["Mangala", "Pingala", "Dhanya", "Bhramari", "Bhadrika", "Ulka", "Siddha", "Sankata"]
YOGINI_YEARS = {
    "Mangala": 1,
    "Pingala": 2,
    "Dhanya": 3,
    "Bhramari": 4,
    "Bhadrika": 5,
    "Ulka": 6,
    "Siddha": 7,
    "Sankata": 8,
}


def _years_to_days(years):
    return years * 365.2425


def _starting_yogini_lord(moon_longitude):
    nak_index = int((moon_longitude % 360) / (360 / 27)) + 1
    seq_index = (nak_index + 3) % 8
    return YOGINI_SEQUENCE[seq_index]


def _generate_yogini_periods(birth_dt, moon_longitude, years=120):
    periods = []
    start_lord = _starting_yogini_lord(moon_longitude)
    start_idx = YOGINI_SEQUENCE.index(start_lord)
    cursor = birth_dt
    elapsed_years = 0.0
    idx = start_idx

    while elapsed_years < years:
        lord = YOGINI_SEQUENCE[idx % len(YOGINI_SEQUENCE)]
        span_years = YOGINI_YEARS[lord]
        end = cursor + timedelta(days=_years_to_days(span_years))
        periods.append(
            {
                "lord": lord,
                "start": cursor,
                "end": end,
                "years": span_years,
            }
        )
        cursor = end
        elapsed_years += span_years
        idx += 1

    return periods


def get_current_yogini(birth_dt, current_dt, moon_longitude):
    periods = _generate_yogini_periods(birth_dt, moon_longitude)
    current = next((p for p in periods if p["start"] <= current_dt < p["end"]), periods[-1])

    elapsed_days = (current_dt - current["start"]).days
    remaining_days = (current["end"] - current_dt).days
    sandhi_active = elapsed_days <= 45 or remaining_days <= 45

    return {
        "yd": current["lord"],
        "yd_start": current["start"],
        "yd_end": current["end"],
        "sandhi_active": sandhi_active,
        "sandhi_confidence_multiplier": 0.8 if sandhi_active else 1.0,
    }


def yogini_cross_validation(vimshottari_active, yogini_active):
    if vimshottari_active and yogini_active:
        return 1.2
    if vimshottari_active or yogini_active:
        return 1.0
    return 0.9
