"""
Archetype Prioritizer — Stabilize and rank archetypes with confidence-weighted pruning.

Reduces archetype overproduction by:
- Pruning weak/noisy archetypes below threshold
- Applying lifecycle-aware weighting
- Detecting fusion patterns
- Producing a stable core identity
"""


def prioritize_archetypes(symbolic_state: dict, prune_threshold: float = 0.3) -> dict:
    """
    Prioritize and prune archetypes for stable identity.

    Parameters
    ----------
    symbolic_state : dict from build_symbolic_state()
    prune_threshold : float, minimum match_score × source_confidence to keep

    Returns
    -------
    dict with: core_identity, dominant (pruned), suppressed, fusion_type
    """
    dominant = symbolic_state.get("dominant_archetypes", [])
    secondary = symbolic_state.get("secondary_archetypes", [])
    lifecycle = symbolic_state.get("lifecycle_state", {})
    all_archetypes = dominant + secondary

    # Score each archetype: match_score × source_confidence
    scored = []
    for arch in all_archetypes:
        composite = arch.get("match_score", 0) * arch.get("source_confidence", 0.5)
        scored.append({**arch, "composite_score": round(composite, 3)})

    scored.sort(key=lambda x: x["composite_score"], reverse=True)

    # Prune below threshold
    kept = [a for a in scored if a["composite_score"] >= prune_threshold]
    suppressed = [a for a in scored if a["composite_score"] < prune_threshold]

    # Lifecycle-aware weighting
    phase = lifecycle.get("current_state", {}).get("phase", "")
    if phase in ("mastery", "building"):
        # Boost archetypes with "scaling" or "authority" in name
        for a in kept:
            if any(kw in a.get("name", "").lower() for kw in ("captain", "tycoon", "industry")):
                a["composite_score"] = round(a["composite_score"] * 1.1, 3)
    elif phase in ("midlife_transition", "first_saturn_return"):
        # Boost archetypes with "reinvention" or "crisis"
        for a in kept:
            if any(kw in a.get("name", "").lower() for kw in ("crisis", "speculative", "reinvent")):
                a["composite_score"] = round(a["composite_score"] * 1.1, 3)

    kept.sort(key=lambda x: x["composite_score"], reverse=True)

    # Core identity = top 1-2 archetypes
    core = kept[:2] if len(kept) >= 2 else kept

    # Detect fusion
    fusion_type = "single"
    if len(core) >= 2:
        # Check if they're complementary or contradictory
        names = [c.get("name", "").lower() for c in core]
        if any("network" in n for n in names) and any("captain" in n or "crisis" in n for n in names):
            fusion_type = "complementary_dual"
        elif any("speculative" in n for n in names) and any("diplomat" in n for n in names):
            fusion_type = "tension_dual"
        else:
            fusion_type = "parallel_dual"

    return {
        "core_identity": {
            "primary": core[0]["name"] if core else "undetermined",
            "secondary": core[1]["name"] if len(core) >= 2 else None,
            "fusion_type": fusion_type,
            "stability": "high" if len(core) == 1 or (len(core) >= 2 and core[0]["composite_score"] > core[1]["composite_score"] * 1.3) else "moderate",
        },
        "dominant_archetypes": core,
        "suppressed_archetypes": [{"id": a["id"], "name": a["name"], "reason": "below_threshold"} for a in suppressed],
        "pruning_stats": {
            "total_candidates": len(all_archetypes),
            "kept": len(kept),
            "pruned": len(suppressed),
            "threshold": prune_threshold,
        },
    }
