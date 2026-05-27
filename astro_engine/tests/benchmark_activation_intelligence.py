"""
Activation Intelligence Benchmark — Density-based past-event prediction.

Tests the new activation_intelligence module against gold fixtures.
Compares baseline confidence vs density-aware confidence.

Usage:
    cd astro_engine
    ../.venv/bin/python tests/benchmark_activation_intelligence.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rules.activation_intelligence import (
    build_activation_profile,
    format_trust_output,
    score_against_actual,
)


# ═══════════════════════════════════════════════════════════════
# GOLD EVENTS
# ═══════════════════════════════════════════════════════════════

SUBJECTS = {
    "A": {"birth_dt": datetime(1975, 7, 22, 18, 15), "lat": 21.2094, "lon": 81.4285, "alt": 297},
    "B": {"birth_dt": datetime(1983, 11, 30, 21, 20), "lat": 23.1186, "lon": 83.1960, "alt": 594},
}

GOLD_EVENTS = [
    {"subject": "A", "event": "Marriage", "date": datetime(2009, 5, 7), "domain": "marriage"},
    {"subject": "A", "event": "Son born", "date": datetime(2010, 12, 4), "domain": "childbirth"},
    {"subject": "A", "event": "Father death", "date": datetime(2018, 3, 15), "domain": "parent_loss"},
    {"subject": "A", "event": "Pune relocation", "date": datetime(2007, 8, 20), "domain": "relocation"},
    {"subject": "B", "event": "Marriage", "date": datetime(2009, 5, 7), "domain": "marriage"},
    {"subject": "B", "event": "Son born", "date": datetime(2010, 12, 4), "domain": "childbirth"},
]


def main():
    print("=" * 80)
    print("  ACTIVATION INTELLIGENCE BENCHMARK")
    print("  Density-based confidence vs baseline confidence")
    print("=" * 80)

    all_results = []
    band_hits = 0
    total = 0

    for event in GOLD_EVENTS:
        subj = event["subject"]
        s = SUBJECTS[subj]
        domain = event["domain"]
        actual = event["date"]
        name = event["event"]

        print(f"\n{'─'*80}")
        print(f"  {name} (Subject {subj}) — Actual: {actual.strftime('%d %b %Y')} | Domain: {domain}")
        print(f"{'─'*80}")

        # Build activation profile
        profile = build_activation_profile(
            s["birth_dt"], s["lat"], s["lon"], s["alt"],
            domain, actual, radius_months=18)

        # Score against actual
        scoring = score_against_actual(profile, actual)

        # Print trust output
        print(f"\n  TRUST OUTPUT:")
        output = format_trust_output(profile, actual)
        for line in output.split("\n"):
            print(f"    {line}")

        # Print scoring
        print(f"\n  SCORING:")
        print(f"    Within band: {'✓ YES' if scoring['within_band'] else '✗ NO'}")
        print(f"    Peak drift: {scoring['peak_distance_days']} days")
        print(f"    Within quarter: {'✓' if scoring['within_quarter_of_peak'] else '✗'}")

        # Track
        total += 1
        if scoring["within_band"]:
            band_hits += 1

        all_results.append({
            "event": name,
            "subject": subj,
            "domain": domain,
            "actual": actual.strftime("%Y-%m-%d"),
            "peak_date": profile.peak_date.strftime("%Y-%m-%d") if profile.peak_date else None,
            "peak_score": profile.peak_score,
            "band_start": profile.band_start.strftime("%Y-%m-%d") if profile.band_start else None,
            "band_end": profile.band_end.strftime("%Y-%m-%d") if profile.band_end else None,
            "band_duration_days": profile.band_duration_days,
            "band_density": profile.band_density,
            "baseline_confidence": profile.baseline_confidence,
            "density_confidence": profile.density_confidence,
            "dasha_pct": profile.dasha_contribution_pct,
            "transit_pct": profile.transit_contribution_pct,
            "fast_pct": profile.fast_contribution_pct,
            "within_band": scoring["within_band"],
            "peak_distance_days": scoring["peak_distance_days"],
            "strongest_month": profile.strongest_month,
        })

    # ── SUMMARY ──
    print(f"\n{'═'*80}")
    print(f"  SUMMARY — {total} events")
    print(f"{'═'*80}")

    print(f"\n  {'Event':<20} {'Band?':<7} {'Drift':<8} {'Baseline':<10} {'Density':<10} {'Layers':<25}")
    print(f"  {'─'*20} {'─'*7} {'─'*8} {'─'*10} {'─'*10} {'─'*25}")

    for r in all_results:
        evt = f"{r['event']}({r['subject']})"[:18]
        band = "✓" if r["within_band"] else "✗"
        drift = f"{r['peak_distance_days']}d"
        base = f"{r['baseline_confidence']:.2f}"
        dens = f"{r['density_confidence']:.2f}"
        layers = f"D={r['dasha_pct']:.0%} T={r['transit_pct']:.0%} F={r['fast_pct']:.0%}"
        print(f"  {evt:<20} {band:<7} {drift:<8} {base:<10} {dens:<10} {layers:<25}")

    # Stats
    avg_baseline = sum(r["baseline_confidence"] for r in all_results) / total
    avg_density = sum(r["density_confidence"] for r in all_results) / total
    avg_drift = sum(r["peak_distance_days"] for r in all_results) / total

    print(f"\n  Band captures actual: {band_hits}/{total} ({band_hits/total:.0%})")
    print(f"  Avg peak drift: {avg_drift:.0f} days")
    print(f"  Avg baseline confidence: {avg_baseline:.2f}")
    print(f"  Avg density confidence: {avg_density:.2f}")

    # ── CONFIDENCE COMPARISON ──
    print(f"\n{'═'*80}")
    print(f"  CONFIDENCE COMPARISON: Baseline vs Density-Aware")
    print(f"{'═'*80}")
    print(f"""
  Baseline confidence: Simple peak/150 normalization.
    - Does not account for sustained activation
    - Does not account for layer agreement
    - Does not account for momentum

  Density confidence: Multi-factor scoring.
    - Activation density (how much of timeline is active)
    - Peak strength (normalized)
    - Sustained length (longer = more confident)
    - Layer agreement (dasha + transit both contributing)
    - Momentum clarity (clear rise → peak → fall)

  Result: Density confidence is {'higher' if avg_density > avg_baseline else 'lower'} on average
  ({avg_density:.2f} vs {avg_baseline:.2f})
    """)

    # Save
    output_dir = Path(__file__).resolve().parent / "benchmark_results"
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "activation_intelligence_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"  Results saved: {output_dir}/activation_intelligence_results.json")


if __name__ == "__main__":
    main()
