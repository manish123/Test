"""
Token Budget — Enforce token limits on semantic payloads.

Provides compression and pruning to fit payloads within contract budgets.
"""

import json


def estimate_tokens(payload: dict) -> int:
    """Estimate token count for a payload (1 token ≈ 4 chars in JSON)."""
    return len(json.dumps(payload, default=str)) // 4


def enforce_budget(payload: dict, budget: int) -> dict:
    """
    Prune payload to fit within token budget.

    Strategy: progressively remove optional/low-priority sections
    until the payload fits.
    """
    current = estimate_tokens(payload)
    if current <= budget:
        return payload

    result = dict(payload)

    # Priority pruning order (remove least important first)
    prune_order = [
        "_meta", "_coherence_detail", "_compression_stats", "_narrative_stats",
        "_minimal_context", "suppressed_archetypes", "resolved_manifestation_path",
        "amplification_vectors", "suppression_vectors",
        "top_causal_narratives", "primary_conflicts",
    ]

    for key in prune_order:
        if key in result:
            del result[key]
            if estimate_tokens(result) <= budget:
                return result

    # If still over budget, truncate list fields
    for key, val in list(result.items()):
        if isinstance(val, list) and len(val) > 2:
            result[key] = val[:2]
            if estimate_tokens(result) <= budget:
                return result

    # If still over, truncate string fields
    for key, val in list(result.items()):
        if isinstance(val, dict):
            for subkey, subval in list(val.items()):
                if isinstance(subval, list) and len(subval) > 1:
                    val[subkey] = subval[:1]

    return result


def compute_budget_utilization(payload: dict, budget: int) -> dict:
    """Compute how much of the budget is used."""
    tokens = estimate_tokens(payload)
    return {
        "tokens_used": tokens,
        "budget": budget,
        "utilization": round(tokens / max(budget, 1), 2),
        "within_budget": tokens <= budget,
        "headroom": max(0, budget - tokens),
    }
