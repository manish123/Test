from astronomy.engine_base import get_comprehensive_planet_data
from features.nakshatra import (
    get_comprehensive_nakshatra_info,
    longitude_to_rashi_dms,
    format_latitude,
    planet_sanskrit_names
)
from features.dignity import get_planet_status, get_sign, SIGN_LORDS, _relationship_tier


def get_planet_sanskrit_name(planet_name):
    """Get Sanskrit name for planet"""
    return planet_sanskrit_names.get(planet_name, planet_name)


def format_motion_symbol(retrograde):
    """Get motion symbol for retrograde/forward"""
    return "↙" if retrograde else "↻"


def get_comprehensive_planet_report(jd, planet_name, location=None):
    """
    Generate comprehensive planetary position report in the requested format
    
    Example output for Venus:
    Venus (Ven)
    Shukra
    Longitude: Mesha 13° 45' 6.23"
    Latitude/Shara: 00° S 13' 29" (-0.23)
    Speed: Planet Speed +1.22 deg/day
    Nakshatra: Bharani, 1st Pada
    Motion: ↻ Forward
    State: Udita
    Residing in: Neutral with Landlord
    Nakshatra Lord: Shukra
    Nakshatra Sub Lord: Shukra
    Right Ascension: +35.69
    Declination/Kranti: +13.95
    Raw Longitude: +13.75
    """
    
    # Get comprehensive planetary data with location
    planet_data = get_comprehensive_planet_data(jd, location)
    
    if planet_name not in planet_data:
        return f"Planet {planet_name} not found in calculations"
    
    data = planet_data[planet_name]
    
    # Basic planet info
    sanskrit_name = get_planet_sanskrit_name(planet_name)
    short_code = planet_name[:3].upper()
    
    # Longitude formatting
    rashi_name, deg, min_val, sec = longitude_to_rashi_dms(data["longitude"])
    longitude_str = f"{rashi_name} {deg}° {min_val}' {sec:.2f}\""
    
    # Latitude formatting
    lat_deg = int(abs(data["latitude"]))
    lat_min = int((abs(data["latitude"]) - lat_deg) * 60)
    lat_sec = ((abs(data["latitude"]) - lat_deg) * 60 - lat_min) * 60
    lat_dir = "S" if data["latitude"] < 0 else "N"
    latitude_str = f"{lat_deg:02d}° {lat_dir} {lat_min}' {lat_sec:.0f}\" ({data['latitude']:+.2f})"
    
    # Speed formatting
    speed_str = f"Planet Speed {data['speed']:+.2f} deg/day"
    
    # Nakshatra information
    nakshatra_info = get_comprehensive_nakshatra_info(data["longitude"])
    nakshatra_str = f"{nakshatra_info['nakshatra']}, {nakshatra_info['pada']}{'st' if nakshatra_info['pada'] == 1 else 'nd' if nakshatra_info['pada'] == 2 else 'rd' if nakshatra_info['pada'] == 3 else 'th'} Pada"
    
    # Motion
    motion_symbol = format_motion_symbol(data["retrograde"])
    motion_str = f"{motion_symbol} {'Retrograde' if data['retrograde'] else 'Forward'}"
    
    # State (dignity/avastha) — computed from longitude directly
    try:
        status = get_planet_status(planet_name, data["longitude"])
        state_mapping = {
            "exalted": "Udita", "debilitated": "Kshudhita", "moolatrikona": "Moolatrikona",
            "own": "Swakshetra", "great_friend": "Prasanna", "friend": "Shanta",
            "neutral": "Dina", "enemy": "Kopita", "bitter_enemy": "Dukhita",
        }
        state_str = state_mapping.get(status, status)
    except:
        state_str = "Unknown"
    
    # Relationship with landlord — computed from longitude directly
    try:
        sign = get_sign(data["longitude"])
        sign_lord = SIGN_LORDS[sign]
        relationship = _relationship_tier(planet_name, sign_lord)
        relationship_mapping = {
            "great_friend": "Great Friend with Landlord",
            "friend": "Friend with Landlord",
            "neutral": "Neutral with Landlord",
            "enemy": "Enemy with Landlord",
            "bitter_enemy": "Bitter Enemy with Landlord",
        }
        relationship_str = relationship_mapping.get(relationship, relationship)
    except:
        relationship_str = "Unknown"
    
    # Nakshatra lords
    nakshatra_lord_sanskrit = planet_sanskrit_names.get(nakshatra_info['lord'], nakshatra_info['lord'])
    nakshatra_sub_lord_sanskrit = planet_sanskrit_names.get(nakshatra_info['sub_lord'], nakshatra_info['sub_lord'])
    
    # Right ascension and declination
    ra_str = f"{data['ra']:+.2f}"
    dec_str = f"{data['dec']:+.2f}"
    
    # Raw longitude
    raw_lon_str = f"{data['longitude']:+.2f}"
    
    # Build the report
    report_lines = [
        f"{planet_name} ({short_code})",
        f"{sanskrit_name}",
        f"Longitude: {longitude_str}",
        f"Latitude/Shara: {latitude_str}",
        f"Speed: {speed_str}",
        f"Nakshatra: {nakshatra_str}",
        f"Motion: {motion_str}",
        f"State: {state_str}",
        f"Residing in: {relationship_str}",
        f"Nakshatra Lord: {nakshatra_lord_sanskrit}",
        f"Nakshatra Sub Lord: {nakshatra_sub_lord_sanskrit}",
        f"Right Ascension: {ra_str}",
        f"Declination/Kranti: {dec_str}",
        f"Raw Longitude: {raw_lon_str}"
    ]
    
    return "\n".join(report_lines)


def get_all_planets_comprehensive_report(jd, location=None):
    """
    Generate comprehensive reports for all planets
    """
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    
    all_reports = {}
    for planet in planets:
        all_reports[planet] = get_comprehensive_planet_report(jd, planet, location)
    
    return all_reports


def print_planet_report(jd, planet_name, location=None):
    """Print comprehensive report for a specific planet"""
    report = get_comprehensive_planet_report(jd, planet_name, location)
    print("=" * 50)
    print(f"COMPREHENSIVE PLANETARY REPORT - {planet_name.upper()}")
    print("=" * 50)
    print(report)
    print("=" * 50)


def print_all_planets_report(jd, location=None):
    """Print comprehensive reports for all planets"""
    reports = get_all_planets_comprehensive_report(jd, location)
    
    for planet, report in reports.items():
        print_planet_report(jd, planet, location)
        print("\n")
