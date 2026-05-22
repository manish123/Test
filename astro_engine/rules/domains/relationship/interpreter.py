"""
Relationship Domain Interpreter

Optimization goal: EMOTIONAL CONNECTION, PARTNERSHIP DEPTH, FAMILY HARMONY
Vocabulary: bonding, distance, karmic lessons, deepening, patience, openness

Relationship interprets conditions through the lens of emotional bonds:
- Saturn = commitment testing (not "loss")
- Nodes = karmic connections (not "crisis")
- Transformation = relationship evolution (not "danger")
"""

from rules.domains.base import BaseDomainInterpreter


class RelationshipInterpreter(BaseDomainInterpreter):
    domain_name = "relationship"
    optimization_goal = "emotional connection, partnership depth, family harmony"

    def interpret(self, symbolic_state):
        themes = []
        opportunities = []
        challenges = []
        risk_points = 0

        # --- Kala Sarpa (relationship: intense karmic bonds) ---
        ks = symbolic_state.get("yogas", {}).get("kala_sarpa", {})
        if ks.get("condition") == "active":
            themes.append("intense karmic relationship patterns active")
            challenges.append("Kala Sarpa — relationships feel fated, less flexibility in patterns")
            opportunities.append("Deep karmic connections available — soul-level bonding possible")

        # --- Sade Sati (relationship: commitment testing) ---
        sade = symbolic_state.get("timing", {}).get("sade_sati", {})
        if sade.get("condition") == "peak":
            themes.append("relationship foundations being tested")
            challenges.append("Sade Sati peak — emotional distance or coldness possible, patience required")
            opportunities.append("Relationships that survive this become unshakeable")
            risk_points += 25
        elif sade.get("condition") in ("rising", "setting"):
            themes.append("relationship patterns shifting")
            challenges.append("Old emotional patterns loosening — discomfort in familiar dynamics")

        # --- Chandrabala (relationship: emotional receptivity) ---
        chandra = symbolic_state.get("timing", {}).get("chandrabala", {})
        if chandra and chandra.get("count") == 8:
            themes.append("emotional transformation in relationships")
            challenges.append("8th from Moon — hidden feelings surfacing, vulnerability required")
            opportunities.append("Deep emotional honesty possible — transformation through intimacy")
            risk_points += 15
        elif chandra and chandra.get("count") in (1, 4, 7):
            opportunities.append("Emotional availability high — good for connection and bonding")

        # --- Moorthy (relationship: receptivity to partner) ---
        moorthy = symbolic_state.get("timing", {}).get("moorthy", {})
        if moorthy.get("grade") == "Loha":
            challenges.append("Reduced emotional receptivity — partner's signals may be missed")
            risk_points += 10
        elif moorthy.get("grade") == "Swarna":
            opportunities.append("High emotional receptivity — attuned to partner's needs")

        # --- Venus state (key planet for relationships) ---
        for p in symbolic_state.get("planets", []):
            if p["name"] == "Venus":
                if p.get("intensity") == "amplified":
                    opportunities.append("Venus amplified — love, beauty, and harmony enhanced")
                elif p.get("intensity") == "dormant":
                    challenges.append("Venus dormant — romantic/aesthetic expression subdued")
                    risk_points += 15
                if p.get("combustion", {}).get("condition") == "combust":
                    challenges.append("Venus combust — relationship needs merged with ego demands")
                    risk_points += 10

            if p["name"] == "Moon":
                if p.get("intensity") == "amplified":
                    opportunities.append("Moon amplified — emotional intelligence and nurturing enhanced")
                elif p.get("intensity") in ("restricted", "dormant"):
                    challenges.append("Moon subdued — emotional expression feels blocked")
                    risk_points += 10

        # --- Dainya (relationship: growth through challenges) ---
        dainya = symbolic_state.get("yogas", {}).get("dainya", {})
        if dainya.get("condition") == "active":
            themes.append("relationship growth through shared challenges")
            opportunities.append("Bonds deepen through navigating difficulty together")

        # --- Node pressure (relationship: karmic patterns) ---
        risk_pressure = symbolic_state.get("risk_pressure", {})
        node_crisis = risk_pressure.get("node_crisis", 0)
        if node_crisis > 30:
            themes.append("karmic relationship patterns intensifying")
            challenges.append("Past-life patterns resurfacing in current relationships")
            opportunities.append("Chance to resolve deep karmic debts with loved ones")

        # --- Summary ---
        risk_level = self._classify_risk(risk_points)

        action_map = {
            "extreme": "SPACE — give yourself and partner breathing room, avoid confrontation",
            "high": "PATIENCE — relationships under pressure, practice compassion",
            "elevated": "GENTLE EFFORT — maintain connection with extra care",
            "moderate": "ENGAGE — normal relationship engagement, be present",
            "low": "DEEPEN — excellent period for intimacy, bonding, and new connections",
        }

        return {
            "domain": self.domain_name,
            "optimization_goal": self.optimization_goal,
            "summary": f"Relationship climate: {risk_level} challenge",
            "intensity": risk_level,
            "themes": themes,
            "opportunities": opportunities,
            "challenges": challenges,
            "action_guidance": action_map[risk_level],
            "risk_level": risk_level,
            "risk_points": round(risk_points, 1),
            "risk_factors": [c for c in challenges],
        }
