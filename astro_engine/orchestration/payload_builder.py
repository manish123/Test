"""
Payload Builder — Build complete orchestration payloads for any target API.

Master entry point that chains: coherent_state → route → budget → sections → payload.
"""

from orchestration.context_router import route_context
from orchestration.token_budget import compute_budget_utilization
from orchestration.prompt_sections import build_section_manifest
from orchestration.context_contracts import get_contract


def build_payload(coherent_state: dict, target: str) -> dict:
    """
    Build a complete orchestration payload for a target API.

    Parameters
    ----------
    coherent_state : dict from build_coherent_state()
    target : str, contract name (personality_context, timing_context, etc.)

    Returns
    -------
    dict with: payload, sections, budget_utilization, contract
    """
    contract = get_contract(target)
    budget = contract["token_budget"]

    # Route to target shape
    routed = route_context(coherent_state, target)

    # Build section manifest
    sections = build_section_manifest(routed, budget)

    # Compute budget utilization
    utilization = compute_budget_utilization(routed, budget)

    return {
        "target": target,
        "payload": routed,
        "sections": sections,
        "budget_utilization": utilization,
        "contract": {
            "name": target,
            "budget": budget,
            "compression": contract["compression"],
            "priority": contract["semantic_priority"],
        },
    }


def build_all_payloads(coherent_state: dict) -> dict:
    """
    Build payloads for ALL target APIs simultaneously.

    Returns dict mapping target_name → payload_result.
    """
    from orchestration.context_contracts import list_contracts
    results = {}
    for target in list_contracts():
        results[target] = build_payload(coherent_state, target)
    return results
