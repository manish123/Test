"""
Timing API Adapter — Converts production birth_data_dict into symbolic timing/prediction payloads.

TEST-repo-only adapter. Does NOT:
- Call OpenAI
- Touch production code
- Modify evaluators or scoring

Produces:
- build_timing_context(birth_data_dict, eval_date) → timing_context payload (≤400 tokens)
- build_prediction_context(birth_data_dict, eval_date) → prediction_context payload (≤250 tokens)
- build_weekly_prediction_injection(birth_data_dict, eval_date) → compact text for LLM prompt
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
from orchestration.context_router import route_context
from orchestration.token_budget import estimate_tokens


def _normalize(birth_data_dict: dict) -> tuple:
    """Normalize production birth_data_dict → (datetime, lat, lon, alt)."""
    birth_dt = birth_data_dict["date"]
    lat = float(birth_data_dict["lat"])
    lon = float(birth_data_dict["lon"])
    alt = float(birth_data_dict.get("alt", 0))
    if not isinstance(birth_dt, datetime):
        raise ValueError(f"birth_data_dict['date'] must be datetime, got {type(birth_dt)}")
    return birth_dt, lat, lon, alt


def build_timing_context(birth_data_dict: dict, eval_date: datetime = None) -> dict:
    """
    Build a timing_context payload (≤400 tokens).

    Contains: lifecycle phase, stability, direction, crisis vectors,
    probable next states, coherence, conflicts, top narratives.
    """
    birth_dt, lat, lon, alt = _normalize(birth_data_dict)
    if eval_date is None:
        eval_date = datetime.now()

    chart = BaseChartState(birth_dt, lat, lon, alt)
    coherent_state = build_coherent_state(chart, eval_date=eval_date)
    return route_context(coherent_state, "timing_context")


def build_prediction_context(birth_data_dict: dict, eval_date: datetime = None) -> dict:
    """
    Build a prediction_context payload (≤250 tokens).

    Contains: identity archetype, lifecycle phase + direction,
    top narratives, primary conflicts. Optimized for weekly predictions.
    """
    birth_dt, lat, lon, alt = _normalize(birth_data_dict)
    if eval_date is None:
        eval_date = datetime.now()

    chart = BaseChartState(birth_dt, lat, lon, alt)
    coherent_state = build_coherent_state(chart, eval_date=eval_date)
    return route_context(coherent_state, "prediction_context")


def build_weekly_prediction_injection(birth_data_dict: dict, eval_date: datetime = None) -> str:
    """
    Build a compact text block for injecting into weekly prediction OpenAI prompts.

    Returns a formatted string (NOT JSON) optimized for LLM consumption.
    """
    ctx = build_prediction_context(birth_data_dict, eval_date)

    lines = ["SYMBOLIC TIMING CONTEXT:"]

    identity = ctx.get("identity", {})
    if identity.get("primary_archetype"):
        lines.append(f"- Archetype: {identity['primary_archetype']}")

    lifecycle = ctx.get("lifecycle", {})
    if lifecycle.get("phase"):
        lines.append(f"- Life Phase: {lifecycle['phase']} ({lifecycle.get('stability', '')})")
    if lifecycle.get("direction"):
        lines.append(f"- Direction: {lifecycle['direction']}")
    crisis = lifecycle.get("crisis_vectors", [])
    if crisis:
        lines.append(f"- Active Crisis: {crisis[0].get('type', '')} (intensity: {crisis[0].get('intensity', '')})")

    conflicts = ctx.get("primary_conflicts", [])
    if conflicts:
        c = conflicts[0]
        lines.append(f"- Conflict: {c.get('type', '')} — {c.get('resolution', '')[:60]}")

    narratives = ctx.get("top_narratives", [])
    if narratives:
        lines.append(f"- Dominant Theme: {narratives[0].get('cause', '')[:80]}")

    coherence = ctx.get("coherence", {})
    if coherence.get("score"):
        lines.append(f"- Coherence: {coherence['score']:.2f} ({coherence.get('fragmentation', '')})")

    return "\n".join(lines)
