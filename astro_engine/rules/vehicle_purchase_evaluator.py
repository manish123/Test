"""
Vehicle Purchase Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow.
Domain: Vehicle Purchase & Vehicle Ownership

Follows the exact same pattern as property_purchase_evaluator.py (PR #19).
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
RULES_DIR = Path(__file__).resolve().parent / "domains" / "property" / "vehicle_purchase_and_vehicle_ownership"

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

# Vehicle Purchase-specific constants
# Venus=Vahana Karaka, Jupiter=expansion, Moon=comfort, Saturn=heavy vehicles, Mars=engineering
VEHICLE_PURCHASE_KARAKAS = {"Venus", "Jupiter", "Moon", "Saturn", "Mars", "Mercury"}
# 4=vehicles/conveyances, 1=self, 9=fortune, 11=gains
VEHICLE_PURCHASE_HOUSES = {4, 1, 9, 11}

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
                "dasha_weight": 0.30,
                "transit_weight": 0.30,
                "fast_trigger_weight": 0.25,
                "classical_weight": 0.15,
            },
            "likelihood_thresholds": {
                "very_high": 55, "high": 40, "moderate": 25, "low": 15,
            },
            "base_scores": {
                "dasha": {"venus_mahadasha_karaka": 48, "fourth_lord_dasha_dignified": 46},
                "transit": {"lagna_lord_4th_activation": 42, "jupiter_trine_4th_lord_d9": 40},
                "fast_trigger": {"sbc_benefic_janma_nakshatra": 32},
            },
            "outcome_calibration": {
                "mode_priority_order": ["luxury_vehicle", "vehicle_purchase", "transport_assets",
                                        "commercial_vehicle", "transport_upgrade"],
                "quality_priority_order": ["supportive", "mixed", "challenging"],
                "default_mode": "vehicle_purchase",
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
# CHART STATE BUILDER (reused from property evaluator pattern)
# ═══════════════════════════════════════════════════════════════

class ChartState:
    """Encapsulates all natal chart data needed for vehicle purchase rule evaluation."""

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


        # All house lords
        self.lagna_lord = SIGN_LORDS[self.asc_sign]
        self.fourth_sign = ((self.asc_sign + 3 - 1) % 12) + 1
        self.fourth_lord = SIGN_LORDS[self.fourth_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.eleventh_sign = ((self.asc_sign + 10 - 1) % 12) + 1
        self.eleventh_lord = SIGN_LORDS[self.eleventh_sign]
        self.sixth_sign = ((self.asc_sign + 5 - 1) % 12) + 1
        self.sixth_lord = SIGN_LORDS[self.sixth_sign]

        # Moon lord (dispositor of Moon)
        self.moon_lord = SIGN_LORDS[self.moon_sign]

        # Planets in 4th house (vehicle house)
        self.fourth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 4
        ]

        # Sensitive Vehicle Points
        # Point 1: Venus + 4th lord longitude sum (vehicle acquisition axis)
        fourth_lord_lon = self.birth_positions[self.fourth_lord]
        venus_lon = self.birth_positions["Venus"]
        self.sensitive_point_1 = (venus_lon + fourth_lord_lon) % 360
        # Point 2: Moon + 4th lord longitude sum (transport comfort axis)
        self.sensitive_point_2 = (self.moon_lon + fourth_lord_lon) % 360

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
# LAYER 1: DASHA EVALUATOR (Vehicle Purchase — 9 rules)
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate dasha rules for vehicle purchase.
    9 rules: Venus MD, Rasi Dasha Jupiter 4th, 4th Lord dignified,
    Jupiter-Ketu, Saturn-Venus, Saturn-Mars, Jupiter-Sun, Moon-Mercury, Rahu-Venus.
    """
    fired = []

    # Rule 1: Venus Mahadasha — primary Vahana Karaka gate (priority 95)
    if md_lord == "Venus":
        fired.append(("venus_vahana_karaka_gate", 48,
                      ["Venus MD — natural Karaka of vehicles and luxuries, primary vehicle purchase window"]))

    # Rule 2: 4th Lord Dasha — direct vehicle ruler (priority 95)
    r2_score = 0
    r2_reasons = []
    fourth_lord = chart.fourth_lord
    fourth_lord_house = chart.planets.get(fourth_lord, {}).get("house", 0)
    fourth_lord_sign = chart.planets.get(fourth_lord, {}).get("sign", 0)
    # Check dignity
    is_strong = (fourth_lord_sign in OWN_SIGNS.get(fourth_lord, []) or
                 fourth_lord_sign == EXALTATION_SIGNS.get(fourth_lord, 0))
    # Check Lagna connection
    lagna_connected = (fourth_lord_house == 1 or
                       chart.planets.get(fourth_lord, {}).get("sign", 0) ==
                       chart.planets.get(chart.lagna_lord, {}).get("sign", 0))
    in_good_house = fourth_lord_house in {1, 4, 9}

    if md_lord == fourth_lord:
        r2_score += 46
        r2_reasons.append(f"MD of 4th lord ({fourth_lord}) — direct vehicle ruler active")
        if is_strong:
            r2_score += 8
            r2_reasons.append(f"  4th lord is dignified (own/exalted sign)")
        if lagna_connected:
            r2_score += 6
            r2_reasons.append(f"  4th lord connected to Lagna/Lagna lord")
        if in_good_house:
            r2_score += 5
            r2_reasons.append(f"  4th lord in house {fourth_lord_house} (1st/4th/9th)")
    elif ad_lord == fourth_lord:
        r2_score += 36
        r2_reasons.append(f"AD of 4th lord ({fourth_lord}) — vehicle sub-period active")
        if is_strong:
            r2_score += 6
            r2_reasons.append(f"  4th lord is dignified")
    if r2_score > 0:
        fired.append(("fourth_lord_vehicle_gate", r2_score, r2_reasons))


    # Rule 3: Jupiter-Ketu — sudden luxury vehicle (priority 85)
    if md_lord == "Jupiter" and ad_lord == "Ketu":
        # Check Ketu position relative to Jupiter
        jup_house = chart.planets.get("Jupiter", {}).get("house", 0)
        ketu_house = chart.planets.get("Ketu", {}).get("house", 0)
        ketu_from_jup = ((ketu_house - jup_house) % 12) + 1
        if ketu_from_jup in {4, 5, 9, 10}:
            fired.append(("jupiter_ketu_motorcar_gate", 40,
                          [f"Jupiter MD + Ketu AD — Ketu in {ketu_from_jup}th from Jupiter, sudden luxury vehicle"]))
        else:
            fired.append(("jupiter_ketu_motorcar_gate", 30,
                          ["Jupiter MD + Ketu AD — vehicle period (Ketu not optimally placed)"]))

    # Rule 4: Saturn-Venus — luxury conveyance (priority 90)
    if md_lord == "Saturn" and ad_lord == "Venus":
        venus_house = chart.planets.get("Venus", {}).get("house", 0)
        venus_sign = chart.planets.get("Venus", {}).get("sign", 0)
        venus_in_good = venus_house in {1, 4, 5, 7, 9, 10, 11}
        score = 44 if venus_in_good else 36
        fired.append(("saturn_venus_luxury_conveyance_gate", score,
                      [f"Saturn MD + Venus AD — luxury vehicle acquisition (Venus in house {venus_house})"]))

    # Rule 5: Saturn-Mars — commercial/heavy transport (priority 82)
    if md_lord == "Saturn" and ad_lord == "Mars":
        mars_sign = chart.planets.get("Mars", {}).get("sign", 0)
        mars_dignified = (mars_sign in OWN_SIGNS.get("Mars", []) or
                          mars_sign == EXALTATION_SIGNS.get("Mars", 0))
        mars_with_lagna = (chart.planets.get("Mars", {}).get("sign", 0) ==
                           chart.planets.get(chart.lagna_lord, {}).get("sign", 0))
        if mars_dignified or mars_with_lagna:
            fired.append(("saturn_mars_transport_asset_gate", 40,
                          ["Saturn MD + Mars AD — Mars dignified, heavy/commercial vehicle acquisition"]))
        else:
            fired.append(("saturn_mars_transport_asset_gate", 28,
                          ["Saturn MD + Mars AD — transport asset period (Mars not strongly dignified)"]))


    # Rule 6: Jupiter-Sun — status vehicle (priority 80)
    if md_lord == "Jupiter" and ad_lord == "Sun":
        fired.append(("jupiter_sun_status_vehicle_gate", 35,
                      ["Jupiter MD + Sun AD — status elevation, high-status vehicle purchase"]))

    # Rule 7: Moon-Mercury — mobility conveyance (priority 75)
    if md_lord == "Moon" and ad_lord == "Mercury":
        fired.append(("moon_mercury_conveyance_gate", 32,
                      ["Moon MD + Mercury AD — commercial mobility, transport asset acquisition"]))
    elif md_lord == "Mercury" and ad_lord == "Moon":
        fired.append(("mercury_moon_conveyance_gate", 28,
                      ["Mercury MD + Moon AD — planned vehicle purchase through commerce"]))

    # Rule 8: Rahu-Venus — peak material luxury vehicle (priority 88)
    if md_lord == "Rahu" and ad_lord == "Venus":
        fired.append(("rahu_venus_material_vehicle_gate", 42,
                      ["Rahu MD + Venus AD — peak materialistic period, luxury vehicle acquisition"]))
    elif md_lord == "Venus" and ad_lord == "Rahu":
        fired.append(("venus_rahu_luxury_gate", 38,
                      ["Venus MD + Rahu AD — intensified luxury desire, vehicle purchase"]))

    # Rule 9: Rasi Dasha Jupiter 4th (priority 80) — approximated
    # Check if Jupiter is in the 4th house from any sign-based reference
    jup_house = chart.planets.get("Jupiter", {}).get("house", 0)
    if jup_house == 4 and md_lord == "Jupiter":
        fired.append(("rasi_dasha_jupiter_4th_vehicle_gate", 38,
                      ["Jupiter in 4th house + Jupiter MD — Rasi Dasha vehicle activation"]))

    # Bonus: Venus as AD lord in any MD (Venus is Vahana Karaka)
    if ad_lord == "Venus" and md_lord != "Saturn" and md_lord != "Rahu":
        if not any("venus" in f[0].lower() for f in fired):
            fired.append(("venus_ad_karaka_bonus", 25,
                          [f"Venus AD in {md_lord} MD — Vahana Karaka sub-period active"]))

    return fired




# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR (Vehicle Purchase — 4 rules)
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate transit rules for vehicle purchase activation.
    4 rules: Lagna lord 4th activation, Jupiter trine 4th lord,
    Venus karaka conjunct Lagna/Moon lord, benefic 4th house transit.
    """
    fired = []

    # Rule 1: Lagna lord transit through 4th house (priority 90)
    lagna_lord = chart.lagna_lord
    lagna_lord_transit_house = transit.planet_houses_from_lagna.get(lagna_lord, 0)
    if lagna_lord_transit_house == 4:
        fired.append(("lagna_lord_4th_vehicle_activation", 42,
                      [f"Transit {lagna_lord} (Lagna lord) in 4th house — self enters vehicle domain"]))

    # Also check Lagna lord trine to 4th lord (Phaladeepika principle)
    fourth_lord_lon = chart.birth_positions[chart.fourth_lord]
    lagna_lord_transit_lon = transit.positions.get(lagna_lord, 0)
    trine_diff = abs((lagna_lord_transit_lon - fourth_lord_lon) % 360)
    trine_diff = min(trine_diff, 360 - trine_diff)
    if (abs(trine_diff - 120) <= 8) or (abs(trine_diff - 240) <= 8):
        fired.append(("lagna_lord_trine_4th_lord", 35,
                      [f"Transit {lagna_lord} trine natal 4th lord ({chart.fourth_lord}) — vehicle activation"]))

    # Rule 2: Jupiter trine 4th lord navamsa (priority 88)
    jup_transit_lon = transit.positions["Jupiter"]
    jup_trine_diff = abs((jup_transit_lon - fourth_lord_lon) % 360)
    jup_trine_diff = min(jup_trine_diff, 360 - jup_trine_diff)
    is_trine = (abs(jup_trine_diff - 120) <= 8) or (abs(jup_trine_diff - 240) <= 8)
    if is_trine:
        fired.append(("jupiter_trine_4th_lord_vehicle", 40,
                      [f"Transit Jupiter trine natal 4th lord ({chart.fourth_lord}) — vehicle blessing window"]))

    # Rule 3: Venus (Vahana Karaka) conjunct natal Lagna lord or Moon lord (priority 78)
    natal_lagna_lord_lon = chart.birth_positions[chart.lagna_lord]
    natal_moon_lord_lon = chart.birth_positions[chart.moon_lord]
    if transit.planet_conjunct_natal("Venus", natal_lagna_lord_lon, orb=5.0):
        fired.append(("venus_karaka_conjunct_lagna_lord", 35,
                      [f"Transit Venus conjunct natal {chart.lagna_lord} (Lagna lord) — vehicle desire activated"]))
    if transit.planet_conjunct_natal("Venus", natal_moon_lord_lon, orb=5.0):
        fired.append(("venus_karaka_conjunct_moon_lord", 32,
                      [f"Transit Venus conjunct natal {chart.moon_lord} (Moon lord) — comfort vehicle desire"]))

    # Rule 4: Benefic planet transit through 4th house (priority 82)
    for benefic in ["Jupiter", "Venus"]:
        ben_house = transit.planet_houses_from_lagna.get(benefic, 0)
        if ben_house == 4:
            fired.append((f"benefic_{benefic.lower()}_4th_house", 38,
                          [f"Transit {benefic} in 4th house — vehicle acquisition support"]))

    return fired




# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR (Vehicle Purchase — 1 rule)
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate fast trigger rules for exact vehicle purchase timing.
    1 rule: SBC benefic transit on Janma Nakshatra.
    """
    fired = []

    # Rule 1: SBC benefic on Janma Nakshatra (priority 92)
    birth_moon_nak_idx = int((chart.moon_lon % 360) / 13.3333333333) % 27
    for benefic in ["Jupiter", "Venus", "Mercury"]:
        ben_lon = transit.positions[benefic]
        ben_nak_idx = int((ben_lon % 360) / 13.3333333333) % 27
        if ben_nak_idx == birth_moon_nak_idx:
            fired.append(("sbc_benefic_janma_nakshatra_vehicle", 32,
                          [f"{benefic} on Janma Nakshatra (SBC activation) — vehicle purchase muhurta"]))
            break

    return fired




# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR (Vehicle Purchase — 8 rules)
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """
    Evaluate classical vehicle purchase patterns (structural — not time-dependent).
    8 rules: 4th-11th exchange, benefic 4th, 4th lord+Mercury, Moon+4th lord Lagna,
    Venus+4th lord Lagna, Jupiter+4th lord, many vehicles yoga, Vargottama golden vehicle.
    """
    results = {
        "timing_modifier": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    fourth_lord = chart.fourth_lord
    fourth_lord_house = chart.planets.get(fourth_lord, {}).get("house", 0)
    fourth_lord_sign = chart.planets.get(fourth_lord, {}).get("sign", 0)
    fourth_house_occ = chart.fourth_house_occupants
    fourth_aspectors = chart._get_aspectors_of_house(4)
    eleventh_lord = chart.eleventh_lord
    eleventh_lord_house = chart.planets.get(eleventh_lord, {}).get("house", 0)
    ninth_lord = chart.ninth_lord
    ninth_lord_house = chart.planets.get(ninth_lord, {}).get("house", 0)

    # Pattern 1: 4th-11th Parivartana Yoga (priority 88)
    if fourth_lord_house == 11 and eleventh_lord_house == 4:
        results["confidence_boost"] += 20
        results["fired_patterns"].append(
            f"4th-11th Parivartana Yoga ({fourth_lord} in 11th, {eleventh_lord} in 4th) — strong vehicle ownership promise")

    # Pattern 2: Benefic in/aspecting 4th house (priority 85)
    benefics_in_4th = [p for p in fourth_house_occ if p in NATURAL_BENEFICS]
    benefic_aspectors_4th = [p for p in fourth_aspectors if p in NATURAL_BENEFICS]
    if benefics_in_4th or benefic_aspectors_4th:
        all_benefics = list(set(benefics_in_4th + benefic_aspectors_4th))
        results["confidence_boost"] += 16
        results["fired_patterns"].append(
            f"Benefic influence on 4th ({', '.join(all_benefics)}) — happiness from vehicles, safe travels")


    # Pattern 3: 4th lord + Mercury in same sign (priority 90)
    mercury_sign = chart.planets.get("Mercury", {}).get("sign", 0)
    if fourth_lord_sign == mercury_sign and fourth_lord != "Mercury":
        results["confidence_boost"] += 18
        results["fired_patterns"].append(
            f"4th lord ({fourth_lord}) conjunct Mercury — commerce + vehicle combination yoga")

    # Pattern 4: Moon + 4th lord in Lagna (priority 82)
    moon_house = chart.planets.get("Moon", {}).get("house", 0)
    if moon_house == 1 and fourth_lord_house == 1:
        results["confidence_boost"] += 16
        results["fired_patterns"].append(
            f"Moon + 4th lord ({fourth_lord}) in Lagna — personal vehicle ownership promise")

    # Pattern 5: Venus + 4th lord in Lagna — royal/luxury vehicle (priority 92)
    venus_house = chart.planets.get("Venus", {}).get("house", 0)
    if venus_house == 1 and fourth_lord_house == 1:
        results["confidence_boost"] += 22
        results["fired_patterns"].append(
            f"Venus + 4th lord ({fourth_lord}) in Lagna — royal luxury vehicle yoga (elephant)")

    # Pattern 6: Jupiter associated with 4th lord (priority 85)
    jupiter_sign = chart.planets.get("Jupiter", {}).get("sign", 0)
    jupiter_aspectors = chart._get_aspectors_of_house(fourth_lord_house)
    jup_conjunct = (jupiter_sign == fourth_lord_sign and fourth_lord != "Jupiter")
    jup_aspects_4th_lord = "Jupiter" in jupiter_aspectors
    if jup_conjunct or jup_aspects_4th_lord:
        results["confidence_boost"] += 15
        results["fired_patterns"].append(
            f"Jupiter associated with 4th lord ({fourth_lord}) — enclosed luxury vehicle (bordered)")

    # Pattern 7: 4th lord + Jupiter + Venus in 9th (priority 95)
    jupiter_house = chart.planets.get("Jupiter", {}).get("house", 0)
    venus_house_val = chart.planets.get("Venus", {}).get("house", 0)
    if fourth_lord_house == 9 and jupiter_house == 9 and venus_house_val == 9:
        results["confidence_boost"] += 25
        results["fired_patterns"].append(
            f"4th lord + Jupiter + Venus in 9th — MANY VEHICLES yoga (fleet ownership)")

    # Pattern 8: Vargottama Lagna lord + 9th lord (priority 98)
    # Approximate: check if Lagna lord is in same sign in D1 and would be in same Navamsa
    lagna_lord_lon = chart.birth_positions[chart.lagna_lord]
    ninth_lord_lon = chart.birth_positions[ninth_lord]
    # Navamsa sign = ((lon % 30) / 3.333...) gives pada, then map
    lagna_lord_d1_sign = get_sign(lagna_lord_lon)
    lagna_lord_navamsa = int((lagna_lord_lon % 30) / 3.333333) + 1
    # Vargottama = D1 sign == Navamsa sign (approximately)
    lagna_lord_vargottama = (lagna_lord_d1_sign == ((lagna_lord_d1_sign - 1) * 9 + lagna_lord_navamsa - 1) % 12 + 1)
    if lagna_lord_vargottama and fourth_lord_house in {1, 4, 5, 7, 9, 10}:
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            f"Lagna lord ({chart.lagna_lord}) Vargottama + strong placement — golden vehicle yoga potential")

    return results




# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR (Vehicle Purchase — 8 rules)
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """
    Evaluate outcome/quality rules for vehicle purchase classification.
    8 rules: defective vehicle, multiple vehicles, luxury enclosed,
    elite luxury, car loans, golden vehicle, malefic losses, transport prosperity.
    """
    fired_rules = []

    fourth_lord = chart.fourth_lord
    fourth_lord_house = chart.planets.get(fourth_lord, {}).get("house", 0)
    fourth_lord_sign = chart.planets.get(fourth_lord, {}).get("sign", 0)
    fourth_house_occ = chart.fourth_house_occupants
    fourth_aspectors = chart._get_aspectors_of_house(4)
    sixth_lord_house = chart.planets.get(chart.sixth_lord, {}).get("house", 0)
    ninth_lord = chart.ninth_lord
    ninth_lord_house = chart.planets.get(ninth_lord, {}).get("house", 0)
    jupiter_house = chart.planets.get("Jupiter", {}).get("house", 0)
    jupiter_sign = chart.planets.get("Jupiter", {}).get("sign", 0)
    venus_house = chart.planets.get("Venus", {}).get("house", 0)

    # Rule 1: 4th lord in Dusthana debilitated — defective vehicle (priority 85)
    is_debilitated = False
    # Check debilitation: Sun=Libra(7), Moon=Scorpio(8), Mars=Cancer(4), etc.
    DEBILITATION = {"Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12,
                    "Jupiter": 10, "Venus": 6, "Saturn": 1}
    if fourth_lord_sign == DEBILITATION.get(fourth_lord, 0):
        is_debilitated = True
    inimical = fourth_lord_house in {6, 8, 12}
    ninth_aspects_4th_lord = ninth_lord_house == fourth_lord_house or (
        chart.planets.get(ninth_lord, {}).get("sign", 0) == fourth_lord_sign)
    if (is_debilitated or inimical) and fourth_lord_house in {6, 8, 12} and ninth_aspects_4th_lord:
        fired_rules.append(("defective_vehicle_outcome", "quality_challenging", 0.85,
            f"4th lord ({fourth_lord}) afflicted in house {fourth_lord_house} — defective/unstable vehicle"))

    # Rule 2: 4th lord + Jupiter + Venus in 9th — multiple vehicles (priority 95)
    venus_house_val = chart.planets.get("Venus", {}).get("house", 0)
    if fourth_lord_house == 9 and jupiter_house == 9 and venus_house_val == 9:
        fired_rules.append(("multiple_vehicle_fleet_outcome", "quality_supportive", 0.95,
            "4th lord + Jupiter + Venus in 9th — fleet of multiple vehicles"))


    # Rule 3: 4th lord + Jupiter — luxury enclosed vehicle (priority 85)
    jup_sign = chart.planets.get("Jupiter", {}).get("sign", 0)
    if jup_sign == fourth_lord_sign and fourth_lord != "Jupiter":
        fired_rules.append(("luxury_enclosed_vehicle_outcome", "quality_supportive", 0.90,
            f"4th lord ({fourth_lord}) conjunct Jupiter — luxury enclosed vehicle (SUV/sedan)"))
    elif "Jupiter" in fourth_aspectors:
        fired_rules.append(("luxury_enclosed_vehicle_outcome", "quality_supportive", 0.85,
            f"Jupiter aspects 4th lord ({fourth_lord}) — comfortable protected vehicle"))

    # Rule 4: Venus + 4th lord in Lagna — elite luxury (priority 92)
    if venus_house == 1 and fourth_lord_house == 1:
        fired_rules.append(("elite_luxury_vehicle_outcome", "quality_supportive", 0.95,
            f"Venus + 4th lord ({fourth_lord}) in Lagna — elite luxury vehicle (elephant class)"))

    # Rule 5: 11th from 6th = car loans (priority 78)
    if sixth_lord_house == 4 or fourth_lord_house == 6:
        fired_rules.append(("debt_financed_vehicle_outcome", "quality_mixed", 0.85,
            f"6th lord ({chart.sixth_lord}) connected to 4th — debt-financed vehicle (car loan)"))

    # Rule 6: Vargottama raja yoga — golden vehicle (priority 96)
    lagna_lord_lon = chart.birth_positions[chart.lagna_lord]
    lagna_lord_d1_sign = get_sign(lagna_lord_lon)
    lagna_lord_navamsa = int((lagna_lord_lon % 30) / 3.333333) + 1
    lagna_lord_vargottama = (lagna_lord_d1_sign == ((lagna_lord_d1_sign - 1) * 9 + lagna_lord_navamsa - 1) % 12 + 1)
    if lagna_lord_vargottama:
        ninth_lord_lon = chart.birth_positions[ninth_lord]
        ninth_lord_d1_sign = get_sign(ninth_lord_lon)
        ninth_lord_navamsa = int((ninth_lord_lon % 30) / 3.333333) + 1
        ninth_lord_vargottama = (ninth_lord_d1_sign == ((ninth_lord_d1_sign - 1) * 9 + ninth_lord_navamsa - 1) % 12 + 1)
        if ninth_lord_vargottama:
            fired_rules.append(("raja_yoga_golden_vehicle_outcome", "quality_supportive", 0.95,
                "Vargottama Lagna + 9th lord — golden/ultra-luxury vehicle raja yoga"))

    # Rule 7: Malefic 4th house without benefic — losses (priority 88)
    malefics_in_4th = [p for p in fourth_house_occ if p in NATURAL_MALEFICS]
    benefics_in_4th = [p for p in fourth_house_occ if p in NATURAL_BENEFICS]
    if malefics_in_4th and not benefics_in_4th:
        fired_rules.append(("malefic_vehicle_loss_outcome", "quality_challenging", 0.90,
            f"Malefics in 4th ({', '.join(malefics_in_4th)}) — vehicle losses, breakdowns, repeated expenses"))

    # Rule 8: Sun + Moon + Jupiter in 9th — transport prosperity (priority 82)
    sun_house = chart.planets.get("Sun", {}).get("house", 0)
    moon_house = chart.planets.get("Moon", {}).get("house", 0)
    if sun_house == 9 and moon_house == 9 and jupiter_house == 9:
        fired_rules.append(("luminaries_jupiter_9th_transport", "quality_supportive", 0.85,
            "Sun + Moon + Jupiter in 9th — rich in vehicles, transport prosperity"))


    # ═══════════════════════════════════════════════════════════
    # RESOLUTION
    # ═══════════════════════════════════════════════════════════
    cal = CALIBRATION.get("outcome_calibration", {})
    default_mode = cal.get("default_mode", "vehicle_purchase")

    # Resolve MODE
    resolved_mode = default_mode
    if venus_house in {1, 4} or fourth_lord == "Venus":
        resolved_mode = "luxury_vehicle"
    if chart.planets.get("Saturn", {}).get("house", 0) == 4 and fourth_lord == "Saturn":
        resolved_mode = "commercial_vehicle"
    if jupiter_house in {4, 9} and venus_house in {4, 9}:
        resolved_mode = "luxury_vehicle"

    # Resolve QUALITY
    quality_rules = [r for r in fired_rules if r[1].startswith("quality_")]
    resolved_quality = "supportive"
    if quality_rules:
        quality_rules.sort(key=lambda r: -r[2])
        quality_map = {
            "quality_supportive": "supportive",
            "quality_challenging": "challenging",
            "quality_mixed": "mixed",
        }
        resolved_quality = quality_map.get(quality_rules[0][1], "supportive")

    return {
        "mode": resolved_mode,
        "quality": resolved_quality,
        "fired_outcomes": [f"{r[0]}: {r[3]}" for r in fired_rules],
        "_classical_rules_fired": fired_rules,
        "_resolution_method": "calibration_priority_order",
        "_calibration_version": CALIBRATION.get("calibration_version", "unknown"),
    }




# ═══════════════════════════════════════════════════════════════
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE (Vehicle Purchase)
# ═══════════════════════════════════════════════════════════════

class VehiclePurchaseWindowResult:
    """Result of evaluating a single vehicle purchase time window."""

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




def scan_vehicle_purchase_windows(chart: ChartState, start_age=18, end_age=60, step_months=6):
    """
    Scan through life from start_age to end_age.
    Vehicle purchase typically happens from age 18-60.
    For each AD period in that range, evaluate the 5-layer engine.
    Returns sorted list of VehiclePurchaseWindowResult.
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
            result = VehiclePurchaseWindowResult()
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
    print("  5-LAYER VEHICLE PURCHASE RULE ENGINE — VEDIC TEXT BASED")
    print("  Domain: Vehicle Purchase & Vehicle Ownership")
    print("  Native: 22 July 1975, 18:15 IST, Bhilai")
    print("=" * 80)

    # Build chart state
    chart = ChartState(BIRTH_DATE, BHILAI_LAT, BHILAI_LON, BHILAI_ALT)

    print(f"\n{'─' * 80}")
    print("  NATAL CHART SUMMARY (Vehicle Purchase Focus)")
    print(f"{'─' * 80}")
    print(f"  Lagna: {SIGN_NAMES[chart.asc_sign]} | Lagna Lord: {chart.lagna_lord}")
    print(f"  Moon: {SIGN_NAMES[chart.moon_sign]} ({chart.moon_nakshatra})")
    print(f"  Moon Lord: {chart.moon_lord}")
    print(f"  4th Lord: {chart.fourth_lord} (house {chart.planets[chart.fourth_lord]['house']})")
    print(f"  9th Lord: {chart.ninth_lord} (house {chart.planets[chart.ninth_lord]['house']})")
    print(f"  11th Lord: {chart.eleventh_lord} (house {chart.planets[chart.eleventh_lord]['house']})")
    print(f"  Venus (Vahana Karaka): house {chart.planets['Venus']['house']}, {SIGN_NAMES[chart.planets['Venus']['sign']]}")
    print(f"  Jupiter: house {chart.planets['Jupiter']['house']}, {SIGN_NAMES[chart.planets['Jupiter']['sign']]}")
    print(f"  Saturn: house {chart.planets['Saturn']['house']}, {SIGN_NAMES[chart.planets['Saturn']['sign']]}")
    print(f"  Mars: house {chart.planets['Mars']['house']}, {SIGN_NAMES[chart.planets['Mars']['sign']]}")
    print(f"  Moon: house {chart.planets['Moon']['house']}, {SIGN_NAMES[chart.planets['Moon']['sign']]}")
    print(f"  Mercury: house {chart.planets['Mercury']['house']}, {SIGN_NAMES[chart.planets['Mercury']['sign']]}")
    print(f"  Rahu: house {chart.planets['Rahu']['house']}, {SIGN_NAMES[chart.planets['Rahu']['sign']]}")
    print(f"  Sensitive Point 1 (Venus+4L): {chart.sensitive_point_1:.2f}°")
    print(f"  Sensitive Point 2 (Moon+4L): {chart.sensitive_point_2:.2f}°")


    # Layer 4 & 5 (structural)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    print(f"\n{'─' * 80}")
    print("  LAYER 4: CLASSICAL PATTERNS (Structural — Vehicle Purchase)")
    print(f"{'─' * 80}")
    print(f"  Timing Modifier: {classical['timing_modifier'].upper()}")
    print(f"  Confidence Boost: {classical['confidence_boost']:+d}")
    for p in classical["fired_patterns"]:
        print(f"    * {p}")
    if not classical["fired_patterns"]:
        print("    (No classical vehicle purchase patterns detected)")

    print(f"\n{'─' * 80}")
    print("  LAYER 5: OUTCOME / QUALITY (Vehicle Purchase Classification)")
    print(f"{'─' * 80}")
    print(f"  Vehicle Mode: {outcome['mode']}")
    print(f"  Quality: {outcome['quality']}")
    for o in outcome["fired_outcomes"]:
        print(f"    * {o}")

    # Scan vehicle purchase windows
    print(f"\n{'─' * 80}")
    print("  SCANNING VEHICLE PURCHASE WINDOWS (Age 18-60, step=6mo)...")
    print(f"{'─' * 80}")

    windows = scan_vehicle_purchase_windows(chart, start_age=18, end_age=60, step_months=6)

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
    print("  TOP 5 VEHICLE PURCHASE WINDOWS — DETAILED 5-LAYER BREAKDOWN")
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
        print(f"\n  STRONGEST VEHICLE PURCHASE WINDOW:")
        print(f"  {top.period_start.strftime('%B %Y')} - {top.period_end.strftime('%B %Y')}")
        print(f"  Age {top.age_start:.1f}-{top.age_end:.1f} | {top.md_lord}-{top.ad_lord}")
        print(f"  Score: {top.total_score:.1f} | {top.likelihood}")
        print(f"\n  Vehicle Mode: {outcome['mode']}")
        print(f"  Quality: {outcome['quality']}")
        print(f"\n  The 5-layer engine evaluated {len(windows)} AD periods with")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['high'])} HIGH+ confidence windows.")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['very_high'])} VERY_HIGH confidence windows.")
    print(f"\n{'=' * 80}")
