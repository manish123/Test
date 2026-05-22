"""
Spirituality Domain Interpreter

Optimization goal: INNER AWARENESS, DETACHMENT, AWAKENING
Vocabulary: deepening, withdrawal, insight, surrender, integration, awakening

Spirituality interprets "difficult" conditions as OPPORTUNITIES:
- Saturn = discipline, tapas, maturation
- Nodes = karmic acceleration, past-life resolution
- Isolation = withdrawal for inner work
- Transformation = death of ego patterns
"""

from rules.domains.base import BaseDomainInterpreter


class SpiritualityInterpreter(BaseDomainInterpreter):
    domain_name = "spirituality"
    optimization_goal = "inner awareness, detachment, and awakening"

    def interpret(self, symbolic_state):
        themes = []
        opportunities = []
        challenges = []
        risk_points = 0  # Spirituality rarely sees "risk" — mostly opportunity

        # Kala Sarpa → spiritual: intense karmic acceleration
        ks = symbolic_state.get("yogas", {}).get("kala_sarpa", {})
        if ks.get("condition") == "active":
            opportunities.append("Kala Sarpa — concentrated karmic processing, ideal for deep meditation")
            themes.append("karmic acceleration")

        # Sade Sati → spiritual: tapas and maturation
        sade = symbolic_state.get("timing", {}).get("sade_sati", {})
        if sade.get("condition") in ("peak", "ashtama"):
            opportunities.append(f"Sade Sati {sade['condition']} — profound spiritual maturation through tapas")
            themes.append("ego dissolution through discipline")
        elif sade.get("condition") in ("rising", "setting"):
            opportunities.append("Saturn preparing/integrating spiritual lessons")
            themes.append("inner restructuring")

        # Chandrabala 8th → spiritual: death/rebirth of patterns
        chandra = symbolic_state.get("timing", {}).get("chandrabala", {})
        if chandra and chandra.get("count") == 8:
            opportunities.append("8th from Moon — excellent for occult study, past-life work, kundalini")
            themes.append("transformation of consciousness")
        elif chandra and chandra.get("count") == 12:
            opportunities.append("12th from Moon — natural withdrawal, meditation comes easily")
            themes.append("dissolution and surrender")

        # Ketu state → spiritual: natural detachment
        for p in symbolic_state.get("planets", []):
            if p["name"] == "Ketu":
                if p.get("intensity") in ("expressed", "amplified"):
                    opportunities.append("Ketu active — natural detachment and intuition heightened")
                    themes.append("moksha energy available")
            if p["name"] == "Jupiter":
                if p.get("intensity") == "amplified":
                    opportunities.append("Jupiter amplified — guru grace, wisdom teachings accessible")
                elif p.get("intensity") == "dormant":
                    challenges.append("Jupiter dormant — spiritual guidance harder to access")
                    risk_points += 10

        # Dainya → spiritual: growth through service and suffering
        dainya = symbolic_state.get("yogas", {}).get("dainya", {})
        if dainya.get("condition") == "active":
            opportunities.append("Dainya yoga — spiritual growth through service to those suffering")
            themes.append("karma yoga activation")

        # Nodes → spiritual: past-life resolution
        risk_pressure = symbolic_state.get("risk_pressure", {})
        if risk_pressure.get("node_crisis", 0) > 30:
            opportunities.append("High nodal energy — past-life themes surfacing for resolution")
            themes.append("ancestral/karmic clearing")

        risk_level = self._classify_risk(risk_points)
        action_map = {
            "extreme": "STILLNESS — deep rest, let transformation complete itself",
            "high": "SURRENDER — accept what is, practice non-resistance",
            "elevated": "CONTEMPLATE — journaling, study, gentle inquiry",
            "moderate": "PRACTICE — regular sadhana, meditation, mantra",
            "low": "EXPAND — excellent for retreats, initiations, deep practices",
        }

        return {
            "domain": self.domain_name,
            "optimization_goal": self.optimization_goal,
            "summary": f"Spiritual climate: {'rich' if len(opportunities) > 2 else 'quiet'} ({len(opportunities)} opportunities)",
            "intensity": "high_opportunity" if len(opportunities) > 2 else "moderate",
            "themes": themes,
            "opportunities": opportunities,
            "challenges": challenges,
            "action_guidance": action_map[risk_level],
            "risk_level": risk_level,
            "risk_points": round(risk_points, 1),
            "risk_factors": challenges,
        }
