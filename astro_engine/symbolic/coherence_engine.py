"""
Coherence Engine — Compute symbolic coherence and detect fragmentation.

Measures how internally consistent the symbolic state is:
- High coherence = archetypes, behaviors, and lifecycle align
- Low coherence = contradictory signals, identity fragmentation
"""


def compute_coherence(symbolic_state: dict) -> dict:
    """
    Compute symbolic coherence score and fragmentation indicators.

    Returns dict with: coherence_score, fragmentation_level,
                       contradiction_density, identity_stability
    """
    archetypes = symbolic_state.get("dominant_archetypes", [])
    conflicts = symbolic_state.get("arbitration_results", [])
    suppressions = symbolic_state.get("suppression_vectors", [])
    lifecycle = symbolic_state.get("lifecycle_state", {})
    behavioral = symbolic_state.get("behavioral_profile", {})

    # Base coherence from archetype confidence spread
    arch_scores = [a.get("match_score", 0) for a in archetypes]
    if len(arch_scores) >= 2:
        # High spread between #1 and #2 = clear identity = high coherence
        spread = arch_scores[0] - arch_scores[1] if arch_scores[0] != arch_scores[1] else 0
        archetype_clarity = min(1.0, spread / 3.0)
    elif arch_scores:
        archetype_clarity = 0.8  # Single dominant = fairly clear
    else:
        archetype_clarity = 0.0

    # Conflict penalty
    conflict_count = len(conflicts)
    conflict_penalty = min(0.4, conflict_count * 0.1)

    # Suppression penalty (suppressed energies = internal tension)
    suppression_penalty = min(0.2, len(suppressions) * 0.05)

    # Lifecycle stability bonus
    stability = lifecycle.get("current_state", {}).get("stability", "medium")
    stability_bonus = {"high": 0.15, "medium": 0.0, "low": -0.1,
                       "restructuring": -0.15, "volatile": -0.2}.get(stability, 0.0)

    # Behavioral alignment (do dominant planets match archetype drivers?)
    dom_planets = behavioral.get("dominant_planets", [])
    alignment_bonus = 0.0
    if dom_planets and archetypes:
        # Simple check: if top planet appears in archetype name/drivers
        top_planet = dom_planets[0][0] if dom_planets else ""
        for arch in archetypes[:1]:
            if top_planet.lower() in str(arch).lower():
                alignment_bonus = 0.1

    # Compute final score
    raw_score = 0.5 + archetype_clarity * 0.3 - conflict_penalty - suppression_penalty + stability_bonus + alignment_bonus
    coherence_score = round(max(0.0, min(1.0, raw_score)), 3)

    # Classify fragmentation
    if coherence_score >= 0.75:
        fragmentation = "low"
    elif coherence_score >= 0.5:
        fragmentation = "moderate"
    elif coherence_score >= 0.3:
        fragmentation = "high"
    else:
        fragmentation = "severe"

    return {
        "coherence_score": coherence_score,
        "fragmentation_level": fragmentation,
        "contradiction_density": conflict_count,
        "identity_stability": "stable" if archetype_clarity > 0.3 else "mixed" if archetype_clarity > 0.1 else "fragmented",
        "components": {
            "archetype_clarity": round(archetype_clarity, 3),
            "conflict_penalty": round(conflict_penalty, 3),
            "suppression_penalty": round(suppression_penalty, 3),
            "stability_bonus": round(stability_bonus, 3),
            "alignment_bonus": round(alignment_bonus, 3),
        },
    }
