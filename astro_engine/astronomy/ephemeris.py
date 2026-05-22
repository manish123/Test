import swisseph as swe


SIDEREAL_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL


def configure_fagan_bradley():
    """Configure ephemeris with FAGAN-BRADLEY ayanamsa (default)"""
    swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY, 0, 0)
    return SIDEREAL_FLAGS


def configure_lahiri():
    """Configure ephemeris with LAHIRI ayanamsa"""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    return SIDEREAL_FLAGS


def configure_ayanamsa(ayanamsa="LAHIRI"):
    """
    Configure ephemeris with specified ayanamsa
    
    Args:
        ayanamsa: Ayanamsa type (default: LAHIRI)
    
    Returns:
        SIDEREAL_FLAGS
    """
    ayanamsa_map = {
        "FAGAN_BRADLEY": swe.SIDM_FAGAN_BRADLEY,
        "LAHIRI": swe.SIDM_LAHIRI,
        "RAMAN": swe.SIDM_RAMAN,
        "KRISHNAMURTI": swe.SIDM_KRISHNAMURTI,
    }
    
    if ayanamsa not in ayanamsa_map:
        ayanamsa = "LAHIRI"
    
    swe.set_sid_mode(ayanamsa_map[ayanamsa], 0, 0)
    return SIDEREAL_FLAGS
