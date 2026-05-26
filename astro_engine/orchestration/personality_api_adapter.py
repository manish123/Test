"""
Personality API Adapter — Converts production birth_data_dict into symbolic personality_context.

This is a TEST-repo-only adapter for validation. It does NOT:
- Call OpenAI
- Touch production code
- Modify the existing personality engine
- Generate final narrative text

It DOES:
- Accept the same birth_data_dict format used by production personality_api
- Build the symbolic cognition state via astro_engine
- Produce a personality_context payload matching the orchestration contract
- Return a deterministic, side-effect-free result

Usage:
    from orchestration.personality_api_adapter import build_personality_context
    result = build_personality_context({"date": datetime_ist, "lat": 21.2, "lon": 81.4})
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

# Ensure astro_engine is importable
_ENGINE_ROOT = str(Path(__file__).resolve().parent.parent)
if _ENGINE_ROOT not in sys.path:
    sys.path.insert(0, _ENGINE_ROOT)

from rules.evaluator_base import BaseChartState
from symbolic.coherent_state_builder import build_coherent_state
from orchestration.context_router import route_context
from orchestration.token_budget import estimate_tokens


# ═══════════════════════════════════════════════════════════════
# INPUT NORMALIZATION
# ═══════════════════════════════════════════════════════════════

def _normalize_birth_data(birth_data_dict: dict) -> tuple:
    """
    Normalize production birth_data_dict into (datetime, lat, lon, alt).

    Production format:
        {"date": datetime_IST, "lat": float, "lon": float}

    Also accepts extended format:
        {"date": datetime_IST, "lat": float, "lon": float, "alt": float}

    Returns:
        (birth_dt, lat, lon, alt)
    """
    birth_dt = birth_data_dict["date"]
    lat = float(birth_data_dict["lat"])
    lon = float(birth_data_dict["lon"])
    alt = float(birth_data_dict.get("alt", 0))

    if not isinstance(birth_dt, datetime):
        raise ValueError(f"birth_data_dict['date'] must be a datetime, got {type(birth_dt)}")

    return birth_dt, lat, lon, alt


# ═══════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════

def build_personality_context(birth_data_dict: dict, eval_date: datetime = None) -> dict:
    """
    Build a personality_context payload from a production-format birth_data_dict.

    Parameters
    ----------
    birth_data_dict : dict
        Same format as production personality_api engine_bridge expects:
        {"date": datetime_IST, "lat": float, "lon": float}
    eval_date : datetime, optional
        Evaluation date for lifecycle phase. Defaults to now.

    Returns
    -------
    dict matching the personality_context orchestration contract:
        {identity, behavioral_core, lifecycle, primary_conflicts,
         top_narratives, coherence, _routing, _meta}

    Properties:
    - Deterministic for same input
    - No side effects
    - No OpenAI calls
    - No mutation of input dict
    - Under 600 token budget
    """
    # Normalize input (never mutate the original)
    birth_dt, lat, lon, alt = _normalize_birth_data(birth_data_dict)

    if eval_date is None:
        eval_date = datetime.now()

    # Build chart state
    chart = BaseChartState(birth_dt, lat, lon, alt)

    # Build full coherent symbolic state
    coherent_state = build_coherent_state(chart, eval_date=eval_date)

    # Route to personality_context contract
    payload = route_context(coherent_state, "personality_context")

    return payload


def build_prompt_injection(birth_data_dict: dict, eval_date: datetime = None) -> str:
    """
    Build a compact text block suitable for injecting into an OpenAI prompt.

    This is the string that would be appended to the system or user prompt
    in the production personality_api to enrich the AI narrative.

    Returns a formatted string (NOT JSON — human-readable for LLM consumption).
    """
    ctx = build_personality_context(birth_data_dict, eval_date)

    # Remove routing metadata for the injection
    identity = ctx.get("identity", {})
    behavioral = ctx.get("behavioral_core", {})
    lifecycle = ctx.get("lifecycle", {})
    conflicts = ctx.get("primary_conflicts", [])
    narratives = ctx.get("top_narratives", [])
    coherence = ctx.get("coherence", {})

    lines = []
    lines.append("SYMBOLIC CONTEXT:")
    lines.append(f"- Primary Archetype: {identity.get('primary_archetype', 'unknown')}")
    if identity.get("secondary_archetype"):
        lines.append(f"- Secondary Archetype: {identity['secondary_archetype']}")
    lines.append(f"- Identity Fusion: {identity.get('fusion_type', 'single')}")
    lines.append(f"- Lifecycle Phase: {lifecycle.get('phase', 'unknown')} ({lifecycle.get('stability', '')})")
    lines.append(f"- Direction: {lifecycle.get('direction', 'unknown')}")

    if behavioral.get("leadership"):
        lines.append(f"- Leadership: {behavioral['leadership'][0][:80]}")
    if behavioral.get("risk"):
        lines.append(f"- Risk Style: {behavioral['risk'][0][:80]}")

    if conflicts:
        c = conflicts[0]
        lines.append(f"- Active Conflict: {c.get('type', '')} — {c.get('resolution', '')[:60]}")

    if narratives:
        lines.append(f"- Primary Narrative: {narratives[0].get('cause', '')[:80]}")

    lines.append(f"- Coherence: {coherence.get('score', 0):.2f} ({coherence.get('fragmentation', 'unknown')})")

    return "\n".join(lines)
