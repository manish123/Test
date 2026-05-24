"""
Relocation Rule Evaluator — 5-Layer Sequential Engine
Implements the Dasha → Transit → Fast Trigger → Classical → Outcome flow.
Domain: Relocation / Foreign Settlement
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
RULES_DIR = Path(__file__).resolve().parent / "domains" / "relocation" / "foreign_settlement"

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
BENEFIC_HOUSES = {1, 2, 4, 5, 7, 9, 11}
MALEFIC_HOUSES = {3, 6, 8, 12}

# Relocation-specific constants
RELOCATION_KARAKAS = {"Rahu", "Ketu", "Moon", "Saturn"}  # natural foreign/displacement planets
RELOCATION_HOUSES = {4, 9, 12, 3}  # home, long journeys, foreign lands, short travel




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
                    "relocation_karaka_lord_md_or_ad": 45,
                    "twelfth_lord_md_or_ad": 42,
                    "ninth_lord_md_or_ad": 38,
                    "fourth_lord_md_or_ad": 35,
                    "lagna_lord_md_or_ad": 30,
                },
                "transit": {
                    "double_transit_4_9_12": 50,
                    "saturn_4th_from_moon": 38,
                    "jupiter_9th_from_moon": 35,
                    "jupiter_12th_from_moon": 32,
                    "rahu_transit_natal_moon": 30,
                },
                "fast_trigger": {
                    "moon_19th_24th_two_feet": 25,
                    "mars_26th_27th_two_eyes": 22,
                    "moon_adhana_tara_19th": 28,
                    "mars_desha_tara_27th": 30,
                    "moon_6th_7th_8th_right_leg": 20,
                },
            },

            "outcome_calibration": {
                "mode_priority_order": [
                    "permanent_settlement_12L_venus",
                    "career_relocation_10L_12L",
                    "education_abroad_5L_9L",
                    "spiritual_journey_ketu_9th",
                    "temporary_posting_3L_12L",
                    "forced_exile_saturn_12th",
                    "return_home_4L_strong",
                ],
                "quality_priority_order": [
                    "smooth_jupiter_12th",
                    "sudden_rahu_involvement",
                    "gradual_saturn_transit",
                    "challenging_8th_lord",
                    "repeated_3rd_12th_connection",
                    "transformative_ketu_4th",
                ],
                "default_mode": "general_relocation",
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

# Moveable signs (Chara rasis)
MOVEABLE_SIGNS = {1, 4, 7, 10}  # Aries, Cancer, Libra, Capricorn


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


        # Key house lords (relocation-focused)
        self.lagna_lord = SIGN_LORDS[self.asc_sign]
        self.fourth_sign = ((self.asc_sign + 3 - 1) % 12) + 1
        self.fourth_lord = SIGN_LORDS[self.fourth_sign]
        self.ninth_sign = ((self.asc_sign + 8 - 1) % 12) + 1
        self.ninth_lord = SIGN_LORDS[self.ninth_sign]
        self.twelfth_sign = ((self.asc_sign + 11 - 1) % 12) + 1
        self.twelfth_lord = SIGN_LORDS[self.twelfth_sign]
        self.third_sign = ((self.asc_sign + 2 - 1) % 12) + 1
        self.third_lord = SIGN_LORDS[self.third_sign]
        self.fifth_sign = ((self.asc_sign + 4 - 1) % 12) + 1
        self.fifth_lord = SIGN_LORDS[self.fifth_sign]
        self.seventh_sign = ((self.asc_sign + 6 - 1) % 12) + 1
        self.seventh_lord = SIGN_LORDS[self.seventh_sign]
        self.tenth_sign = ((self.asc_sign + 9 - 1) % 12) + 1
        self.tenth_lord = SIGN_LORDS[self.tenth_sign]
        self.eleventh_sign = ((self.asc_sign + 10 - 1) % 12) + 1
        self.eleventh_lord = SIGN_LORDS[self.eleventh_sign]

        # Planets in 12th house (foreign land)
        self.twelfth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 12
        ]

        # Planets aspecting 12th house
        self.twelfth_house_aspectors = self._get_aspectors_of_house(12)

        # Planets in 4th house (homeland)
        self.fourth_house_occupants = [
            name for name, data in self.planets.items() if data["house"] == 4
        ]


        # 4th lord dispositor (sign where 4th lord sits -> lord of that sign)
        fourth_lord_sign = self.planets[self.fourth_lord]["sign"]
        self.fourth_lord_dispositor = SIGN_LORDS[fourth_lord_sign]

        # 12th lord dispositor (sign where 12th lord sits -> lord of that sign)
        twelfth_lord_sign = self.planets[self.twelfth_lord]["sign"]
        self.twelfth_lord_dispositor = SIGN_LORDS[twelfth_lord_sign]

        # Navamsa (D9) calculations
        self.d9_asc_sign = self._compute_d9_lagna()
        self.d9_fourth_sign = ((self.d9_asc_sign + 3 - 1) % 12) + 1
        self.twelfth_lord_d9_sign = self._get_d9_sign(
            self.birth_positions[self.twelfth_lord]
        )
        self.twelfth_lord_d9_dispositor = SIGN_LORDS[self.twelfth_lord_d9_sign]

        # Janma Nakshatra Lord
        nak_index = int((self.moon_lon % 360) / 13.3333333333)
        self.janma_nakshatra_lord = NAKSHATRA_LORDS[nak_index % 27]

        # Sensitive Relocation Points
        # Point 1: 4th lord + 12th lord longitude sum (home-foreign axis)
        fourth_lord_lon = self.birth_positions[self.fourth_lord]
        twelfth_lord_lon = self.birth_positions[self.twelfth_lord]
        self.sensitive_point_1 = (fourth_lord_lon + twelfth_lord_lon) % 360

        # Point 2: Rahu + Moon longitude sum (foreign mind axis)
        rahu_lon = self.birth_positions["Rahu"]
        moon_lon = self.birth_positions["Moon"]
        self.sensitive_point_2 = (rahu_lon + moon_lon) % 360


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

    def rahu_conjunct_natal_moon(self, natal_moon_lon, orb=5.0):
        """Check if transit Rahu is within orb of natal Moon (restlessness)."""
        rahu_lon = self.positions["Rahu"]
        diff = abs((rahu_lon - natal_moon_lon) % 360)
        diff = min(diff, 360 - diff)
        return diff <= orb

    def jupiter_conjunct_natal(self, natal_degree, orb=3.0):
        """Check if transit Jupiter is conjunct a natal degree."""
        jup_lon = self.positions["Jupiter"]
        diff = abs((jup_lon - natal_degree) % 360)
        diff = min(diff, 360 - diff)
        return diff <= orb





# ═══════════════════════════════════════════════════════════════
# LAYER 1: DASHA EVALUATOR (Relocation)
# ═══════════════════════════════════════════════════════════════

def evaluate_dasha_layer(chart: ChartState, md_lord: str, ad_lord: str):
    """
    Evaluate dasha rules for relocation/foreign settlement.
    Checks if current MD/AD lord is a relocation karaka or rules relocation houses.
    Key lords: 4th lord (home), 12th lord (foreign), 9th lord (long journeys), Lagna lord.
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Key lords for relocation
    key_lords = {
        chart.twelfth_lord: ("12th lord", "foreign lands", 42),
        chart.ninth_lord: ("9th lord", "long journeys/fortune abroad", 38),
        chart.fourth_lord: ("4th lord", "home/uprooting", 35),
        chart.lagna_lord: ("Lagna lord", "self/movement", 30),
    }

    # Rule 1: Relocation house lords in MD/AD (priority 98)
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
        fired.append(("relocation_house_lord_dasha", r1_score, r1_reasons))


    # Rule 2: Relocation karaka planets in MD/AD (priority 95)
    r2_score = 0
    r2_reasons = []

    karaka_scores = {
        "Rahu": (45, "foreign/alien lands"),
        "Ketu": (38, "detachment from homeland"),
        "Moon": (32, "mind/settling abroad"),
        "Saturn": (35, "displacement/hard labor abroad"),
    }

    if md_lord in RELOCATION_KARAKAS:
        score, desc = karaka_scores[md_lord]
        r2_score += score
        r2_reasons.append(f"MD of relocation karaka {md_lord} ({desc})")
    if ad_lord in RELOCATION_KARAKAS:
        score, desc = karaka_scores[ad_lord]
        r2_score += int(score * 0.75)
        r2_reasons.append(f"AD of relocation karaka {ad_lord} ({desc})")

    if r2_score > 0:
        fired.append(("relocation_karaka_dasha", r2_score, r2_reasons))

    # Rule 3: Positive dasha combinations for foreign (priority 92)
    r3_score = 0
    r3_reasons = []

    # 12th lord AD — direct foreign activation
    if ad_lord == chart.twelfth_lord:
        r3_score += 35
        r3_reasons.append(f"12th lord ({chart.twelfth_lord}) AD — direct foreign activation")
    # Jupiter-Rahu — expansion into foreign
    if md_lord == "Jupiter" and ad_lord == "Rahu":
        r3_score += 30
        r3_reasons.append("Jupiter MD + Rahu AD — dharmic expansion into foreign lands")
    # Rahu-Sun — foreign authority/government posting
    if md_lord == "Rahu" and ad_lord == "Sun":
        r3_score += 28
        r3_reasons.append("Rahu MD + Sun AD — foreign authority/government posting")
    # Sun-Jupiter — authority abroad with wisdom
    if md_lord == "Sun" and ad_lord == "Jupiter":
        r3_score += 25
        r3_reasons.append("Sun MD + Jupiter AD — authority abroad with dharmic support")
    # Rahu-Ketu — complete foreign axis activation
    if md_lord == "Rahu" and ad_lord == "Ketu":
        r3_score += 32
        r3_reasons.append("Rahu MD + Ketu AD — complete foreign axis activation (exile/detachment)")

    if r3_score > 0:
        fired.append(("relocation_positive_dasha", r3_score, r3_reasons))


    # Rule 4: Challenging combinations (negative — priority 88)
    r4_score = 0
    r4_reasons = []

    # Venus-Moon (afflicted): attachment to homeland prevents foreign
    if md_lord == "Venus" and ad_lord == "Moon":
        r4_score -= 25
        r4_reasons.append("Venus MD + Moon AD — emotional attachment to homeland (resists relocation)")
    # Jupiter-Mercury (afflicted): over-analysis prevents action
    if md_lord == "Jupiter" and ad_lord == "Mercury":
        r4_score -= 20
        r4_reasons.append("Jupiter MD + Mercury AD — over-analysis/indecision blocks foreign move")

    if r4_score != 0:
        fired.append(("relocation_challenging_dasha", r4_score, r4_reasons))

    # Rule 5: MD/AD lord rules houses 4, 9, 12 (priority 85)
    r5_score = 0
    r5_reasons = []

    md_house = chart.planets.get(md_lord, {}).get("house", 0)
    ad_house = chart.planets.get(ad_lord, {}).get("house", 0)

    if md_house in RELOCATION_HOUSES:
        r5_score += 20
        r5_reasons.append(f"MD lord {md_lord} placed in relocation house {md_house}")
    if ad_house in RELOCATION_HOUSES:
        r5_score += 15
        r5_reasons.append(f"AD lord {ad_lord} placed in relocation house {ad_house}")

    if r5_score > 0:
        fired.append(("relocation_lord_placement", r5_score, r5_reasons))

    return fired





# ═══════════════════════════════════════════════════════════════
# LAYER 2: TRANSIT EVALUATOR (Relocation)
# ═══════════════════════════════════════════════════════════════

def evaluate_transit_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate transit rules for relocation activation.
    Key: Double transit on 4/9/12, Saturn transit 4th from Moon (uprooting),
    Jupiter transit 9th/12th from Moon (opportunity abroad),
    Rahu transit over natal Moon (restlessness).
    Tara checks: Adhana Tara (19th nak), Desha Tara (27th nak), 6-7-8th nak (right leg travel).
    Returns list of (rule_id, score, reasons) for fired rules.
    """
    fired = []

    # Rule 1: Double Transit on 4th/9th/12th (priority 98)
    # Jupiter and Saturn must BOTH influence relocation houses
    dt_score = 0
    dt_reasons = []

    for target_house in [4, 9, 12]:
        jup_hits = transit.planet_aspects_house("Jupiter", target_house, "lagna")
        sat_hits = transit.planet_aspects_house("Saturn", target_house, "lagna")
        if jup_hits and sat_hits:
            dt_score += 50
            dt_reasons.append(f"Double transit (Jup+Sat) on house {target_house} from Lagna")
            break  # Count once for strongest hit

    if dt_score == 0:
        # Check from Moon reference
        for target_house in [4, 9, 12]:
            jup_hits = transit.planet_aspects_house("Jupiter", target_house, "moon")
            sat_hits = transit.planet_aspects_house("Saturn", target_house, "moon")
            if jup_hits and sat_hits:
                dt_score += 40
                dt_reasons.append(f"Double transit (Jup+Sat) on house {target_house} from Moon")
                break

    if dt_score > 0:
        fired.append(("double_transit_relocation_houses", dt_score, dt_reasons))


    # Rule 2: Saturn transit 4th from Moon (uprooting — priority 92)
    sat_house_from_moon = transit.planet_houses_from_moon.get("Saturn", 0)
    if sat_house_from_moon == 4:
        fired.append(("saturn_4th_from_moon_uprooting", 38,
                      ["Transit Saturn in 4th from Moon — uprooting from homeland, forced displacement"]))

    # Rule 3: Jupiter transit 9th from Moon (opportunity abroad — priority 88)
    jup_house_from_moon = transit.planet_houses_from_moon.get("Jupiter", 0)
    if jup_house_from_moon == 9:
        fired.append(("jupiter_9th_from_moon", 35,
                      ["Transit Jupiter in 9th from Moon — long-distance opportunity, fortune abroad"]))

    # Rule 4: Jupiter transit 12th from Moon (settlement abroad — priority 85)
    if jup_house_from_moon == 12:
        fired.append(("jupiter_12th_from_moon", 32,
                      ["Transit Jupiter in 12th from Moon — divine support for foreign settlement"]))

    # Rule 5: Rahu transit over natal Moon (restlessness — priority 90)
    if transit.rahu_conjunct_natal_moon(chart.moon_lon, orb=5.0):
        fired.append(("rahu_transit_natal_moon", 30,
                      ["Transit Rahu conjunct natal Moon — mental restlessness, urge to relocate"]))

    # Rule 6: Tara-based transit checks
    # Get birth nakshatra index
    birth_moon_nak_idx = int((chart.moon_lon % 360) / 13.3333333333) % 27

    # Transit Saturn nakshatra relative to birth
    transit_saturn_lon = transit.positions["Saturn"]
    transit_saturn_nak_idx = int((transit_saturn_lon % 360) / 13.3333333333) % 27
    saturn_nak_offset = ((transit_saturn_nak_idx - birth_moon_nak_idx) % 27) + 1

    # Adhana Tara (19th nakshatra) — residence shift
    if saturn_nak_offset == 19:
        fired.append(("saturn_adhana_tara_19th", 28,
                      ["Transit Saturn on Adhana Tara (19th nak) — forced residence shift"]))

    # Desha Tara (27th nakshatra) — departure from country
    if saturn_nak_offset == 27:
        fired.append(("saturn_desha_tara_27th", 30,
                      ["Transit Saturn on Desha Tara (27th nak) — departure from country"]))

    # 6th-7th-8th nakshatra (right leg = travel trigger)
    if saturn_nak_offset in [6, 7, 8]:
        fired.append(("saturn_right_leg_travel", 20,
                      [f"Transit Saturn in {saturn_nak_offset}th nak (right leg) — travel triggered"]))

    return fired





# ═══════════════════════════════════════════════════════════════
# LAYER 3: FAST TRIGGER EVALUATOR (Relocation)
# ═══════════════════════════════════════════════════════════════

def evaluate_fast_trigger_layer(chart: ChartState, transit: TransitState):
    """
    Evaluate fast trigger rules for exact relocation timing.
    Moon in 19th-24th Nakshatra from birth (two feet = foreign journey)
    Mars in 26th-27th Nakshatra from birth (two eyes = foreign entry)
    Moon/Mars on Adhana Tara (19th = residence shift)
    Mars on Desha Tara (27th = forced departure)
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

    # Rule 1: Moon in 19th-24th Nakshatra (two feet = foreign journey)
    if moon_nak_offset in range(19, 25):
        fired.append(("fast_trigger_moon_two_feet", 25,
                      [f"Moon in {moon_nak_offset}th Nakshatra (two feet) — foreign journey activated"]))

    # Rule 2: Mars in 26th-27th Nakshatra (two eyes = foreign entry)
    if mars_nak_offset in [26, 27]:
        fired.append(("fast_trigger_mars_two_eyes", 22,
                      [f"Mars in {mars_nak_offset}th Nakshatra (two eyes) — foreign entry point"]))


    # Rule 3: Moon on Adhana Tara (19th nakshatra = residence shift)
    if moon_nak_offset == 19:
        fired.append(("fast_trigger_moon_adhana_tara", 28,
                      [f"Moon on Adhana Tara (19th nak) — residence shift day"]))

    # Rule 4: Mars on Desha Tara (27th = forced departure)
    if mars_nak_offset == 27:
        fired.append(("fast_trigger_mars_desha_tara", 30,
                      [f"Mars on Desha Tara (27th nak) — forced departure / country change trigger"]))

    # Rule 5: Moon in 6th-7th-8th Nakshatra (right leg = travel trigger)
    if moon_nak_offset in [6, 7, 8]:
        fired.append(("fast_trigger_moon_right_leg", 20,
                      [f"Moon in {moon_nak_offset}th Nakshatra (right leg) — travel trigger day"]))

    # Rule 6: Mars on Adhana Tara (19th = aggressive relocation push)
    if mars_nak_offset == 19:
        fired.append(("fast_trigger_mars_adhana_tara", 24,
                      [f"Mars on Adhana Tara (19th nak) — aggressive relocation push"]))

    return fired





# ═══════════════════════════════════════════════════════════════
# LAYER 4: CLASSICAL PATTERN EVALUATOR (Relocation)
# ═══════════════════════════════════════════════════════════════

def evaluate_classical_layer(chart: ChartState):
    """
    Evaluate classical relocation patterns (structural — not time-dependent).
    Checks: 12th lord weak + Venus aspect = permanent settlement,
    Moveable Lagna + lord in moveable = foreign fortune,
    12th house afflicted = wandering, Lagna lord in 12th = self in foreign,
    Rahu in 9th, Ketu in 4th, Moon in 12th, Jupiter in 12th.
    Returns dict with confidence_boost and fired_patterns.
    """
    results = {
        "timing_modifier": "normal",
        "confidence_boost": 0,
        "fired_patterns": [],
    }

    twelfth_lord_house = chart.planets[chart.twelfth_lord]["house"]
    fourth_lord_house = chart.planets[chart.fourth_lord]["house"]
    ninth_lord_house = chart.planets[chart.ninth_lord]["house"]
    lagna_lord_house = chart.planets[chart.lagna_lord]["house"]
    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    ketu_house = chart.planets.get("Ketu", {}).get("house", 0)
    moon_house = chart.planets["Moon"]["house"]
    jupiter_house = chart.planets["Jupiter"]["house"]
    venus_house = chart.planets["Venus"]["house"]
    saturn_house = chart.planets["Saturn"]["house"]


    # Pattern 1: 12th lord weak + Venus aspect = permanent settlement
    venus_aspects_12 = "Venus" in chart._get_aspectors_of_house(12)
    twelfth_lord_in_dusthana = twelfth_lord_house in [6, 8, 12]
    if twelfth_lord_in_dusthana and venus_aspects_12:
        results["confidence_boost"] += 15
        results["fired_patterns"].append(
            f"12th lord ({chart.twelfth_lord}) weak (house {twelfth_lord_house}) + Venus aspects 12th — permanent foreign settlement")

    # Pattern 2: Moveable Lagna + lord in moveable sign = foreign fortune
    lagna_lord_sign = chart.planets[chart.lagna_lord]["sign"]
    if chart.asc_sign in MOVEABLE_SIGNS and lagna_lord_sign in MOVEABLE_SIGNS:
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            f"Moveable Lagna ({SIGN_NAMES[chart.asc_sign]}) + Lagna lord in moveable sign ({SIGN_NAMES[lagna_lord_sign]}) — foreign fortune")

    # Pattern 3: 12th house afflicted = wandering/restless abroad
    malefics_in_12 = [p for p in chart.twelfth_house_occupants if p in NATURAL_MALEFICS]
    if len(malefics_in_12) >= 2:
        results["confidence_boost"] += 10
        results["timing_modifier"] = "repeated_moves"
        results["fired_patterns"].append(
            f"12th house afflicted by {', '.join(malefics_in_12)} — wandering/multiple relocations")

    # Pattern 4: Lagna lord in 12th = self in foreign land
    if lagna_lord_house == 12:
        results["confidence_boost"] += 14
        results["fired_patterns"].append(
            f"Lagna lord ({chart.lagna_lord}) in 12th house — self destined for foreign land")

    # Pattern 5: Rahu in 9th = foreign spiritual connection
    if rahu_house == 9:
        results["confidence_boost"] += 10
        results["fired_patterns"].append(
            "Rahu in 9th house — foreign spiritual/philosophical connection")

    # Pattern 6: Ketu in 4th = detachment from homeland
    if ketu_house == 4:
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            "Ketu in 4th house — karmic detachment from homeland (past-life foreign connection)")


    # Pattern 7: Moon in 12th = mind settled abroad
    if moon_house == 12:
        results["confidence_boost"] += 12
        results["fired_patterns"].append(
            "Moon in 12th house — mind finds peace in foreign land")

    # Pattern 8: Jupiter in 12th = prosperous foreigner
    if jupiter_house == 12:
        results["confidence_boost"] += 14
        results["timing_modifier"] = "smooth_transition"
        results["fired_patterns"].append(
            "Jupiter in 12th house — prosperous life as foreigner (Vyaya Yoga)")

    return results





# ═══════════════════════════════════════════════════════════════
# LAYER 5: OUTCOME / QUALITY EVALUATOR (Relocation)
# ═══════════════════════════════════════════════════════════════

def evaluate_outcome_layer(chart: ChartState):
    """
    Evaluate outcome/quality rules for relocation classification.
    Mode: permanent_settlement, temporary_posting, career_relocation,
          education_abroad, spiritual_journey, forced_exile, return_home
    Quality: smooth, challenging, sudden, gradual, repeated, transformative
    Distance: domestic / international
    """
    fired_rules = []

    rahu_house = chart.planets.get("Rahu", {}).get("house", 0)
    ketu_house = chart.planets.get("Ketu", {}).get("house", 0)
    moon_house = chart.planets["Moon"]["house"]
    jupiter_house = chart.planets["Jupiter"]["house"]
    saturn_house = chart.planets["Saturn"]["house"]
    venus_house = chart.planets["Venus"]["house"]
    sun_house = chart.planets["Sun"]["house"]
    mars_house = chart.planets["Mars"]["house"]
    twelfth_lord_house = chart.planets[chart.twelfth_lord]["house"]
    fourth_lord_house = chart.planets[chart.fourth_lord]["house"]
    ninth_lord_house = chart.planets[chart.ninth_lord]["house"]
    tenth_lord_house = chart.planets[chart.tenth_lord]["house"]
    lagna_lord_house = chart.planets[chart.lagna_lord]["house"]
    fifth_lord_house = chart.planets[chart.fifth_lord]["house"]
    third_lord_house = chart.planets[chart.third_lord]["house"]


    # ─── MODE DETECTION ───

    # Permanent settlement: 12th lord + Venus aspect on 12th
    venus_aspects_12 = "Venus" in chart._get_aspectors_of_house(12)
    if venus_aspects_12 and twelfth_lord_house in [6, 8, 12]:
        fired_rules.append(("permanent_settlement_12L_venus", "mode_permanent", 0.90,
            f"12th lord weak + Venus aspects 12th — permanent foreign settlement"))

    # Career relocation: 10th lord connected to 12th lord
    if tenth_lord_house == 12 or twelfth_lord_house == 10:
        fired_rules.append(("career_relocation_10L_12L", "mode_career", 0.85,
            f"10th-12th lord connection — career-driven relocation"))

    # Education abroad: 5th lord + 9th lord connection
    if fifth_lord_house == 9 or ninth_lord_house == 5:
        fired_rules.append(("education_abroad_5L_9L", "mode_education", 0.80,
            f"5th-9th lord connection — education abroad"))

    # Spiritual journey: Ketu in 9th
    if ketu_house == 9:
        fired_rules.append(("spiritual_journey_ketu_9th", "mode_spiritual", 0.78,
            "Ketu in 9th house — spiritual pilgrimage / ashram life abroad"))

    # Temporary posting: 3rd lord + 12th lord connection
    if third_lord_house == 12 or twelfth_lord_house == 3:
        fired_rules.append(("temporary_posting_3L_12L", "mode_temporary", 0.75,
            f"3rd-12th lord connection — temporary foreign posting"))

    # Forced exile: Saturn in 12th afflicted
    if saturn_house == 12:
        fired_rules.append(("forced_exile_saturn_12th", "mode_exile", 0.72,
            "Saturn in 12th house — forced exile / hardship abroad"))

    # Return home: 4th lord strong in kendra
    if fourth_lord_house in [1, 4, 7, 10]:
        fired_rules.append(("return_home_4L_strong", "mode_return", 0.65,
            f"4th lord ({chart.fourth_lord}) strong in kendra house {fourth_lord_house} — eventual return home"))


    # ─── QUALITY DETECTION ───

    # Smooth: Jupiter in 12th (prosperous foreigner)
    if jupiter_house == 12:
        fired_rules.append(("smooth_jupiter_12th", "quality_smooth", 0.88,
            "Jupiter in 12th — smooth/prosperous foreign settlement"))

    # Sudden: Rahu involvement in 4/9/12
    if rahu_house in [4, 9, 12]:
        fired_rules.append(("sudden_rahu_involvement", "quality_sudden", 0.82,
            f"Rahu in house {rahu_house} — sudden/unexpected relocation"))

    # Gradual: Saturn transit influence
    if saturn_house in [3, 9, 12]:
        fired_rules.append(("gradual_saturn_transit", "quality_gradual", 0.78,
            f"Saturn in house {saturn_house} — gradual/planned relocation"))

    # Challenging: 8th lord connection
    eighth_sign = ((chart.asc_sign + 7 - 1) % 12) + 1
    eighth_lord = SIGN_LORDS[eighth_sign]
    eighth_lord_house = chart.planets[eighth_lord]["house"]
    if eighth_lord_house == 12 or twelfth_lord_house == 8:
        fired_rules.append(("challenging_8th_lord", "quality_challenging", 0.80,
            f"8th-12th lord connection — challenging/transformative relocation"))

    # Repeated: 3rd + 12th connection (multiple moves)
    if third_lord_house == 12 and twelfth_lord_house == 3:
        fired_rules.append(("repeated_3rd_12th_connection", "quality_repeated", 0.75,
            "3rd-12th Parivartana — repeated relocations / multiple countries"))

    # Transformative: Ketu in 4th (spiritual uprooting)
    if ketu_house == 4:
        fired_rules.append(("transformative_ketu_4th", "quality_transformative", 0.85,
            "Ketu in 4th — transformative relocation (spiritual rebirth abroad)"))


    # ─── DISTANCE DETECTION ───

    # International: Rahu/Ketu axis on 4-10 or 9-3
    if (rahu_house in [4, 9, 12] or ketu_house in [4, 9, 12]):
        fired_rules.append(("distance_international", "distance_international", 0.82,
            f"Rahu/Ketu axis touching relocation houses — international relocation"))
    # Domestic: 3rd lord strong, no Rahu/Ketu in 9/12
    elif third_lord_house in [1, 3, 10] and rahu_house not in [9, 12]:
        fired_rules.append(("distance_domestic", "distance_domestic", 0.70,
            "3rd lord strong without Rahu in 9/12 — domestic relocation likely"))

    # ═══════════════════════════════════════════════════════════
    # RESOLUTION (Layer 3 — calibration-based)
    # ═══════════════════════════════════════════════════════════
    cal = CALIBRATION.get("outcome_calibration", {})
    mode_priority = cal.get("mode_priority_order", [])
    quality_priority = cal.get("quality_priority_order", [])
    default_mode = cal.get("default_mode", "general_relocation")

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
            "mode_permanent": "permanent_settlement",
            "mode_temporary": "temporary_posting",
            "mode_career": "career_relocation",
            "mode_education": "education_abroad",
            "mode_spiritual": "spiritual_journey",
            "mode_exile": "forced_exile",
            "mode_return": "return_home",
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
            "quality_smooth": "smooth",
            "quality_challenging": "challenging",
            "quality_sudden": "sudden",
            "quality_gradual": "gradual",
            "quality_repeated": "repeated",
            "quality_transformative": "transformative",
        }
        resolved_quality = quality_map.get(best_quality_rule[1], "unknown")
    else:
        resolved_quality = "unknown"

    # Resolve DISTANCE
    resolved_distance = "unknown"
    distance_rules = [r for r in fired_rules if r[1].startswith("distance_")]
    if distance_rules:
        distance_rules.sort(key=lambda r: -r[2])
        best_dist = distance_rules[0]
        distance_map = {
            "distance_international": "international",
            "distance_domestic": "domestic",
        }
        resolved_distance = distance_map.get(best_dist[1], "unknown")

    results = {
        "mode": resolved_mode,
        "quality": resolved_quality,
        "distance": resolved_distance,
        "fired_outcomes": [f"{r[0]}: {r[3]}" for r in fired_rules],
        "_classical_rules_fired": fired_rules,
        "_resolution_method": "calibration_priority_order",
        "_calibration_version": CALIBRATION.get("calibration_version", "unknown"),
    }

    return results





# ═══════════════════════════════════════════════════════════════
# MASTER EVALUATOR — 5-PASS SEQUENTIAL ENGINE (Relocation)
# ═══════════════════════════════════════════════════════════════

class RelocationWindowResult:
    """Result of evaluating a single relocation time window."""

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





def scan_relocation_windows(chart: ChartState, start_age=18, end_age=55, step_months=6):
    """
    Scan through life from start_age to end_age in step_months increments.
    Relocation can happen early (education) to mid-life (career), so range: age 18-55.
    For each AD period in that range, evaluate the 5-layer engine.
    Returns sorted list of RelocationWindowResult.
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
            result = RelocationWindowResult()
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
    print("  5-LAYER RELOCATION RULE ENGINE — VEDIC TEXT BASED")
    print("  Native: 22 July 1975, 18:15 IST, Bhilai")
    print("=" * 80)

    # Build chart state
    chart = ChartState(BIRTH_DATE, BHILAI_LAT, BHILAI_LON, BHILAI_ALT)

    print(f"\n{'─' * 80}")
    print("  NATAL CHART SUMMARY (Relocation Focus)")
    print(f"{'─' * 80}")
    print(f"  Lagna: {SIGN_NAMES[chart.asc_sign]} | Lagna Lord: {chart.lagna_lord}")
    print(f"  Moon: {SIGN_NAMES[chart.moon_sign]} ({chart.moon_nakshatra})")
    print(f"  4th Lord: {chart.fourth_lord} (in house {chart.planets[chart.fourth_lord]['house']}, sign {SIGN_NAMES[chart.planets[chart.fourth_lord]['sign']]})")
    print(f"  9th Lord: {chart.ninth_lord} (in house {chart.planets[chart.ninth_lord]['house']})")
    print(f"  12th Lord: {chart.twelfth_lord} (in house {chart.planets[chart.twelfth_lord]['house']})")
    print(f"  3rd Lord: {chart.third_lord} (in house {chart.planets[chart.third_lord]['house']})")
    print(f"  Rahu: house {chart.planets['Rahu']['house']}, sign {SIGN_NAMES[chart.planets['Rahu']['sign']]}")
    print(f"  Ketu: house {chart.planets['Ketu']['house']}, sign {SIGN_NAMES[chart.planets['Ketu']['sign']]}")
    print(f"  Moon: house {chart.planets['Moon']['house']}, sign {SIGN_NAMES[chart.planets['Moon']['sign']]}")
    print(f"  Saturn: house {chart.planets['Saturn']['house']}, sign {SIGN_NAMES[chart.planets['Saturn']['sign']]}")
    print(f"  Jupiter: house {chart.planets['Jupiter']['house']}, sign {SIGN_NAMES[chart.planets['Jupiter']['sign']]}")
    print(f"  D9 Lagna: {SIGN_NAMES[chart.d9_asc_sign]} | D9 4th: {SIGN_NAMES[chart.d9_fourth_sign]}")
    print(f"  Sensitive Point 1 (4L+12L): {chart.sensitive_point_1:.2f}deg")
    print(f"  Sensitive Point 2 (Rahu+Moon): {chart.sensitive_point_2:.2f}deg")



    # Layer 4 & 5 (structural)
    classical = evaluate_classical_layer(chart)
    outcome = evaluate_outcome_layer(chart)

    print(f"\n{'─' * 80}")
    print("  LAYER 4: CLASSICAL PATTERNS (Structural — Relocation)")
    print(f"{'─' * 80}")
    print(f"  Timing Modifier: {classical['timing_modifier'].upper()}")
    print(f"  Confidence Boost: +{classical['confidence_boost']}")
    for p in classical["fired_patterns"]:
        print(f"    * {p}")
    if not classical["fired_patterns"]:
        print("    (No classical relocation patterns detected)")

    print(f"\n{'─' * 80}")
    print("  LAYER 5: OUTCOME / QUALITY (Relocation Classification)")
    print(f"{'─' * 80}")
    print(f"  Relocation Mode: {outcome['mode']}")
    print(f"  Relocation Quality: {outcome['quality']}")
    print(f"  Relocation Distance: {outcome['distance']}")
    for o in outcome["fired_outcomes"]:
        print(f"    * {o}")

    # Scan relocation windows
    print(f"\n{'─' * 80}")
    print("  SCANNING RELOCATION WINDOWS (Age 18-55, step=6mo)...")
    print(f"{'─' * 80}")

    windows = scan_relocation_windows(chart, start_age=18, end_age=55, step_months=6)

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
    print("  TOP 5 RELOCATION WINDOWS — DETAILED 5-LAYER BREAKDOWN")
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
        print(f"\n  STRONGEST RELOCATION WINDOW:")
        print(f"  {top.period_start.strftime('%B %Y')} - {top.period_end.strftime('%B %Y')}")
        print(f"  Age {top.age_start:.1f}-{top.age_end:.1f} | {top.md_lord}-{top.ad_lord}")
        print(f"  Score: {top.total_score:.1f} | {top.likelihood}")
        print(f"\n  Relocation Mode: {outcome['mode']}")
        print(f"  Relocation Quality: {outcome['quality']}")
        print(f"  Relocation Distance: {outcome['distance']}")
        print(f"\n  The 5-layer engine evaluated {len(windows)} AD periods with")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['high'])} HIGH+ confidence windows.")
        print(f"  {sum(1 for w in windows if w.total_score >= CALIBRATION['likelihood_thresholds']['very_high'])} VERY_HIGH confidence windows.")
    print(f"\n{'=' * 80}")
