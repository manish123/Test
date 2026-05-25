"""
Wealth, Financial Gain & Accumulation Event Pack — 5-Layer Semantic Architecture

File layout:
  rules/domains/finance/wealth_financial_gain_and_accumulation/
    ARCHITECTURE.md               — 5-layer design document
    wealth_rule.schema.json       — Validation schema
    dasha_rules.json              — Layer 1: Planetary period gates
    transit_rules.json            — Layer 2: Slow planet activation
    fast_trigger_rules.json       — Layer 3: Fast planet exact timing
    classical_patterns.json       — Layer 4: Structural birth chart patterns
    outcome_quality.json          — Layer 5: Event classification
    calibration_schema.json       — Schema for calibration overlay
    calibration_overlay.json      — Empirical tuning

Logic flow:
  Dasha rule fires -> broad window opens
  Transit rule fires -> window becomes active/narrow
  Fast trigger fires -> exact timing narrowed to TARGET_DAY
  Classical pattern -> modifies confidence (natal promise)
  Outcome/quality -> classifies event type/mode/quality
  Decision layer -> outputs BROAD_WINDOW / NARROW_WINDOW / TARGET_DAY
"""

import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_json(filename):
    """Load a JSON rule file from this directory."""
    filepath = os.path.join(_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_dasha_rules():
    """Layer 1: Broad timing — Mahadasha/Antardasha gates."""
    return _load_json("dasha_rules.json")


def get_transit_rules():
    """Layer 2: Medium timing — Jupiter/Saturn transit activation."""
    return _load_json("transit_rules.json")


def get_fast_trigger_rules():
    """Layer 3: Exact timing — Moon/Mars Nakshatra pinpointing."""
    return _load_json("fast_trigger_rules.json")


def get_classical_patterns():
    """Layer 4: Structural — Natal promise patterns."""
    return _load_json("classical_patterns.json")


def get_outcome_quality():
    """Layer 5: Classification — Event type/mode/quality."""
    return _load_json("outcome_quality.json")


def get_calibration_overlay():
    """Empirical calibration overlay for weight/threshold adjustments."""
    return _load_json("calibration_overlay.json")


def get_all_rules():
    """Load all 5 layers concatenated into a single list."""
    return (
        get_dasha_rules()
        + get_transit_rules()
        + get_fast_trigger_rules()
        + get_classical_patterns()
        + get_outcome_quality()
    )


__all__ = [
    "get_dasha_rules",
    "get_transit_rules",
    "get_fast_trigger_rules",
    "get_classical_patterns",
    "get_outcome_quality",
    "get_calibration_overlay",
    "get_all_rules",
]
