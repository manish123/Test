"""
Career API Adapter — Converts production birth_data_dict into symbolic career/business payloads.

TEST-repo-only. Does NOT call OpenAI or touch production code.

Produces:
- build_career_context(birth_data_dict, eval_date) → career_context payload (≤500 tokens)
- build_business_context(birth_data_dict, eval_date) → extended business payload (≤550 tokens)
- build_career_prompt_injection(birth_data_dict, eval_date) → compact text for LLM prompt
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

_ENGINE_ROOT = str(Path(__file__).resolve().parent.parent)
if _ENGINE_ROOT not in sys.path:
    sys.path.insert(0, _ENGINE_ROOT)

from rules.evaluator_base import BaseChartState
from symbolic.coherent_state_builder import build_coherent_state
from symbolic.symbolic_state_engine import build_symbolic_state
from orchestration.context_router import route_context
from orchestration.token_budget import estimate_tokens, enforce_budget


def _normalize(birth_data_dict: dict) -> tuple:
    """Normalize production birth_data_dict → (datetime, lat, lon, alt)."""
    birth_dt = birth_data_dict["date"]
    lat = float(birth_data_dict["lat"])
    lon = float(birth_data_dict["lon"])
    alt = float(birth_data_dict.get("alt", 0))
    if not isinstance(birth_dt, datetime):
        raise ValueError(f"birth_data_dict['date'] must be datetime, got {type(birth_dt)}")
    return birth_dt, lat, lon, alt


def build_career_context(birth_data_dict: dict, eval_date: datetime = None) -> dict:
    """
    Build a career_context payload (≤500 tokens).

    Contains: identity (archetype + fusion), economic style, leadership signature,
    lifecycle phase + direction, and optional conflicts/narratives.
    """
    birth_dt, lat, lon, alt = _normalize(birth_data_dict)
    if eval_date is None:
        eval_date = datetime.now()

    chart = BaseChartState(birth_dt, lat, lon, alt)
    coherent_state = build_coherent_state(chart, eval_date=eval_date)
    return route_context(coherent_state, "career_context")


def build_business_context(birth_data_dict: dict, eval_date: datetime = None) -> dict:
    """
    Build an extended business context payload (≤550 tokens).

    Includes everything in career_context PLUS:
    - Scaling style from archetype
    - Collapse/failure vectors
    - Wealth behavior
    - Partnership style
    - Suppression/amplification vectors
    """
    birth_dt, lat, lon, alt = _normalize(birth_data_dict)
    if eval_date is None:
        eval_date = datetime.now()

    chart = BaseChartState(birth_dt, lat, lon, alt)
    raw_state = build_symbolic_state(chart, eval_date=eval_date)
    coherent_state = build_coherent_state(chart, eval_date=eval_date)

    # Start with career_context base
    career_base = route_context(coherent_state, "career_context")

    # Enrich with business-specific fields from raw symbolic state
    archetypes = raw_state.get("dominant_archetypes", [])
    behavioral = raw_state.get("behavioral_profile", {})
    psych = raw_state.get("psychological_os", {})

    business_enrichment = {
        "scaling_style": _extract_scaling_style(archetypes),
        "collapse_vectors": psych.get("failure_modes", [])[:3],
        "wealth_behavior": raw_state.get("economic_style", {}).get("wealth_behavior", [])[:2],
        "partnership_style": _extract_partnership_style(archetypes),
        "suppression_vectors": [
            {"planet": s.get("planet", ""), "reason": s.get("reason", "")}
            for s in raw_state.get("suppression_vectors", [])[:2]
        ],
        "amplification_vectors": [
            {"planet": a.get("planet", ""), "reason": a.get("reason", "")}
            for a in raw_state.get("amplification_vectors", [])[:2]
        ],
    }

    # Merge into career base
    career_base["business"] = business_enrichment

    # Enforce budget
    career_base = enforce_budget(career_base, 550)

    # Update routing metadata
    if "_routing" in career_base:
        career_base["_routing"]["target"] = "business_context"
        career_base["_routing"]["budget"] = 550
        career_base["_routing"]["tokens_used"] = estimate_tokens(career_base)

    return career_base


def build_career_prompt_injection(birth_data_dict: dict, eval_date: datetime = None) -> str:
    """
    Build a compact text block for injecting into career/business OpenAI prompts.

    Returns formatted string optimized for LLM consumption.
    """
    ctx = build_career_context(birth_data_dict, eval_date)

    lines = ["SYMBOLIC CAREER CONTEXT:"]

    identity = ctx.get("identity", {})
    if identity.get("primary_archetype"):
        lines.append(f"- Archetype: {identity['primary_archetype']}")
    if identity.get("secondary_archetype"):
        lines.append(f"- Secondary: {identity['secondary_archetype']}")
    if identity.get("fusion_type") and identity["fusion_type"] != "single":
        lines.append(f"- Fusion: {identity['fusion_type']}")

    # Economic style
    econ = ctx.get("economic_style", {})
    if econ.get("traits"):
        lines.append(f"- Economic Style: {econ['traits'][0][:80]}")
    if econ.get("wealth_behavior"):
        lines.append(f"- Wealth: {econ['wealth_behavior'][0][:80]}")

    # Leadership
    leadership = ctx.get("leadership_signature", {})
    if leadership.get("traits"):
        lines.append(f"- Leadership: {leadership['traits'][0][:80]}")

    # Lifecycle
    lifecycle = ctx.get("lifecycle", {})
    if lifecycle.get("phase"):
        lines.append(f"- Career Phase: {lifecycle['phase']} ({lifecycle.get('stability', '')})")
    if lifecycle.get("direction"):
        lines.append(f"- Direction: {lifecycle['direction']}")

    # Conflicts
    conflicts = ctx.get("primary_conflicts", [])
    if conflicts:
        c = conflicts[0]
        lines.append(f"- Active Tension: {c.get('type', '')} — {c.get('resolution', '')[:50]}")

    return "\n".join(lines)


def _extract_scaling_style(archetypes: list) -> list:
    """Extract scaling style from dominant archetypes."""
    from symbolic.registry_loader import get_archetype_by_id
    styles = []
    for arch in archetypes[:2]:
        arch_id = arch.get("id", "")
        full = get_archetype_by_id(arch_id)
        if full and full.get("scaling_style"):
            styles.extend(full["scaling_style"][:2])
    return styles[:3]


def _extract_partnership_style(archetypes: list) -> list:
    """Extract partnership style from dominant archetypes."""
    from symbolic.registry_loader import get_archetype_by_id
    styles = []
    for arch in archetypes[:2]:
        arch_id = arch.get("id", "")
        full = get_archetype_by_id(arch_id)
        if full and full.get("partnership_style"):
            styles.extend(full["partnership_style"][:1])
    return styles[:2]
