"""
Coherent State Builder — Master orchestrator for Phase 10B.

Chains: symbolic_state → coherence → prioritization → compression → ranking → prompt context.
Produces the final, stable, low-noise semantic intelligence object.
"""

from symbolic.symbolic_state_engine import build_symbolic_state
from symbolic.coherence_engine import compute_coherence
from symbolic.archetype_prioritizer import prioritize_archetypes
from symbolic.semantic_compressor import compress_symbolic_state
from symbolic.narrative_ranker import rank_narratives
from symbolic.prompt_context_builder import build_prompt_context, build_minimal_context


def build_coherent_state(chart_state, eval_date=None, evaluator_outputs=None):
    """
    Build the complete coherent symbolic state with all Phase 10B processing.

    Parameters
    ----------
    chart_state : BaseChartState or subclass
    eval_date : datetime, optional
    evaluator_outputs : dict, optional

    Returns
    -------
    dict with the full coherent semantic intelligence object.
    """
    # Phase 10A: Raw symbolic state
    raw_state = build_symbolic_state(chart_state, eval_date, evaluator_outputs)

    # Phase 10B: Coherence processing
    coherence = compute_coherence(raw_state)
    prioritized = prioritize_archetypes(raw_state)
    compressed = compress_symbolic_state(raw_state)
    ranked = rank_narratives(raw_state, coherence)
    prompt_ctx = build_prompt_context(raw_state, coherence, prioritized, compressed, ranked)

    return {
        "core_identity": prioritized.get("core_identity", {}),
        "dominant_archetypes": prioritized.get("dominant_archetypes", []),
        "suppressed_archetypes": prioritized.get("suppressed_archetypes", []),
        "behavioral_core": compressed.get("compressed_behaviors", {}),
        "primary_lifecycle_state": raw_state.get("lifecycle_state", {}),
        "primary_conflicts": raw_state.get("arbitration_results", []),
        "resolved_manifestation_path": raw_state.get("manifestation_logic", {}),
        "top_causal_narratives": ranked.get("top_narratives", []),
        "semantic_coherence_score": coherence.get("coherence_score", 0.0),
        "prompt_ready_context": prompt_ctx,
        # Metadata
        "_coherence_detail": coherence,
        "_compression_stats": compressed.get("dedup_stats", {}),
        "_narrative_stats": {"kept": ranked.get("kept", 0), "total": ranked.get("total_candidates", 0)},
        "_minimal_context": build_minimal_context(raw_state),
    }
