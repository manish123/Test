"""
Arbitration Engine — Resolve contradictory astrological signatures.

Uses the arbitration_rules.json registry to determine which planetary
energies dominate, which are suppressed, and how conflicts resolve.
"""

from symbolic.registry_loader import get_arbitration_rules


def resolve_conflicts(chart_state):
    """
    Identify and resolve contradictory signatures in the chart.

    Returns dict with: arbitration_results, suppressed_energies,
                       amplified_energies, dominant_vectors, resolved_paths
    """
    rules = get_arbitration_rules()
    if not rules:
        return {"arbitration_results": [], "suppressed_energies": [], "amplified_energies": []}

    results = []
    suppressed = []
    amplified = []

    planets = chart_state.planets

    # Check for Graha Yuddha (planetary war) — arb_004
    _check_graha_yuddha(planets, results, suppressed, amplified)

    # Check for Mercury chameleon effect — arb_006
    _check_mercury_association(planets, results, suppressed, amplified)

    # Check for compound relationships — arb_001
    _check_compound_relationships(chart_state, results)

    return {
        "arbitration_results": results,
        "suppressed_energies": suppressed,
        "amplified_energies": amplified,
        "dominant_vectors": [r["dominant"] for r in results if "dominant" in r],
        "resolved_paths": [r.get("resolution", "") for r in results],
    }


def _check_graha_yuddha(planets, results, suppressed, amplified):
    """Check for planets within 1 degree (planetary war)."""
    combat_planets = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    for i, p1 in enumerate(combat_planets):
        for p2 in combat_planets[i+1:]:
            if p1 not in planets or p2 not in planets:
                continue
            lon1 = planets[p1].get("longitude", 0)
            lon2 = planets[p2].get("longitude", 0)
            diff = abs((lon1 - lon2) % 360)
            diff = min(diff, 360 - diff)
            if diff <= 1.0:
                # Venus always wins
                if "Venus" in (p1, p2):
                    winner = "Venus"
                    loser = p2 if p1 == "Venus" else p1
                else:
                    # Higher latitude wins (simplified: use longitude as proxy)
                    winner = p1 if lon1 > lon2 else p2
                    loser = p2 if winner == p1 else p1
                results.append({
                    "type": "graha_yuddha",
                    "planets": [p1, p2],
                    "dominant": winner,
                    "subordinate": loser,
                    "resolution": f"{winner} conquers {loser} in planetary war",
                    "rule_ref": "arb_004",
                })
                suppressed.append({"planet": loser, "reason": f"defeated in war by {winner}"})
                amplified.append({"planet": winner, "reason": f"victorious in war over {loser}"})


def _check_mercury_association(planets, results, suppressed, amplified):
    """Check Mercury's association — it adopts the nature of conjunct planets."""
    if "Mercury" not in planets:
        return
    merc_house = planets["Mercury"]["house"]
    malefics_same_house = [n for n in ("Mars", "Saturn", "Rahu", "Ketu")
                          if n in planets and planets[n]["house"] == merc_house]
    benefics_same_house = [n for n in ("Jupiter", "Venus", "Moon")
                          if n in planets and planets[n]["house"] == merc_house]

    if malefics_same_house and not benefics_same_house:
        results.append({
            "type": "mercury_assimilation",
            "dominant": malefics_same_house[0],
            "subordinate": "Mercury",
            "resolution": f"Mercury adopts malefic nature from {malefics_same_house[0]}",
            "rule_ref": "arb_006",
        })
        suppressed.append({"planet": "Mercury", "reason": "neutrality suppressed by malefic association"})
    elif benefics_same_house and not malefics_same_house:
        results.append({
            "type": "mercury_assimilation",
            "dominant": benefics_same_house[0],
            "subordinate": "Mercury",
            "resolution": f"Mercury adopts benefic nature from {benefics_same_house[0]}",
            "rule_ref": "arb_006",
        })
        amplified.append({"planet": "Mercury", "reason": "enhanced by benefic association"})


def _check_compound_relationships(chart_state, results):
    """Check for compound relationship conflicts (natural vs temporary)."""
    # Simplified: flag if lagna lord and 7th lord are natural enemies
    from features.dignity import SIGN_LORDS
    seventh_sign = ((chart_state.asc_sign + 6 - 1) % 12) + 1
    seventh_lord = SIGN_LORDS[seventh_sign]
    lagna_lord = chart_state.lagna_lord

    if lagna_lord != seventh_lord:
        # Check if they're in each other's houses (temporary friendship despite natural enmity)
        ll_house = chart_state.planets.get(lagna_lord, {}).get("house", 0)
        sl_house = chart_state.planets.get(seventh_lord, {}).get("house", 0)
        if ll_house == 7 or sl_house == 1:
            results.append({
                "type": "compound_relationship",
                "planets": [lagna_lord, seventh_lord],
                "resolution": "Natural tension neutralized by positional friendship (Parivartana-like)",
                "rule_ref": "arb_001",
            })
