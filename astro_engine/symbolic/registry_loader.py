"""
Registry Loader — Loads symbolic JSON registries from configs/symbolic/.

All symbolic intelligence lives in JSON. Python only orchestrates.
"""

import json
from pathlib import Path
from functools import lru_cache

_REGISTRY_DIR = Path(__file__).resolve().parent.parent / "configs" / "symbolic"


@lru_cache(maxsize=None)
def _load_registry(filename: str) -> list:
    """Load a JSON registry file. Cached after first load."""
    path = _REGISTRY_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_business_archetypes() -> list:
    return _load_registry("business_archetypes.json")


def get_planetary_behaviors() -> list:
    return _load_registry("planetary_behaviors.json")


def get_arbitration_rules() -> list:
    return _load_registry("arbitration_rules.json")


def get_lifecycle_transitions() -> list:
    return _load_registry("lifecycle_transitions.json")


def get_causal_narratives() -> list:
    return _load_registry("causal_narratives.json")


def get_planetary_behavior(planet_name: str) -> dict:
    """Get behavior profile for a specific planet."""
    for entry in get_planetary_behaviors():
        if planet_name in entry.get("planet", ""):
            return entry
    return {}


def get_archetype_by_id(archetype_id: str) -> dict:
    """Get a specific archetype by ID."""
    for entry in get_business_archetypes():
        if entry.get("archetype_id") == archetype_id:
            return entry
    return {}
