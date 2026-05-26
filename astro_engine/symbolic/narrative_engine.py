"""
Narrative Engine — Generate structured symbolic causality.

IMPORTANT: This engine does NOT generate natural language.
It produces causal fragments, trigger chains, and manifestation logic
as structured semantic objects only. NO OpenAI calls.
"""

from symbolic.registry_loader import get_causal_narratives


def build_causal_narrative(chart_state, archetype_results=None, lifecycle_state=None):
    """
    Generate structured causal narrative fragments.

    Returns dict with: causal_fragments, trigger_chains, suppression_chains,
                       amplification_chains, manifestation_logic
    """
    narratives = get_causal_narratives()
    fragments = []
    trigger_chains = []
    suppression_chains = []
    amplification_chains = []

    planets = chart_state.planets

    # Match causal narratives to chart conditions
    for narrative in narratives:
        relevance = _assess_narrative_relevance(narrative, chart_state)
        if relevance > 0.3:
            fragments.append({
                "narrative_id": narrative.get("narrative_id", ""),
                "core_cause": narrative.get("core_cause", ""),
                "relevance": round(relevance, 2),
                "trigger_chain": narrative.get("trigger_chain", []),
            })
            trigger_chains.extend(narrative.get("trigger_chain", []))

            for sup in narrative.get("suppressing_factors", []):
                suppression_chains.append({"factor": sup, "source": narrative.get("narrative_id", "")})
            for amp in narrative.get("supporting_factors", []):
                amplification_chains.append({"factor": amp, "source": narrative.get("narrative_id", "")})

    # Add archetype-derived narratives
    if archetype_results:
        for arch in archetype_results.get("dominant_archetypes", []):
            fragments.append({
                "narrative_id": f"archetype_{arch['id']}",
                "core_cause": f"Dominant archetype: {arch['name']}",
                "relevance": arch.get("match_score", 0) / 10.0,
                "trigger_chain": [],
            })

    return {
        "causal_fragments": fragments,
        "trigger_chains": trigger_chains[:10],
        "suppression_chains": suppression_chains[:5],
        "amplification_chains": amplification_chains[:5],
        "manifestation_logic": _build_manifestation_logic(fragments, lifecycle_state),
    }


def _assess_narrative_relevance(narrative, chart_state):
    """Score how relevant a causal narrative is to this chart."""
    score = 0.0
    core_cause = narrative.get("core_cause", "").lower()
    planets = chart_state.planets

    # Check if Sun-related narrative matches Sun placement
    if "sun" in core_cause or "surya" in core_cause:
        sun_house = planets.get("Sun", {}).get("house", 0)
        if sun_house in (10, 1, 9):  # Authority houses
            score += 0.5
        sun_status = planets.get("Sun", {}).get("status", "")
        if sun_status == "debilitated":
            score += 0.4  # Debilitated Sun = spiritual malnutrition narrative

    # Check Saturn-related narratives
    if "saturn" in core_cause or "shani" in core_cause:
        sat_house = planets.get("Saturn", {}).get("house", 0)
        if sat_house in (1, 4, 8, 10):
            score += 0.4

    # Check if narrative mentions hierarchy/authority
    if "hierarch" in core_cause or "authority" in core_cause:
        if planets.get("Sun", {}).get("house") == 10:
            score += 0.3

    return min(1.0, score)


def _build_manifestation_logic(fragments, lifecycle_state):
    """Build manifestation logic from fragments + lifecycle context."""
    if not fragments:
        return {"primary_manifestation": "undetermined"}

    top = fragments[0] if fragments else {}
    phase = lifecycle_state.get("current_state", {}).get("phase", "unknown") if lifecycle_state else "unknown"

    return {
        "primary_manifestation": top.get("core_cause", "undetermined"),
        "lifecycle_context": phase,
        "active_triggers": len([f for f in fragments if f.get("relevance", 0) > 0.5]),
    }
