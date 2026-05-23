"""
Base Domain Interpreter — Protocol all domain interpreters must follow.

Each domain interpreter takes the SAME symbolic_state input
and produces domain-specific meaning.

Now event-aware: each interpreter can query its domain-specific events
from the V3 event ontology via the event registry.
"""

from rules.event_registry import (
    get_events_for_domain,
    get_positive_events_for_domain,
    get_negative_events_for_domain,
    get_events_for_domain_and_house,
    get_events_for_domain_and_planet,
    get_domain_event_summary,
)


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

    # ── Event Ontology Awareness ──────────────────────────────────────────────

    def get_my_events(self):
        """Get all events tagged for this domain from V3 ontology."""
        return get_events_for_domain(self.domain_name)

    def get_my_positive_events(self):
        """Get positive-polarity events for this domain."""
        return get_positive_events_for_domain(self.domain_name)

    def get_my_negative_events(self):
        """Get negative-polarity events for this domain."""
        return get_negative_events_for_domain(self.domain_name)

    def get_my_events_for_house(self, house):
        """Get events for this domain activated by a specific house."""
        return get_events_for_domain_and_house(self.domain_name, house)

    def get_my_events_for_planet(self, planet):
        """Get events for this domain where planet is a significator."""
        return get_events_for_domain_and_planet(self.domain_name, planet)

    def get_my_event_summary(self):
        """Get category breakdown of events in this domain."""
        return get_domain_event_summary(self.domain_name)

    def get_activated_events(self, symbolic_state):
        """
        Determine which domain events are potentially activated given the symbolic state.

        Checks:
        - Which planets are amplified/expressed → match to event significators
        - Which houses have active planets → match to event houses

        Returns:
            list of (event, activation_strength) tuples, sorted by strength descending
        """
        my_events = self.get_my_events()
        if not my_events:
            return []

        # Build sets of active planets and occupied houses from symbolic state
        active_planets = set()
        occupied_houses = set()
        for p in symbolic_state.get("planets", []):
            if p.get("intensity") in ("amplified", "expressed"):
                active_planets.add(p["name"])
            house = p.get("house")
            if house:
                occupied_houses.add(house)

        # Score each event by how many significators/houses are active
        activated = []
        for event in my_events:
            planet_hits = len(set(event.planetary_significators) & active_planets)
            house_hits = len(set(event.houses) & occupied_houses)
            strength = planet_hits * 2 + house_hits  # planets weighted 2x
            if strength > 0:
                activated.append((event, strength))

        activated.sort(key=lambda x: -x[1])
        return activated
