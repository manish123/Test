"""
Evaluator Benchmark Harness — Fine-tuning past-event prediction precision.

Uses gold-label fixtures:
  - tests/subjectA.json (12 confirmed events)
  - tests/subjectB.json (2 confirmed events + dual-chart context)

Runs evaluator scans against confirmed dates and produces:
  - Event-by-event accuracy scorecard
  - Domain peak analysis
  - Cross-subject correlation (for shared events)
  - Variant comparison (A/B/C)
  - JSON + console output

Usage:
    cd astro_engine
    ../.venv/bin/python tests/benchmark_evaluators.py
"""

import json
import sys
import csv
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rules.multi_evaluator_runner import evaluate_all_domains, scan_timeline
from rules.evaluator_base import BaseChartState
from symbolic.lifecycle_engine import determine_lifecycle_state
from symbolic.coherent_state_builder import build_coherent_state


# ═══════════════════════════════════════════════════════════════
# FIXTURE LOADING
# ═══════════════════════════════════════════════════════════════

FIXTURE_DIR = Path(__file__).resolve().parent

# Birth data (hardcoded from fixtures — no geocoding dependency)
SUBJECTS = {
    "A": {
        "birth_dt": datetime(1975, 7, 22, 18, 15),
        "lat": 21.2094, "lon": 81.4285, "alt": 297,
    },
    "B": {
        "birth_dt": datetime(1983, 11, 30, 21, 20),
        "lat": 23.1186, "lon": 83.1960, "alt": 594,
    },
}


def load_fixture(subject_id):
    """Load a subject fixture JSON."""
    path = FIXTURE_DIR / f"subject{subject_id}.json"
    with open(path) as f:
        return json.load(f)


def parse_events(fixture):
    """
    Parse confirmed events into a normalized list.
    Returns [{event, domain, year, month, window, is_dual_chart}]
    """
    events = []
    for e in fixture.get("confirmed_events", []):
        event_name = e.get("event", "")
        domain = _event_to_domain(event_name)
        year, month = _parse_date(e)
        window = _compute_window(year, month, e)
        is_dual = "linked_subject" in e

        events.append({
            "event": event_name,
            "domain": domain,
            "year": year,
            "month": month,
            "window": window,
            "is_dual_chart": is_dual,
            "raw": e,
        })
    return events


def _event_to_domain(event_name):
    """Map event name to evaluator domain."""
    mapping = {
        "graduation": "career",
        "odd jobs": "career",
        "MTech": "career",
        "failed business": "business",
        "joined NCR": "relocation",
        "moved to Bhopal": "relocation",
        "joined IBILT": "career",
        "relocated to Pune": "relocation",
        "joined Mastek": "career",
        "mother passed": "parent_loss",
        "father passed": "parent_loss",
        "sister passed": "parent_loss",
        "son born": "childbirth",
        "child_birth": "childbirth",
        "arranged marriage": "marriage",
        "arranged_marriage": "marriage",
    }
    event_lower = event_name.lower()
    for key, domain in mapping.items():
        if key.lower() in event_lower:
            return domain
    return "unknown"


def _parse_date(event_dict):
    """Extract year and month from event dict."""
    date_str = event_dict.get("date") or event_dict.get("year") or ""
    if not date_str:
        # Try range
        range_str = event_dict.get("range", "")
        if "-" in range_str and len(range_str) <= 9:  # "1996-1998"
            parts = range_str.split("-")
            return int(parts[0]), 6  # midpoint
        return 0, 0

    parts = str(date_str).split("-")
    year = int(parts[0]) if parts[0] else 0
    month = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 6
    return year, month


def _compute_window(year, month, event_dict):
    """Compute acceptable prediction window."""
    if event_dict.get("range"):
        parts = event_dict["range"].split("-")
        return (int(parts[0]), int(parts[1]))
    # For exact dates: ±1 year
    return (year - 1, year + 1)


# ═══════════════════════════════════════════════════════════════
# EVALUATOR SCAN
# ═══════════════════════════════════════════════════════════════

def run_evaluator_scan(subject_id, start_year=1993, end_year=2020, step_months=3):
    """Run full evaluator timeline scan for a subject."""
    s = SUBJECTS[subject_id]
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 1, 1)
    return scan_timeline(s["birth_dt"], s["lat"], s["lon"], start, end,
                         step_months=step_months, alt=s["alt"])


def get_domain_peaks(timeline, domain, top_n=10):
    """Extract top scoring peaks for a domain from timeline."""
    peaks = []
    for entry in timeline:
        result = entry["domains"].get(domain, {})
        if "error" in result:
            continue
        score = result.get("score", 0)
        if score > 0:
            peaks.append({
                "date": entry["date"],
                "year": entry["date"].year,
                "month": entry["date"].month,
                "score": score,
                "likelihood": result.get("likelihood", "?"),
                "top_rules": result.get("top_rules", []),
                "fired_count": result.get("fired_count", 0),
            })
    peaks.sort(key=lambda x: x["score"], reverse=True)
    return peaks[:top_n]


def get_score_at_date(timeline, domain, target_year, target_month=None):
    """Get the evaluator score closest to a target date."""
    best = None
    best_dist = 999
    for entry in timeline:
        dt = entry["date"]
        result = entry["domains"].get(domain, {})
        if "error" in result:
            continue
        dist = abs(dt.year - target_year) * 12 + (abs(dt.month - (target_month or 6)))
        if dist < best_dist:
            best_dist = dist
            best = {
                "date": dt,
                "score": result.get("score", 0),
                "likelihood": result.get("likelihood", "?"),
                "top_rules": result.get("top_rules", []),
                "distance_months": dist,
            }
    return best


# ═══════════════════════════════════════════════════════════════
# SCORING
# ═══════════════════════════════════════════════════════════════

@dataclass
class EventScore:
    event: str
    domain: str
    expected_year: int
    expected_month: int
    window: tuple
    predicted_year: int = 0
    predicted_month: int = 0
    predicted_score: float = 0.0
    result: str = "MISSED"  # EXACT, APPROXIMATE, WRONG_TIMING, MISSED, NO_EVALUATOR
    detail: str = ""
    score_points: int = 0
    peak_rank: int = 0  # Where does the actual event rank among all peaks?
    signal_at_event: float = 0.0  # Score at the actual event date


def score_event(event, timeline):
    """Score a single event against the timeline."""
    domain = event["domain"]
    year = event["year"]
    month = event["month"]
    window = event["window"]

    es = EventScore(
        event=event["event"],
        domain=domain,
        expected_year=year,
        expected_month=month,
        window=window,
    )

    if domain == "unknown":
        es.result = "NO_EVALUATOR"
        es.detail = "No evaluator mapped for this event type"
        return es

    # Get peaks for this domain
    peaks = get_domain_peaks(timeline, domain, top_n=20)

    if not peaks:
        es.result = "MISSED"
        es.detail = f"No signal for domain '{domain}'"
        return es

    # Get signal at the actual event date
    at_event = get_score_at_date(timeline, domain, year, month)
    if at_event:
        es.signal_at_event = at_event["score"]

    # Find best peak within window
    in_window = [p for p in peaks if window[0] <= p["year"] <= window[1]]
    best_peak = peaks[0]  # Overall best

    # Determine where the actual event date ranks
    for i, p in enumerate(peaks):
        if abs(p["year"] - year) <= 1:
            es.peak_rank = i + 1
            break

    if in_window:
        best_in_window = max(in_window, key=lambda x: x["score"])
        es.predicted_year = best_in_window["year"]
        es.predicted_month = best_in_window["month"]
        es.predicted_score = best_in_window["score"]

        if abs(best_in_window["year"] - year) <= 1 and (month == 6 or abs(best_in_window["month"] - month) <= 3):
            es.result = "EXACT"
            es.score_points = 3
            es.detail = f"Peak at {best_in_window['year']}-{best_in_window['month']:02d} (score={best_in_window['score']:.0f}, {best_in_window['likelihood']})"
        else:
            es.result = "APPROXIMATE"
            es.score_points = 2
            es.detail = f"Peak at {best_in_window['year']}-{best_in_window['month']:02d} within window {window} (score={best_in_window['score']:.0f})"
    else:
        # No peak in window — check if there's any signal
        es.predicted_year = best_peak["year"]
        es.predicted_month = best_peak["month"]
        es.predicted_score = best_peak["score"]
        es.result = "WRONG_TIMING"
        es.score_points = 1
        es.detail = f"Best peak at {best_peak['year']}-{best_peak['month']:02d} (score={best_peak['score']:.0f}), outside window {window}"

    return es


# ═══════════════════════════════════════════════════════════════
# DUAL-CHART CORRELATION
# ═══════════════════════════════════════════════════════════════

def dual_chart_correlation(timeline_a, timeline_b, domain, target_year, window):
    """Check if both charts show signal in the same window for a shared event."""
    peaks_a = get_domain_peaks(timeline_a, domain, top_n=20)
    peaks_b = get_domain_peaks(timeline_b, domain, top_n=20)

    in_window_a = [p for p in peaks_a if window[0] <= p["year"] <= window[1]]
    in_window_b = [p for p in peaks_b if window[0] <= p["year"] <= window[1]]

    score_a = max([p["score"] for p in in_window_a], default=0)
    score_b = max([p["score"] for p in in_window_b], default=0)

    # Check for overlapping high-signal quarters
    overlap_quarters = []
    for pa in in_window_a:
        for pb in in_window_b:
            if pa["year"] == pb["year"] and abs(pa["month"] - pb["month"]) <= 3:
                overlap_quarters.append({
                    "year": pa["year"],
                    "month": pa["month"],
                    "score_a": pa["score"],
                    "score_b": pb["score"],
                    "combined": pa["score"] + pb["score"],
                })

    overlap_quarters.sort(key=lambda x: x["combined"], reverse=True)

    return {
        "domain": domain,
        "target_year": target_year,
        "window": window,
        "score_a_in_window": score_a,
        "score_b_in_window": score_b,
        "both_active": score_a > 30 and score_b > 30,
        "overlap_quarters": overlap_quarters[:3],
        "correlation_strength": "STRONG" if overlap_quarters and overlap_quarters[0]["combined"] > 100 else
                               "MODERATE" if score_a > 30 and score_b > 30 else "WEAK",
    }


# ═══════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_report(subject_id, events, scores, timeline, dual_results=None):
    """Generate console + JSON report for a subject."""
    fixture = load_fixture(subject_id)

    total_possible = len(scores) * 3
    total_scored = sum(s.score_points for s in scores)
    accuracy = total_scored / total_possible if total_possible > 0 else 0

    exact = sum(1 for s in scores if s.result == "EXACT")
    approx = sum(1 for s in scores if s.result == "APPROXIMATE")
    wrong = sum(1 for s in scores if s.result == "WRONG_TIMING")
    missed = sum(1 for s in scores if s.result == "MISSED")
    no_eval = sum(1 for s in scores if s.result == "NO_EVALUATOR")

    print(f"\n{'═'*80}")
    print(f"  SUBJECT {subject_id} — BENCHMARK RESULTS")
    print(f"  Accuracy: {accuracy:.1%} | Exact: {exact} | Approx: {approx} | Wrong: {wrong} | Missed: {missed} | No Eval: {no_eval}")
    print(f"{'═'*80}")

    print(f"\n  {'Event':<40} {'Domain':<18} {'Expected':<10} {'Predicted':<10} {'Result':<14} {'Signal':<8}")
    print(f"  {'─'*40} {'─'*18} {'─'*10} {'─'*10} {'─'*14} {'─'*8}")

    for s in scores:
        evt = s.event[:38]
        exp = f"{s.expected_year}" if s.expected_month == 6 else f"{s.expected_year}-{s.expected_month:02d}"
        pred = f"{s.predicted_year}-{s.predicted_month:02d}" if s.predicted_year else "—"
        sig = f"{s.signal_at_event:.0f}" if s.signal_at_event else "—"
        print(f"  {evt:<40} {s.domain:<18} {exp:<10} {pred:<10} {s.result:<14} {sig:<8}")

    # Domain peak analysis
    print(f"\n  {'─'*80}")
    print(f"  DOMAIN PEAK ANALYSIS")
    print(f"  {'─'*80}")

    domains_seen = set(s.domain for s in scores if s.domain != "unknown")
    for domain in sorted(domains_seen):
        peaks = get_domain_peaks(timeline, domain, top_n=5)
        if peaks:
            peak_str = ", ".join([f"{p['year']}-{p['month']:02d}({p['score']:.0f})" for p in peaks[:4]])
            print(f"  {domain:<20} {peak_str}")

    # Dual-chart results
    if dual_results:
        print(f"\n  {'─'*80}")
        print(f"  DUAL-CHART CORRELATION")
        print(f"  {'─'*80}")
        for dr in dual_results:
            print(f"  {dr['domain']:<15} target={dr['target_year']} | A={dr['score_a_in_window']:.0f} B={dr['score_b_in_window']:.0f} | {dr['correlation_strength']}")
            if dr["overlap_quarters"]:
                oq = dr["overlap_quarters"][0]
                print(f"  {'':15} Best overlap: {oq['year']}-{oq['month']:02d} (A={oq['score_a']:.0f} + B={oq['score_b']:.0f} = {oq['combined']:.0f})")

    return {
        "subject_id": subject_id,
        "accuracy": accuracy,
        "exact": exact,
        "approximate": approx,
        "wrong_timing": wrong,
        "missed": missed,
        "no_evaluator": no_eval,
        "total_events": len(scores),
        "events": [asdict(s) for s in scores],
        "dual_chart": dual_results,
    }


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("  EVALUATOR BENCHMARK HARNESS")
    print("  Gold-label fixtures: subjectA.json, subjectB.json")
    print("  Marriage: 7 May 2009 | Son born: 4 Dec 2010")
    print("=" * 80)

    # ── SUBJECT A ──
    print("\n  Scanning Subject A timeline (1993-2020, quarterly)...")
    timeline_a = run_evaluator_scan("A", start_year=1993, end_year=2020, step_months=3)

    fixture_a = load_fixture("A")
    events_a = parse_events(fixture_a)
    scores_a = [score_event(e, timeline_a) for e in events_a]

    # ── SUBJECT B ──
    print("  Scanning Subject B timeline (2000-2015, quarterly)...")
    timeline_b = run_evaluator_scan("B", start_year=2000, end_year=2015, step_months=3)

    fixture_b = load_fixture("B")
    events_b = parse_events(fixture_b)
    scores_b = [score_event(e, timeline_b) for e in events_b]

    # ── DUAL-CHART CORRELATION ──
    print("  Computing dual-chart correlation...")
    dual_results = []
    # Marriage (shared event)
    dual_results.append(dual_chart_correlation(
        timeline_a, timeline_b, "marriage", 2009, (2008, 2010)))
    # Childbirth (shared event)
    dual_results.append(dual_chart_correlation(
        timeline_a, timeline_b, "childbirth", 2010, (2009, 2011)))

    # ── REPORTS ──
    report_a = generate_report("A", events_a, scores_a, timeline_a, dual_results)
    report_b = generate_report("B", events_b, scores_b, timeline_b)

    # ── SAVE JSON ──
    output_dir = Path(__file__).resolve().parent / "benchmark_results"
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "benchmark_results.json", "w") as f:
        json.dump({"subject_a": report_a, "subject_b": report_b}, f, indent=2, default=str)

    # ── SAVE CSV ──
    with open(output_dir / "scorecard.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["subject", "event", "domain", "expected_year", "predicted_year",
                        "result", "score_points", "signal_at_event", "predicted_score", "peak_rank"])
        for s in scores_a:
            writer.writerow(["A", s.event, s.domain, s.expected_year, s.predicted_year,
                           s.result, s.score_points, s.signal_at_event, s.predicted_score, s.peak_rank])
        for s in scores_b:
            writer.writerow(["B", s.event, s.domain, s.expected_year, s.predicted_year,
                           s.result, s.score_points, s.signal_at_event, s.predicted_score, s.peak_rank])

    print(f"\n  Results saved: {output_dir}/benchmark_results.json")
    print(f"  Scorecard saved: {output_dir}/scorecard.csv")

    # ── FINAL SUMMARY ──
    print(f"\n{'═'*80}")
    print(f"  OVERALL SUMMARY")
    print(f"{'═'*80}")
    print(f"  Subject A: {report_a['accuracy']:.1%} accuracy ({report_a['exact']} exact, {report_a['approximate']} approx, {report_a['wrong_timing']} wrong, {report_a['missed']} missed)")
    print(f"  Subject B: {report_b['accuracy']:.1%} accuracy ({report_b['exact']} exact, {report_b['approximate']} approx, {report_b['wrong_timing']} wrong, {report_b['missed']} missed)")

    # Dual-chart
    print(f"\n  Dual-Chart Correlation:")
    for dr in dual_results:
        print(f"    {dr['domain']}: {dr['correlation_strength']} (A={dr['score_a_in_window']:.0f}, B={dr['score_b_in_window']:.0f})")

    print(f"\n  Done.")


if __name__ == "__main__":
    main()
