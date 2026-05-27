"""
Activation Intelligence — Density-based temporal scoring for past-event prediction.

Extends temporal_aggregator with:
- Activation density scoring (concentration of signal in a band)
- Momentum detection (rising/falling signal)
- Layer-contribution breakdown (dasha vs transit vs fast)
- Density-aware confidence (replaces peak-only confidence)
- Trust-building presentation format

This module does NOT alter evaluator scoring logic.
It consumes evaluator outputs and produces intelligence views.

Architecture:
    evaluators → multi_evaluator_runner → activation_intelligence → presentation

Usage:
    from rules.activation_intelligence import (
        build_activation_profile,
        compute_density_confidence,
        format_trust_output,
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
from rules.multi_evaluator_runner import evaluate_all_domains, _get_current_dasha
from rules.evaluator_base import BaseChartState


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class RichTimePoint:
    """Scored point with layer breakdown."""
    date: datetime
    total_score: float = 0.0
    dasha_score: float = 0.0
    transit_score: float = 0.0
    fast_score: float = 0.0
    fired_rules: list = field(default_factory=list)
    md_lord: str = ""
    ad_lord: str = ""
    likelihood: str = "VERY_LOW"


@dataclass
class ActivationProfile:
    """Complete activation intelligence for a domain around a date."""
    domain: str
    center_date: datetime
    # Timeline
    timeline: list = field(default_factory=list)  # list[RichTimePoint]
    # Peak
    peak_date: datetime = None
    peak_score: float = 0.0
    # Density band
    band_start: datetime = None
    band_end: datetime = None
    band_duration_days: int = 0
    band_avg_score: float = 0.0
    band_density: float = 0.0  # fraction of band with score > 0
    # Momentum
    rising_start: datetime = None
    peak_momentum_date: datetime = None
    falling_end: datetime = None
    # Layer contributions
    dasha_contribution_pct: float = 0.0
    transit_contribution_pct: float = 0.0
    fast_contribution_pct: float = 0.0
    # Confidence
    baseline_confidence: float = 0.0
    density_confidence: float = 0.0
    # Monthly/Quarterly
    strongest_month: str = ""
    strongest_month_score: float = 0.0
    strongest_quarter: str = ""
    strongest_quarter_score: float = 0.0


# ═══════════════════════════════════════════════════════════════
# RICH TIMELINE SCANNING (with layer breakdown)
# ═══════════════════════════════════════════════════════════════

def scan_rich_timeline(birth_dt, lat, lon, alt, domain,
                       center_date, radius_months=18):
    """
    Scan a domain at monthly resolution with per-layer score breakdown.

    Returns list[RichTimePoint] with dasha/transit/fast scores separated.
    """
    import importlib
    import inspect

    chart = BaseChartState(birth_dt, lat, lon, alt)
    points = []
    start = center_date - relativedelta(months=radius_months)

    for i in range(radius_months * 2):
        dt = start + relativedelta(months=i)

        # Get total score from runner
        all_results = evaluate_all_domains(birth_dt, lat, lon, dt, alt)
        domain_result = all_results.get(domain, {})
        total = domain_result.get("score", 0)
        rules = domain_result.get("top_rules", [])
        likelihood = domain_result.get("likelihood", "VERY_LOW")

        # Get layer breakdown by running evaluator directly
        md_lord, ad_lord = _get_current_dasha(birth_dt, chart.moon_lon, dt)
        dasha_s, transit_s, fast_s = _get_layer_scores(
            birth_dt, lat, lon, alt, domain, dt, md_lord, ad_lord)

        points.append(RichTimePoint(
            date=dt,
            total_score=total,
            dasha_score=dasha_s,
            transit_score=transit_s,
            fast_score=fast_s,
            fired_rules=rules,
            md_lord=md_lord,
            ad_lord=ad_lord,
            likelihood=likelihood,
        ))

    return points


def _get_layer_scores(birth_dt, lat, lon, alt, domain, eval_date, md_lord, ad_lord):
    """Get individual layer scores for a domain at a date."""
    import importlib

    module_name = f"rules.{domain}_evaluator"
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        return 0, 0, 0

    try:
        chart = mod.ChartState(birth_dt, lat, lon, alt)
    except Exception:
        return 0, 0, 0

    # Dasha
    dasha_s = 0
    try:
        import inspect
        sig = inspect.signature(mod.evaluate_dasha_layer)
        if len(sig.parameters) == 3:
            fired = mod.evaluate_dasha_layer(chart, md_lord, ad_lord)
        else:
            transit = mod.TransitState(eval_date, chart)
            fired = mod.evaluate_dasha_layer(chart, transit)
        dasha_s = sum(s for _, s, _ in fired)
    except Exception:
        pass

    # Transit
    transit_s = 0
    try:
        transit = mod.TransitState(eval_date, chart)
        fired = mod.evaluate_transit_layer(chart, transit)
        transit_s = sum(s for _, s, _ in fired)
    except Exception:
        pass

    # Fast trigger
    fast_s = 0
    try:
        transit = mod.TransitState(eval_date, chart)
        fired = mod.evaluate_fast_trigger_layer(chart, transit)
        fast_s = sum(s for _, s, _ in fired)
    except Exception:
        pass

    return dasha_s, transit_s, fast_s


# ═══════════════════════════════════════════════════════════════
# ACTIVATION DENSITY
# ═══════════════════════════════════════════════════════════════

def compute_activation_density(points: list, threshold_pct=0.25):
    """
    Compute activation density metrics for a timeline.

    Activation density = concentration of meaningful signal in a time band.
    Not just the highest peak, but the strength and continuity of the whole period.

    Parameters
    ----------
    points : list[RichTimePoint]
    threshold_pct : float — fraction of peak to use as "active" threshold

    Returns
    -------
    dict with: density, sustained_length, active_count, total_count,
               band_start, band_end, avg_active_score
    """
    if not points or all(p.total_score <= 0 for p in points):
        return {"density": 0, "sustained_length": 0, "band_start": None, "band_end": None}

    peak = max(p.total_score for p in points)
    threshold = peak * threshold_pct

    active = [p for p in points if p.total_score >= threshold]
    total = len(points)

    if not active:
        return {"density": 0, "sustained_length": 0, "band_start": None, "band_end": None}

    # Find longest contiguous active run
    runs = []
    current_run = []
    for p in points:
        if p.total_score >= threshold:
            current_run.append(p)
        else:
            if current_run:
                runs.append(current_run)
                current_run = []
    if current_run:
        runs.append(current_run)

    # Best run = longest or highest-scoring
    best_run = max(runs, key=lambda r: sum(p.total_score for p in r))

    band_start = best_run[0].date
    band_end = best_run[-1].date
    duration = (band_end - band_start).days
    avg_score = sum(p.total_score for p in best_run) / len(best_run)

    return {
        "density": round(len(active) / total, 3),
        "sustained_length": len(best_run),
        "sustained_days": duration,
        "band_start": band_start,
        "band_end": band_end,
        "avg_active_score": round(avg_score, 1),
        "peak_score": peak,
        "active_count": len(active),
        "total_count": total,
    }


# ═══════════════════════════════════════════════════════════════
# MOMENTUM DETECTION
# ═══════════════════════════════════════════════════════════════

def compute_momentum(points: list):
    """
    Detect rising and falling momentum in the activation timeline.

    Returns dict with: rising_start, peak_date, falling_end,
                       rising_slope, falling_slope
    """
    if not points or len(points) < 3:
        return {"rising_start": None, "peak_date": None, "falling_end": None}

    scores = [p.total_score for p in points]
    peak_idx = scores.index(max(scores))
    peak_date = points[peak_idx].date

    # Find rising start (first point where score starts increasing toward peak)
    rising_start = points[0].date
    for i in range(1, peak_idx):
        if scores[i] > scores[i - 1] and scores[i] > 0:
            rising_start = points[i].date
            break

    # Find falling end (last point where score is still meaningful after peak)
    falling_end = points[-1].date
    threshold = max(scores) * 0.2
    for i in range(len(points) - 1, peak_idx, -1):
        if scores[i] >= threshold:
            falling_end = points[i].date
            break

    # Compute slopes
    rising_slope = 0
    if peak_idx > 0:
        rising_days = (peak_date - rising_start).days
        if rising_days > 0:
            rising_slope = round(scores[peak_idx] / rising_days, 2)

    falling_slope = 0
    if peak_idx < len(points) - 1:
        falling_days = (falling_end - peak_date).days
        if falling_days > 0:
            falling_slope = round(scores[peak_idx] / falling_days, 2)

    return {
        "rising_start": rising_start,
        "peak_date": peak_date,
        "falling_end": falling_end,
        "rising_slope": rising_slope,
        "falling_slope": falling_slope,
        "total_active_days": (falling_end - rising_start).days,
    }


# ═══════════════════════════════════════════════════════════════
# LAYER CONTRIBUTION ANALYSIS
# ═══════════════════════════════════════════════════════════════

def compute_layer_contributions(points: list):
    """
    Compute what percentage of total signal comes from each layer.

    Returns dict with: dasha_pct, transit_pct, fast_pct, dominant_layer
    """
    total_dasha = sum(p.dasha_score for p in points if p.dasha_score > 0)
    total_transit = sum(p.transit_score for p in points if p.transit_score > 0)
    total_fast = sum(p.fast_score for p in points if p.fast_score > 0)
    grand_total = total_dasha + total_transit + total_fast

    if grand_total == 0:
        return {"dasha_pct": 0, "transit_pct": 0, "fast_pct": 0, "dominant_layer": "none"}

    dasha_pct = round(total_dasha / grand_total, 3)
    transit_pct = round(total_transit / grand_total, 3)
    fast_pct = round(total_fast / grand_total, 3)

    dominant = "dasha" if dasha_pct >= transit_pct and dasha_pct >= fast_pct else \
               "transit" if transit_pct >= fast_pct else "fast"

    return {
        "dasha_pct": dasha_pct,
        "transit_pct": transit_pct,
        "fast_pct": fast_pct,
        "dominant_layer": dominant,
        "dasha_total": total_dasha,
        "transit_total": total_transit,
        "fast_total": total_fast,
    }


# ═══════════════════════════════════════════════════════════════
# DENSITY-AWARE CONFIDENCE
# ═══════════════════════════════════════════════════════════════

def compute_density_confidence(points: list, density_info: dict, momentum: dict, layers: dict):
    """
    Compute density-aware confidence that incorporates:
    - Sustained activation density (not just peak)
    - Consecutive active periods
    - Dasha-transit concurrence
    - Multi-layer agreement
    - Momentum strength

    Returns dict with: confidence (0-1), components, interpretation
    """
    if not points or density_info.get("density", 0) == 0:
        return {"confidence": 0.0, "interpretation": "no_signal", "components": {}}

    # Component 1: Density (0-1) — how much of the timeline is active
    density = density_info["density"]

    # Component 2: Peak strength (0-1) — normalized peak score
    peak = density_info.get("peak_score", 0)
    peak_strength = min(peak / 120.0, 1.0)

    # Component 3: Sustained length (0-1) — longer bands = more confident
    sustained = density_info.get("sustained_days", 0)
    sustained_factor = min(sustained / 720.0, 1.0)  # 2 years = max

    # Component 4: Multi-layer agreement (0-1)
    # If dasha AND transit both contribute, confidence is higher
    dasha_pct = layers.get("dasha_pct", 0)
    transit_pct = layers.get("transit_pct", 0)
    # Best case: both contribute roughly equally (0.4-0.6 each)
    balance = 1.0 - abs(dasha_pct - transit_pct)
    layer_agreement = balance * 0.7 + (0.3 if dasha_pct > 0.1 and transit_pct > 0.1 else 0)

    # Component 5: Momentum clarity (0-1)
    # Clear rise → peak → fall = high confidence
    active_days = momentum.get("total_active_days", 0)
    momentum_factor = min(active_days / 900.0, 1.0) if active_days > 0 else 0.3

    # Weighted composite
    confidence = (
        density * 0.20 +
        peak_strength * 0.25 +
        sustained_factor * 0.20 +
        layer_agreement * 0.20 +
        momentum_factor * 0.15
    )

    interpretation = "very_low"
    if confidence >= 0.75:
        interpretation = "high"
    elif confidence >= 0.55:
        interpretation = "moderate"
    elif confidence >= 0.35:
        interpretation = "low"

    return {
        "confidence": round(confidence, 3),
        "interpretation": interpretation,
        "components": {
            "density": round(density, 3),
            "peak_strength": round(peak_strength, 3),
            "sustained_factor": round(sustained_factor, 3),
            "layer_agreement": round(layer_agreement, 3),
            "momentum_factor": round(momentum_factor, 3),
        },
    }


# ═══════════════════════════════════════════════════════════════
# BASELINE CONFIDENCE (for comparison)
# ═══════════════════════════════════════════════════════════════

def compute_baseline_confidence(points: list):
    """
    Simple peak-based confidence (the old approach).
    Just peak_score / 150, clamped to [0, 1].
    """
    if not points:
        return 0.0
    peak = max(p.total_score for p in points)
    return round(min(peak / 150.0, 1.0), 3)


# ═══════════════════════════════════════════════════════════════
# MASTER PROFILE BUILDER
# ═══════════════════════════════════════════════════════════════

def build_activation_profile(birth_dt, lat, lon, alt, domain,
                             center_date, radius_months=18):
    """
    Build a complete activation intelligence profile for a domain.

    This is the main entry point. It scans, computes density, momentum,
    layer contributions, and both confidence variants.
    """
    # Scan with layer breakdown
    points = scan_rich_timeline(birth_dt, lat, lon, alt, domain,
                                center_date, radius_months)

    # Density
    density_info = compute_activation_density(points)

    # Momentum
    momentum = compute_momentum(points)

    # Layer contributions
    layers = compute_layer_contributions(points)

    # Confidence variants
    baseline_conf = compute_baseline_confidence(points)
    density_conf = compute_density_confidence(points, density_info, momentum, layers)

    # Monthly/quarterly rollups
    months = defaultdict(list)
    quarters = defaultdict(list)
    for p in points:
        months[(p.date.year, p.date.month)].append(p.total_score)
        q = (p.date.year, (p.date.month - 1) // 3 + 1)
        quarters[q].append(p.total_score)

    best_month = max(months.items(), key=lambda x: sum(x[1]) / len(x[1])) if months else None
    best_quarter = max(quarters.items(), key=lambda x: sum(x[1]) / len(x[1])) if quarters else None

    # Build profile
    profile = ActivationProfile(domain=domain, center_date=center_date)
    profile.timeline = points

    # Peak
    if points:
        peak_p = max(points, key=lambda p: p.total_score)
        profile.peak_date = peak_p.date
        profile.peak_score = peak_p.total_score

    # Band
    if density_info.get("band_start"):
        profile.band_start = density_info["band_start"]
        profile.band_end = density_info["band_end"]
        profile.band_duration_days = density_info.get("sustained_days", 0)
        profile.band_avg_score = density_info.get("avg_active_score", 0)
        profile.band_density = density_info.get("density", 0)

    # Momentum
    profile.rising_start = momentum.get("rising_start")
    profile.peak_momentum_date = momentum.get("peak_date")
    profile.falling_end = momentum.get("falling_end")

    # Layers
    profile.dasha_contribution_pct = layers.get("dasha_pct", 0)
    profile.transit_contribution_pct = layers.get("transit_pct", 0)
    profile.fast_contribution_pct = layers.get("fast_pct", 0)

    # Confidence
    profile.baseline_confidence = baseline_conf
    profile.density_confidence = density_conf["confidence"]

    # Monthly/Quarterly
    if best_month:
        key, scores = best_month
        profile.strongest_month = f"{key[0]}-{key[1]:02d}"
        profile.strongest_month_score = round(sum(scores) / len(scores), 1)
    if best_quarter:
        key, scores = best_quarter
        profile.strongest_quarter = f"{key[0]}-Q{key[1]}"
        profile.strongest_quarter_score = round(sum(scores) / len(scores), 1)

    return profile


# ═══════════════════════════════════════════════════════════════
# TRUST-BUILDING PRESENTATION
# ═══════════════════════════════════════════════════════════════

def format_trust_output(profile: ActivationProfile, actual_date: datetime = None):
    """
    Format an ActivationProfile into a user-facing trust-building output.

    Returns a multi-line string suitable for display.
    """
    lines = []

    # Band
    if profile.band_start and profile.band_end:
        lines.append(f"High-density band: {profile.band_start.strftime('%b %Y')} → {profile.band_end.strftime('%b %Y')}")
        lines.append(f"Band duration: {profile.band_duration_days} days ({profile.band_duration_days // 30} months)")

    # Strongest month
    if profile.strongest_month:
        lines.append(f"Strongest month: {profile.strongest_month} (avg: {profile.strongest_month_score:.0f})")

    # Peak
    if profile.peak_date:
        lines.append(f"Peak signal: {profile.peak_date.strftime('%b %Y')} (score: {profile.peak_score:.0f})")

    # Confidence
    lines.append(f"Density confidence: {profile.density_confidence:.2f}")
    lines.append(f"Baseline confidence: {profile.baseline_confidence:.2f}")

    # Layer breakdown
    lines.append(f"Layer mix: dasha={profile.dasha_contribution_pct:.0%} transit={profile.transit_contribution_pct:.0%} fast={profile.fast_contribution_pct:.0%}")

    # Actual event check
    if actual_date:
        if profile.band_start and profile.band_end:
            if profile.band_start <= actual_date <= profile.band_end:
                lines.append(f"Actual event ({actual_date.strftime('%d %b %Y')}): ✓ INSIDE BAND")
            else:
                dist = min(abs((actual_date - profile.band_start).days),
                          abs((actual_date - profile.band_end).days))
                lines.append(f"Actual event ({actual_date.strftime('%d %b %Y')}): {dist} days from band edge")
        if profile.peak_date:
            peak_dist = abs((profile.peak_date - actual_date).days)
            lines.append(f"Peak drift: {peak_dist} days from actual")

    return "\n".join(lines)


def score_against_actual(profile: ActivationProfile, actual_date: datetime):
    """Score a profile against the actual event date."""
    result = {
        "peak_distance_days": 999,
        "within_band": False,
        "band_overlap": 0.0,
        "within_month_of_peak": False,
        "within_quarter_of_peak": False,
    }

    if profile.peak_date:
        result["peak_distance_days"] = abs((profile.peak_date - actual_date).days)
        result["within_month_of_peak"] = result["peak_distance_days"] <= 30
        result["within_quarter_of_peak"] = result["peak_distance_days"] <= 90

    if profile.band_start and profile.band_end:
        if profile.band_start <= actual_date <= profile.band_end:
            result["within_band"] = True
            result["band_overlap"] = 1.0
        else:
            dist = min(abs((actual_date - profile.band_start).days),
                      abs((actual_date - profile.band_end).days))
            if dist <= 30:
                result["band_overlap"] = 0.7
            elif dist <= 90:
                result["band_overlap"] = 0.3

    return result
