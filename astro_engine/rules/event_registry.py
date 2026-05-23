"""
Event Registry — Query API for the Event Ontology (V3).

Provides fast lookups for domain interpreters and scoring engines:
- get_events_for_domain(domain) → list of events tagged for that domain
- get_events_by_category(category) → list of events in a category
- get_event(event_id) → single event by ID
- get_events_by_house(house) → events activated by a specific house
- get_events_by_planet(planet) → events where planet is a significator
- get_events_by_polarity(polarity) → filter by positive/negative/mixed/neutral
- get_domain_event_summary(domain) → category breakdown for a domain

This module is read-only. It never modifies the ontology.
"""

from typing import List, Dict, Optional
from rules.event_ontology import EVENT_MAP_V3, EVENT_INDEX, Event, DOMAINS, CATEGORIES


# ═══════════════════════════════════════════════════════════════
# PRE-BUILT INDEXES (computed once at import time)
# ═══════════════════════════════════════════════════════════════

# domain → list of events
_DOMAIN_INDEX: Dict[str, List[Event]] = {d: [] for d in DOMAINS}
for _e in EVENT_MAP_V3:
    for _d in _e.domains:
        if _d in _DOMAIN_INDEX:
            _DOMAIN_INDEX[_d].append(_e)

# category → list of events
_CATEGORY_INDEX: Dict[str, List[Event]] = {}
for _e in EVENT_MAP_V3:
    _CATEGORY_INDEX.setdefault(_e.category, []).append(_e)

# house → list of events
_HOUSE_INDEX: Dict[int, List[Event]] = {h: [] for h in range(1, 13)}
for _e in EVENT_MAP_V3:
    for _h in _e.houses:
        _HOUSE_INDEX[_h].append(_e)

# planet → list of events
_PLANET_INDEX: Dict[str, List[Event]] = {}
for _e in EVENT_MAP_V3:
    for _p in _e.planetary_significators:
        _PLANET_INDEX.setdefault(_p, []).append(_e)

# polarity → list of events
_POLARITY_INDEX: Dict[str, List[Event]] = {}
for _e in EVENT_MAP_V3:
    _POLARITY_INDEX.setdefault(_e.polarity, []).append(_e)


# ═══════════════════════════════════════════════════════════════
# QUERY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_event(event_id: str) -> Optional[Event]:
    """Get a single event by its unique ID. Returns None if not found."""
    return EVENT_INDEX.get(event_id)


def get_events_for_domain(domain: str) -> List[Event]:
    """
    Get all events tagged for a specific domain.

    Args:
        domain: one of trading, career, relationship, health, spirituality, general_life

    Returns:
        List of Event objects belonging to that domain
    """
    return _DOMAIN_INDEX.get(domain, [])


def get_events_by_category(category: str) -> List[Event]:
    """
    Get all events in a specific category.

    Args:
        category: one of career_enterprise, relationships_family, health_wellbeing,
                  spiritual_learning, life_shifts_assets, trading_market

    Returns:
        List of Event objects in that category
    """
    return _CATEGORY_INDEX.get(category, [])


def get_events_by_house(house: int) -> List[Event]:
    """
    Get all events associated with a specific house (1-12).

    Useful for: "what events are possible when house 10 is activated?"
    """
    return _HOUSE_INDEX.get(house, [])


def get_events_by_planet(planet: str) -> List[Event]:
    """
    Get all events where a planet is a significator.

    Useful for: "what events does Jupiter activate?"
    """
    return _PLANET_INDEX.get(planet, [])


def get_events_by_polarity(polarity: str) -> List[Event]:
    """
    Filter events by polarity: positive, negative, mixed, neutral.
    """
    return _POLARITY_INDEX.get(polarity, [])


def get_domain_event_ids(domain: str) -> List[str]:
    """Get just the event_ids for a domain (lightweight query)."""
    return [e.event_id for e in _DOMAIN_INDEX.get(domain, [])]


def get_domain_event_summary(domain: str) -> Dict[str, int]:
    """
    Get category breakdown for a domain.

    Returns:
        dict mapping category → count of events in that domain
    """
    events = get_events_for_domain(domain)
    summary = {}
    for e in events:
        cat_label = CATEGORIES.get(e.category, e.category)
        summary[cat_label] = summary.get(cat_label, 0) + 1
    return summary


def get_events_for_domain_and_house(domain: str, house: int) -> List[Event]:
    """
    Get events that belong to a domain AND are associated with a specific house.

    Useful for: "what career events fire when house 10 is activated?"
    """
    domain_events = set(id(e) for e in _DOMAIN_INDEX.get(domain, []))
    return [e for e in _HOUSE_INDEX.get(house, []) if id(e) in domain_events]


def get_events_for_domain_and_planet(domain: str, planet: str) -> List[Event]:
    """
    Get events that belong to a domain AND have a specific planet as significator.

    Useful for: "what trading events does Jupiter activate?"
    """
    domain_events = set(id(e) for e in _DOMAIN_INDEX.get(domain, []))
    return [e for e in _PLANET_INDEX.get(planet, []) if id(e) in domain_events]


def get_positive_events_for_domain(domain: str) -> List[Event]:
    """Get only positive-polarity events for a domain."""
    return [e for e in _DOMAIN_INDEX.get(domain, []) if e.polarity == "positive"]


def get_negative_events_for_domain(domain: str) -> List[Event]:
    """Get only negative-polarity events for a domain."""
    return [e for e in _DOMAIN_INDEX.get(domain, []) if e.polarity == "negative"]


def get_life_stage_events() -> List[Event]:
    """Get all events that are life-stage-sensitive (interpretation changes with age)."""
    return [e for e in EVENT_MAP_V3 if e.life_stage_sensitive]


def get_non_repeatable_events() -> List[Event]:
    """Get all one-time events (e.g., first_child, immigration)."""
    return [e for e in EVENT_MAP_V3 if not e.repeatable]
