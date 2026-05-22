import swisseph as swe


SIDEREAL_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

# Location coordinates for Pune, India
PUNE_COORDINATES = {
    "latitude": 18.5204,  # N
    "longitude": 73.8567,  # E
    "altitude": 560  # meters above sea level
}


def configure_ephemeris():
    swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY, 0, 0)


def get_planet_positions(jd, location=None):
    configure_ephemeris()
    
    # Use Pune as default location if none provided
    if location is None:
        location = PUNE_COORDINATES

    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,
    }

    results = {}

    for name, p in planets.items():
        # Calculate with topocentric corrections for location
        flags = SIDEREAL_FLAGS
        if location:
            flags |= swe.FLG_TOPOCTR
        
        # Use swe.calc_ut with location parameters for topocentric calculations
        # The correct API for pyswisseph is swe.calc_ut(jd, planet_id, flags)
        # Location is set separately using swe.set_topo()
        if location:
            swe.set_topo(location["longitude"], location["latitude"], location["altitude"])
        
        result = swe.calc_ut(jd, p, flags)
        lon = result[0][0]
        results[name] = lon

    results["Ketu"] = (results["Rahu"] + 180) % 360

    return results


def get_planet_latitudes(jd, location=None):
    configure_ephemeris()
    
    if location is None:
        location = PUNE_COORDINATES

    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,
    }

    results = {}
    for name, p in planets.items():
        flags = SIDEREAL_FLAGS
        if location:
            flags |= swe.FLG_TOPOCTR
            
        if location:
            swe.set_topo(location["longitude"], location["latitude"], location["altitude"])
            
        result = swe.calc_ut(jd, p, flags)
        lat = result[0][1]
        results[name] = lat

    results["Ketu"] = -results["Rahu"]
    return results


def get_retrograde_flags(jd, location=None):
    configure_ephemeris()
    
    if location is None:
        location = PUNE_COORDINATES

    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,
    }

    results = {}
    for name, p in planets.items():
        # Use SWIEPH + SPEED flags to get speed data
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        if location:
            flags |= swe.FLG_TOPOCTR
            
        if location:
            swe.set_topo(location["longitude"], location["latitude"], location["altitude"])
            
        result = swe.calc_ut(jd, p, flags)
        speed_longitude = result[0][3]
        results[name] = speed_longitude < 0

    results["Ketu"] = not results["Rahu"]
    return results


def get_planet_speeds(jd, location=None):
    configure_ephemeris()
    
    if location is None:
        location = PUNE_COORDINATES

    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,
    }

    results = {}
    for name, p in planets.items():
        # Use SWIEPH + SPEED flags to get speed data
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        if location:
            flags |= swe.FLG_TOPOCTR
            
        if location:
            swe.set_topo(location["longitude"], location["latitude"], location["altitude"])
            
        result = swe.calc_ut(jd, p, flags)
        speed_longitude = result[0][3]  # Speed in longitude
        results[name] = speed_longitude

    results["Ketu"] = -results["Rahu"]
    return results


def get_right_ascension_declination(jd, location=None):
    configure_ephemeris()
    
    if location is None:
        location = PUNE_COORDINATES

    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,
    }

    results = {}
    for name, p in planets.items():
        # Get equatorial coordinates (right ascension and declination)
        # Use topocentric flags if location is provided
        flags = swe.FLG_EQUATORIAL
        if location:
            flags |= swe.FLG_TOPOCTR
            
        if location:
            swe.set_topo(location["longitude"], location["latitude"], location["altitude"])
            
        result = swe.calc_ut(jd, p, flags)
        ra = result[0][0]  # Right ascension in degrees
        dec = result[0][1]  # Declination in degrees
        results[name] = {"ra": ra, "dec": dec}

    results["Ketu"] = {"ra": results["Rahu"]["ra"] + 180, "dec": -results["Rahu"]["dec"]}
    return results


def get_comprehensive_planet_data(jd, location=None):
    """
    Get comprehensive planetary data including longitude, latitude, speed, motion, RA, Dec
    """
    positions = get_planet_positions(jd, location)
    latitudes = get_planet_latitudes(jd, location)
    speeds = get_planet_speeds(jd, location)
    retrograde_flags = get_retrograde_flags(jd, location)
    ra_dec = get_right_ascension_declination(jd, location)
    
    comprehensive_data = {}
    for planet in positions.keys():
        comprehensive_data[planet] = {
            "longitude": positions[planet],
            "latitude": latitudes[planet],
            "speed": speeds[planet],
            "retrograde": retrograde_flags[planet],
            "ra": ra_dec[planet]["ra"],
            "dec": ra_dec[planet]["dec"]
        }
    
    return comprehensive_data



def get_house_cusps(jd, lat, lon):
    """
    Compute house cusps using Placidus system with Fagan-Bradley ayanamsa.

    Pure ephemeris call — no interpretation.

    Args:
        jd: Julian Day number
        lat: geographic latitude
        lon: geographic longitude

    Returns:
        dict with:
            "ascendant": float (sidereal longitude of ascendant)
            "houses": tuple of 12 cusp longitudes
    """
    configure_ephemeris()

    flags = SIDEREAL_FLAGS
    try:
        houses, asc = swe.houses_ex(jd, lat, lon, b"P", flags)
    except TypeError:
        houses, asc = swe.houses(jd, lat, lon)

    return {
        "ascendant": asc[0],
        "houses": houses,
    }
