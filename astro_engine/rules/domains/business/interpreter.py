"""
Business Domain Interpreter

Optimization goal: ENTREPRENEURIAL GROWTH, COMMERCIAL SCALING, VENTURE TIMING
Vocabulary: launch, scale, pivot, consolidate, protect capital, expand, network

Business interprets the SAME symbolic conditions through a commercial lens:
- Saturn pressure = structural consolidation opportunity (not "avoid")
- Node activation = unconventional market disruption potential
- Mercury amplified = deal-making and commercial fluency peak
- Jupiter amplified = expansion and funding windows open
- Mars amplified = aggressive execution but overextension risk

Key differences from trading domain:
- Trading optimizes for DAILY execution timing
- Business optimizes for LIFECYCLE decisions (launch, scale, pivot, exit)
- Business has a longer time horizon (months/years, not days)
- Risk here = operational risk, not PnL drawdown
"""

from rules.domains.base import BaseDomainInterpreter


class BusinessInterpreter(BaseDomainInterpreter):
    domain_name = "business"
    optimization_goal = "entrepreneurial growth, commercial scaling, and venture timing"

    # Business-specific risk weights (calibrated for operational decisions)
    _RISK_WEIGHTS = {
        "node_crisis": 1.2,          # Nodes = market disruption / unconventional paths
        "sade_sati": 1.3,            # Saturn pressure = restructuring forced
        "chandrabala_8th": 1.5,      # 8th from Moon = hidden liabilities surface
        "kala_sarpa": 1.1,           # Concentrated axis = less flexibility
        "dainya": 1.3,               # Resource stress = cash flow pressure
        "jupiter_saturn_conflict": 1.4,  # Expansion vs restriction friction
    }

    def interpret(self, symbolic_state):
        themes = []
        opportunities = []
        challenges = []
        risk_points = 0

        # --- Kala Sarpa (business: focused single-axis growth) ---
        ks = symbolic_state.get("yogas", {}).get("kala_sarpa", {})
        if ks.get("condition") == "active":
            themes.append("concentrated business focus along one market axis")
            opportunities.append("Kala Sarpa — deep single-minded commercial focus, niche domination possible")
            challenges.append("Reduced diversification capacity — all eggs in one basket")
            risk_points += 10 * self._RISK_WEIGHTS["kala_sarpa"]

        # --- Sade Sati (business: operational restructuring) ---
        sade = symbolic_state.get("timing", {}).get("sade_sati", {})
        if sade.get("condition") == "peak":
            themes.append("major business restructuring phase")
            challenges.append("Sade Sati peak — existing business model under heavy pressure, pivot or restructure")
            opportunities.append("Opportunity to rebuild operations from stronger commercial foundation")
            risk_points += 25 * self._RISK_WEIGHTS["sade_sati"]
        elif sade.get("condition") == "rising":
            themes.append("business transition approaching")
            challenges.append("Sade Sati rising — current revenue model stability loosening")
            risk_points += 10
        elif sade.get("condition") == "ashtama":
            themes.append("hidden business transformation")
            opportunities.append("Behind-the-scenes restructuring may reveal new revenue streams")
            risk_points += 15

        # --- Chandrabala (business: 8th = hidden liabilities) ---
        chandra = symbolic_state.get("timing", {}).get("chandrabala", {})
        if chandra and chandra.get("count") == 8:
            themes.append("hidden business liabilities surfacing")
            challenges.append("8th from Moon — do NOT sign major contracts or close deals today")
            risk_points += 20 * self._RISK_WEIGHTS["chandrabala_8th"]
        elif chandra and chandra.get("count") in (10, 11):
            opportunities.append("High commercial visibility — excellent for pitching, networking, closing")

        # --- Moorthy (business: market receptivity) ---
        moorthy = symbolic_state.get("timing", {}).get("moorthy", {})
        if moorthy.get("grade") == "Loha":
            challenges.append("Market environment resistant — sales friction high, reduce outbound")
            risk_points += 12
        elif moorthy.get("grade") == "Swarna":
            opportunities.append("Market highly receptive — ideal for launches, pitches, expansion moves")

        # --- Dainya (business: cash flow pressure) ---
        dainya = symbolic_state.get("yogas", {}).get("dainya", {})
        if dainya.get("condition") == "active":
            themes.append("cash flow under stress from exchange obligations")
            challenges.append("Dainya yoga — revenue tied to difficult service obligations or debt covenants")
            opportunities.append("Growth through solving hard operational problems others avoid")
            risk_points += 15 * self._RISK_WEIGHTS["dainya"]

        # --- Mahapurusha (business: exceptional commercial capacity) ---
        mahap = symbolic_state.get("yogas", {}).get("mahapurusha", {})
        if mahap.get("condition") == "active":
            opportunities.append(f"Mahapurusha yoga — exceptional commercial execution capacity ({mahap.get('planets', '')})")
            themes.append("peak entrepreneurial expression period")

        # --- Dasha sandhi (business: strategic direction unclear) ---
        sandhi = symbolic_state.get("timing", {}).get("dasha_sandhi", {})
        if sandhi.get("condition") == "sandhi":
            themes.append("business strategy in transition")
            challenges.append("Dasha sandhi — avoid major investments, acquisitions, or launches during transition")
            risk_points += 15

        # --- Key planets for business ---
        for p in symbolic_state.get("planets", []):
            # Mercury = commerce, deals, communication
            if p["name"] == "Mercury":
                if p.get("intensity") == "amplified":
                    opportunities.append("Mercury amplified — deal-making, negotiations, and commercial fluency at peak")
                    themes.append("high commercial intelligence period")
                elif p.get("intensity") == "dormant":
                    challenges.append("Mercury dormant — commercial instincts dulled, avoid complex negotiations")
                    risk_points += 12

            # Jupiter = expansion, funding, growth
            if p["name"] == "Jupiter":
                if p.get("intensity") == "amplified":
                    opportunities.append("Jupiter amplified — expansion, funding, and growth opportunities accessible")
                elif p.get("intensity") == "dormant":
                    challenges.append("Jupiter dormant — growth capital and mentorship harder to access")
                    risk_points += 10

            # Mars = execution energy, but overextension risk
            if p["name"] == "Mars":
                if p.get("intensity") == "amplified":
                    opportunities.append("Mars amplified — aggressive execution energy, high productivity")
                    challenges.append("Mars amplified — watch for overextension, burnout, or premature scaling")

            # Saturn = structure, processes, longevity
            if p["name"] == "Saturn":
                if p.get("intensity") in ("amplified", "expressed"):
                    themes.append("discipline and structured operations rewarded")
                    opportunities.append("Saturn active — excellent for building processes, systems, and long-term infrastructure")

            # Sun = authority, leadership, brand visibility
            if p["name"] == "Sun":
                if p.get("intensity") == "amplified":
                    opportunities.append("Sun amplified — personal brand and leadership visibility enhanced")

        # --- Node pressure (business: market disruption) ---
        risk_pressure = symbolic_state.get("risk_pressure", {})
        node_crisis = risk_pressure.get("node_crisis", 0)
        if node_crisis > 30:
            themes.append("unconventional market disruption forces")
            challenges.append("High node crisis — established business patterns disrupted, adapt or pivot")
            opportunities.append("First-mover advantage in emerging unconventional markets")
            risk_points += 15 * self._RISK_WEIGHTS["node_crisis"]
        elif node_crisis < -10:
            opportunities.append("Node energy favorably supporting existing business structures")

        # --- Summary ---
        risk_level = self._classify_risk(risk_points)

        action_map = {
            "extreme": "PROTECT — halt expansion, secure existing revenue, preserve capital",
            "high": "CONSOLIDATE — strengthen current operations, avoid new ventures",
            "elevated": "CAUTIOUS GROWTH — continue operations with reduced risk appetite",
            "moderate": "EXECUTE — normal business operations, pursue calculated growth",
            "low": "SCALE — excellent period for launches, expansion, and bold moves",
        }

        return {
            "domain": self.domain_name,
            "optimization_goal": self.optimization_goal,
            "summary": f"Business outlook: {risk_level} risk, {len(opportunities)} opportunities active",
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
