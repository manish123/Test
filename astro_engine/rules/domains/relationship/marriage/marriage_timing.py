"""
Marriage Timing — Converts fired rules into timing predictions.

Logic flow:
    Dasha rule fires → BROAD_WINDOW (months)
    Transit rule fires → NARROW_WINDOW (weeks)
    Fast trigger fires → TARGET_DAY (days)

Each fired rule carries a window specification:
    broad_window_days: maximum outer boundary
    exact_window_days: inner precision boundary
    confidence_decay_days: how quickly confidence drops after peak

This module combines multiple windows into a single timing prediction.
"""

from typing import Dict, Any, List
from datetime import date, timedelta


def compute_timing(evaluation_result: Dict[str, Any], eval_date: date = None) -> Dict[str, Any]:
    """
    Compute timing predictions from fired marriage rules.

    Args:
        evaluation_result: output of evaluate_marriage_rules()
        eval_date: evaluation date (defaults to today)

    Returns:
        dict with:
            "signal_level": NO_SIGNAL | BROAD_WINDOW | NARROW_WINDOW | TARGET_DAY
            "broad_window": {"start": date, "end": date, "days": int} or None
            "narrow_window": {"start": date, "end": date, "days": int} or None
            "target_window": {"start": date, "end": date, "days": int} or None
            "confidence_peak_date": date when confidence is highest
            "confidence_decay": how quickly confidence drops (days)
            "timing_sources": which rule types contributed
    """
    if eval_date is None:
        eval_date = date.today()

    fired = evaluation_result.get("fired_rules", [])
    composite_signal = evaluation_result.get("composite_signal", "NO_SIGNAL")

    if not fired:
        return {
            "signal_level": "NO_SIGNAL",
            "broad_window": None,
            "narrow_window": None,
            "target_window": None,
            "confidence_peak_date": None,
            "confidence_decay": None,
            "timing_sources": [],
        }

    # Collect windows from all fired rules
    broad_windows = []
    exact_windows = []
    decay_values = []
    timing_sources = set()

    for rule in fired:
        window = rule.get("window", {})
        rule_type = rule.get("rule_type", "unknown")
        timing_sources.add(rule_type)

        broad_days = window.get("broad_window_days", 180)
        exact_days = window.get("exact_window_days", 30)
        decay_days = window.get("confidence_decay_days", 30)

        broad_windows.append(broad_days)
        exact_windows.append(exact_days)
        decay_values.append(decay_days)

    # Compute composite windows
    # Broad window: use the SHORTEST broad window (intersection logic)
    min_broad = min(broad_windows) if broad_windows else 180
    # Exact window: use the SHORTEST exact window (tightest precision)
    min_exact = min(exact_windows) if exact_windows else 30
    # Confidence decay: use the SHORTEST decay (fastest falloff)
    min_decay = min(decay_values) if decay_values else 30

    # Build timing output
    broad_window = {
        "start": eval_date,
        "end": eval_date + timedelta(days=min_broad),
        "days": min_broad,
    }

    narrow_window = None
    target_window = None

    if composite_signal in ("NARROW_WINDOW", "TARGET_DAY"):
        # Narrow window starts from eval_date, bounded by exact_window
        narrow_start = eval_date
        narrow_end = eval_date + timedelta(days=min_exact * 3)  # 3× exact for narrow
        narrow_window = {
            "start": narrow_start,
            "end": narrow_end,
            "days": min_exact * 3,
        }

    if composite_signal == "TARGET_DAY":
        # Target window is the tightest precision available
        target_start = eval_date
        target_end = eval_date + timedelta(days=min_exact)
        target_window = {
            "start": target_start,
            "end": target_end,
            "days": min_exact,
        }

    # Confidence peak: midpoint of the tightest window
    if target_window:
        peak_offset = min_exact // 2
    elif narrow_window:
        peak_offset = (min_exact * 3) // 2
    else:
        peak_offset = min_broad // 2

    confidence_peak_date = eval_date + timedelta(days=peak_offset)

    return {
        "signal_level": composite_signal,
        "broad_window": _serialize_window(broad_window),
        "narrow_window": _serialize_window(narrow_window) if narrow_window else None,
        "target_window": _serialize_window(target_window) if target_window else None,
        "confidence_peak_date": confidence_peak_date.isoformat(),
        "confidence_decay_days": min_decay,
        "timing_sources": sorted(timing_sources),
        "timing_summary": _build_timing_summary(composite_signal, broad_window, narrow_window, target_window),
    }


def _serialize_window(window: Dict) -> Dict[str, Any]:
    """Convert date objects to ISO strings for JSON serialization."""
    if window is None:
        return None
    return {
        "start": window["start"].isoformat() if isinstance(window["start"], date) else window["start"],
        "end": window["end"].isoformat() if isinstance(window["end"], date) else window["end"],
        "days": window["days"],
    }


def _build_timing_summary(signal: str, broad, narrow, target) -> str:
    """Generate a human-readable timing summary."""
    if signal == "NO_SIGNAL":
        return "No marriage timing signals detected."
    if signal == "TARGET_DAY":
        return f"High-precision window: within {target['days']} days. Broad context: {broad['days']} days."
    if signal == "NARROW_WINDOW":
        return f"Narrow window: within {narrow['days']} days. Broad context: {broad['days']} days."
    if signal == "BROAD_WINDOW":
        return f"Broad window active: within {broad['days']} days."
    return f"Weak signal detected. Broad context: {broad['days']} days."
