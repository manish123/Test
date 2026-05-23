"""
Marriage Window Analysis for native born 22 July 1975, 18:15 IST, Bhilai
Uses the astro_engine to compute birth chart, dasha timeline, and marriage windows.
"""

import sys
sys.path.insert(0, '/projects/sandbox/Test/astro_engine')

import swisseph as swe
from datetime import datetime, timedelta
from astronomy.engine_base import get_planet_positions, get_house_cusps, configure_ephemeris
from astronomy.utils import normalize_lon
from features.dasha import (
    get_current_vimshottari, _generate_md_periods, _generate_ad_periods,
    _starting_lord_from_moon, DASHA_SEQUENCE, DASHA_YEARS
)
from features.dignity import SIGN_LORDS, get_sign
from features.nakshatra import get_nakshatra

# ═══════════════════════════════════════════════════════════════════
# BIRTH DATA
# ═══════════════════════════════════════════════════════════════════
BIRTH_DATE = datetime(1975, 7, 22, 18, 15)  # IST
BHILAI_LAT = 21.2094
BHILAI_LON = 81.4285
BHILAI_ALT = 297  # meters

IST_OFFSET = timedelta(hours=5, minutes=30)

def ist_to_utc(dt):
    return dt - IST_OFFSET

def get_jd(dt_ist):
    dt_utc = ist_to_utc(dt_ist)
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute / 60.0)

# ═══════════════════════════════════════════════════════════════════
# STEP 1: BIRTH CHART CALCULATION
# ═══════════════════════════════════════════════════════════════════
print("=" * 70)
print("BIRTH CHART: 22 July 1975, 18:15 IST, Bhilai (21.21°N, 81.43°E)")
print("=" * 70)

configure_ephemeris()
location = {"latitude": BHILAI_LAT, "longitude": BHILAI_LON, "altitude": BHILAI_ALT}

birth_jd = get_jd(BIRTH_DATE)
birth_positions = get_planet_positions(birth_jd, location)
house_data = get_house_cusps(birth_jd, BHILAI_LAT, BHILAI_LON)

asc_lon = house_data["ascendant"]
asc_sign = int(normalize_lon(asc_lon) // 30) + 1

SIGN_NAMES = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
    5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
    9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
}

print(f"\nAscendant (Lagna): {SIGN_NAMES[asc_sign]} ({asc_lon:.2f}°)")
print(f"\nPlanetary Positions (Sidereal - Lahiri):")
print(f"{'Planet':<12} {'Longitude':>10} {'Sign':<14} {'House':>6} {'Nakshatra':<20}")
print("-" * 65)

planet_data = {}
for name, lon in birth_positions.items():
    sign = get_sign(lon)
    house = int((((sign - asc_sign) % 12) + 1))
    nak = get_nakshatra(lon)
    planet_data[name] = {"lon": lon, "sign": sign, "house": house, "nakshatra": nak}
    print(f"{name:<12} {lon:>10.2f} {SIGN_NAMES[sign]:<14} {house:>6} {nak:<20}")

# ═══════════════════════════════════════════════════════════════════
# STEP 2: MARRIAGE SIGNIFICATORS
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("MARRIAGE SIGNIFICATORS")
print("=" * 70)

seventh_sign = ((asc_sign + 6 - 1) % 12) + 1
seventh_lord = SIGN_LORDS[seventh_sign]
second_sign = ((asc_sign + 1 - 1) % 12) + 1
second_lord = SIGN_LORDS[second_sign]
eleventh_sign = ((asc_sign + 10 - 1) % 12) + 1
eleventh_lord = SIGN_LORDS[eleventh_sign]

# Navamsa lagna (D9) - simplified calculation
moon_lon = birth_positions["Moon"]
natal_moon_sign = get_sign(moon_lon)

print(f"\nLagna Sign: {SIGN_NAMES[asc_sign]} (Lord: {SIGN_LORDS[asc_sign]})")
print(f"7th House Sign: {SIGN_NAMES[seventh_sign]} (Lord: {seventh_lord})")
print(f"2nd House Sign: {SIGN_NAMES[second_sign]} (Lord: {second_lord})")
print(f"11th House Sign: {SIGN_NAMES[eleventh_sign]} (Lord: {eleventh_lord})")
print(f"Moon Sign: {SIGN_NAMES[natal_moon_sign]} (Natal Moon)")
print(f"Venus position: {SIGN_NAMES[planet_data['Venus']['sign']]} in house {planet_data['Venus']['house']}")
print(f"Jupiter position: {SIGN_NAMES[planet_data['Jupiter']['sign']]} in house {planet_data['Jupiter']['house']}")

# Key marriage planets
marriage_planets = {seventh_lord, "Venus", "Jupiter", second_lord}
print(f"\nKey Marriage Significators: {', '.join(sorted(marriage_planets))}")

# ═══════════════════════════════════════════════════════════════════
# STEP 3: VIMSHOTTARI DASHA TIMELINE (Birth to Age 40)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("VIMSHOTTARI DASHA TIMELINE (Birth to Age 40)")
print("=" * 70)

md_periods = _generate_md_periods(BIRTH_DATE, moon_lon, years=60)

print(f"\nMahadasha Sequence:")
print(f"{'MD Lord':<12} {'Start':<14} {'End':<14} {'Age Start':>10} {'Age End':>8}")
print("-" * 60)

relevant_mds = []
for md in md_periods:
    if md["end"] < BIRTH_DATE:
        continue
    age_start = (md["start"] - BIRTH_DATE).days / 365.25
    age_end = (md["end"] - BIRTH_DATE).days / 365.25
    if age_start > 45:
        break
    relevant_mds.append(md)
    print(f"{md['lord']:<12} {md['start'].strftime('%Y-%m-%d'):<14} {md['end'].strftime('%Y-%m-%d'):<14} {age_start:>10.1f} {age_end:>8.1f}")

# ═══════════════════════════════════════════════════════════════════
# STEP 4: MARRIAGE WINDOW ANALYSIS (Dasha-based)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("MARRIAGE WINDOWS (Dasha-Based Analysis)")
print("=" * 70)

# Marriage is most likely during:
# 1. MD of 7th lord
# 2. MD of Venus (natural karaka of marriage)
# 3. MD of 2nd lord (family formation)
# 4. AD of 7th lord within any supportive MD
# 5. AD of Venus within any supportive MD
# 6. Jupiter/Venus AD in any MD (natural benefics for marriage)

marriage_windows = []

for md in relevant_mds:
    age_at_md_start = (md["start"] - BIRTH_DATE).days / 365.25
    age_at_md_end = (md["end"] - BIRTH_DATE).days / 365.25
    
    # Skip if person is too young (< 18) or too old for first marriage (> 38)
    if age_at_md_end < 18 or age_at_md_start > 38:
        continue
    
    ad_periods = _generate_ad_periods(md)
    
    for ad in ad_periods:
        age_at_ad_start = (ad["start"] - BIRTH_DATE).days / 365.25
        age_at_ad_end = (ad["end"] - BIRTH_DATE).days / 365.25
        
        # Only consider marriage-age windows (18-35 for first marriage)
        if age_at_ad_end < 18 or age_at_ad_start > 35:
            continue
        
        # Score this MD-AD combination for marriage
        score = 0
        reasons = []
        
        # MD scoring
        if md["lord"] == seventh_lord:
            score += 45
            reasons.append(f"MD of 7th lord ({seventh_lord})")
        elif md["lord"] == "Venus":
            score += 40
            reasons.append("MD of Venus (marriage karaka)")
        elif md["lord"] == second_lord:
            score += 25
            reasons.append(f"MD of 2nd lord ({second_lord})")
        elif md["lord"] == "Jupiter":
            score += 20
            reasons.append("MD of Jupiter (benefic)")
        elif md["lord"] == "Moon":
            score += 15
            reasons.append("MD of Moon (mind/emotions)")
        
        # AD scoring
        if ad["lord"] == seventh_lord:
            score += 35
            reasons.append(f"AD of 7th lord ({seventh_lord})")
        elif ad["lord"] == "Venus":
            score += 30
            reasons.append("AD of Venus (marriage karaka)")
        elif ad["lord"] == second_lord:
            score += 20
            reasons.append(f"AD of 2nd lord ({second_lord})")
        elif ad["lord"] == "Jupiter":
            score += 18
            reasons.append("AD of Jupiter (benefic)")
        elif ad["lord"] == eleventh_lord:
            score += 15
            reasons.append(f"AD of 11th lord ({eleventh_lord})")
        
        # Check if MD lord is placed in marriage-relevant house natally
        if md["lord"] in planet_data:
            md_natal_house = planet_data[md["lord"]]["house"]
            if md_natal_house in [7, 2, 11]:
                score += 15
                reasons.append(f"MD lord in natal house {md_natal_house}")
        
        # Check if AD lord is placed in marriage-relevant house natally
        if ad["lord"] in planet_data:
            ad_natal_house = planet_data[ad["lord"]]["house"]
            if ad_natal_house in [7, 2, 11]:
                score += 12
                reasons.append(f"AD lord in natal house {ad_natal_house}")
        
        # Bonus: 7th lord + Venus combination
        if (md["lord"] == seventh_lord and ad["lord"] == "Venus") or \
           (md["lord"] == "Venus" and ad["lord"] == seventh_lord):
            score += 20
            reasons.append("7th lord + Venus combination!")
        
        # Only include if score is meaningful
        if score >= 30:
            # Determine likelihood band
            if score >= 70:
                likelihood = "VERY HIGH"
            elif score >= 55:
                likelihood = "HIGH"
            elif score >= 40:
                likelihood = "MODERATE"
            else:
                likelihood = "LOW-MODERATE"
            
            marriage_windows.append({
                "md": md["lord"],
                "ad": ad["lord"],
                "start": max(ad["start"], BIRTH_DATE + timedelta(days=18*365)),
                "end": ad["end"],
                "age_start": max(age_at_ad_start, 18.0),
                "age_end": age_at_ad_end,
                "score": score,
                "likelihood": likelihood,
                "reasons": reasons,
            })

# Sort by score descending
marriage_windows.sort(key=lambda x: x["score"], reverse=True)

print(f"\nFound {len(marriage_windows)} potential marriage windows (score ≥ 30):")
print(f"\n{'Rank':<5} {'Period':<25} {'Age':>8} {'Score':>6} {'Likelihood':<12} {'MD-AD':<20}")
print("-" * 85)

for i, w in enumerate(marriage_windows[:20], 1):
    period = f"{w['start'].strftime('%b %Y')} - {w['end'].strftime('%b %Y')}"
    age_range = f"{w['age_start']:.1f}-{w['age_end']:.1f}"
    md_ad = f"{w['md']}-{w['ad']}"
    print(f"{i:<5} {period:<25} {age_range:>8} {w['score']:>6} {w['likelihood']:<12} {md_ad:<20}")

print("\n" + "=" * 70)
print("TOP 5 MARRIAGE WINDOWS - DETAILED ANALYSIS")
print("=" * 70)

for i, w in enumerate(marriage_windows[:5], 1):
    print(f"\n{'─' * 60}")
    print(f"  Window #{i}: {w['start'].strftime('%B %Y')} to {w['end'].strftime('%B %Y')}")
    print(f"  Age: {w['age_start']:.1f} to {w['age_end']:.1f} years")
    print(f"  MD: {w['md']} | AD: {w['ad']}")
    print(f"  Score: {w['score']}/100 | Likelihood: {w['likelihood']}")
    print(f"  Reasons:")
    for r in w['reasons']:
        print(f"    • {r}")

# ═══════════════════════════════════════════════════════════════════
# STEP 5: TRANSIT OVERLAY (Jupiter/Saturn double transit)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("TRANSIT OVERLAY: Jupiter & Saturn over 7th house/lord")
print("=" * 70)
print("\nChecking Jupiter and Saturn transits over 7th house for top windows...")

# For each top window, check Jupiter and Saturn positions at midpoint
for i, w in enumerate(marriage_windows[:5], 1):
    mid_date = w["start"] + (w["end"] - w["start"]) / 2
    mid_jd = get_jd(mid_date)
    
    transit_positions = get_planet_positions(mid_jd, location)
    jup_sign = get_sign(transit_positions["Jupiter"])
    sat_sign = get_sign(transit_positions["Saturn"])
    
    jup_house_from_lagna = ((jup_sign - asc_sign) % 12) + 1
    sat_house_from_lagna = ((sat_sign - asc_sign) % 12) + 1
    jup_house_from_moon = ((jup_sign - natal_moon_sign) % 12) + 1
    sat_house_from_moon = ((sat_sign - natal_moon_sign) % 12) + 1
    
    # Check double transit on 7th house (sign of 7th house or aspecting it)
    # Jupiter aspects: 5, 7, 9 from its position
    # Saturn aspects: 3, 7, 10 from its position
    jup_aspects_houses = [jup_house_from_lagna, 
                          ((jup_house_from_lagna + 4) % 12) or 12,
                          ((jup_house_from_lagna + 6) % 12) or 12,
                          ((jup_house_from_lagna + 8) % 12) or 12]
    sat_aspects_houses = [sat_house_from_lagna,
                          ((sat_house_from_lagna + 2) % 12) or 12,
                          ((sat_house_from_lagna + 6) % 12) or 12,
                          ((sat_house_from_lagna + 9) % 12) or 12]
    
    jup_on_7 = 7 in jup_aspects_houses
    sat_on_7 = 7 in sat_aspects_houses
    double_transit = jup_on_7 and sat_on_7
    
    # Check from Moon sign too
    jup_aspects_moon = [jup_house_from_moon,
                        ((jup_house_from_moon + 4) % 12) or 12,
                        ((jup_house_from_moon + 6) % 12) or 12,
                        ((jup_house_from_moon + 8) % 12) or 12]
    sat_aspects_moon = [sat_house_from_moon,
                        ((sat_house_from_moon + 2) % 12) or 12,
                        ((sat_house_from_moon + 6) % 12) or 12,
                        ((sat_house_from_moon + 9) % 12) or 12]
    
    jup_on_7_moon = 7 in jup_aspects_moon
    sat_on_7_moon = 7 in sat_aspects_moon
    double_transit_moon = jup_on_7_moon and sat_on_7_moon
    
    transit_status = "✓ DOUBLE TRANSIT ACTIVE" if double_transit else "✗ No double transit"
    transit_moon = "✓ DT from Moon" if double_transit_moon else "✗ No DT from Moon"
    
    print(f"\n  Window #{i} ({w['start'].strftime('%b %Y')}-{w['end'].strftime('%b %Y')}, Age {w['age_start']:.1f}-{w['age_end']:.1f}):")
    print(f"    Transit Jupiter: {SIGN_NAMES[jup_sign]} (H{jup_house_from_lagna} from Lagna)")
    print(f"    Transit Saturn: {SIGN_NAMES[sat_sign]} (H{sat_house_from_lagna} from Lagna)")
    print(f"    From Lagna: {transit_status}")
    print(f"    From Moon:  {transit_moon}")
    
    # Update score based on transit
    if double_transit:
        w["score"] += 20
        w["reasons"].append("Double transit (Jup+Sat) on 7th from Lagna!")
    if double_transit_moon:
        w["score"] += 15
        w["reasons"].append("Double transit (Jup+Sat) on 7th from Moon!")

# Re-sort after transit overlay
marriage_windows.sort(key=lambda x: x["score"], reverse=True)

print("\n" + "=" * 70)
print("FINAL VERDICT: MOST LIKELY MARRIAGE WINDOWS")
print("=" * 70)

for i, w in enumerate(marriage_windows[:7], 1):
    # Recalculate likelihood after transit
    if w["score"] >= 85:
        w["likelihood"] = "VERY HIGH"
    elif w["score"] >= 65:
        w["likelihood"] = "HIGH"
    elif w["score"] >= 50:
        w["likelihood"] = "MODERATE"
    else:
        w["likelihood"] = "LOW-MODERATE"
    
    print(f"\n  #{i} | {w['start'].strftime('%B %Y')} – {w['end'].strftime('%B %Y')}")
    print(f"      Age: {w['age_start']:.1f} to {w['age_end']:.1f} | Score: {w['score']} | {w['likelihood']}")
    print(f"      MD: {w['md']} | AD: {w['ad']}")
    for r in w['reasons']:
        print(f"      • {r}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print(f"\nFor a 51-year-old native (born 22 July 1975, Bhilai),")
print(f"marriage most likely occurred during one of the top-ranked windows above.")
print(f"The strongest window should align with the actual marriage year.")
print("=" * 70)
