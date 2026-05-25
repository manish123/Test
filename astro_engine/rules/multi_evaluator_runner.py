"""
Multi-Evaluator Runner — Runs all domain evaluators for a single person.

Provides:
- evaluate_all_domains(birth_dt, lat, lon, eval_date) → combined result dict
- scan_timeline(birth_dt, lat, lon, start_date, end_date, step_months) → timeline

Usage:
    python rules/multi_evaluator_runner.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rules.evaluator_base import SIGN_NAMES, BaseChartState, BaseTransitState


# ═══════════════════════════════════════════════════════════════
# EVALUATOR REGISTRY
# ═══════════════════════════════════════════════════════════════

def _load_evaluators():
    """
    Dynamically load all available evaluators.
    Returns dict of {domain_name: evaluator_module}.
    """
    evaluators = {}

    try:
        from rules import wealth_evaluator
        evaluators["wealth"] = wealth_evaluator
    except ImportError:
        pass

    try:
        from rules import marriage_evaluator
        evaluators["marriage"] = marriage_evaluator
    except ImportError:
        pass

    try:
        from rules import career_evaluator
        evaluators["career"] = career_evaluator
    except ImportError:
        pass

    try:
        from rules import business_evaluator
        evaluators["business"] = business_evaluator
    except ImportError:
        pass

    try:
        from rules import childbirth_evaluator
        evaluators["childbirth"] = childbirth_evaluator
    except ImportError:
        pass

    try:
        from rules import property_evaluator
        evaluators["property"] = property_evaluator
    except ImportError:
        pass

    try:
        from rules import property_purchase_evaluator
        evaluators["property_purchase"] = property_purchase_evaluator
    except ImportError:
        pass

    try:
        from rules import medical_evaluator
        evaluators["medical"] = medical_evaluator
    except ImportError:
        pass

    try:
        from rules import fame_evaluator
        evaluators["fame"] = fame_evaluator
    except ImportError:
        pass

    try:
        from rules import relocation_evaluator
        evaluators["relocation"] = relocation_evaluator
    except ImportError:
        pass

    try:
        from rules import financial_crisis_evaluator
        evaluators["financial_crisis"] = financial_crisis_evaluator
    except ImportError:
        pass

    try:
        from rules import vehicle_purchase_evaluator
        evaluators["vehicle_purchase"] = vehicle_purchase_evaluator
    except ImportError:
        pass

    try:
        from rules import parent_loss_evaluator
        evaluators["parent_loss"] = parent_loss_evaluator
    except ImportError:
        pass

    return evaluators


# ═══════════════════════════════════════════════════════════════
# SINGLE-DATE MULTI-DOMAIN EVALUATION
# ═══════════════════════════════════════════════════════════════

def evaluate_all_domains(birth_dt, lat, lon, eval_date, alt=0):
    """
    Run all available evaluators for a single date.

    Returns dict: {domain_name: {score, likelihood, timing_band, fired_rules, ...}}
    """
    evaluators = _load_evaluators()
    results = {}

    for domain_name, mod in evaluators.items():
        try:
            # Wealth evaluator has evaluate_wealth_for_date
            if domain_name == "wealth":
                chart = mod.ChartState(birth_dt, lat, lon, alt)
                r = mod.evaluate_wealth_for_date(chart, eval_date)
                results[domain_name] = {
                    "score": round(r.total_score, 2),
                    "likelihood": r.likelihood,
                    "timing_band": r.timing_band,
                    "fired_count": len(r.dasha_fired) + len(r.fast_trigger_fired),
                    "top_rules": [rid for rid, _, _ in (r.dasha_fired + r.fast_trigger_fired)[:3]],
                    "classical": r.classical.get("wealth_promise", "unknown"),
                    "outcome": r.outcome.get("wealth_type", "unknown"),
                }
            else:
                # Other evaluators: instantiate chart + transit, run layers if available
                chart = mod.ChartState(birth_dt, lat, lon, alt)
                transit = mod.TransitState(eval_date, chart)

                fired = []
                score = 0

                # Try dasha layer
                if hasattr(mod, 'evaluate_dasha_layer'):
                    try:
                        import inspect
                        sig = inspect.signature(mod.evaluate_dasha_layer)
                        params = list(sig.parameters.keys())
                        if len(params) == 3:  # chart, md_lord, ad_lord
                            # Need dasha info — skip for now (requires full dasha computation)
                            pass
                        elif len(params) == 2:  # chart, transit
                            dasha_results = mod.evaluate_dasha_layer(chart, transit)
                            fired.extend(dasha_results)
                            score += sum(s for _, s, _ in dasha_results)
                    except Exception:
                        pass

                # Try transit layer
                if hasattr(mod, 'evaluate_transit_layer'):
                    try:
                        transit_results = mod.evaluate_transit_layer(chart, transit)
                        fired.extend(transit_results)
                        score += sum(s for _, s, _ in transit_results)
                    except Exception:
                        pass

                # Try fast trigger layer
                if hasattr(mod, 'evaluate_fast_trigger_layer'):
                    try:
                        fast_results = mod.evaluate_fast_trigger_layer(chart, transit)
                        fired.extend(fast_results)
                        score += sum(s for _, s, _ in fast_results)
                    except Exception:
                        pass

                # Try classical layer
                classical_info = "unknown"
                if hasattr(mod, 'evaluate_classical_layer'):
                    try:
                        classical = mod.evaluate_classical_layer(chart)
                        if isinstance(classical, dict):
                            classical_info = classical.get("career_promise",
                                           classical.get("fertility_promise",
                                           classical.get("wealth_promise", "evaluated")))
                    except Exception:
                        pass

                results[domain_name] = {
                    "score": round(score, 2),
                    "likelihood": _score_to_likelihood(score),
                    "fired_count": len(fired),
                    "top_rules": [rid for rid, _, _ in fired[:3]],
                    "classical": classical_info,
                }

        except Exception as e:
            results[domain_name] = {"error": str(e)[:100]}

    return results


def _score_to_likelihood(score):
    if score >= 55:
        return "VERY_HIGH"
    elif score >= 40:
        return "HIGH"
    elif score >= 25:
        return "MODERATE"
    elif score >= 15:
        return "LOW"
    return "VERY_LOW"


# ═══════════════════════════════════════════════════════════════
# TIMELINE SCANNER
# ═══════════════════════════════════════════════════════════════

def scan_timeline(birth_dt, lat, lon, start_date, end_date, step_months=3, alt=0):
    """
    Scan a date range and evaluate all domains at each step.

    Returns list of {date, domains: {domain: result}}.
    """
    timeline = []
    current = start_date

    while current <= end_date:
        domain_results = evaluate_all_domains(birth_dt, lat, lon, current, alt)
        timeline.append({
            "date": current,
            "domains": domain_results,
        })
        current += relativedelta(months=step_months)

    return timeline


# ═══════════════════════════════════════════════════════════════
# MAIN — RUN FOR BASE SUBJECT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Base subject: 22 July 1975, 18:15 IST, Bhilai
    BIRTH_DT = datetime(1975, 7, 22, 18, 15)
    LAT, LON, ALT = 21.2094, 81.4285, 297

    START = datetime(2025, 6, 1)
    END = datetime(2035, 6, 1)

    print("=" * 80)
    print("  MULTI-EVALUATOR TIMELINE — Base Subject (22 Jul 1975, 18:15, Bhilai)")
    print(f"  Period: {START.strftime('%b %Y')} → {END.strftime('%b %Y')} (10 years, quarterly)")
    print("=" * 80)

    # Show available evaluators
    evaluators = _load_evaluators()
    print(f"\n  Available evaluators: {', '.join(sorted(evaluators.keys()))}")
    print(f"  Total: {len(evaluators)} domains")

    # Run timeline
    timeline = scan_timeline(BIRTH_DT, LAT, LON, START, END, step_months=6, alt=ALT)

    # Print wealth/finance focused summary
    print(f"\n  ── WEALTH & FINANCE TIMELINE (6-month steps) ──\n")
    print(f"  {'Date':<12} {'Wealth':<10} {'Property':<10} {'Business':<10} {'Career':<10} {'Finance Crisis':<14}")
    print(f"  {'─'*12} {'─'*10} {'─'*10} {'─'*10} {'─'*10} {'─'*14}")

    for entry in timeline:
        dt = entry["date"]
        d = entry["domains"]

        def _fmt(domain):
            r = d.get(domain, {})
            if "error" in r:
                return "ERR"
            score = r.get("score", 0)
            lh = r.get("likelihood", "?")
            if lh == "VERY_HIGH":
                return f"{score:.0f}★★"
            elif lh == "HIGH":
                return f"{score:.0f}★"
            elif lh == "MODERATE":
                return f"{score:.0f}●"
            elif lh == "LOW":
                return f"{score:.0f}○"
            return f"{score:.0f}·"

        print(f"  {dt.strftime('%Y-%m'):<12} {_fmt('wealth'):<10} {_fmt('property'):<10} "
              f"{_fmt('business'):<10} {_fmt('career'):<10} {_fmt('financial_crisis'):<14}")

    # Detailed best periods
    print(f"\n  ── TOP WEALTH WINDOWS ──\n")
    wealth_scores = [(e["date"], e["domains"].get("wealth", {}).get("score", 0),
                      e["domains"].get("wealth", {})) for e in timeline]
    wealth_scores.sort(key=lambda x: x[1], reverse=True)

    for dt, score, info in wealth_scores[:5]:
        if score > 0:
            lh = info.get("likelihood", "?")
            rules = info.get("top_rules", [])
            print(f"  {dt.strftime('%Y-%m')} | Score: {score:.1f} | {lh} | {', '.join(rules[:2])}")

    print("\n  Done.")
