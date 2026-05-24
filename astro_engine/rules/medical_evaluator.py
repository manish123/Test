"""
Medical Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow.
Domain: Surgery and Medical Events
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
RULES_DIR = Path(__file__).resolve().parent / "domains" / "medical" / "surgery_and_medical_events"

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
BENEFIC_HOUSES = {1, 2, 4, 5, 7, 9, 11}
MALEFIC_HOUSES = {3, 6, 8, 12}

# Medical-specific constants
MEDICAL_KARAKAS = {"Mars", "Saturn", "Rahu", "Ketu", "Sun"}  # disease/surgery planets
MEDICAL_HOUSES = {6, 8, 12, 1, 2, 7}  # disease, trauma, hospitalization, body, maraka houses




# ═══════════════════════════════════════════════════════════════
# CALIBRATION OVERLAY LOADER (Layer 3)
# ═══════════════════════════════════════════════════════════════

def _load_calibration():
    """
    Load calibration overlay from JSON.
    Returns dict with layer_weights, likelihood_thresholds, base_scores,
    outcome_calibration, and rule_adjustments.

    If file not found, returns sensible defaults.
    Calibration is NEVER hardcoded — always loaded from external config.
    """
    calibration_path = RULES_DIR / "calibration_overlay.json"
    try:
        with open(calibration_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback defaults — should never be needed in production
        return {
            "layer_weights": {
                "dasha_weight": 0.35,
                "transit_weight": 0.35,
                "fast_trigger_weight": 0.20,
                "classical_weight": 0.10,
            },
            "likelihood_thresholds": {
                "very_high": 55,
                "high": 40,
                "moderate": 25,
                "low": 15,
            },


            "base_scores": {
                "dasha": {
                    "medical_karaka_lord_md_or_ad": 45,
                    "sixth_lord_md_or_ad": 42,
                    "eighth_lord_md_or_ad": 40,
                    "twelfth_lord_md_or_ad": 38,
                    "second_lord_md_or_ad": 35,
                    "seventh_lord_md_or_ad": 33,
                },
                "transit": {
                    "lagna_lord_transit_6_8_12": 50,
                    "rahu_conjunct_natal_mars": 42,
                    "rahu_conjunct_natal_8th_lord": 40,
                    "saturn_over_lagna_sphuta": 38,
                    "saturn_8th_from_moon": 45,
                },
                "fast_trigger": {
                    "vinasha_tara_23rd": 30,
                    "vipat_tara_3rd": 25,
                    "pratyak_tara_5th": 22,
                    "mars_anga_gochara_1st_2nd": 28,
                    "moon_vipat_pratyak_3rd_5th": 20,
                },
            },

            "outcome_calibration": {
                "mode_priority_order": [
                    "surgery_mars_ketu_6_8",
                    "chronic_disease_saturn_6th",
                    "acute_illness_sun_mars_afflicted",
                    "hospitalization_12L_8L",
                    "recovery_jupiter_venus",
                    "injury_mars_rahu_8th",
                ],
                "quality_priority_order": [
                    "life_threatening_8L_2L",
                    "manageable_jupiter_aspect",
                    "painful_mars_saturn",
                    "healing_venus_jupiter_5th",
                ],
                "default_mode": "general_medical",
            },
        }


# Module-level calibration (loaded once at import)
CALIBRATION = _load_calibration()





SIGN_NAMES = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
    5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
    9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
}

# Nakshatra lords (Vimshottari sequence)
NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]

# Jupiter special aspects: from its position, it aspects houses 5, 7, 9 away
# Saturn special aspects: from its position, it aspects houses 3, 7, 10 away
JUPITER_ASPECTS = [5, 7, 9]
SATURN_ASPECTS = [3, 7, 10]
MARS_ASPECTS = [4, 7, 8]


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
    """Encapsulates all natal chart data needed for rule evaluation."""

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
                "longitude": lon_val,
                "sign": sign,
                "house": house,
                "nakshatra": get_nakshatra(lon_val),
            }



        # Key house lords (medical-focused)
        self.lagna_lord = SIGN_LORDS[self.asc_sign]
        self.sixth_sign = ((self.asc_sign + 5 - 1) % 12) + 1
        self.sixth_lord = SIGN_LORDS[self.sixth_sign]
        self.eighth_sign = ((self.asc_sign + 7 - 1) % 12) + 1
        self.eighth_lord = SIGN_LORDS[self.eighth_sign]
        self.twelfth_sign = ((self.asc_sign + 11 - 1) % 12) + 1
        self.twelfth_lord = SIGN_LORDS[self.twelfth_sign]
        self.second_sign = ((self.asc_sign + 1 - 1) % 12) + 1
        self.second_lord = SIGN_LORDS[self.second_sign]
        self.seventh_sign = ((self.asc_sign + 6 - 1) % 12) + 1
        self.seventh_lord = SIGN_LORDS[self.seventh_sign]
        self.fourth_sign = ((self.asc_sign + 3 - 1) % 12) + 1
        self.fourth_lord = SIGN_LORDS[self.fourth_sign]
        self.fifth_sign = ((self.asc_sign + 4 - 1) % 12) + 1
        self.fifth_lord = SIGN_LORDS[self.fifth_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.tenth_sign = ((self.asc_sign + 9 - 1) % 12) + 1
        self.tenth_lord = SIGN_LORDS[self.tenth_sign]
        self.eleventh_sign = ((self.asc_sign + 10 - 1) % 12) + 1
        self.eleventh_lord = SIGN_LORDS[self.eleventh_sign]
        self.third_sign = ((self.asc_sign + 2 - 1) % 12) + 1
        self.third_lord = SIGN_LORDS[self.third_sign]

        # Planets in 6th house (disease)
        self.sixth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 6
        ]

        # Planets in 8th house (trauma/surgery)
        self.eighth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 8
        ]

        # Planets aspecting 6th house
        self.sixth_house_aspectors = self._get_aspectors_of_house(6)

        # Planets aspecting 8th house
        self.eighth_house_aspectors = self._get_aspectors_of_house(8)



        # Karakamsa (Atmakaraka in Navamsa sign)
        self.atmakaraka = self._compute_atmakaraka()
        self.karakamsa_sign = self._get_d9_sign(self.birth_positions[self.atmakaraka])

        # Sensitive Medical Points
        # Point 1: 6th lord + 8th lord longitude sum (disease-trauma axis)
        sixth_lord_lon = self.birth_positions[self.sixth_lord]
        eighth_lord_lon = self.birth_positions[self.eighth_lord]
        self.sensitive_point_1 = (sixth_lord_lon + eighth_lord_lon) % 360

        # Point 2: Mars + Saturn longitude sum (surgery axis)
        mars_lon = self.birth_positions["Mars"]
        saturn_lon = self.birth_positions["Saturn"]
        self.sensitive_point_2 = (mars_lon + saturn_lon) % 360

        # Lagna Sphuta (ascendant degree)
        self.lagna_sphuta = self.asc_lon


    def _compute_atmakaraka(self):
        """Compute Atmakaraka (planet with highest degree in sign)."""
        max_deg = -1
        ak = "Sun"
        for name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]:
            if name in self.birth_positions:
                lon_val = self.birth_positions[name]
                deg_in_sign = lon_val % 30
                if name == "Rahu":
                    deg_in_sign = 30 - deg_in_sign  # Rahu is reverse
                if deg_in_sign > max_deg:
                    max_deg = deg_in_sign
                    ak = name
        return ak



    def _get_aspectors_of_house(self, target_house):
        """Get planets that aspect a given house via Vedic aspects."""
        aspectors = []
        for name, data in self.planets.items():
            planet_house = data["house"]
            # All planets aspect 7th from themselves
            if ((planet_house + 7 - 1 - 1) % 12) + 1 == target_house:
                aspectors.append(name)
            # Jupiter special aspects (5, 7, 9)
            if name == "Jupiter":
                for asp in [5, 9]:
                    if ((planet_house + asp - 1 - 1) % 12) + 1 == target_house:
                        aspectors.append(name)
            # Saturn special aspects (3, 7, 10)
            if name == "Saturn":
                for asp in [3, 10]:
                    if ((planet_house + asp - 1 - 1) % 12) + 1 == target_house:
                        aspectors.append(name)
            # Mars special aspects (4, 7, 8)
            if name == "Mars":
                for asp in [4, 8]:
                    if ((planet_house + asp - 1 - 1) % 12) + 1 == target_house:
                        aspectors.append(name)
        return list(set(aspectors))

    def _compute_d9_lagna(self):
        """Compute Navamsa lagna sign from ascendant longitude."""
        return self._get_d9_sign(self.asc_lon)

    def _get_d9_sign(self, longitude):
        """Get the Navamsa sign for a given longitude."""
        lon = normalize_lon(longitude)
        sign = int(lon // 30) + 1
        degree_in_sign = lon % 30
        navamsa_index = int(degree_in_sign / 3.333333333)  # 0-8

        # Starting navamsa depends on sign element
        if sign in [1, 5, 9]:    # Fire signs start from Aries
            start = 1
        elif sign in [2, 6, 10]:  # Earth signs start from Capricorn
            start = 10
        elif sign in [3, 7, 11]:  # Air signs start from Libra
            start = 7
        else:                     # Water signs start from Cancer
            start = 4

        d9_sign = ((start - 1 + navamsa_index) % 12) + 1
        return d9_sign

    def get_house_from_sign(self, transit_sign, reference_sign=None):
        """Get house number from a sign, relative to reference (default: lagna)."""
        ref = reference_sign or self.asc_sign
        return ((transit_sign - ref) % 12) + 1





# ═══════════════════════════════════════════════════════════════
# TRANSIT STATE (computed for a specific date)
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
            self.planet_houses_from_moon[name] = chart.get_house_from_sign(
                sign, chart.moon_sign
            )

    def planet_aspects_house(self, planet, target_house, from_ref="lagna"):
        """Check if a transit planet aspects a target house."""
        if from_ref == "lagna":
            p_house = self.planet_houses_from_lagna[planet]
        else:
            p_house = self.planet_houses_from_moon[planet]

        # All planets aspect 7th from themselves
        aspected = [((p_house + 6) % 12) + 1]

        if planet == "Jupiter":
            aspected.extend([((p_house + 4) % 12) + 1, ((p_house + 8) % 12) + 1])
        elif planet == "Saturn":
            aspected.extend([((p_house + 2) % 12) + 1, ((p_house + 9) % 12) + 1])
        elif planet == "Mars":
            aspected.extend([((p_house + 3) % 12) + 1, ((p_house + 7) % 12) + 1])

        # Also include conjunction (being in the house)
        aspected.append(p_house)

        return target_house in aspected



    def planet_in_sign(self, planet, target_sign):
        """Check if transit planet is in a specific sign."""
        return self.planet_signs.get(planet) == target_sign

    def rahu_conjunct_natal(self, natal_lon, orb=5.0):
        """Check if transit Rahu is within orb of a natal degree."""
        rahu_lon = self.positions["Rahu"]
        diff = abs((rahu_lon - natal_lon) % 360)
        diff = min(diff, 360 - diff)
        return diff <= orb

    def saturn_conjunct_natal(self, natal_lon, orb=5.0):
        """Check if transit Saturn is within orb of a natal degree."""
        sat_lon = self.positions["Saturn"]
        diff = abs((sat_lon - natal_lon) % 360)
        diff = min(diff, 360 - diff)
        return diff <= orb





# ═══════════════════════════════════════════════════════════════
# LAYER 1: DASHA EVALUATOR (Medical)
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate dasha rules for surgery/medical events.
    Key lords: 6th lord (disease), 8th lord (trauma/surgery), 12th lord (hospitalization),
               2nd lord (maraka), 7th lord (maraka).
    Positive recovery: Jupiter-Venus = recovery period.
    Negative: Mars-Ketu = surgery, Moon-Mars = bleeding, Saturn-Saturn = chronic,
              Mars-Sun afflicted = fever/distress.
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Key lords for medical events
    key_lords = {
        chart.sixth_lord: ("6th lord", "disease", 42),
        chart.eighth_lord: ("8th lord", "trauma/surgery", 40),
        chart.twelfth_lord: ("12th lord", "hospitalization", 38),
        chart.second_lord: ("2nd lord", "maraka (death-inflicting)", 35),
        chart.seventh_lord: ("7th lord", "maraka (death-inflicting)", 33),
    }

    # Rule 1: Medical house lords in MD/AD (priority 98)
    r1_score = 0
    r1_reasons = []

    for lord, (label, domain, base_score) in key_lords.items():
        if md_lord == lord:
            r1_score += base_score
            r1_reasons.append(f"MD of {label} ({lord}) — {domain}")
        if ad_lord == lord:
            r1_score += int(base_score * 0.8)
            r1_reasons.append(f"AD of {label} ({lord}) — {domain}")

    if r1_score > 0:
        fired.append(("medical_house_lord_dasha", r1_score, r1_reasons))



    # Rule 2: Medical karaka planets in MD/AD (priority 95)
    r2_score = 0
    r2_reasons = []

    karaka_scores = {
        "Mars": (45, "surgery/wounds/inflammation"),
        "Saturn": (40, "chronic disease/bones/nerves"),
        "Rahu": (38, "mysterious illness/poisoning"),
        "Ketu": (36, "sudden surgery/karmic illness"),
        "Sun": (32, "fever/heart/vitality loss"),
    }

    if md_lord in MEDICAL_KARAKAS:
        score, desc = karaka_scores[md_lord]
        r2_score += score
        r2_reasons.append(f"MD of medical karaka {md_lord} ({desc})")
    if ad_lord in MEDICAL_KARAKAS:
        score, desc = karaka_scores[ad_lord]
        r2_score += int(score * 0.75)
        r2_reasons.append(f"AD of medical karaka {ad_lord} ({desc})")

    if r2_score > 0:
        fired.append(("medical_karaka_dasha", r2_score, r2_reasons))

    # Rule 3: Negative dasha combinations for medical crises (priority 92)
    r3_score = 0
    r3_reasons = []

    # Mars-Ketu = surgery (knife + sudden)
    if md_lord == "Mars" and ad_lord == "Ketu":
        r3_score += 48
        r3_reasons.append("Mars MD + Ketu AD — surgery/cutting/sudden medical intervention")
    # Moon-Mars = bleeding/blood issues
    if md_lord == "Moon" and ad_lord == "Mars":
        r3_score += 38
        r3_reasons.append("Moon MD + Mars AD — bleeding/blood disorders/hemorrhage")
    # Saturn-Saturn = chronic suffering
    if md_lord == "Saturn" and ad_lord == "Saturn":
        r3_score += 42
        r3_reasons.append("Saturn MD + Saturn AD — chronic disease/prolonged suffering")
    # Mars-Sun afflicted = fever/distress
    if md_lord == "Mars" and ad_lord == "Sun":
        r3_score += 35
        r3_reasons.append("Mars MD + Sun AD — high fever/inflammatory distress/pitta aggravation")
    # Rahu-Mars = accidents/poisoning
    if md_lord == "Rahu" and ad_lord == "Mars":
        r3_score += 40
        r3_reasons.append("Rahu MD + Mars AD — accidents/poisoning/mysterious wounds")
    # Ketu-Saturn = nerve damage/paralysis
    if md_lord == "Ketu" and ad_lord == "Saturn":
        r3_score += 38
        r3_reasons.append("Ketu MD + Saturn AD — nerve damage/paralysis/karmic chronic illness")

    if r3_score > 0:
        fired.append(("medical_negative_dasha", r3_score, r3_reasons))



    # Rule 4: Positive recovery combinations (priority 88)
    r4_score = 0
    r4_reasons = []

    # Jupiter-Venus = recovery period
    if md_lord == "Jupiter" and ad_lord == "Venus":
        r4_score -= 30
        r4_reasons.append("Jupiter MD + Venus AD — recovery period/healing/medical relief")
    # Venus-Jupiter = healing grace
    if md_lord == "Venus" and ad_lord == "Jupiter":
        r4_score -= 25
        r4_reasons.append("Venus MD + Jupiter AD — divine healing grace/recovery from illness")
    # Jupiter-Moon = mental recovery
    if md_lord == "Jupiter" and ad_lord == "Moon":
        r4_score -= 20
        r4_reasons.append("Jupiter MD + Moon AD — mental/emotional recovery, nurturing care")

    if r4_score != 0:
        fired.append(("medical_recovery_dasha", r4_score, r4_reasons))

    # Rule 5: MD/AD lord is a Maraka lord (priority 85)
    r5_score = 0
    r5_reasons = []

    maraka_lords = {chart.second_lord, chart.seventh_lord}
    if md_lord in maraka_lords:
        r5_score += 30
        r5_reasons.append(f"MD lord {md_lord} is Maraka lord — life-threatening period")
    if ad_lord in maraka_lords:
        r5_score += 25
        r5_reasons.append(f"AD lord {ad_lord} is Maraka lord — health crisis sub-period")

    if r5_score > 0:
        fired.append(("medical_maraka_dasha", r5_score, r5_reasons))

    # Rule 6: MD/AD lord placed in medical houses (priority 80)
    r6_score = 0
    r6_reasons = []

    md_house = chart.planets.get(md_lord, {}).get("house", 0)
    ad_house = chart.planets.get(ad_lord, {}).get("house", 0)

    if md_house in MEDICAL_HOUSES:
        r6_score += 20
        r6_reasons.append(f"MD lord {md_lord} placed in medical house {md_house}")
    if ad_house in MEDICAL_HOUSES:
        r6_score += 15
        r6_reasons.append(f"AD lord {ad_lord} placed in medical house {ad_house}")

    if r6_score > 0:
        fired.append(("medical_lord_placement", r6_score, r6_reasons))

    return fired





# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR (Medical)
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate transit rules for medical event activation.
    Key: Lagna lord transit through 6/8/12 (crisis),
    Rahu conjunct natal Mars (accidents), Rahu conjunct natal 8th lord (accidents),
    Saturn over Lagna Sphuta (bad health), Saturn transit 8th from Moon (Ashtama Shani).
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Rule 1: Lagna lord transit through 6/8/12 (health crisis — priority 98)
    lagna_lord_house_transit = transit.planet_houses_from_lagna.get(chart.lagna_lord, 0)
    if lagna_lord_house_transit in [6, 8, 12]:
        house_meaning = {6: "disease", 8: "trauma/surgery", 12: "hospitalization"}
        fired.append(("lagna_lord_transit_6_8_12", 50,
                      [f"Transit Lagna lord ({chart.lagna_lord}) in {lagna_lord_house_transit}th house — {house_meaning[lagna_lord_house_transit]} crisis"]))

    # Rule 2: Rahu conjunct natal Mars (accidents/wounds — priority 95)
    natal_mars_lon = chart.birth_positions["Mars"]
    if transit.rahu_conjunct_natal(natal_mars_lon, orb=5.0):
        fired.append(("rahu_conjunct_natal_mars", 42,
                      ["Transit Rahu conjunct natal Mars — accident/wound/surgical emergency"]))

    # Rule 3: Rahu conjunct natal 8th lord (trauma activation — priority 92)
    natal_8th_lord_lon = chart.birth_positions[chart.eighth_lord]
    if transit.rahu_conjunct_natal(natal_8th_lord_lon, orb=5.0):
        fired.append(("rahu_conjunct_natal_8th_lord", 40,
                      [f"Transit Rahu conjunct natal 8th lord ({chart.eighth_lord}) — trauma/surgery activation"]))

    # Rule 4: Saturn over Lagna Sphuta (bad health — priority 90)
    if transit.saturn_conjunct_natal(chart.lagna_sphuta, orb=5.0):
        fired.append(("saturn_over_lagna_sphuta", 38,
                      ["Transit Saturn over Lagna Sphuta — deteriorating health/vitality loss"]))

    # Rule 5: Saturn transit 8th from Moon — Ashtama Shani (priority 95)
    sat_house_from_moon = transit.planet_houses_from_moon.get("Saturn", 0)
    if sat_house_from_moon == 8:
        fired.append(("saturn_8th_from_moon_ashtama", 45,
                      ["Transit Saturn in 8th from Moon (Ashtama Shani) — severe health crisis/surgery period"]))

    # Rule 6: Mars transit through 6/8 from Lagna (surgical trigger)
    mars_house_lagna = transit.planet_houses_from_lagna.get("Mars", 0)
    if mars_house_lagna in [6, 8]:
        fired.append(("mars_transit_6_8", 30,
                      [f"Transit Mars in {mars_house_lagna}th from Lagna — surgical/wound trigger"]))

    return fired





# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR (Medical)
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate fast trigger rules for exact medical event timing.
    Vinasha Tara (23rd Nakshatra from Moon) = surgery/trauma
    Vipat Tara (3rd Nakshatra) = danger
    Pratyak Tara (5th Nakshatra) = obstacles/procedure day
    Mars in 1st-2nd Nakshatra from Moon (Anga Gochara face = death/emergency)
    Moon in 3rd or 5th Nakshatra from birth (Vipat/Pratyak = medical procedure day)
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Get Moon's birth nakshatra index (0-26)
    birth_moon_nak_idx = int((chart.moon_lon % 360) / 13.3333333333) % 27

    # Transit Moon nakshatra position relative to birth
    transit_moon_lon = transit.positions["Moon"]
    transit_moon_nak_idx = int((transit_moon_lon % 360) / 13.3333333333) % 27
    moon_nak_offset = ((transit_moon_nak_idx - birth_moon_nak_idx) % 27) + 1

    # Transit Mars nakshatra position relative to birth
    transit_mars_lon = transit.positions["Mars"]
    transit_mars_nak_idx = int((transit_mars_lon % 360) / 13.3333333333) % 27
    mars_nak_offset = ((transit_mars_nak_idx - birth_moon_nak_idx) % 27) + 1

    # Rule 1: Vinasha Tara (23rd Nakshatra from Moon) = surgery/trauma
    if moon_nak_offset == 23:
        fired.append(("fast_trigger_vinasha_tara_23rd", 30,
                      ["Moon on Vinasha Tara (23rd nak) — surgery/trauma/destruction day"]))

    # Rule 2: Vipat Tara (3rd Nakshatra) = danger
    if moon_nak_offset == 3:
        fired.append(("fast_trigger_vipat_tara_3rd", 25,
                      ["Moon on Vipat Tara (3rd nak) — danger/medical complication day"]))

    # Rule 3: Pratyak Tara (5th Nakshatra) = obstacles/procedure day
    if moon_nak_offset == 5:
        fired.append(("fast_trigger_pratyak_tara_5th", 22,
                      ["Moon on Pratyak Tara (5th nak) — obstacles/medical procedure day"]))

    # Rule 4: Mars in 1st-2nd Nakshatra from Moon (Anga Gochara face = death/emergency)
    if mars_nak_offset in [1, 2]:
        fired.append(("fast_trigger_mars_anga_gochara_face", 28,
                      [f"Mars in {mars_nak_offset}th Nakshatra (Anga Gochara - face) — death/medical emergency"]))

    # Rule 5: Moon in 3rd or 5th Nakshatra from birth (Vipat/Pratyak = medical procedure day)
    if moon_nak_offset in [3, 5]:
        tara_name = "Vipat" if moon_nak_offset == 3 else "Pratyak"
        fired.append(("fast_trigger_moon_vipat_pratyak", 20,
                      [f"Moon in {moon_nak_offset}th Nakshatra ({tara_name} Tara) — medical procedure/crisis day"]))

    # Rule 6: Mars on Vinasha Tara (23rd) — surgical intervention
    if mars_nak_offset == 23:
        fired.append(("fast_trigger_mars_vinasha_tara", 26,
                      ["Mars on Vinasha Tara (23rd nak) — surgical intervention/wound"]))

    return fired





# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR (Medical)
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """
    Evaluate classical medical patterns (structural — not time-dependent).
    Checks: 6th + 8th lords in Lagna with Sun/Mars,
    6th lord in 6/1/8 = ulcers/bruises, Saturn-Mars in 6th + Sun/Rahu aspect,
    Moon Papakartari + Saturn 7th = bodily suffering,
    Mars/Ketu in 6/8 = ulcers/wounds,
    Mars in 4th/5th from Karakamsa = ulcers (Jaimini).
    Returns dict with confidence_boost and fired_patterns.
    """
    results = {
        "timing_modifier": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    sixth_lord_house = chart.planets[chart.sixth_lord]["house"]
    eighth_lord_house = chart.planets[chart.eighth_lord]["house"]
    lagna_lord_house = chart.planets[chart.lagna_lord]["house"]
    mars_house = chart.planets["Mars"]["house"]
    saturn_house = chart.planets["Saturn"]["house"]
    sun_house = chart.planets["Sun"]["house"]
    moon_house = chart.planets["Moon"]["house"]
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    ketu_house = chart.planets.get("Ketu", {}).get("house", 0)
    jupiter_house = chart.planets["Jupiter"]["house"]
    venus_house = chart.planets["Venus"]["house"]



    # Pattern 1: 6th + 8th lords in Lagna with Sun/Mars — severe disease
    if sixth_lord_house == 1 and eighth_lord_house == 1:
        if sun_house == 1 or mars_house == 1:
            results["confidence_boost"] += 18
            results["timing_modifier"] = "acute_onset"
            results["fired_patterns"].append(
                f"6th lord ({chart.sixth_lord}) + 8th lord ({chart.eighth_lord}) in Lagna with Sun/Mars — severe disease/trauma in body")

    # Pattern 2: 6th lord in 6/1/8 = ulcers/bruises
    if sixth_lord_house in [6, 1, 8]:
        results["confidence_boost"] += 12
        house_effect = {6: "recurrent disease", 1: "disease affecting body/appearance", 8: "chronic hidden disease"}
        results["fired_patterns"].append(
            f"6th lord ({chart.sixth_lord}) in house {sixth_lord_house} — {house_effect[sixth_lord_house]}/ulcers/bruises")

    # Pattern 3: Saturn-Mars in 6th + Sun/Rahu aspect = lingering illness
    if saturn_house == 6 and mars_house == 6:
        sun_aspects_6 = "Sun" in chart.sixth_house_aspectors
        rahu_aspects_6 = "Rahu" in chart.sixth_house_aspectors or rahu_house == 6
        if sun_aspects_6 or rahu_aspects_6:
            results["confidence_boost"] += 16
            results["timing_modifier"] = "chronic_lingering"
            results["fired_patterns"].append(
                "Saturn + Mars in 6th house with Sun/Rahu aspect — lingering illness/prolonged suffering")

    # Pattern 4: Moon Papakartari + Saturn in 7th = bodily suffering
    # Papakartari: malefics on both sides of Moon
    moon_prev_house = ((moon_house - 2) % 12) + 1
    moon_next_house = (moon_house % 12) + 1
    malefic_prev = any(chart.planets[p]["house"] == moon_prev_house for p in NATURAL_MALEFICS if p in chart.planets)
    malefic_next = any(chart.planets[p]["house"] == moon_next_house for p in NATURAL_MALEFICS if p in chart.planets)
    papakartari = malefic_prev and malefic_next

    if papakartari and saturn_house == 7:
        results["confidence_boost"] += 14
        results["fired_patterns"].append(
            "Moon in Papakartari Yoga + Saturn in 7th house — bodily suffering/chronic health issues")

    # Pattern 5: Mars/Ketu in 6/8 = ulcers/wounds
    if mars_house in [6, 8] or ketu_house in [6, 8]:
        wounds = []
        if mars_house in [6, 8]:
            wounds.append(f"Mars in {mars_house}th")
        if ketu_house in [6, 8]:
            wounds.append(f"Ketu in {ketu_house}th")
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            f"{' + '.join(wounds)} — ulcers/wounds/surgical marks on body")



    # Pattern 6: Mars in 4th/5th from Karakamsa = ulcers (Jaimini Sutra)
    karakamsa_house = ((chart.karakamsa_sign - chart.asc_sign) % 12) + 1
    mars_from_karakamsa = ((mars_house - karakamsa_house) % 12) + 1
    if mars_from_karakamsa in [4, 5]:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(
            f"Mars in {mars_from_karakamsa}th from Karakamsa ({SIGN_NAMES[chart.karakamsa_sign]}) — ulcers/boils (Jaimini)")

    # Pattern 7: Jupiter aspects 6th or 8th = divine protection / recovery
    jupiter_aspects_6 = "Jupiter" in chart.sixth_house_aspectors
    jupiter_aspects_8 = "Jupiter" in chart.eighth_house_aspectors
    if jupiter_aspects_6 or jupiter_aspects_8:
        results["confidence_boost"] -= 8
        target = "6th" if jupiter_aspects_6 else "8th"
        results["fired_patterns"].append(
            f"Jupiter aspects {target} house — divine protection / recovery from illness")

    # Pattern 8: 8th lord in 8th (Sarala Yoga component) — survives crises
    if eighth_lord_house == 8:
        results["confidence_boost"] -= 5
        results["fired_patterns"].append(
            f"8th lord ({chart.eighth_lord}) in 8th house (Sarala Yoga) — survives medical crises/transformation")

    return results





# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR (Medical)
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """
    Evaluate outcome/quality rules for medical event classification.
    Mode: surgery, chronic_disease, acute_illness, hospitalization, recovery, injury
    Quality: life_threatening, manageable, painful, healing
    Body system: cardiovascular, nervous, digestive, blood, bones, skin
    """
    fired_rules = []

    mars_house = chart.planets["Mars"]["house"]
    saturn_house = chart.planets["Saturn"]["house"]
    sun_house = chart.planets["Sun"]["house"]
    moon_house = chart.planets["Moon"]["house"]
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    ketu_house = chart.planets.get("Ketu", {}).get("house", 0)
    jupiter_house = chart.planets["Jupiter"]["house"]
    venus_house = chart.planets["Venus"]["house"]
    sixth_lord_house = chart.planets[chart.sixth_lord]["house"]
    eighth_lord_house = chart.planets[chart.eighth_lord]["house"]
    twelfth_lord_house = chart.planets[chart.twelfth_lord]["house"]
    second_lord_house = chart.planets[chart.second_lord]["house"]
    seventh_lord_house = chart.planets[chart.seventh_lord]["house"]
    lagna_lord_house = chart.planets[chart.lagna_lord]["house"]



    # ─── MODE DETECTION ───

    # Surgery: Mars/Ketu in 6/8
    if (mars_house in [6, 8] or ketu_house in [6, 8]):
        fired_rules.append(("surgery_mars_ketu_6_8", "mode_surgery", 0.90,
            f"Mars/Ketu in 6th/8th house — surgical intervention indicated"))

    # Chronic disease: Saturn in 6th or aspecting 6th
    if saturn_house == 6 or "Saturn" in chart.sixth_house_aspectors:
        fired_rules.append(("chronic_disease_saturn_6th", "mode_chronic", 0.85,
            f"Saturn influencing 6th house — chronic/long-lasting disease"))

    # Acute illness: Sun/Mars afflicted in 1st/6th
    if (sun_house in [1, 6] and mars_house in [1, 6]):
        fired_rules.append(("acute_illness_sun_mars_afflicted", "mode_acute", 0.82,
            "Sun + Mars in 1st/6th — acute inflammatory illness"))

    # Hospitalization: 12th lord + 8th lord connection
    if twelfth_lord_house == 8 or eighth_lord_house == 12:
        fired_rules.append(("hospitalization_12L_8L", "mode_hospitalization", 0.80,
            f"12th-8th lord connection — hospitalization/confinement"))

    # Recovery: Jupiter-Venus strong in kendras/trikonas
    if jupiter_house in [1, 4, 5, 7, 9, 10] and venus_house in [1, 4, 5, 7, 9, 10]:
        fired_rules.append(("recovery_jupiter_venus", "mode_recovery", 0.78,
            "Jupiter + Venus strong in kendras/trikonas — recovery/healing capacity"))

    # Injury: Mars + Rahu in 8th
    if mars_house == 8 and rahu_house == 8:
        fired_rules.append(("injury_mars_rahu_8th", "mode_injury", 0.88,
            "Mars + Rahu in 8th house — severe injury/accident"))



    # ─── QUALITY DETECTION ───

    # Life-threatening: 8th lord + 2nd lord connection (maraka + longevity)
    if eighth_lord_house == 2 or second_lord_house == 8:
        fired_rules.append(("life_threatening_8L_2L", "quality_life_threatening", 0.90,
            f"8th-2nd lord connection — life-threatening medical event"))

    # Manageable: Jupiter aspect on 6th/8th
    jupiter_aspects_6 = "Jupiter" in chart.sixth_house_aspectors
    jupiter_aspects_8 = "Jupiter" in chart.eighth_house_aspectors
    if jupiter_aspects_6 or jupiter_aspects_8:
        fired_rules.append(("manageable_jupiter_aspect", "quality_manageable", 0.82,
            "Jupiter aspects disease/trauma house — manageable/recoverable illness"))

    # Painful: Mars + Saturn connection (inflammation + chronic pain)
    mars_sign = chart.planets["Mars"]["sign"]
    saturn_sign = chart.planets["Saturn"]["sign"]
    mars_saturn_same_house = mars_house == saturn_house
    if mars_saturn_same_house or mars_house in [6, 8] and saturn_house in [6, 8]:
        fired_rules.append(("painful_mars_saturn", "quality_painful", 0.85,
            "Mars-Saturn connection in disease houses — painful/prolonged suffering"))

    # Healing: Venus + Jupiter in 5th/9th (divine grace)
    if (venus_house in [5, 9] or jupiter_house in [5, 9]):
        fired_rules.append(("healing_venus_jupiter_5th", "quality_healing", 0.78,
            "Venus/Jupiter in trikona — healing capacity/divine medical grace"))



    # ─── BODY SYSTEM DETECTION ───

    # Cardiovascular: Sun afflicted in 4th/5th or Leo sign
    sun_sign = chart.planets["Sun"]["sign"]
    if sun_house in [4, 5] or sun_sign == 5:  # Leo
        fired_rules.append(("body_cardiovascular", "body_cardiovascular", 0.75,
            "Sun in 4th/5th or Leo — cardiovascular system vulnerability"))

    # Nervous: Ketu/Mercury afflicted
    mercury_house = chart.planets["Mercury"]["house"]
    if ketu_house in [1, 6, 8] or (mercury_house in [6, 8] and ketu_house == mercury_house):
        fired_rules.append(("body_nervous", "body_nervous", 0.72,
            "Ketu/Mercury affliction — nervous system vulnerability"))

    # Digestive: Moon/Mars in 5th/6th or Virgo
    moon_sign = chart.planets["Moon"]["sign"]
    if (moon_house in [5, 6] or mars_house in [5, 6]) and (moon_sign == 6 or mars_sign == 6):
        fired_rules.append(("body_digestive", "body_digestive", 0.70,
            "Moon/Mars in 5th/6th with Virgo influence — digestive system vulnerability"))

    # Blood: Mars afflicted in 6/8
    if mars_house in [6, 8]:
        fired_rules.append(("body_blood", "body_blood", 0.74,
            f"Mars in {mars_house}th house — blood/surgical/inflammatory system"))

    # Bones: Saturn in 1/6/8/10
    if saturn_house in [1, 6, 8, 10]:
        fired_rules.append(("body_bones", "body_bones", 0.72,
            f"Saturn in house {saturn_house} — bones/joints/structural vulnerability"))

    # Skin: Rahu/Ketu in 1/2/6
    if rahu_house in [1, 2, 6] or ketu_house in [1, 2, 6]:
        fired_rules.append(("body_skin", "body_skin", 0.68,
            "Rahu/Ketu in 1st/2nd/6th — skin/allergic/mysterious ailments"))



    # ═══════════════════════════════════════════════════════════
    # RESOLUTION (Layer 3 — calibration-based)
    # ═══════════════════════════════════════════════════════════
    cal = CALIBRATION.get("outcome_calibration", {})
    mode_priority = cal.get("mode_priority_order", [])
    quality_priority = cal.get("quality_priority_order", [])
    default_mode = cal.get("default_mode", "general_medical")

    # Resolve MODE
    resolved_mode = "unknown"
    mode_rules = [r for r in fired_rules if r[1].startswith("mode_")]
    if mode_rules:
        def _mode_sort_key(rule):
            tag = rule[0]
            try:
                priority_idx = mode_priority.index(tag)
            except ValueError:
                priority_idx = 999
            return (priority_idx, -rule[2])

        mode_rules.sort(key=_mode_sort_key)
        best_mode_rule = mode_rules[0]
        mode_map = {
            "mode_surgery": "surgery",
            "mode_chronic": "chronic_disease",
            "mode_acute": "acute_illness",
            "mode_hospitalization": "hospitalization",
            "mode_recovery": "recovery",
            "mode_injury": "injury",
        }
        resolved_mode = mode_map.get(best_mode_rule[1], default_mode)
    else:
        resolved_mode = default_mode

    # Resolve QUALITY
    resolved_quality = "unknown"
    quality_rules = [r for r in fired_rules if r[1].startswith("quality_")]
    if quality_rules:
        def _quality_sort_key(rule):
            tag = rule[0]
            try:
                priority_idx = quality_priority.index(tag)
            except ValueError:
                priority_idx = 999
            return (priority_idx, -rule[2])

        quality_rules.sort(key=_quality_sort_key)
        best_quality_rule = quality_rules[0]
        quality_map = {
            "quality_life_threatening": "life_threatening",
            "quality_manageable": "manageable",
            "quality_painful": "painful",
            "quality_healing": "healing",
        }
        resolved_quality = quality_map.get(best_quality_rule[1], "unknown")
    else:
        resolved_quality = "unknown"



    # Resolve BODY SYSTEM
    resolved_body_system = "unknown"
    body_rules = [r for r in fired_rules if r[1].startswith("body_")]
    if body_rules:
        body_rules.sort(key=lambda r: -r[2])
        best_body = body_rules[0]
        body_map = {
            "body_cardiovascular": "cardiovascular",
            "body_nervous": "nervous",
            "body_digestive": "digestive",
            "body_blood": "blood",
            "body_bones": "bones",
            "body_skin": "skin",
        }
        resolved_body_system = body_map.get(best_body[1], "unknown")

    results = {
        "mode": resolved_mode,
        "quality": resolved_quality,
        "body_system": resolved_body_system,
        "fired_outcomes": [f"{r[0]}: {r[3]}" for r in fired_rules],
        "_classical_rules_fired": fired_rules,
        "_resolution_method": "calibration_priority_order",
        "_calibration_version": CALIBRATION.get("calibration_version", "unknown"),
    }

    return results





# ═══════════════════════════════════════════════════════════════
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE (Medical)
# ═══════════════════════════════════════════════════════════════

class MedicalWindowResult:
    """Result of evaluating a single medical event time window."""

    def __init__(self):
        self.period_start = None
        self.period_end = None
        self.md_lord = ""
        self.ad_lord = ""
        self.age_start = 0.0
        self.age_end = 0.0

        # Layer results
        self.dasha_fired = []
        self.transit_fired = []
        self.fast_trigger_fired = []
        self.classical = {}
        self.outcome = {}

        # Composite
        self.total_score = 0
        self.timing_band = "broad"
        self.likelihood = "low"

    def compute_composite_score(self):
        """
        Compute total score from all layers.
        Weights and thresholds loaded from calibration overlay (Layer 3).
        Classical rules provide detection; calibration provides scoring.
        """
        dasha_score = sum(s for _, s, _ in self.dasha_fired)
        transit_score = sum(s for _, s, _ in self.transit_fired)
        fast_score = sum(s for _, s, _ in self.fast_trigger_fired)
        classical_boost = self.classical.get("confidence_boost", 0)

        # Layer weights from calibration (NOT hardcoded)
        lw = CALIBRATION["layer_weights"]
        self.total_score = (
            dasha_score * lw["dasha_weight"] +
            transit_score * lw["transit_weight"] +
            fast_score * lw["fast_trigger_weight"] +
            classical_boost * lw["classical_weight"]
        )

        # Determine timing band
        if fast_score > 20:
            self.timing_band = "exact"
        elif transit_score > 25:
            self.timing_band = "narrow"
        elif dasha_score > 20:
            self.timing_band = "broad"

        # Likelihood thresholds from calibration (NOT hardcoded)
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





def scan_medical_windows(chart: ChartState, start_age=1, end_age=70, step_months=6):
    """
    Scan through life from start_age to end_age in step_months increments.
    Medical events can happen any time in life, so range: age 1-70.
    For each AD period in that range, evaluate the 5-layer engine.
    Returns sorted list of MedicalWindowResult.
    """
    results = []

    # Generate MD periods for the relevant age range
    md_periods = _generate_md_periods(chart.birth_dt, chart.moon_lon, years=80)

    # Classical patterns (structural, computed once)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    for md in md_periods:
        md_age_start = (md["start"] - chart.birth_dt).days / 365.25
        md_age_end = (md["end"] - chart.birth_dt).days / 365.25

        # Skip MDs entirely outside our age range
        if md_age_end < start_age or md_age_start > end_age:
            continue

        # Generate AD periods within this MD
        ad_periods = _generate_ad_periods(md)

        for ad in ad_periods:
            ad_age_start = (ad["start"] - chart.birth_dt).days / 365.25
            ad_age_end = (ad["end"] - chart.birth_dt).days / 365.25

            # Skip ADs outside our age range
            if ad_age_end < start_age or ad_age_start > end_age:
                continue

            # Effective window (clipped to age range)
            effective_start = max(ad["start"], chart.birth_dt + timedelta(days=start_age * 365.25))
            effective_end = min(ad["end"], chart.birth_dt + timedelta(days=end_age * 365.25))

            # LAYER 1: DASHA
            dasha_results = evaluate_dasha_layer(chart, md["lord"], ad["lord"])

            # If NO dasha rule fires, skip (gate)
            if not dasha_results:
                continue

            # LAYER 2: TRANSIT (evaluate at midpoint of AD period)
            mid_date = effective_start + (effective_end - effective_start) / 2
            transit = TransitState(mid_date, chart)
            transit_results = evaluate_transit_layer(chart, transit)

            # LAYER 3: FAST TRIGGER (same midpoint)
            fast_trigger_results = evaluate_fast_trigger_layer(chart, transit)



            # Also check transit at start and end of period
            transit_start = TransitState(effective_start, chart)
            transit_end = TransitState(effective_end, chart)

            transit_results_start = evaluate_transit_layer(chart, transit_start)
            transit_results_end = evaluate_transit_layer(chart, transit_end)

            # Merge transit results (take best from any point)
            all_transit = {}
            for tr_list in [transit_results, transit_results_start, transit_results_end]:
                for rule_id, score, reasons in tr_list:
                    if rule_id not in all_transit or score > all_transit[rule_id][1]:
                        all_transit[rule_id] = (rule_id, score, reasons)
            merged_transit = list(all_transit.values())

            all_fast = {}
            ft_start = evaluate_fast_trigger_layer(chart, transit_start)
            ft_end = evaluate_fast_trigger_layer(chart, transit_end)
            for ft_list in [fast_trigger_results, ft_start, ft_end]:
                for rule_id, score, reasons in ft_list:
                    if rule_id not in all_fast or score > all_fast[rule_id][1]:
                        all_fast[rule_id] = (rule_id, score, reasons)
            merged_fast = list(all_fast.values())

            # Build result
            result = MedicalWindowResult()
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

    # Sort by total score descending
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
    print("  5-LAYER MEDICAL RULE ENGINE — VEDIC TEXT BASED")
    print("  Native: 22 July 1975, 18:15 IST, Bhilai")
    print("=" * 80)

    # Build chart state
    chart = ChartState(BIRTH_DATE, BHILAI_LAT, BHILAI_LON, BHILAI_ALT)

    print(f"\n{'─' * 80}")
    print("  NATAL CHART SUMMARY (Medical Focus)")
    print(f"{'─' * 80}")
    print(f"  Lagna: {SIGN_NAMES[chart.asc_sign]} | Lagna Lord: {chart.lagna_lord}")
    print(f"  Moon: {SIGN_NAMES[chart.moon_sign]} ({chart.moon_nakshatra})")
    print(f"  6th Lord: {chart.sixth_lord} (in house {chart.planets[chart.sixth_lord]['house']}, sign {SIGN_NAMES[chart.planets[chart.sixth_lord]['sign']]})")
    print(f"  8th Lord: {chart.eighth_lord} (in house {chart.planets[chart.eighth_lord]['house']})")
    print(f"  12th Lord: {chart.twelfth_lord} (in house {chart.planets[chart.twelfth_lord]['house']})")
    print(f"  2nd Lord (Maraka): {chart.second_lord} (in house {chart.planets[chart.second_lord]['house']})")
    print(f"  7th Lord (Maraka): {chart.seventh_lord} (in house {chart.planets[chart.seventh_lord]['house']})")
    print(f"  Mars: house {chart.planets['Mars']['house']}, sign {SIGN_NAMES[chart.planets['Mars']['sign']]}")
    print(f"  Saturn: house {chart.planets['Saturn']['house']}, sign {SIGN_NAMES[chart.planets['Saturn']['sign']]}")
    print(f"  Rahu: house {chart.planets['Rahu']['house']}, sign {SIGN_NAMES[chart.planets['Rahu']['sign']]}")
    print(f"  Ketu: house {chart.planets['Ketu']['house']}, sign {SIGN_NAMES[chart.planets['Ketu']['sign']]}")
    print(f"  Sun: house {chart.planets['Sun']['house']}, sign {SIGN_NAMES[chart.planets['Sun']['sign']]}")
    print(f"  Jupiter: house {chart.planets['Jupiter']['house']}, sign {SIGN_NAMES[chart.planets['Jupiter']['sign']]}")
    print(f"  Venus: house {chart.planets['Venus']['house']}, sign {SIGN_NAMES[chart.planets['Venus']['sign']]}")
    print(f"  Atmakaraka: {chart.atmakaraka} | Karakamsa: {SIGN_NAMES[chart.karakamsa_sign]}")
    print(f"  Sensitive Point 1 (6L+8L): {chart.sensitive_point_1:.2f}deg")
    print(f"  Sensitive Point 2 (Mars+Saturn): {chart.sensitive_point_2:.2f}deg")
    print(f"  Lagna Sphuta: {chart.lagna_sphuta:.2f}deg")



    # Layer 4 & 5 (structural)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    print(f"\n{'─' * 80}")
    print("  LAYER 4: CLASSICAL PATTERNS (Structural — Medical)")
    print(f"{'─' * 80}")
    print(f"  Timing Modifier: {classical['timing_modifier'].upper()}")
    print(f"  Confidence Boost: +{classical['confidence_boost']}")
    for p in classical["fired_patterns"]:
        print(f"    * {p}")
    if not classical["fired_patterns"]:
        print("    (No classical medical patterns detected)")

    print(f"\n{'─' * 80}")
    print("  LAYER 5: OUTCOME / QUALITY (Medical Classification)")
    print(f"{'─' * 80}")
    print(f"  Medical Mode: {outcome['mode']}")
    print(f"  Medical Quality: {outcome['quality']}")
    print(f"  Body System: {outcome['body_system']}")
    for o in outcome["fired_outcomes"]:
        print(f"    * {o}")

    # Scan medical windows
    print(f"\n{'─' * 80}")
    print("  SCANNING MEDICAL WINDOWS (Age 1-70, step=6mo)...")
    print(f"{'─' * 80}")

    windows = scan_medical_windows(chart, start_age=1, end_age=70, step_months=6)

    print(f"\n  Found {len(windows)} windows where dasha rules fired.")
    print(f"  Showing top 15 ranked by composite 5-layer score:\n")

    print(f"  {'#':<3} {'Period':<28} {'Age':<10} {'Score':<7} {'Band':<8} {'Likelihood':<12} {'MD-AD':<18}")
    print(f"  {'---':<3} {'---':<28} {'---':<10} {'---':<7} {'---':<8} {'---':<12} {'---':<18}")

    for i, w in enumerate(windows[:15], 1):
        period = f"{w.period_start.strftime('%b %Y')} - {w.period_end.strftime('%b %Y')}"
        age = f"{w.age_start:.1f}-{w.age_end:.1f}"
        md_ad = f"{w.md_lord}-{w.ad_lord}"
        print(f"  {i:<3} {period:<28} {age:<10} {w.total_score:<7.1f} {w.timing_band:<8} {w.likelihood:<12} {md_ad:<18}")



    # Detailed top 5
    print(f"\n{'=' * 80}")
    print("  TOP 5 MEDICAL WINDOWS — DETAILED 5-LAYER BREAKDOWN")
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
        print(f"\n  STRONGEST MEDICAL WINDOW:")
        print(f"  {top.period_start.strftime('%B %Y')} - {top.period_end.strftime('%B %Y')}")
        print(f"  Age {top.age_start:.1f}-{top.age_end:.1f} | {top.md_lord}-{top.ad_lord}")
        print(f"  Score: {top.total_score:.1f} | {top.likelihood}")
        print(f"\n  Medical Mode: {outcome['mode']}")
        print(f"  Medical Quality: {outcome['quality']}")
        print(f"  Body System: {outcome['body_system']}")
        print(f"\n  The 5-layer engine evaluated {len(windows)} AD periods with")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['high'])} HIGH+ confidence windows.")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['very_high'])} VERY_HIGH confidence windows.")
    print(f"\n{'=' * 80}")
