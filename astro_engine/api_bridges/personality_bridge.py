"""
Personality API Bridge — Domain-aware engine wrapper for personality_api.

This bridge:
- Receives birth data from the personality API router
- Runs the personality engine (Mode A — natal chart only)
- Extracts the neutral SymbolicResult for the natal chart
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

# ── sys.path setup ────────────────────────────────────────────────────────────
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
    Compute personality profile with domain-neutral interpretation.

    Args:
        birth_data_dict: {"date": datetime (IST), "lat": float, "lon": float}
        domain: interpretation lens (default: "general_life")
                Can be overridden for specialized personality readings:
                - "general_life": balanced, neutral (default)
                - "career": personality through professional lens
                - "relationship": personality through partnership lens
                - "spirituality": personality through spiritual lens

    Returns:
        dict with:
            "personality_profile": natal personality data (atmakaraka, guna, etc.)
            "symbolic_state": neutral symbolic conditions for birth chart
            "domain_reading": domain-interpreted life context
            "domain": which domain was applied

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
    Internal: run personality engine → extract symbolic state → apply domain interpreter.
    """
    from main import _run_single
    from rules.symbolic.planetary_conditions import build_symbolic_state
    from rules.domains import get_domain_interpreter

    # Run engine at birth date (personality is natal — fixed, never changes)
    birth_dt = birth_data_dict["date"]
    engine_result = _run_single(
        date=birth_dt,
        birth_data=birth_data_dict,
        governance_profile="personal",
        use_trading_gate=False,         # NEVER apply trading gate to personality
        use_trading_event_filter=False,  # NEVER filter by trading relevance
        use_nakshatra_rulebook_bias=False,
    )

    # Extract personality profile
    personality_profile = engine_result.get("personality_profile", {})

    # Extract neutral symbolic state (Layer C1)
    symbolic_state = build_symbolic_state(engine_result)

    # Apply domain-specific interpretation (Layer C2)
    interpreter = get_domain_interpreter(domain)
    domain_reading = interpreter.interpret(symbolic_state)

    return {
        "personality_profile": personality_profile,
        "symbolic_state": symbolic_state,
        "domain_reading": domain_reading,
        "domain": domain,
    }
