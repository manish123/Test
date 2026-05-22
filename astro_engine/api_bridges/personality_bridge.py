"""
Personality API Bridge — Domain-aware engine wrapper for personality_api.

Uses run_pipeline() (typed pipeline path) instead of _run_single().
Parity verified: 5 dates × 2 configs = 10/10 exact match.

This bridge:
- Receives birth data from the personality API router
- Runs the personality engine via pipeline (natal chart — Mode A)
- Extracts the neutral SymbolicResult
- Applies domain="general_life" interpreter (personality is not domain-specific)
- Returns personality profile + general life symbolic context

The personality API uses domain="general_life" because:
- Personality is WHO YOU ARE, not what you should do
- It should NEVER be colored by trading bias
- General life provides balanced, neutral framing
"""

from __future__ import annotations

import logging
import os
import sys
import traceback
from typing import Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class EngineError(Exception):
    """Raised when personality engine fails."""
    pass


def get_personality_data(
    birth_data_dict: dict,
    domain: str = "general_life",
) -> dict:
    """
    Compute personality profile with domain-neutral interpretation via pipeline.

    Args:
        birth_data_dict: {"date": datetime (IST), "lat": float, "lon": float}
        domain: interpretation lens (default: "general_life")

    Returns:
        dict with:
            "personality_profile": natal personality data
            "symbolic_state": neutral symbolic conditions
            "domain_reading": domain-interpreted context
            "domain": which domain was applied
            "decision": engine decision dict (for natal chart)

    Raises:
        EngineError on failure
    """
    try:
        return _compute_with_domain(birth_data_dict, domain)
    except Exception as exc:
        logger.error(
            "Personality engine (domain=%s) failed for birth_data=%s\n%s",
            domain,
            {k: str(v) for k, v in birth_data_dict.items()},
            traceback.format_exc(),
        )
        raise EngineError(f"Personality computation failed (domain={domain}).") from exc


def _compute_with_domain(birth_data_dict: dict, domain: str) -> dict:
    """
    Internal: run pipeline at birth date → extract symbolic state → apply domain.
    """
    from pipeline import run_astronomy, run_features, run_rules, run_decisions
    from rules.symbolic.planetary_conditions import build_symbolic_state
    from rules.domains import get_domain_interpreter

    # Personality is natal — evaluated at birth date, never changes
    birth_dt = birth_data_dict["date"]

    config = {
        "governance_profile": "personal",
        "use_trading_gate": False,
        "use_trading_event_filter": False,
        "use_nakshatra_rulebook_bias": False,
    }

    # Run pipeline
    astro = run_astronomy(birth_dt, birth_data_dict)
    features = run_features(astro, birth_data_dict, birth_dt)
    rule_output = run_rules(features, birth_data_dict, birth_dt, config)
    decision = run_decisions(rule_output, config)

    # Extract personality profile from rule output
    personality_profile = rule_output.get("personality_profile", {})

    # Build legacy-compatible dict for symbolic state extraction
    legacy_compat = {
        "planets": rule_output["planets"],
        "yoga": rule_output["yoga"],
        "tara": {
            "score": rule_output["tara_score"],
            "raw_score": rule_output["tara_raw_score"],
            "rulebook_action": rule_output["rulebook_action"],
            "rulebook_reason": rule_output["rulebook_reason"],
        },
        "moorthy": {"grade": rule_output["moorthy_grade"], "factor": rule_output["moorthy_factor"]},
        "nodes": {"kala_sarpa": rule_output["kala_sarpa"], "kala_sarpa_type": rule_output["kala_sarpa_type"]},
        "dasha": {"md": rule_output["dasha"], "ad": rule_output["antardasha"], "sandhi": features.dasha.sandhi_active},
        "risk_context": rule_output["risk_context"],
    }

    # Extract neutral symbolic state (Layer C1)
    symbolic_state = build_symbolic_state(legacy_compat)

    # Apply domain interpreter (Layer C2)
    interpreter = get_domain_interpreter(domain)
    domain_reading = interpreter.interpret(symbolic_state)

    return {
        "personality_profile": personality_profile,
        "symbolic_state": symbolic_state,
        "domain_reading": domain_reading,
        "domain": domain,
        "decision": decision,
    }
