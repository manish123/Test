"""
Career Domain Interpreter

Optimization goal: PROFESSIONAL GROWTH, AUTHORITY, ACHIEVEMENT
Vocabulary: restructuring, opportunity, visibility, leadership, patience

Career interprets the SAME conditions very differently from trading:
- Saturn pressure = restructuring opportunity (not "avoid")
- Node activation = unconventional career paths opening
- High intensity = visibility period (not "volatility")
"""

from rules.domains.base import BaseDomainInterpreter


class CareerInterpreter(BaseDomainInterpreter):
    domain_name = "career"
    optimization_goal = "professional growth, authority, and achievement"

    def interpret(self, symbolic_state):
        themes = []
        opportunities = []
        challenges = []
        risk_points = 0

        # --- Kala Sarpa (career: focused ambition axis) ---
        ks = symbolic_state.get("yogas", {}).get("kala_sarpa", {})
        if ks.get("condition") == "active":
            themes.append("concentrated career focus along one axis")
            opportunities.append("Kala Sarpa — deep single-minded professional focus available")
            # In career, this is neutral-to-positive (focus is an asset)

        # --- Sade Sati (career: organizational restructuring) ---
        sade = symbolic_state.get("timing", {}).get("sade_sati", {})
        if sade.get("condition") == "peak":
            themes.append("major professional restructuring")
            challenges.append("Sade Sati peak — old career structures dissolving, rebuild required")
            opportunities.append("Opportunity to rebuild professional identity from stronger foundation")
            risk_points += 20
        elif sade.get("condition") == "rising":
            themes.append("career transition preparing")
            challenges.append("Sade Sati rising — current role stability loosening")
        elif sade.get("condition") == "ashtama":
            themes.append("deep professional transformation")
            opportunities.append("Hidden career opportunities through unconventional paths")

        # --- Chandrabala (career: 8th = behind-the-scenes work) ---
        chandra = symbolic_state.get("timing", {}).get("chandrabala", {})
        if chandra and chandra.get("count") == 8:
            themes.append("behind-the-scenes professional work")
            challenges.append("Not a visibility day — work will not be publicly recognized today")
            # NOT a "hard block" like trading — just reduced visibility
            risk_points += 10
        elif chandra and chandra.get("count") in (10, 11):
            opportunities.append("High professional visibility — actions get noticed")

        # --- Moorthy (career: Loha = extra effort needed) ---
        moorthy = symbolic_state.get("timing", {}).get("moorthy", {})
        if moorthy.get("grade") == "Loha":
            challenges.append("Extra effort required for professional outcomes today")
            risk_points += 10
        elif moorthy.get("grade") == "Swarna":
            opportunities.append("Professional environment highly receptive to your initiatives")

        # --- Dainya (career: growth through adversity) ---
        dainya = symbolic_state.get("yogas", {}).get("dainya", {})
        if dainya.get("condition") == "active":
            themes.append("growth through professional adversity")
            opportunities.append("Dainya yoga — career advancement linked to solving difficult problems")
            challenges.append("Resources may be tied to challenging service obligations")

        # --- Mahapurusha (career: exceptional structural power) ---
        mahap = symbolic_state.get("yogas", {}).get("mahapurusha", {})
        if mahap.get("condition") == "active":
            opportunities.append(f"Mahapurusha yoga — exceptional professional capacity active ({mahap['planets']})")
            themes.append("peak professional expression period")

        # --- Dasha sandhi (career: transition between themes) ---
        sandhi = symbolic_state.get("timing", {}).get("dasha_sandhi", {})
        if sandhi.get("condition") == "sandhi":
            themes.append("professional direction in transition")
            challenges.append("Career themes shifting — avoid major commitments during transition")
            risk_points += 15

        # --- Key planets for career ---
        for p in symbolic_state.get("planets", []):
            if p["name"] == "Sun" and p.get("intensity") == "amplified":
                opportunities.append("Sun amplified — leadership visibility and authority enhanced")
            if p["name"] == "Saturn" and p.get("intensity") in ("amplified", "expressed"):
                themes.append("discipline and structured effort rewarded")
            if p["name"] == "Jupiter" and p.get("intensity") == "dormant":
                challenges.append("Jupiter dormant — mentorship and expansion opportunities limited")
                risk_points += 10

        # --- Node pressure (career: unconventional paths) ---
        risk_pressure = symbolic_state.get("risk_pressure", {})
        node_crisis = risk_pressure.get("node_crisis", 0)
        if node_crisis > 30:
            themes.append("unconventional career disruption")
            challenges.append("Established professional path under pressure — adapt or pivot")
            opportunities.append("Unconventional opportunities may emerge from disruption")
            risk_points += 15
        elif node_crisis < -10:
            opportunities.append("Node energy favorably supporting professional structures")

        # --- Summary ---
        risk_level = self._classify_risk(risk_points)

        action_map = {
            "extreme": "PAUSE — major restructuring needed before advancing",
            "high": "CONSOLIDATE — protect current position, avoid risky moves",
            "elevated": "STEADY EFFORT — continue with caution, no major pivots",
            "moderate": "ADVANCE — normal professional engagement, take calculated steps",
            "low": "EXPAND — excellent period for professional growth and visibility",
        }

        return {
            "domain": self.domain_name,
            "optimization_goal": self.optimization_goal,
            "summary": f"Career outlook: {risk_level} challenge, active themes: {len(themes)}",
            "intensity": risk_level,
            "themes": themes,
            "opportunities": opportunities,
            "challenges": challenges,
            "action_guidance": action_map[risk_level],
            "risk_level": risk_level,
            "risk_points": round(risk_points, 1),
            "risk_factors": [c for c in challenges],
        }
