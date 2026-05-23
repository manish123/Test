"""
Business Launch Event Pack — Rule definitions for business timing.

File layout (mirrors marriage event pack pattern):
  rules/domains/business/business_launch/
    schema.py              — JSON Schema definition (as Python dict)
    dasha_rules.py         — Broad timing: Mahadasha/Antardasha combinations
    transit_rules.py       — Medium timing: Jupiter/Saturn transits
    fast_trigger_rules.py  — Exact timing: Moon/Mars Nakshatra triggers
    classical_patterns.py  — Natal promise: yogas, house activations, D9

Logic flow:
  Dasha rule fires → broad business window opens
  Transit rule fires → window becomes active/narrow
  Fast trigger fires → exact timing narrowed to TARGET_DAY
  Decision layer → outputs BROAD_WINDOW / NARROW_WINDOW / TARGET_DAY
"""

from rules.domains.business.business_launch.dasha_rules import DASHA_RULES
from rules.domains.business.business_launch.transit_rules import TRANSIT_RULES
from rules.domains.business.business_launch.fast_trigger_rules import FAST_TRIGGER_RULES
from rules.domains.business.business_launch.classical_patterns import CLASSICAL_PATTERNS

ALL_BUSINESS_RULES = DASHA_RULES + TRANSIT_RULES + FAST_TRIGGER_RULES + CLASSICAL_PATTERNS

__all__ = [
    "DASHA_RULES",
    "TRANSIT_RULES",
    "FAST_TRIGGER_RULES",
    "CLASSICAL_PATTERNS",
    "ALL_BUSINESS_RULES",
]
