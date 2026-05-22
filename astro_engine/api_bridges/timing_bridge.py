"""
Timing API Bridge — Domain-aware engine wrapper for timing_api.

This bridge:
- Receives birth data + evaluation date from the timing API router
- Runs the engine (legacy _run_single or pipeline)
- Extracts the neutral SymbolicResult
- Applies the CORRECT domain interpreter based on the endpoint:
    /timing (career/money) → domain="career" or domain="trading"
    /horizon              → domain="career" (multi-horizon predictions)
- Returns domain-interpreted reading alongside raw engine data

The timing API NEVER interprets planetary meaning directly.
All meaning comes from the domain interpreter.
"""

from __future__ import annotations

import logging
import os
import sys
import traceback
from datetime import date, datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ── sys.path setup ────────────────────────────────────────────────────────────
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
    Compute timing data with domain-specific interpretation.

    Args:
        birth_data_dict: {"date": datetime (IST), "lat": float, "lon": float}
        evaluation_date: date object
        domain: "trading" | "career" (default: "career")

    Returns:
        dict with:
            "engine_result": raw engine output (legacy format)
            "symbolic_state": neutral symbolic conditions (dict)
            "domain_reading": domain-interpreted reading (dict)
            "domain": which domain was applied

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
    Internal: run engine → extract symbolic state → apply domain interpreter.
    """
    from main import _run_single
    from rules.symbolic.planetary_conditions import build_symbolic_state
    from rules.domains import get_domain_interpreter

    # Build evaluation datetime (9:15 IST market open)
    eval_dt = datetime(evaluation_date.year, evaluation_date.month, evaluation_date.day, 9, 15)

    # Run the legacy engine (full production logic)
    engine_result = _run_single(
        date=eval_dt,
        birth_data=birth_data_dict,
        use_trading_gate=(domain == "trading"),
        trading_gate_profile="adaptive_lite_plus" if domain == "trading" else "strict",
        use_trading_event_filter=(domain == "trading"),
        use_nakshatra_rulebook_bias=(domain == "trading"),
        use_asset_timeline_events=(domain == "trading"),
    )

    # Extract neutral symbolic state (Layer C1)
    symbolic_state = build_symbolic_state(engine_result)

    # Apply domain-specific interpretation (Layer C2)
    interpreter = get_domain_interpreter(domain)
    domain_reading = interpreter.interpret(symbolic_state)

    return {
        "engine_result": engine_result,
        "symbolic_state": symbolic_state,
        "domain_reading": domain_reading,
        "domain": domain,
    }
