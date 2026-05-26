"""
Prompt Context Builder — Produce compact semantic context for future LLM orchestration.

IMPORTANT: This module does NOT call OpenAI or generate prompts.
It produces structured, token-efficient semantic payloads that future
API layers can inject into LLM context windows.
"""


def build_prompt_context(symbolic_state: dict, coherence: dict,
                         prioritized: dict, compressed: dict,
                         ranked_narratives: dict) -> dict:
    """
    Build a compact, prompt-ready semantic context payload.

    Optimized for:
    - Low token count (compact representation)
    - High semantic density (maximum meaning per token)
    - Structured for LLM consumption (clear sections)

    Returns dict suitable for future prompt injection.
    """
    # Core identity (most important — always include)
    core_identity = prioritized.get("core_identity", {})

    # Behavioral core (compressed, top traits only)
    behaviors = compressed.get("compressed_behaviors", {})

    # Lifecycle (single sentence equivalent)
    lifecycle = symbolic_state.get("lifecycle_state", {})
    current_phase = lifecycle.get("current_state", {})

    # Top narratives (ranked, max 3)
    top_narr = ranked_narratives.get("top_narratives", [])[:3]

    # Conflicts (only if present)
    conflicts = symbolic_state.get("arbitration_results", [])

    # Build compact payload
    payload = {
        "identity": {
            "primary_archetype": core_identity.get("primary", "undetermined"),
            "secondary_archetype": core_identity.get("secondary"),
            "fusion_type": core_identity.get("fusion_type", "single"),
            "stability": core_identity.get("stability", "unknown"),
        },
        "behavioral_core": {
            "leadership": behaviors.get("leadership", [])[:2],
            "risk": behaviors.get("risk", [])[:2],
            "economic": behaviors.get("economic", [])[:2],
        },
        "lifecycle": {
            "phase": current_phase.get("label", "unknown"),
            "stability": current_phase.get("stability", "unknown"),
            "direction": lifecycle.get("expansion_indicators", {}).get("net_direction", "unknown"),
        },
        "primary_conflicts": [
            {"type": c.get("type", ""), "resolution": c.get("resolution", "")}
            for c in conflicts[:2]
        ],
        "top_narratives": [
            {"cause": n.get("core_cause", ""), "relevance": n.get("rank_score", 0)}
            for n in top_narr
        ],
        "coherence": {
            "score": coherence.get("coherence_score", 0),
            "fragmentation": coherence.get("fragmentation_level", "unknown"),
        },
    }

    # Compute token estimate (rough: 1 token ≈ 4 chars in JSON)
    import json
    payload_str = json.dumps(payload, default=str)
    estimated_tokens = len(payload_str) // 4

    payload["_meta"] = {
        "estimated_tokens": estimated_tokens,
        "sections": len(payload) - 1,  # Exclude _meta itself
        "version": "10B",
    }

    return payload


def build_minimal_context(symbolic_state: dict) -> dict:
    """
    Ultra-compact context for token-constrained scenarios.
    ~50-80 tokens. Contains only the absolute essentials.
    """
    summary = symbolic_state.get("symbolic_summary", {})
    return {
        "archetype": summary.get("primary_archetype", "unknown"),
        "phase": summary.get("lifecycle_phase", "unknown"),
        "planet": summary.get("dominant_planet", "unknown"),
        "direction": summary.get("net_direction", "unknown"),
        "conflicts": summary.get("active_conflicts", 0),
    }
