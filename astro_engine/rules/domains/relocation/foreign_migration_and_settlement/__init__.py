"""Foreign Migration & Settlement Event Pack — 5-Layer Semantic Architecture"""
import json, os
_DIR = os.path.dirname(os.path.abspath(__file__))
def _load_json(filename):
    with open(os.path.join(_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)
def get_dasha_rules(): return _load_json("dasha_rules.json")
def get_transit_rules(): return _load_json("transit_rules.json")
def get_fast_trigger_rules(): return _load_json("fast_trigger_rules.json")
def get_classical_patterns(): return _load_json("classical_patterns.json") if os.path.exists(os.path.join(_DIR, "classical_patterns.json")) else []
def get_outcome_quality(): return _load_json("outcome_quality.json") if os.path.exists(os.path.join(_DIR, "outcome_quality.json")) else []
def get_calibration_overlay(): return _load_json("calibration_overlay.json")
def get_all_rules():
    rules = get_dasha_rules() + get_transit_rules() + get_fast_trigger_rules() + get_classical_patterns() + get_outcome_quality()
    return rules
