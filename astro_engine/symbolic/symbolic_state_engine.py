"""
Symbolic State Engine — Aggregate all symbolic outputs into one canonical object.

This is the master aggregator that produces the complete symbolic cognition state.
It becomes the future semantic context layer for personality API, timing API,
career API, weekly prediction generation, and OpenAI orchestration.
"""

from datetime import datetime

from symbolic.archetype_engine import determine_archetypes
from symbolic.planetary_behavior_engine import build_behavioral_profile
from symbolic.arbitration_engine import resolve_conflicts
from symbolic.lifecycle_engine import determine_lifecycle_state
from symbolic.narrative_engine import build_causal_narrative


def build_symbolic_state(chart_state, eval_date=None, evaluator_outputs=None):
    """
    Aggregate all symbolic engines into one canonical semantic object.

    Parameters
    ----------
    chart_state : BaseChartState or subclass
        Natal chart data.
    eval_date : datetime, optional
        Evaluation date (for lifecycle phase). Defaults to now.
    evaluator_outputs : dict, optional
        Results from domain evaluators (for context).

    Returns
    -------
    dict — the complete symbolic cognition state.
    """
    if eval_date is None:
        eval_date = datetime.now()

    # 1. Archetypes
    archetypes = determine_archetypes(chart_state, evaluator_outputs)

    # 2. Behavioral profile
    behavioral = build_behavioral_profile(chart_state)

    # 3. Arbitration
    arbitration = resolve_conflicts(chart_state)

    # 4. Lifecycle
    lifecycle = determine_lifecycle_state(chart_state, eval_date)

    # 5. Narrative
    narrative = build_causal_narrative(chart_state, archetypes, lifecycle)

    # 6. Compose canonical output
    return {
        "dominant_archetypes": archetypes.get("dominant_archetypes", []),
        "secondary_archetypes": archetypes.get("secondary_archetypes", []),
        "behavioral_profile": behavioral.get("behavioral_profile", {}),
        "leadership_signature": behavioral.get("leadership_signature", {}),
        "risk_signature": behavioral.get("volatility_signature", {}),
        "economic_style": behavioral.get("economic_style", {}),
        "psychological_os": behavioral.get("psychological_os", {}),
        "lifecycle_state": lifecycle,
        "arbitration_results": arbitration.get("arbitration_results", []),
        "suppression_vectors": arbitration.get("suppressed_energies", []),
        "amplification_vectors": arbitration.get("amplified_energies", []),
        "causal_narratives": narrative.get("causal_fragments", []),
        "trigger_chains": narrative.get("trigger_chains", []),
        "manifestation_logic": narrative.get("manifestation_logic", {}),
        "symbolic_summary": {
            "primary_archetype": archetypes.get("dominant_archetypes", [{}])[0].get("name", "undetermined") if archetypes.get("dominant_archetypes") else "undetermined",
            "lifecycle_phase": lifecycle.get("current_state", {}).get("label", "unknown"),
            "dominant_planet": behavioral.get("behavioral_profile", {}).get("dominant_planets", [("unknown", 0)])[0][0] if behavioral.get("behavioral_profile", {}).get("dominant_planets") else "unknown",
            "net_direction": lifecycle.get("expansion_indicators", {}).get("net_direction", "unknown"),
            "active_conflicts": len(arbitration.get("arbitration_results", [])),
        },
    }
