"""
Health Domain Interpreter

Optimization goal: PHYSICAL VITALITY, RECOVERY, LONGEVITY
Vocabulary: vitality, rest, recovery, strain, resilience, healing
"""

from rules.domains.base import BaseDomainInterpreter


class HealthInterpreter(BaseDomainInterpreter):
    domain_name = "health"
    optimization_goal = "physical vitality, recovery, and longevity"

    def interpret(self, symbolic_state):
        themes = []
        opportunities = []
        challenges = []
        risk_points = 0

        # Sade Sati → chronic strain
        sade = symbolic_state.get("timing", {}).get("sade_sati", {})
        if sade.get("condition") == "peak":
            challenges.append("Sade Sati peak — chronic fatigue or low vitality possible, prioritize rest")
            risk_points += 25
        elif sade.get("condition") == "ashtama":
            challenges.append("Ashtama Shani — hidden health issues may surface, get checkups")
            risk_points += 30

        # Mars state → physical energy
        for p in symbolic_state.get("planets", []):
            if p["name"] == "Mars":
                if p.get("intensity") == "amplified":
                    opportunities.append("Mars amplified — physical energy and stamina high")
                elif p.get("intensity") in ("restricted", "dormant"):
                    challenges.append("Mars subdued — low physical energy, avoid overexertion")
                    risk_points += 15
            if p["name"] == "Sun":
                if p.get("intensity") == "dormant":
                    challenges.append("Sun dormant — vitality and immunity reduced")
                    risk_points += 15

        # Moorthy
        moorthy = symbolic_state.get("timing", {}).get("moorthy", {})
        if moorthy.get("grade") == "Loha":
            challenges.append("Body-environment friction — susceptibility to illness higher")
            risk_points += 10

        # Node pressure → sudden health events
        risk_pressure = symbolic_state.get("risk_pressure", {})
        if risk_pressure.get("node_crisis", 0) > 40:
            challenges.append("High node crisis — unexpected health events possible, be vigilant")
            risk_points += 20

        risk_level = self._classify_risk(risk_points)
        action_map = {
            "extreme": "REST — prioritize recovery, avoid strenuous activity",
            "high": "CAUTION — light activity only, monitor symptoms",
            "elevated": "MODERATE — normal activity with extra rest",
            "moderate": "ACTIVE — maintain healthy routines",
            "low": "THRIVE — excellent vitality period, push physical boundaries",
        }

        return {
            "domain": self.domain_name,
            "optimization_goal": self.optimization_goal,
            "summary": f"Health outlook: {risk_level}",
            "intensity": risk_level,
            "themes": themes,
            "opportunities": opportunities,
            "challenges": challenges,
            "action_guidance": action_map[risk_level],
            "risk_level": risk_level,
            "risk_points": round(risk_points, 1),
            "risk_factors": challenges,
        }
