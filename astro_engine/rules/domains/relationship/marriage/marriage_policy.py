"""
Marriage Policy — Domain interpretation of fired marriage rules.

Takes the output of rule_evaluator.evaluate_marriage_rules() and produces
human-meaningful relationship guidance.

This module converts neutral signals into:
- commitment_likelihood: how likely is a formal commitment
- union_type: marriage, engagement, cohabitation, renewal
- timing_phase: observation, preparation, active, confirmation
- guidance: what to pay attention to

It does NOT predict "marriage will happen." It describes the current
phase of relationship activation and what it means.
"""

from typing import Dict, Any, List


# ═══════════════════════════════════════════════════════════════
# PHASE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

def _classify_phase(composite_signal: str, highest_likelihood: str) -> str:
    """
    Determine the current marriage/relationship phase.

    Returns one of:
        "dormant"       — no active signals
        "observation"   — weak signals, worth watching
        "preparation"   — moderate signals, window building
        "active"        — strong signals, window open
        "confirmation"  — very strong signals, event imminent
    """
    if composite_signal == "NO_SIGNAL":
        return "dormant"
    if composite_signal == "WEAK_SIGNAL":
        return "observation"
    if highest_likelihood in ("very_high", "high") and composite_signal in ("NARROW_WINDOW", "TARGET_DAY"):
        return "confirmation"
    if highest_likelihood in ("high", "very_high"):
        return "active"
    if highest_likelihood == "moderate":
        return "preparation"
    return "observation"


def _determine_union_type(fired_rules: List[Dict]) -> str:
    """
    Determine the most likely type of union based on fired rules.

    Returns one of:
        "marriage"       — formal marriage/wedding
        "commitment"     — engagement, serious commitment
        "cohabitation"   — living together, informal union
        "renewal"        — relationship renewal/recommitment
        "general_bond"   — unspecified partnership deepening
    """
    labels = [r["outputs"].get("symbolic_label", "") for r in fired_rules]

    if any("marriage" in l for l in labels):
        return "marriage"
    if any("commitment" in l for l in labels):
        return "commitment"
    if any("family_forming" in l for l in labels):
        return "marriage"  # family formation implies marriage
    if any("union" in l for l in labels):
        return "commitment"
    if any("relationship_growth" in l for l in labels):
        return "general_bond"
    return "general_bond"


def _generate_guidance(phase: str, union_type: str, fired_rules: List[Dict]) -> List[str]:
    """
    Generate actionable guidance based on the current phase and union type.
    """
    guidance = []

    if phase == "dormant":
        guidance.append("No active marriage signals detected in current period.")
        guidance.append("Focus on personal growth and relationship quality.")
        return guidance

    if phase == "observation":
        guidance.append("Early marriage-related signals detected.")
        guidance.append("This is an observation phase — no action needed yet.")
        guidance.append("Monitor relationship developments over coming months.")
        return guidance

    if phase == "preparation":
        guidance.append(f"Marriage conditions are building. Union type indicated: {union_type}.")
        guidance.append("This is a preparation window — conversations about commitment may arise naturally.")
        if any(r["rule_type"] == "dasha" for r in fired_rules):
            guidance.append("Dasha activation supports long-term relationship decisions.")

    if phase == "active":
        guidance.append(f"Marriage window is ACTIVE. Indicated: {union_type}.")
        guidance.append("Multiple astrological factors support formal commitment in this period.")
        if any(r["rule_type"] == "transit" for r in fired_rules):
            guidance.append("Transit support confirms the timing is favorable for action.")
        guidance.append("If relationship is ready, this is a supportive period for commitment decisions.")

    if phase == "confirmation":
        guidance.append(f"STRONG marriage confirmation signals. Indicated: {union_type}.")
        guidance.append("Both broad and precise timing indicators are aligned.")
        if any(r["rule_type"] == "fast_trigger" for r in fired_rules):
            guidance.append("Fast triggers active — exact timing can be narrowed to days/weeks.")
        guidance.append("If commitment is desired, this is among the strongest windows available.")

    return guidance


# ═══════════════════════════════════════════════════════════════
# MAIN POLICY FUNCTION
# ═══════════════════════════════════════════════════════════════

def interpret_marriage_signals(evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interpret fired marriage rules into meaningful relationship guidance.

    Args:
        evaluation_result: output of evaluate_marriage_rules()

    Returns:
        dict with:
            "phase": dormant/observation/preparation/active/confirmation
            "union_type": marriage/commitment/cohabitation/renewal/general_bond
            "commitment_likelihood": 0.0-1.0
            "timing_phase": broad/narrow/exact
            "guidance": list of guidance strings
            "active_labels": list of symbolic labels from fired rules
            "rule_summary": brief summary of what fired
    """
    fired = evaluation_result.get("fired_rules", [])
    composite_signal = evaluation_result.get("composite_signal", "NO_SIGNAL")
    highest_likelihood = evaluation_result.get("highest_likelihood", "very_low")
    best_timing = evaluation_result.get("best_timing", "broad")

    # Classify phase
    phase = _classify_phase(composite_signal, highest_likelihood)

    # Determine union type
    union_type = _determine_union_type(fired) if fired else "none"

    # Commitment likelihood (0-1)
    likelihood_map = {"very_low": 0.1, "low": 0.25, "moderate": 0.50, "high": 0.75, "very_high": 0.90}
    commitment_likelihood = likelihood_map.get(highest_likelihood, 0.0)

    # Boost if multiple rule types fired together
    types_fired = set(r["rule_type"] for r in fired)
    if len(types_fired) >= 3:
        commitment_likelihood = min(1.0, commitment_likelihood + 0.10)
    elif len(types_fired) >= 2:
        commitment_likelihood = min(1.0, commitment_likelihood + 0.05)

    # Generate guidance
    guidance = _generate_guidance(phase, union_type, fired)

    # Collect active labels
    active_labels = [r["outputs"].get("symbolic_label", r["rule_id"]) for r in fired]

    # Rule summary
    if not fired:
        rule_summary = "No marriage rules fired for the current period."
    else:
        rule_types = ", ".join(sorted(types_fired))
        rule_summary = f"{len(fired)} rules fired ({rule_types}). Signal: {composite_signal}. Phase: {phase}."

    return {
        "phase": phase,
        "union_type": union_type,
        "commitment_likelihood": round(commitment_likelihood, 3),
        "timing_phase": best_timing,
        "guidance": guidance,
        "active_labels": active_labels,
        "rule_summary": rule_summary,
        "composite_signal": composite_signal,
        "total_rules_fired": len(fired),
    }
