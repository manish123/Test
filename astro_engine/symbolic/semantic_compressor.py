"""
Semantic Compressor — Merge overlapping symbolic meanings and reduce redundancy.

Deduplicates behavioral traits, merges similar narrative fragments,
and produces a compact semantic representation.
"""


def compress_symbolic_state(symbolic_state: dict) -> dict:
    """
    Compress symbolic state by merging overlaps and removing redundancy.

    Returns dict with: compressed_behaviors, compressed_narratives,
                       dedup_stats, semantic_density
    """
    # Compress behavioral traits
    leadership = symbolic_state.get("leadership_signature", {}).get("traits", [])
    risk = symbolic_state.get("risk_signature", {}).get("risk_traits", [])
    economic = symbolic_state.get("economic_style", {}).get("traits", [])

    compressed_leadership = _deduplicate_traits(leadership)
    compressed_risk = _deduplicate_traits(risk)
    compressed_economic = _deduplicate_traits(economic)

    # Compress narratives
    narratives = symbolic_state.get("causal_narratives", [])
    compressed_narratives = _merge_similar_narratives(narratives)

    # Compress trigger chains
    triggers = symbolic_state.get("trigger_chains", [])
    compressed_triggers = list(dict.fromkeys(triggers))[:5]  # Deduplicate, keep top 5

    # Compute density
    original_items = len(leadership) + len(risk) + len(economic) + len(narratives) + len(triggers)
    compressed_items = len(compressed_leadership) + len(compressed_risk) + len(compressed_economic) + len(compressed_narratives) + len(compressed_triggers)
    density = round(compressed_items / max(original_items, 1), 2)

    return {
        "compressed_behaviors": {
            "leadership": compressed_leadership,
            "risk": compressed_risk,
            "economic": compressed_economic,
        },
        "compressed_narratives": compressed_narratives,
        "compressed_triggers": compressed_triggers,
        "dedup_stats": {
            "original_items": original_items,
            "compressed_items": compressed_items,
            "reduction_ratio": round(1.0 - density, 2) if density < 1.0 else 0.0,
        },
        "semantic_density": density,
    }


def _deduplicate_traits(traits: list) -> list:
    """Remove semantically similar traits (simple substring matching)."""
    if not traits:
        return []
    kept = []
    for trait in traits:
        # Skip if a very similar trait already exists
        is_dup = False
        trait_lower = trait.lower()
        for existing in kept:
            existing_lower = existing.lower()
            # Check for high overlap (one contains the other, or >60% word overlap)
            if trait_lower in existing_lower or existing_lower in trait_lower:
                is_dup = True
                break
            words_a = set(trait_lower.split())
            words_b = set(existing_lower.split())
            if len(words_a & words_b) > 0.6 * min(len(words_a), len(words_b)):
                is_dup = True
                break
        if not is_dup:
            kept.append(trait)
    return kept[:4]  # Cap at 4 traits per category


def _merge_similar_narratives(narratives: list) -> list:
    """Merge narratives with similar core_cause."""
    if not narratives:
        return []
    seen_causes = set()
    merged = []
    for n in narratives:
        cause = n.get("core_cause", "")
        # Simple dedup by first 30 chars of cause
        key = cause[:30].lower().strip()
        if key not in seen_causes:
            seen_causes.add(key)
            merged.append(n)
    return merged[:5]  # Cap at 5 narratives
