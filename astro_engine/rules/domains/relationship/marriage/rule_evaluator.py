"""
Generic Rule Evaluator — Data-driven rule engine for marriage (and future event packs).

Loads JSON rule files and evaluates them against a chart_state dict.
Returns a list of fired rules with their outputs and match details.

This evaluator is GENERIC — it works for any event pack that follows
the marriage_rule.schema.json format. The same engine will later be
reused for childbirth, career_switch, business_launch, relocation, etc.

Usage:
    from rules.domains.relationship.marriage.rule_evaluator import evaluate_marriage_rules

    chart_state = {
        "dasha_md": "Jupiter",
        "dasha_ad": "Sun",
        "seventh_lord": "Jupiter",
        "second_lord": "Moon",
        "lagna_lord": "Mercury",
        "planets_in_house": {7: [], 2: ["Moon"], 11: ["Mercury"]},
        "transit_jupiter_house": 12,
        "transit_saturn_house": 9,
        "transit_moon_house": 1,
        "transit_mars_house": 10,
        "transit_jupiter_aspecting": [4, 6, 8],  # houses Jupiter aspects
        "transit_saturn_aspecting": [11, 3, 6],  # houses Saturn aspects
        "jupiter_longitude": 88.04,
        "sensitive_points": {"lagna_lord_plus_7th_lord_point": 84.75},
    }

    results = evaluate_marriage_rules(chart_state)
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path


# ═══════════════════════════════════════════════════════════════
# RULE LOADING
# ═══════════════════════════════════════════════════════════════

_RULES_DIR = Path(__file__).parent


def load_rules(rule_file: str) -> List[Dict[str, Any]]:
    """Load rules from a JSON file in the marriage rules directory."""
    filepath = _RULES_DIR / rule_file
    if not filepath.exists():
        return []
    with open(filepath, "r") as f:
        return json.load(f)


def load_all_marriage_rules() -> List[Dict[str, Any]]:
    """Load all active marriage rules from all JSON files."""
    all_rules = []
    for filename in ["dasha_rules.json", "transit_rules.json", "fast_trigger_rules.json"]:
        rules = load_rules(filename)
        all_rules.extend(rules)
    # Sort by priority (highest first)
    all_rules.sort(key=lambda r: r.get("priority", 50), reverse=True)
    return all_rules


# ═══════════════════════════════════════════════════════════════
# CONDITION EVALUATION
# ═══════════════════════════════════════════════════════════════

def _resolve_symbolic_value(value, chart_state: Dict[str, Any]):
    """
    Resolve symbolic references like "7th_lord", "2nd_lord", "lagna_lord"
    to their actual planet names from chart_state.
    """
    if isinstance(value, str):
        mapping = {
            "7th_lord": chart_state.get("seventh_lord"),
            "2nd_lord": chart_state.get("second_lord"),
            "lagna_lord": chart_state.get("lagna_lord"),
            "Venus": "Venus",
            "Jupiter": "Jupiter",
            "Saturn": "Saturn",
            "Mars": "Mars",
            "Moon": "Moon",
            "Sun": "Sun",
            "Mercury": "Mercury",
            "Rahu": "Rahu",
            "Ketu": "Ketu",
        }
        return mapping.get(value, value)
    if isinstance(value, list):
        return [_resolve_symbolic_value(v, chart_state) for v in value]
    return value


def _evaluate_single_condition(condition: Dict[str, Any], chart_state: Dict[str, Any]) -> bool:
    """
    Evaluate a single condition against the chart state.

    Returns True if the condition is met, False otherwise.
    """
    kind = condition["kind"]
    operator = condition["operator"]
    raw_value = condition["value"]
    value = _resolve_symbolic_value(raw_value, chart_state)
    orb = condition.get("orb_degrees", 5.0)

    # ── DASHA CONDITIONS ──────────────────────────────────────────────────────
    if kind == "dasha_lord":
        actual = chart_state.get("dasha_md")
        if operator == "equals":
            return actual == value
        if operator == "in":
            return actual in value if isinstance(value, list) else actual == value

    if kind == "antardasha_lord":
        actual = chart_state.get("dasha_ad")
        if operator == "equals":
            return actual == value
        if operator == "in":
            return actual in value if isinstance(value, list) else actual == value

    # ── HOUSE CONDITIONS ──────────────────────────────────────────────────────
    if kind == "planet_in_house":
        planets_in_house = chart_state.get("planets_in_house", {})
        if operator == "equals":
            # Check if value (planet name) is in any relevant house
            for house, planets in planets_in_house.items():
                if value in planets:
                    return True
            return False
        if operator == "in":
            # Check if any of the listed houses have planets
            if isinstance(value, list):
                for house in value:
                    if planets_in_house.get(house):
                        return True
            return False

    if kind == "house_lord":
        # Check if dasha/antardasha lord rules specific houses
        if operator == "in" and isinstance(value, list):
            md = chart_state.get("dasha_md")
            ad = chart_state.get("dasha_ad")
            house_lords = chart_state.get("house_lords", {})
            for house in value:
                lord = house_lords.get(house)
                if lord and (lord == md or lord == ad):
                    return True
            return False

    # ── TRANSIT CONDITIONS ────────────────────────────────────────────────────
    if kind == "transit_house":
        if operator == "in":
            # Check if Jupiter or Saturn is transiting the listed houses
            jup_house = chart_state.get("transit_jupiter_house")
            sat_house = chart_state.get("transit_saturn_house")
            moon_house = chart_state.get("transit_moon_house")
            mars_house = chart_state.get("transit_mars_house")
            if isinstance(value, list):
                return (jup_house in value or sat_house in value or
                        moon_house in value or mars_house in value)
            return False
        if operator == "aspecting":
            # Check if Jupiter or Saturn aspects the resolved target
            target = value
            jup_aspects = chart_state.get("transit_jupiter_aspecting", [])
            sat_aspects = chart_state.get("transit_saturn_aspecting", [])
            # If target is a planet name, check if it's aspected
            aspected_planets = chart_state.get("planets_aspected_by_transit", {})
            if target in aspected_planets:
                return True
            # If target is a house number
            if isinstance(target, int):
                return target in jup_aspects or target in sat_aspects
            return False

    if kind == "transit_aspect":
        if operator == "equals":
            # Check if a specific planet is transiting
            transit_planets = chart_state.get("active_transit_planets", [])
            return value in transit_planets
        if operator == "conjunct":
            # Check if value planet is in conjunction with marriage significators
            conjunctions = chart_state.get("transit_conjunctions", [])
            return value in conjunctions
        if operator == "trine":
            # Check trine aspect
            trine_targets = chart_state.get("transit_trines", {})
            return value in trine_targets

    # ── PLANET ASPECT CONDITIONS ──────────────────────────────────────────────
    if kind == "planet_aspect":
        if operator == "equals":
            active_aspects = chart_state.get("active_planet_aspects", [])
            return value in active_aspects
        if operator == "in":
            active_aspects = chart_state.get("active_planet_aspects", [])
            if isinstance(value, list):
                return any(v in active_aspects for v in value)

    # ── NAVAMSA CONDITIONS ────────────────────────────────────────────────────
    if kind == "navamsa_house":
        if operator == "in":
            d9_activated_houses = chart_state.get("d9_activated_houses", [])
            if isinstance(value, list):
                return any(h in d9_activated_houses for h in value)

    if kind == "navamsa_lagna":
        d9_lagna_activated = chart_state.get("d9_lagna_activated", False)
        return d9_lagna_activated

    # ── MATHEMATICAL POINT CONDITIONS ─────────────────────────────────────────
    if kind == "mathematical_point":
        sensitive_points = chart_state.get("sensitive_points", {})
        jupiter_lon = chart_state.get("jupiter_longitude", 0)

        if isinstance(raw_value, str) and raw_value in sensitive_points:
            target_lon = sensitive_points[raw_value]

            if operator == "within_orb":
                distance = abs((jupiter_lon - target_lon + 180) % 360 - 180)
                return distance <= orb
            if operator == "trine":
                trine_1 = (target_lon + 120) % 360
                trine_2 = (target_lon + 240) % 360
                d1 = abs((jupiter_lon - trine_1 + 180) % 360 - 180)
                d2 = abs((jupiter_lon - trine_2 + 180) % 360 - 180)
                return min(d1, d2) <= orb
            if operator == "opposite":
                opp = (target_lon + 180) % 360
                distance = abs((jupiter_lon - opp + 180) % 360 - 180)
                return distance <= orb

    # ── DARAKARAKA ────────────────────────────────────────────────────────────
    if kind == "darakaraka":
        dk = chart_state.get("darakaraka")
        if operator == "equals":
            return dk == value

    # ── DEFAULT: condition type not implemented ───────────────────────────────
    return False


def _evaluate_condition_group(conditions: List[Dict], chart_state: Dict, mode: str = "all") -> bool:
    """
    Evaluate a group of conditions.
    mode="all" → all must pass (AND)
    mode="any" → at least one must pass (OR)
    mode="none" → none must pass (NOT)
    """
    if not conditions:
        if mode == "none":
            return True  # no exclusions = passes
        if mode == "any":
            return True  # empty any_of = no requirement
        return True  # empty all_of = passes vacuously

    results = [_evaluate_single_condition(c, chart_state) for c in conditions]

    if mode == "all":
        return all(results)
    if mode == "any":
        return any(results)
    if mode == "none":
        return not any(results)
    return False


# ═══════════════════════════════════════════════════════════════
# RULE EVALUATION
# ═══════════════════════════════════════════════════════════════

def evaluate_rule(rule: Dict[str, Any], chart_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Evaluate a single rule against chart state.

    Returns:
        dict with rule output if fired, None if not fired.
    """
    # Skip non-active rules
    if rule.get("status") not in ("active", "experimental"):
        return None

    conditions = rule.get("conditions", {})

    # Evaluate all_of (required — must ALL pass)
    all_of = conditions.get("all_of", [])
    if not _evaluate_condition_group(all_of, chart_state, mode="all"):
        return None

    # Evaluate any_of (at least one must pass, if present)
    any_of = conditions.get("any_of", [])
    if any_of and not _evaluate_condition_group(any_of, chart_state, mode="any"):
        return None

    # Evaluate none_of (none must pass)
    none_of = conditions.get("none_of", [])
    if none_of and not _evaluate_condition_group(none_of, chart_state, mode="none"):
        return None

    # Rule fired — return output
    return {
        "rule_id": rule["rule_id"],
        "name": rule["name"],
        "rule_type": rule["rule_type"],
        "priority": rule.get("priority", 50),
        "polarity": rule.get("polarity", "neutral"),
        "outputs": rule.get("outputs", {}),
        "window": rule.get("window", {}),
        "weights": rule.get("weights", {}),
    }


def evaluate_marriage_rules(chart_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate ALL marriage rules against the current chart state.

    Args:
        chart_state: dict with current planetary/dasha/transit state

    Returns:
        dict with:
            "fired_rules": list of fired rule outputs (sorted by priority)
            "dasha_fired": rules of type dasha/compound that fired
            "transit_fired": rules of type transit that fired
            "fast_trigger_fired": rules of type fast_trigger that fired
            "highest_likelihood": best likelihood_band achieved
            "best_timing": most precise timing_band achieved
            "composite_signal": NO_SIGNAL | BROAD_WINDOW | NARROW_WINDOW | TARGET_DAY
            "total_fired": count of fired rules
    """
    all_rules = load_all_marriage_rules()
    fired = []

    for rule in all_rules:
        result = evaluate_rule(rule, chart_state)
        if result:
            fired.append(result)

    # Classify fired rules by type
    dasha_fired = [r for r in fired if r["rule_type"] in ("dasha", "compound")]
    transit_fired = [r for r in fired if r["rule_type"] == "transit"]
    fast_trigger_fired = [r for r in fired if r["rule_type"] == "fast_trigger"]

    # Determine highest likelihood band
    band_order = ["very_low", "low", "moderate", "high", "very_high"]
    highest_likelihood = "very_low"
    for r in fired:
        band = r["outputs"].get("likelihood_band", "very_low")
        if band_order.index(band) > band_order.index(highest_likelihood):
            highest_likelihood = band

    # Determine best timing precision
    timing_order = ["broad", "narrow", "exact"]
    best_timing = "broad"
    for r in fired:
        timing = r["outputs"].get("timing_band", "broad")
        if timing in timing_order and timing_order.index(timing) > timing_order.index(best_timing):
            best_timing = timing

    # Composite signal determination
    if not fired:
        composite_signal = "NO_SIGNAL"
    elif fast_trigger_fired and (dasha_fired or transit_fired):
        composite_signal = "TARGET_DAY"
    elif transit_fired and dasha_fired:
        composite_signal = "NARROW_WINDOW"
    elif dasha_fired or transit_fired:
        composite_signal = "BROAD_WINDOW"
    else:
        composite_signal = "WEAK_SIGNAL"

    return {
        "fired_rules": fired,
        "dasha_fired": dasha_fired,
        "transit_fired": transit_fired,
        "fast_trigger_fired": fast_trigger_fired,
        "highest_likelihood": highest_likelihood,
        "best_timing": best_timing,
        "composite_signal": composite_signal,
        "total_fired": len(fired),
    }
