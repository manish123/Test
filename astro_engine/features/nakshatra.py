from astronomy.utils import normalize_lon


NAKSHATRA_SIZE = 13.3333333333

nakshatra_list = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

# Nakshatra lords (ruling planets)
nakshatra_lords = [
    "Ketu",      # Ashwini
    "Venus",     # Bharani
    "Sun",       # Krittika
    "Moon",      # Rohini
    "Mars",      # Mrigashira
    "Rahu",      # Ardra
    "Jupiter",   # Punarvasu
    "Saturn",    # Pushya
    "Mercury",   # Ashlesha
    "Ketu",      # Magha
    "Venus",     # Purva Phalguni
    "Sun",       # Uttara Phalguni
    "Moon",      # Hasta
    "Mars",      # Chitra
    "Rahu",      # Swati
    "Jupiter",   # Vishakha
    "Saturn",    # Anuradha
    "Mercury",   # Jyeshtha
    "Ketu",      # Mula
    "Venus",     # Purva Ashadha
    "Sun",       # Uttara Ashadha
    "Moon",      # Shravana
    "Mars",      # Dhanishta
    "Rahu",      # Shatabhisha
    "Jupiter",   # Purva Bhadrapada
    "Saturn",    # Uttara Bhadrapada
    "Mercury",   # Revati
]

# Sanskrit names for planets
planet_sanskrit_names = {
    "Sun": "Surya",
    "Moon": "Chandra",
    "Mars": "Mangala",
    "Mercury": "Budha",
    "Jupiter": "Guru",
    "Venus": "Shukra",
    "Saturn": "Shani",
    "Rahu": "Rahu",
    "Ketu": "Ketu"
}

# Sanskrit names for nakshatras
nakshatra_sanskrit = {
    "Ashwini": "Ashwini",
    "Bharani": "Bharani",
    "Krittika": "Krittika",
    "Rohini": "Rohini",
    "Mrigashira": "Mrigashira",
    "Ardra": "Ardra",
    "Punarvasu": "Punarvasu",
    "Pushya": "Pushya",
    "Ashlesha": "Ashlesha",
    "Magha": "Magha",
    "Purva Phalguni": "Purva Phalguni",
    "Uttara Phalguni": "Uttara Phalguni",
    "Hasta": "Hasta",
    "Chitra": "Chitra",
    "Swati": "Swati",
    "Vishakha": "Vishakha",
    "Anuradha": "Anuradha",
    "Jyeshtha": "Jyeshtha",
    "Mula": "Mula",
    "Purva Ashadha": "Purva Ashadha",
    "Uttara Ashadha": "Uttara Ashadha",
    "Shravana": "Shravana",
    "Dhanishta": "Dhanishta",
    "Shatabhisha": "Shatabhisha",
    "Purva Bhadrapada": "Purva Bhadrapada",
    "Uttara Bhadrapada": "Uttara Bhadrapada",
    "Revati": "Revati"
}

# Rashi names for longitude display
rashi_names = [
    "Mesha", "Vrishabha", "Mithuna", "Karka",
    "Simha", "Kanya", "Tula", "Vrishchika",
    "Dhanu", "Makara", "Kumbha", "Meena"
]

def get_nakshatra(lon):
    lon = normalize_lon(lon)
    index = min(len(nakshatra_list) - 1, int(lon / NAKSHATRA_SIZE))
    return nakshatra_list[index]


def get_nakshatra_with_pada(lon):
    """
    Get nakshatra name and pada (quarter) for a given longitude
    """
    lon = normalize_lon(lon)
    nakshatra_index = min(len(nakshatra_list) - 1, int(lon / NAKSHATRA_SIZE))
    nakshatra_name = nakshatra_list[nakshatra_index]
    
    # Calculate pada (each nakshatra has 4 padas of 3°20' each)
    pada_size = NAKSHATRA_SIZE / 4  # 3.3333333333 degrees per pada
    pada_lon_in_nakshatra = lon % NAKSHATRA_SIZE
    pada_number = int(pada_lon_in_nakshatra / pada_size) + 1  # 1 to 4
    
    return nakshatra_name, pada_number


def get_nakshatra_lord(nakshatra_name):
    """
    Get the ruling planet (lord) of a nakshatra
    """
    if nakshatra_name in nakshatra_list:
        index = nakshatra_list.index(nakshatra_name)
        return nakshatra_lords[index]
    return None


def get_nakshatra_sub_lord(nakshatra_name, pada_number):
    """
    Get the sub-lord of a nakshatra pada
    For simplicity, using the same as nakshatra lord (can be enhanced with Vimshottari dasha system)
    """
    return get_nakshatra_lord(nakshatra_name)


def longitude_to_dms(lon):
    """
    Convert longitude to degrees, minutes, seconds format
    """
    lon = normalize_lon(lon)
    degrees = int(lon)
    minutes = int((lon - degrees) * 60)
    seconds = ((lon - degrees) * 60 - minutes) * 60
    return degrees, minutes, seconds


def longitude_to_rashi_dms(lon):
    """
    Convert longitude to Rashi with degrees, minutes, seconds
    """
    lon = normalize_lon(lon)
    rashi_index = int(lon / 30)
    rashi_name = rashi_names[rashi_index]
    lon_in_rashi = lon % 30
    degrees, minutes, seconds = longitude_to_dms(lon_in_rashi)
    return rashi_name, degrees, minutes, seconds


def format_latitude(lat):
    """
    Format latitude with direction indicator
    """
    if lat > 0:
        return f"{abs(lat):.2f}° N"
    elif lat < 0:
        return f"{abs(lat):.2f}° S"
    else:
        return "0.00°"


def get_comprehensive_nakshatra_info(lon):
    """
    Get comprehensive nakshatra information for a given longitude
    """
    nakshatra_name, pada_number = get_nakshatra_with_pada(lon)
    lord = get_nakshatra_lord(nakshatra_name)
    sub_lord = get_nakshatra_sub_lord(nakshatra_name, pada_number)
    sanskrit_name = nakshatra_sanskrit.get(nakshatra_name, nakshatra_name)
    
    return {
        "nakshatra": nakshatra_name,
        "sanskrit_name": sanskrit_name,
        "pada": pada_number,
        "lord": lord,
        "sub_lord": sub_lord,
        "lord_sanskrit": planet_sanskrit_names.get(lord, lord)
    }
