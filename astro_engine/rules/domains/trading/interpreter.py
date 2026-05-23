"""
Trading Domain Interpreter

Optimization goal: CAPITAL PRESERVATION + EXECUTION TIMING
Vocabulary: avoid, reduce leverage, block entry, directional bias, position size

This domain is AGGRESSIVE about risk avoidance because:
- Losses compound exponentially
- A single bad day can erase a week of gains
- Emotional trading under pressure causes drawdown spirals
"""

from rules.domains.base import BaseDomainInterpreter


class TradingInterpreter(BaseDomainInterpreter):
    domain_name = "trading"
    optimization_goal = "capital preservation and execution timing"

    # Trading-specific risk multipliers (amplified vs general life)
    _RISK_WEIGHTS = {
        "node_crisis": 1.5,       # Nodes = unpredictable = dangerous for capital
        "maraka": 1.2,            # Maraka = loss potential
        "sade_sati": 1.0,         # Saturn pressure = slow grinding losses
        "chandrabala_8th": 2.0,   # 8th from Moon = transformation = DO NOT TRADE
        "kala_sarpa": 1.3,        # Concentrated energy = whipsaw potential
        "dainya": 1.4,            # Exchange yoga = resources under stress
    }

    def interpret(self, symbolic_state):
        themes = []
        opportunities = []
        challenges = []
        risk_points = 0

        # --- Kala Sarpa (trading: whipsaw risk) ---
        ks = symbolic_state.get("yogas", {}).get("kala_sarpa", {})
        if ks.get("condition") == "active":
            challenges.append("Kala Sarpa active — concentrated energy = whipsaw potential, reduce position size")
            risk_points += 25 * self._RISK_WEIGHTS["kala_sarpa"]
            themes.append("axis-bound volatility")

        # --- Sade Sati (trading: slow grinding losses) ---
        sade = symbolic_state.get("timing", {}).get("sade_sati", {})
        if sade.get("condition") not in ("none", None):
            challenges.append(f"Sade Sati ({sade['condition']}) — systematic pressure on emotional decision-making")
            risk_points += 15 * self._RISK_WEIGHTS["sade_sati"]
            themes.append("emotional discipline under test")

        # --- Chandrabala (trading: 8th = hard block) ---
        chandra = symbolic_state.get("timing", {}).get("chandrabala", {})
        if chandra and chandra.get("count") == 8:
            challenges.append("Chandrabala 8th — transformation axis active, NOT a trading day")
            risk_points += 40 * self._RISK_WEIGHTS["chandrabala_8th"]
            themes.append("hard execution block")

        # --- Moorthy (trading: Loha = reduce size) ---
        moorthy = symbolic_state.get("timing", {}).get("moorthy", {})
        if moorthy.get("grade") == "Loha":
            challenges.append("Moorthy Loha — environment resists intentions, reduce exposure")
            risk_points += 15
        elif moorthy.get("grade") == "Swarna":
            opportunities.append("Moorthy Swarna — environment supports execution")

        # --- Dainya (trading: resources under stress) ---
        dainya = symbolic_state.get("yogas", {}).get("dainya", {})
        if dainya.get("condition") == "active":
            challenges.append("Dainya yoga — capital/resources connected to challenging exchanges")
            risk_points += 20 * self._RISK_WEIGHTS["dainya"]

        # --- Mahapurusha (trading: structural advantage) ---
        mahap = symbolic_state.get("yogas", {}).get("mahapurusha", {})
        if mahap.get("condition") == "active":
            opportunities.append(f"Mahapurusha active ({mahap['planets']}) — structural advantage for conviction trades")

        # --- Node pressure (trading: unpredictability) ---
        risk_pressure = symbolic_state.get("risk_pressure", {})
        node_crisis = risk_pressure.get("node_crisis", 0)
        if node_crisis > 30:
            challenges.append("High node crisis — extreme unpredictability, stay flat")
            risk_points += node_crisis * 0.5 * self._RISK_WEIGHTS["node_crisis"]
        elif node_crisis > 0:
            challenges.append("Moderate node pressure — reduce directional bets")
            risk_points += node_crisis * 0.3

        # --- Planet intensity (trading: low multiplier dasha lord = weak conviction) ---
        for p in symbolic_state.get("planets", []):
            if p.get("intensity") == "dormant" and p.get("name") in ["Jupiter", "Mercury"]:
                challenges.append(f"{p['name']} dormant — {p['name']}-related setups lack conviction")

        # --- Tara (trading: negative = adverse timing) ---
        tara = symbolic_state.get("tara", {})
        if tara.get("score", 0) < -5:
            challenges.append("Tara strongly negative — timing friction against entries")
            risk_points += 15

        # --- Summary ---
        risk_level = self._classify_risk(risk_points)

        action_map = {
            "extreme": "AVOID — do not trade, capital preservation mode",
            "high": "AVOID or minimal size — wait for better alignment",
            "elevated": "LOW SIZE — reduced exposure, tight stops, no averaging",
            "moderate": "MODERATE — normal size, follow system signals",
            "low": "FULL EXECUTION — conditions support conviction trades",
        }

        return {
            "domain": self.domain_name,
            "optimization_goal": self.optimization_goal,
            "summary": f"Trading risk: {risk_level} ({risk_points:.0f} pts)",
            "intensity": risk_level,
            "themes": themes,
            "opportunities": opportunities,
            "challenges": challenges,
            "action_guidance": action_map[risk_level],
            "risk_level": risk_level,
            "risk_points": round(risk_points, 1),
            "risk_factors": [c for c in challenges],
            "activated_events": [(e.event_id, e.title, s) for e, s in self.get_activated_events(symbolic_state)[:10]],
        }
