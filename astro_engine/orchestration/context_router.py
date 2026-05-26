"""
Context Router — Route symbolic state to the correct contract-shaped payload.

Maps API consumers to their required semantic sections.
"""

from orchestration.context_contracts import get_contract, get_token_budget
from orchestration.token_budget import enforce_budget, estimate_tokens


def route_context(coherent_state: dict, target: str) -> dict:
    """
    Route a coherent symbolic state to a target API contract.

    Parameters
    ----------
    coherent_state : dict from build_coherent_state()
    target : str, one of: minimal_context, personality_context, timing_context,
             career_context, prediction_context, relationship_context, full_symbolic_context

    Returns
    -------
    dict shaped to the target contract, within token budget.
    """
    contract = get_contract(target)
    budget = contract["token_budget"]
    priority = contract["semantic_priority"]

    # Build payload based on semantic priority
    payload = _extract_by_priority(coherent_state, priority, target)

    # Enforce token budget
    payload = enforce_budget(payload, budget)

    # Add routing metadata
    payload["_routing"] = {
        "target": target,
        "budget": budget,
        "tokens_used": estimate_tokens(payload),
        "compression": contract["compression"],
    }

    return payload


def _extract_by_priority(state: dict, priorities: list, target: str) -> dict:
    """Extract fields from state based on semantic priority ordering."""
    payload = {}

    for section in priorities:
        if section == "identity":
            payload["identity"] = _extract_identity(state)
        elif section == "behavioral_core":
            payload["behavioral_core"] = state.get("behavioral_core", {})
        elif section == "lifecycle":
            payload["lifecycle"] = _extract_lifecycle(state)
        elif section == "conflicts":
            payload["primary_conflicts"] = state.get("primary_conflicts", [])[:3]
        elif section == "narratives":
            payload["top_narratives"] = [
                {"cause": n.get("core_cause", ""), "relevance": n.get("rank_score", n.get("relevance", 0))}
                for n in state.get("top_causal_narratives", [])[:3]
            ]
        elif section == "coherence":
            detail = state.get("_coherence_detail", {})
            payload["coherence"] = {
                "score": detail.get("coherence_score", state.get("semantic_coherence_score", 0)),
                "fragmentation": detail.get("fragmentation_level", "unknown"),
            }
        elif section == "suppression":
            payload["suppression_vectors"] = state.get("suppression_vectors", [])[:3] if "suppression_vectors" in state else []
        elif section == "psychological_os":
            # Extract from prompt_ready_context if available
            prc = state.get("prompt_ready_context", {})
            payload["psychological_os"] = state.get("psychological_os", prc.get("psychological_os", {}))
        elif section == "economic_style":
            payload["economic_style"] = state.get("economic_style", {})
        elif section == "leadership":
            payload["leadership_signature"] = state.get("leadership_signature", {})

    return payload


def _extract_identity(state: dict) -> dict:
    """Extract identity section."""
    ci = state.get("core_identity", {})
    return {
        "primary_archetype": ci.get("primary", "undetermined"),
        "secondary_archetype": ci.get("secondary"),
        "fusion_type": ci.get("fusion_type", "single"),
        "stability": ci.get("stability", "unknown"),
    }


def _extract_lifecycle(state: dict) -> dict:
    """Extract lifecycle section."""
    lc = state.get("primary_lifecycle_state", {})
    current = lc.get("current_state", {})
    return {
        "phase": current.get("label", "unknown"),
        "stability": current.get("stability", "unknown"),
        "direction": lc.get("expansion_indicators", {}).get("net_direction", "unknown"),
        "crisis_vectors": lc.get("crisis_vectors", []),
        "probable_next_states": lc.get("probable_next_states", [])[:2],
    }
