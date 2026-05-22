"""
Timing API Bridge — Domain-aware engine wrapper for timing_api.

Uses run_pipeline() (typed pipeline path) instead of _run_single().
Parity verified: 5 dates × 2 configs = 10/10 exact match.

This bridge:
- Receives birth data + evaluation date from the timing API router
- Runs the engine via pipeline (astronomy → features → rules → decisions)
- Extracts the neutral SymbolicResult
- Applies the CORRECT domain interpreter based on the endpoint
- Returns domain-interpreted reading alongside engine decision
"""

from __future__ import annotations

import logging
import os
import sys
import traceback
from datetime import date, datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class EngineError(Exception):
    """Raised when engine computation fails."""
    pass


def get_timing_data(
    birth_data_dict: dict,
    evaluation_date: date,
    domain: str = "career",
) -> dict:
    """
    Compute timing data with domain-specific interpretation via pipeline.

    Args:
        birth_data_dict: {"date": datetime (IST), "lat": float, "lon": float}
        evaluation_date: date object
        domain: "trading" | "career" (default: "career")

    Returns:
        dict with:
            "decision": engine decision dict (action, confidence, risk, etc.)
            "symbolic_state": neutral symbolic conditions (dict)
            "domain_reading": domain-interpreted reading (dict)
            "domain": which domain was applied
            "rule_output": full rule pipeline output for downstream use

    Raises:
        EngineError on failure
    """
    try:
        return _compute_with_domain(birth_data_dict, evaluation_date, domain)
    except Exception as exc:
        logger.error(
            "Timing engine (domain=%s) failed for birth_data=%s eval=%s\n%s",
            domain,
            {k: str(v) for k, v in birth_data_dict.items()},
            evaluation_date,
            traceback.format_exc(),
        )
        raise EngineError(f"Timing computation failed (domain={domain}).") from exc


def _compute_with_domain(birth_data_dict: dict, evaluation_date: date, domain: str) -> dict:
    """
    Internal: run pipeline → extract symbolic state → apply domain interpreter.
    """
    from pipeline import run_astronomy, run_features, run_rules, run_decisions
    from rules.symbolic.planetary_conditions import build_symbolic_state
    from rules.domains import get_domain_interpreter

    # Build evaluation datetime (9:15 IST market open)
    eval_dt = datetime(evaluation_date.year, evaluation_date.month, evaluation_date.day, 9, 15)

    # Configure based on domain
    config = {
        "use_trading_gate": (domain == "trading"),
        "trading_gate_profile": "adaptive_lite_plus" if domain == "trading" else "strict",
        "use_trading_event_filter": (domain == "trading"),
        "use_nakshatra_rulebook_bias": (domain == "trading"),
        "use_asset_timeline_events": (domain == "trading"),
        "governance_profile": "professional",
    }

    # Run pipeline stages
    astro = run_astronomy(eval_dt, birth_data_dict)
    features = run_features(astro, birth_data_dict, eval_dt)
    rule_output = run_rules(features, birth_data_dict, eval_dt, config)
    decision = run_decisions(rule_output, config)

    # Build a legacy-compatible result dict for symbolic state extraction
    # (build_symbolic_state expects the _run_single output shape)
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

    # Apply domain-specific interpretation (Layer C2)
    interpreter = get_domain_interpreter(domain)
    domain_reading = interpreter.interpret(symbolic_state)

    return {
        "decision": decision,
        "symbolic_state": symbolic_state,
        "domain_reading": domain_reading,
        "domain": domain,
        "rule_output": rule_output,
    }
