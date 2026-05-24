"""
Financial Crisis & Debt Event Pack — 5-Layer Semantic Architecture

File layout:
  rules/domains/finance/financial_crisis_and_debt/
    ARCHITECTURE.md                       — 5-layer design document
    financial_crisis_rule.schema.json     — Validation schema
    dasha_rules.json                      — Layer 1: Planetary period gates
    transit_rules.json                    — Layer 2: Slow planet activation
    fast_trigger_rules.json               — Layer 3: Fast planet exact timing
    classical_patterns.json               — Layer 4: Structural birth chart patterns
    outcome_quality.json                  — Layer 5: Financial crisis classification
    calibration_schema.json               — Schema for calibration overlay
    calibration_overlay.json              — Empirical tuning

Logic flow:
  Dasha rule fires -> broad financial crisis window opens
  Transit rule fires -> window becomes active/narrow
  Fast trigger fires -> exact timing narrowed to TARGET_DAY
  Classical pattern -> modifies confidence (natal debt/poverty yoga)
  Outcome/quality -> classifies event (bankruptcy/asset_seizure/speculative_collapse/chronic_debt)
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
    """Layer 1: Broad timing — Mahadasha/Antardasha gates for financial crisis."""
    return _load_json("dasha_rules.json")


def get_transit_rules():
    """Layer 2: Medium timing — Saturn/Jupiter/Rahu transit activation."""
    return _load_json("transit_rules.json")


def get_fast_trigger_rules():
    """Layer 3: Exact timing — Mars Nakshatra/Sanghatika/Vinasha pinpointing."""
    return _load_json("fast_trigger_rules.json")


def get_classical_patterns():
    """Layer 4: Structural — Natal poverty/debt yoga patterns."""
    return _load_json("classical_patterns.json")


def get_outcome_quality():
    """Layer 5: Classification — Financial crisis mode/quality."""
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
