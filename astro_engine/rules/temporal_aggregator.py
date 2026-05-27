"""
Temporal Aggregator — Multi-resolution roll-up for past-event prediction.

Consumes raw evaluator point-in-time scores and produces:
- Sustained activation bands
- Monthly/quarterly confidence bands
- Peak + window presentation
- Multi-resolution scoring

This module does NOT alter evaluator scoring logic.
It aggregates evaluator outputs into trust-building temporal views.

Architecture:
    evaluators (point-in-time) → temporal_aggregator → presentation layer

Usage:
    from rules.temporal_aggregator import (
        scan_monthly_timeline,
        compute_activation_band,
        compute_confidence_band,
        build_event_prediction,
    )
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dateutil.relativedelta import relativedelta
from rules.multi_evaluator_runner import evaluate_all_domains


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class TimePoint:
    """Single scored point in time."""
    date: datetime
    score: float
    rules: list = field(default_factory=list)
    likelihood: str = "VERY_LOW"


@dataclass
class ActivationBand:
    """A sustained period of evaluator activation."""
    start: datetime
    end: datetime
    peak_date: datetime
    peak_score: float
    avg_score: float
    duration_days: int
    point_count: int
    density: float  # fraction of points above threshold


@dataclass
class EventPrediction:
    """Complete multi-resolution prediction for a past event."""
    domain: str
    # Peak
    peak_date: datetime = None
    peak_score: float = 0.0
    # Sustained band
    band_start: datetime = None
    band_end: datetime = None
    band_duration_days: int = 0
    band_avg_score: float = 0.0
    # Monthly
    strongest_month: str = ""
    strongest_month_score: float = 0.0
    # Quarterly
    strongest_quarter: str = ""
    strongest_quarter_score: float = 0.0
    # Confidence
    confidence: float = 0.0
    # Raw timeline
    timeline: list = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# TIMELINE SCANNING
# ═══════════════════════════════════════════════════════════════

def scan_monthly_timeline(birth_dt, lat, lon, alt, domain,
                          center_date, radius_months=18):
    """
    Scan a domain at monthly resolution around a center date.

    Parameters
    ----------
    birth_dt : datetime — natal birth datetime
    lat, lon, alt : float — birth location
    domain : str — evaluator domain name
    center_date : datetime — center of scan window
    radius_months : int — months before and after center (default 18)

    Returns
    -------
    list[TimePoint] — monthly scored timeline
    """
    points = []
    start = center_date - relativedelta(months=radius_months)

    for i in range(radius_months * 2):
        dt = start + relativedelta(months=i)
        result = evaluate_all_domains(birth_dt, lat, lon, dt, alt)
        domain_result = result.get(domain, {})
        score = domain_result.get("score", 0)
        rules = domain_result.get("top_rules", [])
        likelihood = domain_result.get("likelihood", "VERY_LOW")
        points.append(TimePoint(date=dt, score=score, rules=rules, likelihood=likelihood))

    return points


def scan_weekly_timeline(birth_dt, lat, lon, alt, domain,
                         center_date, radius_weeks=26):
    """
    Scan a domain at weekly resolution around a center date.

    Returns list[TimePoint] — weekly scored timeline (52 points default).
    """
    points = []
    start = center_date - timedelta(weeks=radius_weeks)

    for i in range(radius_weeks * 2):
        dt = start + timedelta(weeks=i)
        result = evaluate_all_domains(birth_dt, lat, lon, dt, alt)
        domain_result = result.get(domain, {})
        score = domain_result.get("score", 0)
        rules = domain_result.get("top_rules", [])
        points.append(TimePoint(date=dt, score=score, rules=rules))

    return points


# ═══════════════════════════════════════════════════════════════
# ACTIVATION BAND DETECTION
# ═══════════════════════════════════════════════════════════════

def compute_activation_band(points: list, threshold_pct=0.4):
    """
    Find the strongest sustained activation band in a timeline.

    A band is a contiguous sequence of points where score >= threshold.
    Threshold = threshold_pct × peak_score.

    Parameters
    ----------
    points : list[TimePoint]
    threshold_pct : float — fraction of peak to use as activation threshold

    Returns
    -------
    ActivationBand or None if no activation found
    """
    if not points or all(p.score == 0 for p in points):
        return None

    peak_point = max(points, key=lambda p: p.score)
    threshold = peak_point.score * threshold_pct

    # Find all contiguous bands above threshold
    bands = []
    current_band = []

    for p in points:
        if p.score >= threshold:
            current_band.append(p)
        else:
            if current_band:
                bands.append(current_band)
                current_band = []
    if current_band:
        bands.append(current_band)

    if not bands:
        return None

    # Find the band containing the peak (or the longest band)
    # ALSO check for band closest to center of timeline (expected event area)
    best_band = None
    for band in bands:
        if peak_point in band:
            best_band = band
            break

    if best_band is None:
        best_band = max(bands, key=lambda b: sum(p.score for p in b))

    # Compute band metrics
    band_start = best_band[0].date
    band_end = best_band[-1].date
    duration = (band_end - band_start).days
    avg_score = sum(p.score for p in best_band) / len(best_band)
    density = len([p for p in best_band if p.score > 0]) / max(len(best_band), 1)

    return ActivationBand(
        start=band_start,
        end=band_end,
        peak_date=peak_point.date,
        peak_score=peak_point.score,
        avg_score=round(avg_score, 1),
        duration_days=duration,
        point_count=len(best_band),
        density=round(density, 2),
    )


def compute_secondary_bands(points: list, primary_band: ActivationBand,
                            threshold_pct=0.3):
    """
    Find secondary activation bands outside the primary band.
    Useful for detecting multiple relocation events or recurring patterns.
    """
    if not points or primary_band is None:
        return []

    threshold = primary_band.peak_score * threshold_pct
    secondary = []
    current_band = []

    for p in points:
        # Skip points inside primary band
        if primary_band.start <= p.date <= primary_band.end:
            if current_band:
                secondary.append(current_band)
                current_band = []
            continue

        if p.score >= threshold:
            current_band.append(p)
        else:
            if current_band and len(current_band) >= 2:
                secondary.append(current_band)
            current_band = []

    if current_band and len(current_band) >= 2:
        secondary.append(current_band)

    # Convert to ActivationBands
    result = []
    for band in secondary:
        peak_p = max(band, key=lambda p: p.score)
        avg = sum(p.score for p in band) / len(band)
        result.append(ActivationBand(
            start=band[0].date,
            end=band[-1].date,
            peak_date=peak_p.date,
            peak_score=peak_p.score,
            avg_score=round(avg, 1),
            duration_days=(band[-1].date - band[0].date).days,
            point_count=len(band),
            density=1.0,
        ))

    result.sort(key=lambda b: b.peak_score, reverse=True)
    return result[:3]


# ═══════════════════════════════════════════════════════════════
# MONTHLY / QUARTERLY ROLLUPS
# ═══════════════════════════════════════════════════════════════

def rollup_monthly(points: list):
    """
    Roll up timeline points into monthly averages.
    Returns list of {month, year, avg_score, max_score, point_count}.
    """
    months = defaultdict(list)
    for p in points:
        key = (p.date.year, p.date.month)
        months[key].append(p.score)

    result = []
    for (year, month), scores in sorted(months.items()):
        result.append({
            "year": year,
            "month": month,
            "label": f"{year}-{month:02d}",
            "avg_score": round(sum(scores) / len(scores), 1),
            "max_score": max(scores),
            "point_count": len(scores),
        })

    return result


def rollup_quarterly(points: list):
    """
    Roll up timeline points into quarterly averages.
    Returns list of {year, quarter, label, avg_score, max_score}.
    """
    quarters = defaultdict(list)
    for p in points:
        q = (p.date.month - 1) // 3 + 1
        key = (p.date.year, q)
        quarters[key].append(p.score)

    result = []
    for (year, q), scores in sorted(quarters.items()):
        result.append({
            "year": year,
            "quarter": q,
            "label": f"{year}-Q{q}",
            "avg_score": round(sum(scores) / len(scores), 1),
            "max_score": max(scores),
            "point_count": len(scores),
        })

    return result


def strongest_month(points: list):
    """Find the month with highest average score."""
    monthly = rollup_monthly(points)
    if not monthly:
        return None
    return max(monthly, key=lambda m: m["avg_score"])


def strongest_quarter(points: list):
    """Find the quarter with highest average score."""
    quarterly = rollup_quarterly(points)
    if not quarterly:
        return None
    return max(quarterly, key=lambda q: q["avg_score"])


# ═══════════════════════════════════════════════════════════════
# CONFIDENCE BAND
# ═══════════════════════════════════════════════════════════════

def compute_confidence_band(points: list, band: ActivationBand = None):
    """
    Compute a confidence score for the prediction based on:
    - Sustained activation density
    - Peak strength relative to noise
    - Band duration (longer = more confident)
    - Score consistency within band

    Returns dict with confidence (0-1), components, and interpretation.
    """
    if not points or all(p.score == 0 for p in points):
        return {"confidence": 0.0, "interpretation": "no_signal"}

    peak = max(p.score for p in points)
    active_points = [p for p in points if p.score > 0]
    total_points = len(points)

    # Component 1: Activation density (what fraction of timeline is active)
    density = len(active_points) / total_points if total_points > 0 else 0

    # Component 2: Peak strength (normalized to 0-1, assuming 100 is strong)
    peak_strength = min(peak / 150.0, 1.0)

    # Component 3: Band duration (longer sustained = more confident)
    band_factor = 0.5
    if band:
        # 6+ months of sustained activation = high confidence
        band_factor = min(band.duration_days / 540.0, 1.0)

    # Component 4: Consistency (low variance within band = more confident)
    consistency = 0.5
    if band and band.point_count > 1:
        scores_in_band = [p.score for p in points
                         if band.start <= p.date <= band.end and p.score > 0]
        if scores_in_band:
            mean = sum(scores_in_band) / len(scores_in_band)
            variance = sum((s - mean) ** 2 for s in scores_in_band) / len(scores_in_band)
            cv = (variance ** 0.5) / mean if mean > 0 else 1.0
            consistency = max(0, 1.0 - cv)  # Lower CV = higher consistency

    # Weighted composite
    confidence = (
        density * 0.20 +
        peak_strength * 0.35 +
        band_factor * 0.25 +
        consistency * 0.20
    )

    interpretation = "no_signal"
    if confidence >= 0.7:
        interpretation = "high_confidence"
    elif confidence >= 0.5:
        interpretation = "moderate_confidence"
    elif confidence >= 0.3:
        interpretation = "low_confidence"
    else:
        interpretation = "very_low_confidence"

    return {
        "confidence": round(confidence, 3),
        "interpretation": interpretation,
        "components": {
            "density": round(density, 3),
            "peak_strength": round(peak_strength, 3),
            "band_factor": round(band_factor, 3),
            "consistency": round(consistency, 3),
        },
    }


# ═══════════════════════════════════════════════════════════════
# MASTER PREDICTION BUILDER
# ═══════════════════════════════════════════════════════════════

def build_event_prediction(birth_dt, lat, lon, alt, domain,
                           center_date, radius_months=18):
    """
    Build a complete multi-resolution event prediction.

    This is the main entry point for past-event prediction.
    It scans at monthly resolution, computes bands, rollups, and confidence.

    Parameters
    ----------
    birth_dt, lat, lon, alt : birth data
    domain : str — evaluator domain
    center_date : datetime — approximate expected event date
    radius_months : int — scan radius (default 18 months each side)

    Returns
    -------
    EventPrediction with all temporal views populated.
    """
    # Scan monthly timeline
    points = scan_monthly_timeline(birth_dt, lat, lon, alt, domain,
                                   center_date, radius_months)

    # Compute activation band (use 30% threshold — balances precision and coverage)
    band = compute_activation_band(points, threshold_pct=0.30)

    # Monthly and quarterly rollups
    best_month = strongest_month(points)
    best_quarter = strongest_quarter(points)

    # Confidence
    conf = compute_confidence_band(points, band)

    # Build prediction
    pred = EventPrediction(domain=domain)
    pred.timeline = points

    if band:
        pred.peak_date = band.peak_date
        pred.peak_score = band.peak_score
        pred.band_start = band.start
        pred.band_end = band.end
        pred.band_duration_days = band.duration_days
        pred.band_avg_score = band.avg_score
    elif points:
        peak_p = max(points, key=lambda p: p.score)
        pred.peak_date = peak_p.date
        pred.peak_score = peak_p.score

    if best_month:
        pred.strongest_month = best_month["label"]
        pred.strongest_month_score = best_month["avg_score"]

    if best_quarter:
        pred.strongest_quarter = best_quarter["label"]
        pred.strongest_quarter_score = best_quarter["avg_score"]

    pred.confidence = conf["confidence"]

    return pred


# ═══════════════════════════════════════════════════════════════
# PRESENTATION HELPERS
# ═══════════════════════════════════════════════════════════════

def format_prediction_for_user(pred: EventPrediction):
    """
    Format an EventPrediction into a user-facing trust-building string.

    Output format:
        HIGH probability band: Nov 2007 → Oct 2010
        Strongest month: Jul 2008
        Confidence: 0.72 (high)
    """
    lines = []

    if pred.band_start and pred.band_end:
        lines.append(f"HIGH probability band: {pred.band_start.strftime('%b %Y')} → {pred.band_end.strftime('%b %Y')}")
        lines.append(f"Band duration: {pred.band_duration_days} days ({pred.band_duration_days // 30} months)")

    if pred.strongest_month:
        lines.append(f"Strongest month: {pred.strongest_month} (avg score: {pred.strongest_month_score:.0f})")

    if pred.strongest_quarter:
        lines.append(f"Strongest quarter: {pred.strongest_quarter} (avg score: {pred.strongest_quarter_score:.0f})")

    if pred.peak_date:
        lines.append(f"Peak signal: {pred.peak_date.strftime('%b %Y')} (score: {pred.peak_score:.0f})")

    lines.append(f"Confidence: {pred.confidence:.2f}")

    return "\n".join(lines)


def score_against_actual(pred: EventPrediction, actual_date: datetime):
    """
    Score a prediction against the actual event date.

    Returns dict with multi-resolution match quality.
    """
    result = {
        "actual_date": actual_date,
        "peak_distance_days": 999,
        "within_band": False,
        "within_month_of_peak": False,
        "within_quarter_of_peak": False,
        "band_overlap": 0.0,
    }

    if pred.peak_date:
        result["peak_distance_days"] = abs((pred.peak_date - actual_date).days)
        result["within_month_of_peak"] = result["peak_distance_days"] <= 30
        result["within_quarter_of_peak"] = result["peak_distance_days"] <= 90

    if pred.band_start and pred.band_end:
        if pred.band_start <= actual_date <= pred.band_end:
            result["within_band"] = True
            result["band_overlap"] = 1.0
        else:
            dist = min(abs((actual_date - pred.band_start).days),
                      abs((actual_date - pred.band_end).days))
            if dist <= 30:
                result["band_overlap"] = 0.7
            elif dist <= 90:
                result["band_overlap"] = 0.3

    return result
