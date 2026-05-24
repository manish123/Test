"""
Financial Crisis & Debt Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow.
Domain: Financial Crisis & Debt

Follows the exact same pattern as vehicle_purchase_evaluator.py.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import swisseph as swe
from astronomy.engine_base import get_planet_positions, get_house_cusps, configure_ephemeris
from astronomy.utils import normalize_lon
from features.dasha import get_current_vimshottari, _generate_md_periods, _generate_ad_periods
from features.dignity import SIGN_LORDS, get_sign
from features.nakshatra import get_nakshatra



# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════
IST_OFFSET = timedelta(hours=5, minutes=30)
RULES_DIR = Path(__file__).resolve().parent / "domains" / "finance" / "financial_crisis_and_debt"

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

# Financial Crisis-specific constants
# 6th lord=debt, 8th lord=crisis/destruction, 12th lord=loss/expenditure
CRISIS_KARAKAS = {"Saturn", "Rahu", "Mars", "Ketu"}
# 2=savings, 6=debt, 8=crisis, 11=income, 12=loss
CRISIS_HOUSES = {2, 6, 8, 11, 12}

SIGN_NAMES = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
    5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
    9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
}

# Exaltation signs for dignity checks
EXALTATION_SIGNS = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6,
    "Jupiter": 4, "Venus": 12, "Saturn": 7, "Rahu": 3, "Ketu": 9
}
DEBILITATION_SIGNS = {
    "Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12,
    "Jupiter": 10, "Venus": 6, "Saturn": 1, "Rahu": 9, "Ketu": 3
}
OWN_SIGNS = {
    "Sun": [5], "Moon": [4], "Mars": [1, 8], "Mercury": [3, 6],
    "Jupiter": [9, 12], "Venus": [2, 7], "Saturn": [10, 11],
    "Rahu": [11], "Ketu": [8]
}



# ═══════════════════════════════════════════════════════════════
# CALIBRATION OVERLAY LOADER
# ═══════════════════════════════════════════════════════════════

def _load_calibration():
    """Load calibration overlay from JSON."""
    calibration_path = RULES_DIR / "calibration_overlay.json"
    try:
        with open(calibration_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "layer_weights": {
                "dasha_weight": 0.35,
                "transit_weight": 0.30,
                "fast_trigger_weight": 0.20,
                "classical_weight": 0.15,
            },
            "likelihood_thresholds": {
                "very_high": 55, "high": 40, "moderate": 25, "low": 15,
            },
            "outcome_calibration": {
                "mode_priority_order": ["complete_destitution", "sudden_bankruptcy",
                    "asset_seizure", "speculative_collapse", "hidden_liability",
                    "financial_dysfunction", "loan_dependency", "bad_loans"],
                "quality_priority_order": ["challenging", "mixed", "neutral"],
                "default_mode": "financial_crisis",
            },
        }


CALIBRATION = _load_calibration()


def ist_to_utc(dt):
    return dt - IST_OFFSET


def get_jd(dt_ist):
    dt_utc = ist_to_utc(dt_ist)
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute / 60.0)



# ═══════════════════════════════════════════════════════════════
# CHART STATE BUILDER
# ═══════════════════════════════════════════════════════════════

class ChartState:
    """Encapsulates all natal chart data needed for financial crisis rule evaluation."""

    def __init__(self, birth_dt, lat, lon, alt=0):
        self.birth_dt = birth_dt
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.location = {"latitude": lat, "longitude": lon, "altitude": alt}

        configure_ephemeris()
        self.birth_jd = get_jd(birth_dt)
        self.birth_positions = get_planet_positions(self.birth_jd, self.location)
        self.house_data = get_house_cusps(self.birth_jd, lat, lon)

        self.asc_lon = self.house_data["ascendant"]
        self.asc_sign = int(normalize_lon(self.asc_lon) // 30) + 1
        self.moon_lon = self.birth_positions["Moon"]
        self.moon_sign = get_sign(self.moon_lon)
        self.moon_nakshatra = get_nakshatra(self.moon_lon)

        # Compute planet data
        self.planets = {}
        for name, lon_val in self.birth_positions.items():
            sign = get_sign(lon_val)
            house = ((sign - self.asc_sign) % 12) + 1
            self.planets[name] = {
                "longitude": lon_val, "sign": sign,
                "house": house, "nakshatra": get_nakshatra(lon_val),
            }


        # House lords — financial crisis relevant
        self.lagna_lord = SIGN_LORDS[self.asc_sign]
        self.second_sign = ((self.asc_sign + 1 - 1) % 12) + 1
        self.second_lord = SIGN_LORDS[self.second_sign]
        self.third_sign = ((self.asc_sign + 2 - 1) % 12) + 1
        self.third_lord = SIGN_LORDS[self.third_sign]
        self.fifth_sign = ((self.asc_sign + 4 - 1) % 12) + 1
        self.fifth_lord = SIGN_LORDS[self.fifth_sign]
        self.sixth_sign = ((self.asc_sign + 5 - 1) % 12) + 1
        self.sixth_lord = SIGN_LORDS[self.sixth_sign]
        self.eighth_sign = ((self.asc_sign + 7 - 1) % 12) + 1
        self.eighth_lord = SIGN_LORDS[self.eighth_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.tenth_sign = ((self.asc_sign + 9 - 1) % 12) + 1
        self.tenth_lord = SIGN_LORDS[self.tenth_sign]
        self.eleventh_sign = ((self.asc_sign + 10 - 1) % 12) + 1
        self.eleventh_lord = SIGN_LORDS[self.eleventh_sign]
        self.twelfth_sign = ((self.asc_sign + 11 - 1) % 12) + 1
        self.twelfth_lord = SIGN_LORDS[self.twelfth_sign]

        # Moon lord (dispositor of Moon)
        self.moon_lord = SIGN_LORDS[self.moon_sign]

    def _get_aspectors_of_house(self, target_house):
        """Get planets that aspect a given house via Vedic aspects."""
        aspectors = []
        for name, data in self.planets.items():
            planet_house = data["house"]
            if ((planet_house + 7 - 1 - 1) % 12) + 1 == target_house:
                aspectors.append(name)
            if name == "Jupiter":
                for asp in [5, 9]:
                    if ((planet_house + asp - 1 - 1) % 12) + 1 == target_house:
                        aspectors.append(name)
            if name == "Saturn":
                for asp in [3, 10]:
                    if ((planet_house + asp - 1 - 1) % 12) + 1 == target_house:
                        aspectors.append(name)
            if name == "Mars":
                for asp in [4, 8]:
                    if ((planet_house + asp - 1 - 1) % 12) + 1 == target_house:
                        aspectors.append(name)
        return list(set(aspectors))

    def get_house_from_sign(self, transit_sign, reference_sign=None):
        """Get house number from a sign, relative to reference (default: lagna)."""
        ref = reference_sign or self.asc_sign
        return ((transit_sign - ref) % 12) + 1



# ═══════════════════════════════════════════════════════════════
# TRANSIT STATE
# ═══════════════════════════════════════════════════════════════

class TransitState:
    """Encapsulates transit positions for a specific date."""

    def __init__(self, date, chart: ChartState):
        self.date = date
        self.chart = chart
        configure_ephemeris()
        self.jd = get_jd(date)
        self.positions = get_planet_positions(self.jd, chart.location)

        self.planet_signs = {}
        self.planet_houses_from_lagna = {}
        self.planet_houses_from_moon = {}

        for name, lon_val in self.positions.items():
            sign = get_sign(lon_val)
            self.planet_signs[name] = sign
            self.planet_houses_from_lagna[name] = chart.get_house_from_sign(sign)
            self.planet_houses_from_moon[name] = chart.get_house_from_sign(sign, chart.moon_sign)

    def planet_conjunct_natal(self, planet, natal_degree, orb=5.0):
        """Check if a transit planet is conjunct a natal degree."""
        p_lon = self.positions[planet]
        diff = abs((p_lon - natal_degree) % 360)
        diff = min(diff, 360 - diff)
        return diff <= orb



# ═══════════════════════════════════════════════════════════════
# LAYER 1: DASHA EVALUATOR (Financial Crisis — 8 rules)
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate dasha rules for financial crisis.
    8 rules from dasha_rules.json.
    """
    fired = []

    # Helper: check if a planet is associated with dusthana lords
    dusthana_lords = {chart.sixth_lord, chart.eighth_lord, chart.twelfth_lord}
    trinal_lords = {chart.lagna_lord, chart.fifth_lord, chart.ninth_lord}

    # Rule 1: Planet associated with 6/8/12 lords without trinal aspect (priority 88)
    for lord in [md_lord, ad_lord]:
        lord_sign = chart.planets.get(lord, {}).get("sign", 0)
        # Check if associated with dusthana lord (same sign)
        associated = False
        for dl in dusthana_lords:
            if dl != lord and chart.planets.get(dl, {}).get("sign", 0) == lord_sign:
                associated = True
                break
        # Check if has trinal lord aspect (same sign as trinal lord = conjunction proxy)
        trinal_aspect = False
        for tl in trinal_lords:
            if tl != lord and chart.planets.get(tl, {}).get("sign", 0) == lord_sign:
                trinal_aspect = True
                break
        if associated and not trinal_aspect:
            score = 45 if lord == md_lord else 35
            fired.append(("dusthana_associated_financial_loss_gate", score,
                          [f"{lord} {'MD' if lord == md_lord else 'AD'} associated with dusthana lord, no trinal protection — financial harm"]))
            break


    # Rule 2: 8th Lord Dasha — financial crisis gate (priority 92)
    if md_lord == chart.eighth_lord:
        fired.append(("eighth_lord_financial_crisis_gate", 50,
                      [f"8th lord ({chart.eighth_lord}) MD — sudden financial crisis window active"]))
    elif ad_lord == chart.eighth_lord:
        fired.append(("eighth_lord_financial_crisis_gate", 40,
                      [f"8th lord ({chart.eighth_lord}) AD — financial crisis sub-period active"]))

    # Rule 3: Rahu Dasha bankruptcy gate (priority 90)
    if md_lord == "Rahu":
        rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
        rahu_sign = chart.planets.get("Rahu", {}).get("sign", 0)
        is_debilitated = (rahu_sign == DEBILITATION_SIGNS.get("Rahu", 0))
        in_dusthana = rahu_house in {8, 12}
        if in_dusthana or is_debilitated:
            fired.append(("rahu_dusthana_bankruptcy_gate", 48,
                          [f"Rahu MD in house {rahu_house} {'(debilitated)' if is_debilitated else ''} — severe bankruptcy risk"]))
        else:
            fired.append(("rahu_general_financial_risk", 30,
                          ["Rahu MD active — general financial instability risk"]))

    # Rule 4: Venus Dasha dusthana business loss (priority 85)
    if md_lord == "Venus":
        venus_house = chart.planets.get("Venus", {}).get("house", 0)
        if venus_house in {6, 8, 12}:
            fired.append(("venus_dusthana_business_loss_gate", 42,
                          [f"Venus MD in house {venus_house} (dusthana) — business loss period"]))


    # Rule 5: Rahu in 2nd house — capital drain (priority 82)
    if md_lord == "Rahu" or ad_lord == "Rahu":
        rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
        if rahu_house == 2:
            score = 40 if md_lord == "Rahu" else 32
            fired.append(("rahu_2nd_capital_drain_gate", score,
                          [f"Rahu {'MD' if md_lord == 'Rahu' else 'AD'} in 2nd house — savings drainage active"]))

    # Rule 6: Jupiter-Saturn adverse alignment (priority 86)
    if md_lord == "Jupiter" and ad_lord == "Saturn":
        jup_sign = chart.planets.get("Jupiter", {}).get("sign", 0)
        sat_sign = chart.planets.get("Saturn", {}).get("sign", 0)
        sat_from_jup = ((sat_sign - jup_sign) % 12) + 1
        if sat_from_jup in {6, 8, 12}:
            fired.append(("jupiter_saturn_industrial_loss_gate", 44,
                          [f"Jupiter MD + Saturn AD — Saturn in {sat_from_jup}th from Jupiter, industrial/financial loss"]))

    # Rule 7: Mercury in dusthana — asset loss (priority 80)
    if md_lord == "Mercury":
        merc_house = chart.planets.get("Mercury", {}).get("house", 0)
        if merc_house in {6, 8, 12}:
            fired.append(("mercury_dusthana_asset_loss_gate", 38,
                          [f"Mercury MD in house {merc_house} (dusthana) — poor financial judgment, asset loss"]))

    # Rule 8: Saturn-Mars debt accumulation (priority 88)
    if md_lord == "Saturn" and ad_lord == "Mars":
        mars_sign = chart.planets.get("Mars", {}).get("sign", 0)
        mars_debilitated = (mars_sign == DEBILITATION_SIGNS.get("Mars", 0))
        sat_sign = chart.planets.get("Saturn", {}).get("sign", 0)
        mars_from_sat = ((mars_sign - sat_sign) % 12) + 1
        adverse = mars_debilitated or mars_from_sat in {8, 12}
        if adverse:
            fired.append(("saturn_mars_debt_accumulation_gate", 46,
                          [f"Saturn MD + Mars AD — Mars {'debilitated' if mars_debilitated else f'in {mars_from_sat}th from Saturn'}, heavy debt"]))
        else:
            fired.append(("saturn_mars_general_stress", 28,
                          ["Saturn MD + Mars AD — financial stress period (Mars not severely afflicted)"]))

    # Bonus: 6th lord dasha (debt activation)
    if md_lord == chart.sixth_lord:
        if not any("dusthana" in f[0] for f in fired):
            fired.append(("sixth_lord_debt_activation", 35,
                          [f"6th lord ({chart.sixth_lord}) MD — debt house ruler active, financial obligations increase"]))

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR (Financial Crisis — 4 rules)
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate transit rules for financial crisis activation.
    4 rules: Saturn on Sun, Jupiter 8/9/12 from Moon,
    Rahu adverse from Moon, malefics left-leg nakshatras.
    """
    fired = []

    # Rule 1: Saturn transit on natal Sun (priority 90)
    natal_sun_lon = chart.birth_positions["Sun"]
    if transit.planet_conjunct_natal("Saturn", natal_sun_lon, orb=5.0):
        fired.append(("saturn_sun_sudden_financial_loss", 44,
                      ["Transit Saturn conjunct natal Sun — sudden financial loss, authority collapse"]))

    # Rule 2: Jupiter in 8/9/12 from Moon (priority 85)
    jup_from_moon = transit.planet_houses_from_moon.get("Jupiter", 0)
    if jup_from_moon in {8, 9, 12}:
        fired.append(("jupiter_adverse_moon_financial_loss", 40,
                      [f"Transit Jupiter in {jup_from_moon}th from Moon — false optimism, financial over-extension"]))

    # Rule 3: Rahu in 2/5/7/9/12 from Moon (priority 87)
    rahu_from_moon = transit.planet_houses_from_moon.get("Rahu", 0)
    if rahu_from_moon in {2, 5, 7, 9, 12}:
        fired.append(("rahu_adverse_moon_financial_instability", 42,
                      [f"Transit Rahu in {rahu_from_moon}th from Moon — deception, speculation failure"]))

    # Rule 4: Saturn/Rahu/Ketu in 9-11th nakshatra from Janma (priority 88)
    birth_moon_nak_idx = int((chart.moon_lon % 360) / 13.3333333333) % 27
    for malefic in ["Saturn", "Rahu", "Ketu"]:
        mal_lon = transit.positions[malefic]
        mal_nak_idx = int((mal_lon % 360) / 13.3333333333) % 27
        nak_dist = (mal_nak_idx - birth_moon_nak_idx) % 27
        if nak_dist in {8, 9, 10}:  # 9th, 10th, 11th (0-indexed: 8,9,10)
            fired.append(("malefic_left_leg_nakshatra_destruction", 44,
                          [f"Transit {malefic} in {nak_dist+1}th nakshatra from Janma (left leg SBC) — financial destruction"]))
            break

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR (Financial Crisis — 3 rules)
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate fast trigger rules for exact financial crisis timing.
    3 rules: Mars left-hand, Sanghatika (16th), Vinasha (23rd).
    """
    fired = []
    birth_moon_nak_idx = int((chart.moon_lon % 360) / 13.3333333333) % 27

    # Rule 1: Mars in 12-15th nakshatra from Janma (priority 90)
    mars_lon = transit.positions["Mars"]
    mars_nak_idx = int((mars_lon % 360) / 13.3333333333) % 27
    mars_nak_dist = (mars_nak_idx - birth_moon_nak_idx) % 27
    if mars_nak_dist in {11, 12, 13, 14}:  # 12th-15th (0-indexed: 11,12,13,14)
        fired.append(("mars_left_hand_poverty_fast_trigger", 35,
                      [f"Mars in {mars_nak_dist+1}th nakshatra from Janma (left hand SBC) — poverty trigger"]))

    # Rule 2: Moon/Mars on 16th nakshatra - Sanghatika (priority 88)
    for planet in ["Moon", "Mars"]:
        p_lon = transit.positions[planet]
        p_nak_idx = int((p_lon % 360) / 13.3333333333) % 27
        p_nak_dist = (p_nak_idx - birth_moon_nak_idx) % 27
        if p_nak_dist == 15:  # 16th (0-indexed: 15)
            fired.append(("sanghatika_debt_trigger", 32,
                          [f"Transit {planet} on 16th nakshatra (Sanghatika) from Janma — debt trigger"]))
            break

    # Rule 3: Moon/Mars on 23rd nakshatra - Vinasha (priority 92)
    for planet in ["Moon", "Mars"]:
        p_lon = transit.positions[planet]
        p_nak_idx = int((p_lon % 360) / 13.3333333333) % 27
        p_nak_dist = (p_nak_idx - birth_moon_nak_idx) % 27
        if p_nak_dist == 22:  # 23rd (0-indexed: 22)
            fired.append(("vinasha_asset_destruction_trigger", 38,
                          [f"Transit {planet} on 23rd nakshatra (Vinasha) from Janma — asset destruction trigger"]))
            break

    return fired



# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR (Financial Crisis — 8 rules)
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """
    Evaluate classical financial crisis patterns (structural — not time-dependent).
    8 rules from classical_patterns.json.
    """
    results = {
        "timing_modifier": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    second_lord = chart.second_lord
    second_lord_house = chart.planets.get(second_lord, {}).get("house", 0)
    eleventh_lord = chart.eleventh_lord
    eleventh_lord_house = chart.planets.get(eleventh_lord, {}).get("house", 0)
    sixth_lord = chart.sixth_lord
    eighth_lord = chart.eighth_lord
    twelfth_lord = chart.twelfth_lord
    lagna_lord = chart.lagna_lord
    lagna_lord_house = chart.planets.get(lagna_lord, {}).get("house", 0)
    twelfth_lord_house = chart.planets.get(twelfth_lord, {}).get("house", 0)
    fifth_lord = chart.fifth_lord
    fifth_lord_house = chart.planets.get(fifth_lord, {}).get("house", 0)
    ninth_lord = chart.ninth_lord
    ninth_lord_house = chart.planets.get(ninth_lord, {}).get("house", 0)

    # Pattern 1: 2nd & 11th lords in evil houses (priority 90)
    if second_lord_house in {6, 8, 12} and eleventh_lord_house in {6, 8, 12}:
        results["confidence_boost"] += 22
        results["fired_patterns"].append(
            f"2nd lord ({second_lord}) in {second_lord_house}th + 11th lord ({eleventh_lord}) in {eleventh_lord_house}th — structural poverty yoga")


    # Pattern 2: 2nd & 11th lords with Mars/Rahu (priority 88)
    second_lord_sign = chart.planets.get(second_lord, {}).get("sign", 0)
    eleventh_lord_sign = chart.planets.get(eleventh_lord, {}).get("sign", 0)
    mars_sign = chart.planets.get("Mars", {}).get("sign", 0)
    rahu_sign = chart.planets.get("Rahu", {}).get("sign", 0)
    second_with_mars_rahu = (second_lord_sign == mars_sign or second_lord_sign == rahu_sign)
    eleventh_with_mars_rahu = (eleventh_lord_sign == mars_sign or eleventh_lord_sign == rahu_sign)
    if second_with_mars_rahu and eleventh_with_mars_rahu:
        results["confidence_boost"] += 20
        results["fired_patterns"].append(
            f"2nd lord ({second_lord}) + 11th lord ({eleventh_lord}) contaminated by Mars/Rahu — insolvency yoga")

    # Pattern 3: Ascendant-12th exchange (priority 86)
    if lagna_lord_house == 12 and twelfth_lord_house == 1:
        results["confidence_boost"] += 18
        results["fired_patterns"].append(
            f"1st-12th Parivartana ({lagna_lord} in 12th, {twelfth_lord} in 1st) — self-created poverty yoga")

    # Pattern 4: Lagna lord in 8th with Ketu (priority 87)
    ketu_sign = chart.planets.get("Ketu", {}).get("sign", 0)
    lagna_lord_sign = chart.planets.get(lagna_lord, {}).get("sign", 0)
    if lagna_lord_house == 8 and lagna_lord_sign == ketu_sign:
        results["confidence_boost"] += 19
        results["fired_patterns"].append(
            f"Lagna lord ({lagna_lord}) in 8th with Ketu — hidden sudden poverty yoga")

    # Pattern 5: 5th & 9th lords in 6th/12th (priority 85)
    fifth_in_dusthana = fifth_lord_house in {6, 12}
    ninth_in_dusthana = ninth_lord_house in {6, 12}
    if fifth_in_dusthana or ninth_in_dusthana:
        boost = 16 if (fifth_in_dusthana and ninth_in_dusthana) else 10
        results["confidence_boost"] += boost
        parts = []
        if fifth_in_dusthana:
            parts.append(f"5th lord ({fifth_lord}) in {fifth_lord_house}th")
        if ninth_in_dusthana:
            parts.append(f"9th lord ({ninth_lord}) in {ninth_lord_house}th")
        results["fired_patterns"].append(
            f"{' + '.join(parts)} — speculative loss yoga")


    # Pattern 6: Mars-Saturn in 2nd (priority 89)
    mars_house = chart.planets.get("Mars", {}).get("house", 0)
    saturn_house = chart.planets.get("Saturn", {}).get("house", 0)
    if mars_house == 2 and saturn_house == 2:
        results["confidence_boost"] += 22
        results["fired_patterns"].append(
            "Mars + Saturn in 2nd house — wealth destruction yoga (litigation + restriction)")

    # Pattern 7: Moon with Rahu/Ketu + malefic aspect (priority 84)
    moon_sign = chart.planets.get("Moon", {}).get("sign", 0)
    moon_with_rahu_ketu = (moon_sign == rahu_sign or moon_sign == ketu_sign)
    if moon_with_rahu_ketu:
        moon_house = chart.planets.get("Moon", {}).get("house", 0)
        moon_aspectors = chart._get_aspectors_of_house(moon_house)
        malefic_aspects = [p for p in moon_aspectors if p in NATURAL_MALEFICS]
        if malefic_aspects:
            results["confidence_boost"] += 15
            results["fired_patterns"].append(
                f"Moon with {'Rahu' if moon_sign == rahu_sign else 'Ketu'} + malefic aspect ({', '.join(malefic_aspects)}) — chronic poverty yoga")

    # Pattern 8: Moon weak + Jupiter in dusthana (priority 82)
    jupiter_house = chart.planets.get("Jupiter", {}).get("house", 0)
    moon_debilitated = (moon_sign == DEBILITATION_SIGNS.get("Moon", 0))
    if jupiter_house in {6, 8, 12} and moon_debilitated:
        results["confidence_boost"] += 14
        results["fired_patterns"].append(
            f"Moon debilitated + Jupiter in {jupiter_house}th (dusthana) — no wealth retention yoga")

    return results



# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR (Financial Crisis — 10 rules)
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """
    Evaluate outcome/quality rules for financial crisis classification.
    10 rules from outcome_quality.json.
    """
    fired_rules = []

    sun_house = chart.planets.get("Sun", {}).get("house", 0)
    sun_sign = chart.planets.get("Sun", {}).get("sign", 0)
    saturn_sign = chart.planets.get("Saturn", {}).get("sign", 0)
    saturn_house = chart.planets.get("Saturn", {}).get("house", 0)
    rahu_sign = chart.planets.get("Rahu", {}).get("sign", 0)
    moon_sign = chart.planets.get("Moon", {}).get("sign", 0)
    moon_house = chart.planets.get("Moon", {}).get("house", 0)
    mars_house = chart.planets.get("Mars", {}).get("house", 0)
    mars_sign = chart.planets.get("Mars", {}).get("sign", 0)
    mercury_house = chart.planets.get("Mercury", {}).get("house", 0)
    jupiter_house = chart.planets.get("Jupiter", {}).get("house", 0)
    eighth_lord = chart.eighth_lord
    eighth_lord_house = chart.planets.get(eighth_lord, {}).get("house", 0)
    eighth_lord_sign = chart.planets.get(eighth_lord, {}).get("sign", 0)
    second_lord = chart.second_lord
    eleventh_lord = chart.eleventh_lord
    fifth_lord = chart.fifth_lord
    fifth_lord_house = chart.planets.get(fifth_lord, {}).get("house", 0)
    ninth_lord = chart.ninth_lord
    ninth_lord_house = chart.planets.get(ninth_lord, {}).get("house", 0)
    tenth_lord = chart.tenth_lord
    tenth_lord_house = chart.planets.get(tenth_lord, {}).get("house", 0)
    tenth_lord_sign = chart.planets.get(tenth_lord, {}).get("sign", 0)
    sixth_lord = chart.sixth_lord
    sixth_lord_house = chart.planets.get(sixth_lord, {}).get("house", 0)
    lagna_lord = chart.lagna_lord
    lagna_lord_house = chart.planets.get(lagna_lord, {}).get("house", 0)


    # Rule 1: Royal punishment — asset seizure (priority 88)
    sun_afflicted_saturn = (sun_sign == saturn_sign)
    sun_afflicted_rahu = (sun_sign == rahu_sign)
    sun_aspectors = chart._get_aspectors_of_house(sun_house)
    sun_sat_aspect = "Saturn" in sun_aspectors
    if (sun_afflicted_saturn or sun_afflicted_rahu or sun_sat_aspect) and sun_house in {2, 10, 11}:
        fired_rules.append(("royal_punishment_asset_seizure", "quality_challenging", 0.88,
            f"Sun afflicted by {'Saturn' if sun_afflicted_saturn or sun_sat_aspect else 'Rahu'} in {sun_house}th — government asset seizure"))

    # Rule 2: Sudden bankruptcy from prosperity (priority 92)
    eighth_strong = (eighth_lord_sign in OWN_SIGNS.get(eighth_lord, []) or
                     eighth_lord_sign == EXALTATION_SIGNS.get(eighth_lord, 0) or
                     eighth_lord_house in {1, 4, 7, 10})
    eighth_afflicts_wealth = (eighth_lord_house in {2, 11} or
                              eighth_lord_sign == chart.planets.get(second_lord, {}).get("sign", 0) or
                              eighth_lord_sign == chart.planets.get(eleventh_lord, {}).get("sign", 0))
    if eighth_strong and eighth_afflicts_wealth:
        fired_rules.append(("sudden_bankruptcy_from_prosperity", "quality_challenging", 0.92,
            f"Strong 8th lord ({eighth_lord}) afflicting wealth houses — sudden bankruptcy risk"))

    # Rule 3: Speculative collapse (priority 86)
    if fifth_lord_house in {6, 8, 12} and ninth_lord_house in {6, 8, 12}:
        fired_rules.append(("speculative_collapse_outcome", "quality_challenging", 0.86,
            f"5th lord ({fifth_lord}) in {fifth_lord_house}th + 9th lord ({ninth_lord}) in {ninth_lord_house}th — speculative collapse"))

    # Rule 4: Arudha 12th Jupiter — tax burden (priority 78)
    # Approximate Arudha Lagna: count from lagna lord house to lagna lord sign
    al_house = ((lagna_lord_house - 1) * 2 + 1) % 12
    if al_house == 0:
        al_house = 12
    jup_from_al = ((jupiter_house - al_house) % 12) + 1
    if jup_from_al == 12:
        fired_rules.append(("arudha_jupiter_12th_tax_burden", "quality_challenging", 0.80,
            "Jupiter in 12th from Arudha Lagna — tax/regulatory burden driving financial drain"))


    # Rule 5: Arudha 12th Mercury — litigation drain (priority 76)
    merc_from_al = ((mercury_house - al_house) % 12) + 1
    if merc_from_al == 12:
        fired_rules.append(("arudha_mercury_12th_litigation_drain", "quality_challenging", 0.78,
            "Mercury in 12th from Arudha Lagna — litigation/disputes driving financial drain"))

    # Rule 6: Moon-Mars in 8th — hidden liability (priority 84)
    if moon_house == 8 and mars_house == 8:
        fired_rules.append(("chandra_mangala_8th_hidden_liability", "quality_challenging", 0.84,
            "Moon + Mars in 8th house — hidden liabilities, unknown debts surfacing"))

    # Rule 7: 11th from 6th — loan dependency (priority 80)
    sixth_lord_strong = (sixth_lord_house in {1, 4, 7, 10} or
                         chart.planets.get(sixth_lord, {}).get("sign", 0) in OWN_SIGNS.get(sixth_lord, []))
    if sixth_lord_strong:
        eleventh_from_sixth = ((sixth_lord_house + 10) % 12) + 1
        # Check if benefic in that house
        for name, data in chart.planets.items():
            if data["house"] == eleventh_from_sixth and name in NATURAL_BENEFICS:
                fired_rules.append(("11th_from_6th_loan_dependency", "quality_challenging", 0.80,
                    f"Strong 6th lord + benefic in 11th from 6th — chronic loan dependency pattern"))
                break

    # Rule 8: Saturn in 2nd hostile — financial dysfunction (priority 82)
    if saturn_house == 2:
        sat_sign_val = chart.planets.get("Saturn", {}).get("sign", 0)
        is_debilitated = (sat_sign_val == DEBILITATION_SIGNS.get("Saturn", 0))
        # Enemy signs for Saturn: Sun's (Leo=5) and Moon's (Cancer=4)
        is_enemy = sat_sign_val in {4, 5}
        if is_debilitated or is_enemy:
            fired_rules.append(("saturn_2nd_hostile_financial_dysfunction", "quality_challenging", 0.82,
                f"Saturn in 2nd in {'debilitation' if is_debilitated else 'enemy sign'} — systematic financial dysfunction"))

    # Rule 9: Sun in 6th — bad loans/bribery (priority 75)
    if sun_house == 6:
        fired_rules.append(("sun_6th_bad_loans_bribery", "quality_challenging", 0.78,
            "Sun in 6th — losses through bad loans to others and corruption"))

    # Rule 10: Weak 10th + afflicted 3rd/9th — begging (priority 95)
    tenth_weak = (tenth_lord_sign == DEBILITATION_SIGNS.get(tenth_lord, 0) or
                  tenth_lord_house in {6, 8, 12})
    if tenth_weak:
        third_lord = chart.third_lord
        third_lord_house = chart.planets.get(third_lord, {}).get("house", 0)
        third_aspectors = chart._get_aspectors_of_house(3)
        ninth_aspectors = chart._get_aspectors_of_house(9)
        malefics_3rd = [p for p in third_aspectors if p in NATURAL_MALEFICS]
        malefics_9th = [p for p in ninth_aspectors if p in NATURAL_MALEFICS]
        benefics_3rd = [p for p in third_aspectors if p in NATURAL_BENEFICS]
        benefics_9th = [p for p in ninth_aspectors if p in NATURAL_BENEFICS]
        third_afflicted = malefics_3rd and not benefics_3rd
        ninth_afflicted = malefics_9th and not benefics_9th
        if third_afflicted or ninth_afflicted:
            # Check no Jupiter/Venus aspect on 10th
            tenth_aspectors = chart._get_aspectors_of_house(tenth_lord_house)
            if "Jupiter" not in tenth_aspectors and "Venus" not in tenth_aspectors:
                fired_rules.append(("weak_10th_3rd_9th_destitution", "quality_challenging", 0.90,
                    f"Weak 10th lord + afflicted {'3rd' if third_afflicted else '9th'} — complete destitution risk"))


    # ═══════════════════════════════════════════════════════════
    # RESOLUTION
    # ═══════════════════════════════════════════════════════════
    cal = CALIBRATION.get("outcome_calibration", {})
    default_mode = cal.get("default_mode", "financial_crisis")

    # Resolve MODE
    resolved_mode = default_mode
    if any("bankruptcy" in r[0] for r in fired_rules):
        resolved_mode = "sudden_bankruptcy"
    elif any("seizure" in r[0] for r in fired_rules):
        resolved_mode = "asset_seizure"
    elif any("speculative" in r[0] for r in fired_rules):
        resolved_mode = "speculative_collapse"
    elif any("hidden" in r[0] for r in fired_rules):
        resolved_mode = "hidden_liability"
    elif any("destitution" in r[0] for r in fired_rules):
        resolved_mode = "complete_destitution"
    elif any("loan" in r[0] for r in fired_rules):
        resolved_mode = "loan_dependency"

    # Resolve QUALITY
    resolved_quality = "challenging"
    if not fired_rules:
        resolved_quality = "neutral"

    return {
        "mode": resolved_mode,
        "quality": resolved_quality,
        "fired_outcomes": [f"{r[0]}: {r[3]}" for r in fired_rules],
        "_classical_rules_fired": fired_rules,
        "_resolution_method": "calibration_priority_order",
        "_calibration_version": CALIBRATION.get("calibration_version", "unknown"),
    }



# ═══════════════════════════════════════════════════════════════
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE (Financial Crisis)
# ═══════════════════════════════════════════════════════════════

class FinancialCrisisWindowResult:
    """Result of evaluating a single financial crisis time window."""

    def __init__(self):
        self.period_start = None
        self.period_end = None
        self.md_lord = ""
        self.ad_lord = ""
        self.age_start = 0.0
        self.age_end = 0.0
        self.dasha_fired = []
        self.transit_fired = []
        self.fast_trigger_fired = []
        self.classical = {}
        self.outcome = {}
        self.total_score = 0
        self.timing_band = "broad"
        self.likelihood = "low"

    def compute_composite_score(self):
        """Compute total score from all layers using calibration weights."""
        dasha_score = sum(s for _, s, _ in self.dasha_fired)
        transit_score = sum(s for _, s, _ in self.transit_fired)
        fast_score = sum(s for _, s, _ in self.fast_trigger_fired)
        classical_boost = self.classical.get("confidence_boost", 0)

        lw = CALIBRATION["layer_weights"]
        self.total_score = (
            dasha_score * lw["dasha_weight"] +
            transit_score * lw["transit_weight"] +
            fast_score * lw["fast_trigger_weight"] +
            classical_boost * lw["classical_weight"]
        )

        if fast_score > 20:
            self.timing_band = "exact"
        elif transit_score > 25:
            self.timing_band = "narrow"
        elif dasha_score > 20:
            self.timing_band = "broad"

        lt = CALIBRATION["likelihood_thresholds"]
        if self.total_score >= lt["very_high"]:
            self.likelihood = "VERY_HIGH"
        elif self.total_score >= lt["high"]:
            self.likelihood = "HIGH"
        elif self.total_score >= lt["moderate"]:
            self.likelihood = "MODERATE"
        elif self.total_score >= lt["low"]:
            self.likelihood = "LOW"
        else:
            self.likelihood = "VERY_LOW"



def scan_financial_crisis_windows(chart: ChartState, start_age=18, end_age=60, step_months=6):
    """
    Scan through life from start_age to end_age.
    Financial crisis can happen from age 18-60.
    For each AD period in that range, evaluate the 5-layer engine.
    Returns sorted list of FinancialCrisisWindowResult.
    """
    results = []

    md_periods = _generate_md_periods(chart.birth_dt, chart.moon_lon, years=80)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    for md in md_periods:
        md_age_start = (md["start"] - chart.birth_dt).days / 365.25
        md_age_end = (md["end"] - chart.birth_dt).days / 365.25

        if md_age_end < start_age or md_age_start > end_age:
            continue

        ad_periods = _generate_ad_periods(md)

        for ad in ad_periods:
            ad_age_start = (ad["start"] - chart.birth_dt).days / 365.25
            ad_age_end = (ad["end"] - chart.birth_dt).days / 365.25

            if ad_age_end < start_age or ad_age_start > end_age:
                continue

            effective_start = max(ad["start"], chart.birth_dt + timedelta(days=start_age * 365.25))
            effective_end = min(ad["end"], chart.birth_dt + timedelta(days=end_age * 365.25))

            # LAYER 1: DASHA (gate)
            dasha_results = evaluate_dasha_layer(chart, md["lord"], ad["lord"])
            if not dasha_results:
                continue

            # LAYER 2: TRANSIT (evaluate at midpoint, start, end)
            mid_date = effective_start + (effective_end - effective_start) / 2
            transit = TransitState(mid_date, chart)
            transit_results = evaluate_transit_layer(chart, transit)

            transit_start = TransitState(effective_start, chart)
            transit_end = TransitState(effective_end, chart)
            transit_results_start = evaluate_transit_layer(chart, transit_start)
            transit_results_end = evaluate_transit_layer(chart, transit_end)

            # Merge transit results (best score per rule)
            all_transit = {}
            for tr_list in [transit_results, transit_results_start, transit_results_end]:
                for rule_id, score, reasons in tr_list:
                    if rule_id not in all_transit or score > all_transit[rule_id][1]:
                        all_transit[rule_id] = (rule_id, score, reasons)
            merged_transit = list(all_transit.values())


            # LAYER 3: FAST TRIGGER
            fast_trigger_results = evaluate_fast_trigger_layer(chart, transit)
            ft_start = evaluate_fast_trigger_layer(chart, transit_start)
            ft_end = evaluate_fast_trigger_layer(chart, transit_end)
            all_fast = {}
            for ft_list in [fast_trigger_results, ft_start, ft_end]:
                for rule_id, score, reasons in ft_list:
                    if rule_id not in all_fast or score > all_fast[rule_id][1]:
                        all_fast[rule_id] = (rule_id, score, reasons)
            merged_fast = list(all_fast.values())

            # Build result
            result = FinancialCrisisWindowResult()
            result.period_start = effective_start
            result.period_end = effective_end
            result.md_lord = md["lord"]
            result.ad_lord = ad["lord"]
            result.age_start = max(ad_age_start, start_age)
            result.age_end = min(ad_age_end, end_age)
            result.dasha_fired = dasha_results
            result.transit_fired = merged_transit
            result.fast_trigger_fired = merged_fast
            result.classical = classical
            result.outcome = outcome
            result.compute_composite_score()

            results.append(result)

    results.sort(key=lambda r: r.total_score, reverse=True)
    return results



# ═══════════════════════════════════════════════════════════════
# MAIN — RUN FOR 22 JULY 1975 18:15 BHILAI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    BIRTH_DATE = datetime(1975, 7, 22, 18, 15)
    BHILAI_LAT = 21.2094
    BHILAI_LON = 81.4285
    BHILAI_ALT = 297

    print("=" * 80)
    print("  5-LAYER FINANCIAL CRISIS & DEBT RULE ENGINE — VEDIC TEXT BASED")
    print("  Domain: Financial Crisis & Debt")
    print("  Native: 22 July 1975, 18:15 IST, Bhilai")
    print("=" * 80)

    # Build chart state
    chart = ChartState(BIRTH_DATE, BHILAI_LAT, BHILAI_LON, BHILAI_ALT)

    print(f"\n{'─' * 80}")
    print("  NATAL CHART SUMMARY (Financial Crisis Focus)")
    print(f"{'─' * 80}")
    print(f"  Lagna: {SIGN_NAMES[chart.asc_sign]} | Lagna Lord: {chart.lagna_lord}")
    print(f"  Moon: {SIGN_NAMES[chart.moon_sign]} ({chart.moon_nakshatra})")
    print(f"  Moon Lord: {chart.moon_lord}")
    print(f"  6th Lord (Debt): {chart.sixth_lord} (house {chart.planets[chart.sixth_lord]['house']})")
    print(f"  8th Lord (Crisis): {chart.eighth_lord} (house {chart.planets[chart.eighth_lord]['house']})")
    print(f"  12th Lord (Loss): {chart.twelfth_lord} (house {chart.planets[chart.twelfth_lord]['house']})")
    print(f"  2nd Lord (Savings): {chart.second_lord} (house {chart.planets[chart.second_lord]['house']})")
    print(f"  11th Lord (Income): {chart.eleventh_lord} (house {chart.planets[chart.eleventh_lord]['house']})")
    print(f"  Saturn: house {chart.planets['Saturn']['house']}, {SIGN_NAMES[chart.planets['Saturn']['sign']]}")
    print(f"  Rahu: house {chart.planets['Rahu']['house']}, {SIGN_NAMES[chart.planets['Rahu']['sign']]}")
    print(f"  Mars: house {chart.planets['Mars']['house']}, {SIGN_NAMES[chart.planets['Mars']['sign']]}")
    print(f"  Jupiter: house {chart.planets['Jupiter']['house']}, {SIGN_NAMES[chart.planets['Jupiter']['sign']]}")


    # Layer 4 & 5 (structural)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    print(f"\n{'─' * 80}")
    print("  LAYER 4: CLASSICAL PATTERNS (Structural — Financial Crisis)")
    print(f"{'─' * 80}")
    print(f"  Timing Modifier: {classical['timing_modifier'].upper()}")
    print(f"  Confidence Boost: {classical['confidence_boost']:+d}")
    for p in classical["fired_patterns"]:
        print(f"    * {p}")
    if not classical["fired_patterns"]:
        print("    (No classical financial crisis patterns detected)")

    print(f"\n{'─' * 80}")
    print("  LAYER 5: OUTCOME / QUALITY (Financial Crisis Classification)")
    print(f"{'─' * 80}")
    print(f"  Crisis Mode: {outcome['mode']}")
    print(f"  Quality: {outcome['quality']}")
    for o in outcome["fired_outcomes"]:
        print(f"    * {o}")
    if not outcome["fired_outcomes"]:
        print("    (No specific crisis classification detected)")

    # Scan financial crisis windows
    print(f"\n{'─' * 80}")
    print("  SCANNING FINANCIAL CRISIS WINDOWS (Age 18-60)...")
    print(f"{'─' * 80}")

    windows = scan_financial_crisis_windows(chart, start_age=18, end_age=60)

    print(f"\n  Found {len(windows)} windows where dasha rules fired.")
    print(f"  Showing top 10 ranked by composite 5-layer score:\n")

    print(f"  {'#':<3} {'Period':<28} {'Age':<10} {'Score':<7} {'Band':<8} {'Likelihood':<12} {'MD-AD':<18}")
    print(f"  {'---':<3} {'---':<28} {'---':<10} {'---':<7} {'---':<8} {'---':<12} {'---':<18}")

    for i, w in enumerate(windows[:10], 1):
        period = f"{w.period_start.strftime('%b %Y')} - {w.period_end.strftime('%b %Y')}"
        age = f"{w.age_start:.1f}-{w.age_end:.1f}"
        md_ad = f"{w.md_lord}-{w.ad_lord}"
        print(f"  {i:<3} {period:<28} {age:<10} {w.total_score:<7.1f} {w.timing_band:<8} {w.likelihood:<12} {md_ad:<18}")


    # Detailed top 5
    print(f"\n{'=' * 80}")
    print("  TOP 5 FINANCIAL CRISIS WINDOWS — DETAILED 5-LAYER BREAKDOWN")
    print(f"{'=' * 80}")

    for i, w in enumerate(windows[:5], 1):
        print(f"\n  +{'─' * 76}+")
        print(f"  | #{i} | {w.period_start.strftime('%B %Y')} - {w.period_end.strftime('%B %Y')}")
        print(f"  | Age: {w.age_start:.1f} - {w.age_end:.1f} | MD: {w.md_lord} | AD: {w.ad_lord}")
        print(f"  | COMPOSITE SCORE: {w.total_score:.1f} | Likelihood: {w.likelihood} | Band: {w.timing_band}")
        print(f"  +{'─' * 76}+")

        print(f"  | LAYER 1 — DASHA (Gate):")
        for rule_id, score, reasons in w.dasha_fired:
            for r in reasons:
                print(f"  |   [{score:>3}] {r}")

        print(f"  | LAYER 2 — TRANSIT (Activation):")
        if w.transit_fired:
            for rule_id, score, reasons in w.transit_fired:
                for r in reasons:
                    print(f"  |   [{score:>3}] {r}")
        else:
            print(f"  |   (No transit activation at sample points)")

        print(f"  | LAYER 3 — FAST TRIGGER (Exact):")
        if w.fast_trigger_fired:
            for rule_id, score, reasons in w.fast_trigger_fired:
                for r in reasons:
                    print(f"  |   [{score:>3}] {r}")
        else:
            print(f"  |   (No fast trigger at sample points)")

        print(f"  +{'─' * 76}+")

    print(f"\n{'=' * 80}")
    print("  CONCLUSION")
    print(f"{'=' * 80}")
    if windows:
        top = windows[0]
        print(f"\n  HIGHEST FINANCIAL CRISIS RISK WINDOW:")
        print(f"  {top.period_start.strftime('%B %Y')} - {top.period_end.strftime('%B %Y')}")
        print(f"  Age {top.age_start:.1f}-{top.age_end:.1f} | {top.md_lord}-{top.ad_lord}")
        print(f"  Score: {top.total_score:.1f} | {top.likelihood}")
        print(f"\n  Crisis Mode: {outcome['mode']}")
        print(f"  Quality: {outcome['quality']}")
        print(f"\n  The 5-layer engine evaluated {len(windows)} AD periods with")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['high'])} HIGH+ confidence windows.")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['very_high'])} VERY_HIGH confidence windows.")
    print(f"\n{'=' * 80}")
