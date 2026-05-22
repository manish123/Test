"""
Base Domain Interpreter — Protocol all domain interpreters must follow.

Each domain interpreter takes the SAME symbolic_state input
and produces domain-specific meaning.
"""


class BaseDomainInterpreter:
    """
    Base class for domain interpretation profiles.

    All interpreters receive the same symbolic_state dict (from Layer C1)
    and produce domain-specific readings.
    """

    domain_name = "base"
    optimization_goal = "undefined"

    # What this domain optimizes for (different per domain)
    # Trading: capital preservation
    # Career: professional growth
    # Relationship: emotional connection
    # Health: physical vitality
    # Spirituality: inner awareness

    def interpret(self, symbolic_state):
        """
        Interpret symbolic state through this domain's lens.

        Args:
            symbolic_state: dict from rules.symbolic.planetary_conditions.build_symbolic_state()

        Returns:
            dict with:
                "domain": str — which domain lens was applied
                "summary": str — one-line domain-specific reading
                "intensity": str — overall intensity level
                "themes": list[str] — active life themes in this domain
                "opportunities": list[str] — what's favorable in this domain
                "challenges": list[str] — what requires attention in this domain
                "action_guidance": str — what to do (domain-specific vocabulary)
                "risk_level": str — low/moderate/elevated/high/extreme
                "risk_factors": list[str] — specific risks in this domain
        """
        raise NotImplementedError("Each domain must implement interpret()")

    def _classify_risk(self, risk_points):
        """Universal risk classification from accumulated points."""
        if risk_points >= 80:
            return "extreme"
        if risk_points >= 60:
            return "high"
        if risk_points >= 40:
            return "elevated"
        if risk_points >= 20:
            return "moderate"
        return "low"

    def _extract_active_planets(self, symbolic_state, min_intensity="expressed"):
        """Get planets above a certain intensity threshold."""
        intensity_order = ["dormant", "restricted", "subdued", "expressed", "amplified"]
        threshold_idx = intensity_order.index(min_intensity)
        active = []
        for p in symbolic_state.get("planets", []):
            p_idx = intensity_order.index(p.get("intensity", "expressed"))
            if p_idx >= threshold_idx:
                active.append(p)
        return active
