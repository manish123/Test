"""
Business Rule Schema Definition (v1.0)

This module defines the JSON Schema for business domain rules.
The schema follows the same pattern as marriage_rule.schema.json but
adapted for business event families.

File layout mirrors:
  rules/domains/relationship/marriage/marriage_rule.schema.json

Usage:
    from rules.domains.business.business_launch.schema import BUSINESS_RULE_SCHEMA
    # Use for validation of rule JSON files
"""

BUSINESS_RULE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://astrolyn.ai/schemas/business_rule.schema.json",
    "title": "BusinessRule",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "rule_id", "name", "domain", "event_family",
        "rule_type", "status", "priority", "conditions", "outputs"
    ],
    "properties": {
        "rule_id": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "source_text": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "work_name": {"type": "string"},
                "chapter": {"type": ["string", "null"]},
                "verse": {"type": ["string", "null"]},
                "page": {"type": ["string", "null"]},
                "quote": {"type": ["string", "null"]},
            },
        },
        "domain": {"type": "string", "enum": ["business"]},
        "event_family": {
            "type": "string",
            "enum": [
                "business_launch", "business_expansion", "business_closure",
                "business_partnership", "profit_growth", "speculative_business",
                "funding", "scaling",
            ],
        },
        "event_subtype": {"type": "array", "items": {"type": "string"}},
        "rule_type": {
            "type": "string",
            "enum": [
                "dasha", "transit", "fast_trigger", "classical_pattern",
                "compound", "yoga", "house_activation", "d9", "combination",
            ],
        },
        "status": {"type": "string", "enum": ["active", "experimental", "calibration", "deprecated"]},
        "priority": {"type": "integer", "minimum": 1, "maximum": 100},
        "polarity": {"type": "string", "enum": ["supportive", "neutral", "challenging", "mixed"]},
        "timing_band": {"type": "string", "enum": ["broad", "medium", "exact", "none"]},
        "conditions": {
            "type": "object",
            "required": ["all_of"],
            "properties": {
                "all_of": {"type": "array"},
                "any_of": {"type": "array"},
                "none_of": {"type": "array"},
            },
        },
        "signals": {
            "type": "object",
            "properties": {
                "dasha": {"type": "array", "items": {"type": "string"}},
                "transit": {"type": "array", "items": {"type": "string"}},
                "houses": {"type": "array", "items": {"type": "string"}},
                "planets": {"type": "array", "items": {"type": "string"}},
                "nakshatra": {"type": "array", "items": {"type": "string"}},
                "d9": {"type": "array", "items": {"type": "string"}},
                "sensitive_points": {"type": "array", "items": {"type": "string"}},
            },
        },
        "window": {
            "type": "object",
            "properties": {
                "broad_window_days": {"type": "integer", "minimum": 0},
                "exact_window_days": {"type": "integer", "minimum": 0},
                "confidence_decay_days": {"type": "integer", "minimum": 0},
            },
        },
        "weights": {
            "type": "object",
            "properties": {
                "dasha_weight": {"type": "number"},
                "transit_weight": {"type": "number"},
                "fast_trigger_weight": {"type": "number"},
                "classical_weight": {"type": "number"},
            },
        },
        "interpretation": {
            "type": "object",
            "properties": {
                "meaning": {"type": "string"},
                "mode": {"type": "string"},
                "quality": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
        },
        "outputs": {
            "type": "object",
            "required": ["symbolic_label", "likelihood_band", "timing_band"],
            "properties": {
                "symbolic_label": {"type": "string"},
                "likelihood_band": {"type": "string", "enum": ["very_low", "low", "moderate", "high", "very_high"]},
                "timing_band": {"type": "string", "enum": ["broad", "narrow", "exact"]},
                "recommended_action": {"type": "string"},
            },
        },
        "metadata": {"type": "object", "additionalProperties": True},
        "notes": {"type": "string"},
    },
    "condition_kinds": [
        "dasha_lord", "antardasha_lord", "house_lord", "planet_in_house",
        "planet_aspect", "planet_dignity", "planet_conjunction",
        "transit_house", "transit_aspect", "transit_conjunction",
        "navamsa_house", "navamsa_lagna", "navamsa_lord", "parivartana",
        "relative_position", "nakshatra", "nakshatra_from_moon",
        "age_pattern", "sensitive_point", "yoga_active",
        "house_lord_position", "malefic_association",
    ],
    "condition_operators": [
        "equals", "in", "not_in", "overlaps", "within_orb",
        "aspecting", "conjunct", "trine", "square", "opposite",
        "kendra_from", "trikona_from", "is_strong", "is_weak",
        "is_exalted", "is_own_sign", "is_moolatrikona", "has_exchange",
    ],
}
