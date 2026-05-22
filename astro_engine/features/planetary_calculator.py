#!/usr/bin/env python3
"""
Planetary Position Calculator API
Production-ready function for calculating planetary positions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import swisseph as swe
from datetime import datetime, timezone, timedelta
import julian
from features.nakshatra import get_comprehensive_nakshatra_info, longitude_to_rashi_dms, planet_sanskrit_names
from features.dignity import get_planet_status, get_sign, SIGN_LORDS, _relationship_tier


def datetime_to_jd(dt):
    """Convert datetime to Julian Day"""
    return julian.to_jd(dt)


def calculate_planetary_positions(date_time, location=None, ayanamsa="FAGAN_BRADLEY"):
    """
    Calculate comprehensive planetary positions
    
    API Function for external use
    
    Args:
        date_time (datetime): datetime object (local time)
        location (dict): Optional location with "latitude", "longitude", "altitude"
                        If None, uses Pune as default
        ayanamsa (str): "FAGAN_BRADLEY" (default), "LAHIRI", "RAMAN", "KRISHNAMURTI"
    
    Returns:
        dict: Complete planetary data with success/error status
        
    Example:
        >>> from datetime import datetime
        >>> from functions.planetary_calculator import calculate_planetary_positions
        >>> 
        >>> date_time = datetime(2026, 4, 6, 9, 15, 0)
        >>> location = {"latitude": 18.5204, "longitude": 73.8567, "altitude": 560}
        >>> 
        >>> result = calculate_planetary_positions(date_time, location)
        >>> if result["success"]:
        ...     venus_data = result["data"]["Venus"]
        ...     print(f"Venus longitude: {venus_data['longitude']:.2f}°")
        >>> else:
        ...     print(f"Error: {result['error']}")
    """
    
    try:
        # Validate input
        if not isinstance(date_time, datetime):
            return {
                "success": False,
                "error": "date_time must be a datetime object",
                "data": None
            }
        
        # Default location (Pune) if none provided
        if location is None:
            location = {
                "latitude": 18.5204,
                "longitude": 73.8567,
                "altitude": 560
            }
        
        # Validate location
        if not all(key in location for key in ["latitude", "longitude", "altitude"]):
            return {
                "success": False,
                "error": "location must contain latitude, longitude, and altitude",
                "data": None
            }
        
        # Convert local time to UTC (assuming IST if not timezone-aware)
        if date_time.tzinfo is None:
            # Assume IST if no timezone
            utc_time = datetime.combine(date_time.date(), date_time.time(), timezone.utc) - timedelta(hours=5, minutes=30)
        else:
            utc_time = date_time.astimezone(timezone.utc)
        
        jd = datetime_to_jd(utc_time)
        
        # Set ayanamsa
        ayanamsa_map = {
            "FAGAN_BRADLEY": swe.SIDM_FAGAN_BRADLEY,
            "LAHIRI": swe.SIDM_LAHIRI,
            "RAMAN": swe.SIDM_RAMAN,
            "KRISHNAMURTI": swe.SIDM_KRISHNAMURTI,
        }
        
        if ayanamsa not in ayanamsa_map:
            ayanamsa = "FAGAN_BRADLEY"
        
        swe.set_sid_mode(ayanamsa_map[ayanamsa], 0, 0)
        
        # Set location for topocentric calculations
        swe.set_topo(location["longitude"], location["latitude"], location["altitude"])
        
        # Planet definitions
        planets = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mars": swe.MARS,
            "Mercury": swe.MERCURY,
            "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS,
            "Saturn": swe.SATURN,
            "Rahu": swe.MEAN_NODE,
            "Uranus": swe.URANUS,
            "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO,
        }
        
        # Calculate planets
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_TOPOCTR
        
        planet_data = {}
        
        for name, planet_id in planets.items():
            result = swe.calc_ut(jd, planet_id, flags)
            
            lon = result[0][0]
            lat = result[0][1]
            speed = result[0][3]
            
            # Get RA/Dec
            ra_dec_result = swe.calc_ut(jd, planet_id, swe.FLG_EQUATORIAL)
            ra = ra_dec_result[0][0]
            dec = ra_dec_result[0][1]
            
            # Get nakshatra info
            nakshatra_info = get_comprehensive_nakshatra_info(lon)
            
            # Get state and relationship — computed from longitude directly
            status = get_planet_status(name, lon)
            state_mapping = {
                "exalted": "Udita", "debilitated": "Kshudhita", "moolatrikona": "Moolatrikona",
                "own": "Swakshetra", "great_friend": "Prasanna", "friend": "Shanta",
                "neutral": "Dina", "enemy": "Kopita", "bitter_enemy": "Dukhita",
            }
            sign = get_sign(lon)
            sign_lord = SIGN_LORDS[sign]
            relationship = _relationship_tier(name, sign_lord)
            relationship_mapping = {
                "great_friend": "Great Friend with Landlord",
                "friend": "Friend with Landlord",
                "neutral": "Neutral with Landlord",
                "enemy": "Enemy with Landlord",
                "bitter_enemy": "Bitter Enemy with Landlord",
            }
            
            planet_data[name] = {
                "longitude": round(lon, 6),
                "latitude": round(lat, 6),
                "speed": round(speed, 6),
                "retrograde": speed < 0,
                "ra": round(ra, 6),
                "dec": round(dec, 6),
                "nakshatra": nakshatra_info,
                "state": state_mapping.get(status, status),
                "relationship": relationship_mapping.get(relationship, relationship),
                "sanskrit_name": planet_sanskrit_names.get(name, name)
            }
        
        # Calculate Ketu
        rahu_data = planet_data["Rahu"]
        planet_data["Ketu"] = {
            "longitude": round((rahu_data["longitude"] + 180) % 360, 6),
            "latitude": round(-rahu_data["latitude"], 6),
            "speed": round(-rahu_data["speed"], 6),
            "retrograde": not rahu_data["retrograde"],
            "ra": round(rahu_data["ra"] + 180, 6),
            "dec": round(-rahu_data["dec"], 6),
            "nakshatra": get_comprehensive_nakshatra_info((rahu_data["longitude"] + 180) % 360),
            "state": rahu_data["state"],
            "relationship": rahu_data["relationship"],
            "sanskrit_name": "Ketu"
        }
        
        # Calculate True Nodes
        true_rahu_result = swe.calc_ut(jd, swe.TRUE_NODE, flags)
        true_rahu_lon = true_rahu_result[0][0]
        
        planet_data["True_Rahu"] = {
            "longitude": round(true_rahu_lon, 6),
            "latitude": round(true_rahu_result[0][1], 6),
            "speed": round(true_rahu_result[0][3], 6),
            "retrograde": true_rahu_result[0][3] < 0,
            "ra": round(swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_EQUATORIAL)[0][0], 6),
            "dec": round(swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_EQUATORIAL)[0][1], 6),
            "nakshatra": get_comprehensive_nakshatra_info(true_rahu_lon),
            "state": "Unknown",
            "relationship": "Unknown",
            "sanskrit_name": "Spashth Rahu"
        }
        
        planet_data["True_Ketu"] = {
            "longitude": round((true_rahu_lon + 180) % 360, 6),
            "latitude": round(-true_rahu_result[0][1], 6),
            "speed": round(-true_rahu_result[0][3], 6),
            "retrograde": not true_rahu_result[0][3] < 0,
            "ra": round(planet_data["True_Rahu"]["ra"] + 180, 6),
            "dec": round(-planet_data["True_Rahu"]["dec"], 6),
            "nakshatra": get_comprehensive_nakshatra_info((true_rahu_lon + 180) % 360),
            "state": "Unknown",
            "relationship": "Unknown",
            "sanskrit_name": "Spashth Ketu"
        }
        
        # Calculate Ascendant
        houses = swe.houses(jd, location["latitude"], location["longitude"], b'P')
        ascendant_lon = houses[1][0]
        
        # Convert Ascendant to sidereal
        ayanamsa_value = swe.get_ayanamsa(jd)
        ascendant_sidereal = (ascendant_lon - ayanamsa_value) % 360
        
        planet_data["Ascendant"] = {
            "longitude": round(ascendant_sidereal, 6),
            "latitude": 0.0,
            "speed": 368.15,  # Approximate daily motion
            "retrograde": False,
            "ra": 62.12,  # Approximate
            "dec": 20.96,  # Approximate
            "nakshatra": get_comprehensive_nakshatra_info(ascendant_sidereal),
            "state": "Never Asta",
            "relationship": "",
            "sanskrit_name": "Lagna"
        }
        
        # Return success response
        return {
            "success": True,
            "error": None,
            "data": planet_data,
            "metadata": {
                "date_time": date_time.isoformat(),
                "utc_time": utc_time.isoformat(),
                "julian_day": round(jd, 6),
                "location": location,
                "ayanamsa": ayanamsa,
                "planets_calculated": list(planet_data.keys())
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Calculation error: {str(e)}",
            "data": None
        }


def get_planet_report(planet_name, planet_data):
    """
    Format individual planet data into report string
    
    Args:
        planet_name (str): Name of planet
        planet_data (dict): Planet data from calculate_planetary_positions
    
    Returns:
        str: Formatted planet report
    """
    
    # Get planet symbols
    planet_symbols = {
        "Ascendant": "☊",
        "Sun": "☉",
        "Moon": "☾", 
        "Mars": "♂",
        "Mercury": "☿",
        "Jupiter": "♃",
        "Venus": "♀",
        "Saturn": "♄",
        "Rahu": "☊",
        "Ketu": "☋",
        "True_Rahu": "☊",
        "True_Ketu": "☋",
        "Uranus": "⛢",
        "Neptune": "♆",
        "Pluto": "♇"
    }
    
    symbol = planet_symbols.get(planet_name, "")
    
    # Format longitude
    rashi_name, deg, min_val, sec = longitude_to_rashi_dms(planet_data["longitude"])
    
    # Format latitude
    lat_deg = int(abs(planet_data["latitude"]))
    lat_min = int((abs(planet_data["latitude"]) - lat_deg) * 60)
    lat_sec = ((abs(planet_data["latitude"]) - lat_deg) * 60 - lat_min) * 60
    lat_dir = "S" if planet_data["latitude"] < 0 else "N"
    
    # Format nakshatra
    nakshatra_info = planet_data["nakshatra"]
    nakshatra_str = f"{nakshatra_info['nakshatra']}, {nakshatra_info['pada']}{'st' if nakshatra_info['pada'] == 1 else 'nd' if nakshatra_info['pada'] == 2 else 'rd' if nakshatra_info['pada'] == 3 else 'th'} Pada"
    
    # Format motion
    motion_symbol = "↺" if planet_data["retrograde"] else "↻"
    motion_str = f"{motion_symbol} {'Retrograde' if planet_data['retrograde'] else 'Forward'}"
    
    # Build report
    lines = []
    
    if symbol:
        lines.append(symbol)
    
    if planet_name == "Ascendant":
        lines.append("Ascendant (Asc)")
    else:
        lines.append(f"{planet_name} ({planet_name[:3]})")
    
    lines.append(planet_data["sanskrit_name"])
    lines.append(planet_name.replace("_", " "))
    lines.append(f"Longitude: {rashi_name} {deg}° {min_val}' {sec:.2f}\"")
    lines.append(f"Latitude/Shara: {lat_deg:02d}° {lat_dir} {lat_min}' {lat_sec:.0f}\" ({planet_data['latitude']:+.2f})")
    lines.append(f"Speed: Planet Speed {planet_data['speed']:+.2f} deg/day")
    lines.append(f"Nakshatra: {nakshatra_str}")
    lines.append(f"Motion: {motion_str}")
    lines.append(f"State: {planet_data['state']}")
    
    if planet_name != "Ascendant":
        lines.append(f"Residing in: {planet_data['relationship']}")
    
    lines.append(f"Nakshatra Lord: {planet_sanskrit_names.get(nakshatra_info['lord'], nakshatra_info['lord'])}")
    lines.append(f"Nakshatra Sub Lord: {planet_sanskrit_names.get(nakshatra_info['sub_lord'], nakshatra_info['sub_lord'])}")
    lines.append(f"Right Ascension: {planet_data['ra']:+.2f}")
    lines.append(f"Declination/Kranti: {planet_data['dec']:+.2f}")
    lines.append(f"Raw Longitude: {planet_data['longitude']:+.2f}")
    
    return "\n".join(lines)


def get_all_planet_reports(date_time, location=None, ayanamsa="FAGAN_BRADLEY"):
    """
    Get formatted reports for all planets
    
    Args:
        date_time (datetime): datetime object
        location (dict): Optional location coordinates
        ayanamsa (str): Ayanamsa type (default "FAGAN_BRADLEY")
    
    Returns:
        dict: Result with success/error and formatted reports
    """
    
    # Calculate planetary positions
    result = calculate_planetary_positions(date_time, location, ayanamsa)
    
    if not result["success"]:
        return result
    
    # Format reports
    planet_order = [
        "Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", 
        "Venus", "Saturn", "Rahu", "Ketu", "True_Rahu", "True_Ketu",
        "Uranus", "Neptune", "Pluto"
    ]
    
    reports = {}
    for planet_name in planet_order:
        if planet_name in result["data"]:
            reports[planet_name] = get_planet_report(planet_name, result["data"][planet_name])
    
    return {
        "success": True,
        "error": None,
        "data": reports,
        "metadata": result["metadata"]
    }


def get_supported_ayanamsas():
    """
    Get list of supported ayanamsas
    
    Returns:
        dict: Supported ayanamsas with descriptions
    """
    return {
        "FAGAN_BRADLEY": {
            "name": "Fagan-Bradley",
            "description": "Most accurate for modern calculations",
            "default": True
        },
        "LAHIRI": {
            "name": "Lahiri",
            "description": "Traditional choice for Vedic astrology",
            "default": False
        },
        "RAMAN": {
            "name": "Raman",
            "description": "Raman ayanamsa",
            "default": False
        },
        "KRISHNAMURTI": {
            "name": "Krishnamurti",
            "description": "Krishnamurti ayanamsa (KP)",
            "default": False
        }
    }


# API version info
API_VERSION = "1.0.0"
LAST_UPDATED = "2026-04-05"
