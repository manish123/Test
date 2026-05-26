"""
Narrative Ranker — Prioritize causally central narratives and suppress weak fragments.

Ranks by symbolic explanatory power: how much of the chart's behavior
does this narrative explain?
"""


def rank_narratives(symbolic_state: dict, coherence_result: dict = None) -> dict:
    """
    Rank causal narratives by relevance and explanatory power.

    Returns dict with: top_narratives, suppressed_narratives, explanatory_coverage
    """
    narratives = symbolic_state.get("causal_narratives", [])
    if not narratives:
        return {"top_narratives": [], "suppressed_narratives": [], "explanatory_coverage": 0.0}

    # Score each narrative
    scored = []
    for n in narratives:
        relevance = n.get("relevance", 0)
        has_triggers = len(n.get("trigger_chain", [])) > 0
        is_archetype_derived = "archetype_" in n.get("narrative_id", "")

        # Composite ranking score
        rank_score = relevance * 2.0
        if has_triggers:
            rank_score += 0.3  # Bonus for having causal chain
        if is_archetype_derived:
            rank_score += 0.2  # Bonus for archetype grounding

        # Coherence bonus: if coherence is high, boost all narratives slightly
        if coherence_result and coherence_result.get("coherence_score", 0) > 0.6:
            rank_score *= 1.1

        scored.append({**n, "rank_score": round(rank_score, 3)})

    scored.sort(key=lambda x: x["rank_score"], reverse=True)

    # Split into top (kept) and suppressed (weak)
    threshold = 0.3
    top = [n for n in scored if n["rank_score"] >= threshold]
    suppressed = [n for n in scored if n["rank_score"] < threshold]

    # Explanatory coverage: what fraction of narratives are strong?
    coverage = len(top) / max(len(scored), 1)

    return {
        "top_narratives": top[:5],
        "suppressed_narratives": [{"id": n.get("narrative_id", ""), "reason": "low_rank_score"} for n in suppressed],
        "explanatory_coverage": round(coverage, 2),
        "total_candidates": len(narratives),
        "kept": len(top),
    }
