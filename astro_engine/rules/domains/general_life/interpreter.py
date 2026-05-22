"""
General Life Domain Interpreter

Optimization goal: BALANCED ADAPTATION, GROWTH, AND MEANING
Vocabulary: phase, transition, growth, integration, patience, engagement

General Life provides a NEUTRAL balanced reading across all domains.
It does NOT over-weight risk (like trading) or over-weight opportunity (like spirituality).
It describes WHAT IS HAPPENING without prescribing a single optimization axis.
"""

from rules.domains.base import BaseDomainInterpreter


class GeneralLifeInterpreter(BaseDomainInterpreter):
    domain_name = "general_life"
    optimization_goal = "balanced adaptation, growth, and meaning"

    def interpret(self, symbolic_state):
        themes = []
        opportunities = []
        challenges = []
        risk_points = 0

        # --- Overall energy characterization ---
        planets = symbolic_state.get("planets", [])
        amplified = [p["name"] for p in planets if p.get("intensity") == "amplified"]
        dormant = [p["name"] for p in planets if p.get("intensity") == "dormant"]

        if amplified:
            themes.append(f"High-energy planets: {', '.join(amplified)}")
        if dormant:
            themes.append(f"Low-energy planets: {', '.join(dormant)}")

        # --- Kala Sarpa (general: focused life axis) ---
        ks = symbolic_state.get("yogas", {}).get("kala_sarpa", {})
        if ks.get("condition") == "active":
            themes.append("Life energy concentrated along one axis — less diversification, more depth")
            challenges.append("Reduced flexibility in life choices")
            opportunities.append("Deep focus available for singular pursuits")

        # --- Sade Sati (general: life restructuring) ---
        sade = symbolic_state.get("timing", {}).get("sade_sati", {})
        if sade.get("condition") == "peak":
            themes.append("Major life restructuring phase")
            challenges.append("Old life patterns dissolving — discomfort and uncertainty")
            opportunities.append("Foundation for next life chapter being laid")
            risk_points += 20
        elif sade.get("condition") in ("rising", "setting", "ashtama"):
            themes.append("Life transition in progress")
            risk_points += 10

        # --- Chandrabala (general: emotional day quality) ---
        chandra = symbolic_state.get("timing", {}).get("chandrabala", {})
        if chandra:
            themes.append(chandra.get("description", ""))

        # --- Moorthy (general: environmental support) ---
        moorthy = symbolic_state.get("timing", {}).get("moorthy", {})
        if moorthy.get("grade") == "Swarna":
            opportunities.append("Environment highly supportive of your intentions today")
        elif moorthy.get("grade") == "Loha":
            challenges.append("Environment somewhat resistant — extra effort needed")
            risk_points += 10

        # --- Dasha sandhi (general: life direction unclear) ---
        sandhi = symbolic_state.get("timing", {}).get("dasha_sandhi", {})
        if sandhi.get("condition") == "sandhi":
            themes.append("Life direction in transition — old chapter closing, new one opening")
            challenges.append("Avoid major irreversible decisions during transition")
            risk_points += 10

        # --- Yogas ---
        dainya = symbolic_state.get("yogas", {}).get("dainya", {})
        if dainya.get("condition") == "active":
            themes.append("Growth-through-challenge pattern active")
            challenges.append("Some life areas require extra effort")
            opportunities.append("Adversity producing hidden benefits")

        mahap = symbolic_state.get("yogas", {}).get("mahapurusha", {})
        if mahap.get("condition") == "active":
            opportunities.append(f"Exceptional personal capacity active — use it")

        # --- Summary characterization ---
        risk_level = self._classify_risk(risk_points)

        # General life uses descriptive, not prescriptive language
        intensity_descriptions = {
            "extreme": "HIGH INSTABILITY / HIGH TRANSFORMATION",
            "high": "SIGNIFICANT TRANSITION",
            "elevated": "MODERATE CHANGE",
            "moderate": "STEADY DEVELOPMENT",
            "low": "STABLE GROWTH",
        }

        action_map = {
            "extreme": "ADAPT — major life changes in progress, flexibility essential",
            "high": "NAVIGATE — significant transitions, stay grounded",
            "elevated": "ADJUST — some areas require attention and adaptation",
            "moderate": "ENGAGE — life flowing normally, pursue goals",
            "low": "FLOURISH — stable period, excellent for building",
        }

        return {
            "domain": self.domain_name,
            "optimization_goal": self.optimization_goal,
            "summary": intensity_descriptions[risk_level],
            "intensity": risk_level,
            "themes": themes,
            "opportunities": opportunities,
            "challenges": challenges,
            "action_guidance": action_map[risk_level],
            "risk_level": risk_level,
            "risk_points": round(risk_points, 1),
            "risk_factors": challenges,
        }
