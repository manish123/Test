import csv
import math
import os
from datetime import datetime


def apply_feedback(weights, actual, confidence):
    updated = dict(weights)

    if not actual and confidence > 80:
        updated["dasha"] = max(0.0, updated.get("dasha", 0.12) - 0.05)
        updated["ashtakavarga"] = updated.get("ashtakavarga", 0.08) + 0.05
        updated["yoga_bhanga"] = updated.get("yoga_bhanga", 0.0) + 0.1

    if actual and confidence < 40:
        updated["transit"] = updated.get("transit", 0.12) + 0.1
        updated["tara"] = updated.get("tara", 0.0) + 0.05

    return updated


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _action_bias(action):
    mapping = {
        "GO FULL": 1.0,
        "CONTROLLED AGGRESSION": 0.75,
        "AGGRESSIVE": 0.75,
        "MODERATE": 0.35,
        "LOW SIZE / TEST TRADE": 0.1,
        "LOW SIZE / WAIT": -0.15,
        "AVOID": -0.65,
        "SURVIVE": -0.85,
    }
    return mapping.get(str(action or "").strip().upper(), 0.0)


def _signal_from_period(period):
    decision = period.get("decision") or {}
    confidence = max(0.0, min(100.0, _to_float(decision.get("confidence"), 0.0)))
    risk = max(0.0, min(100.0, _to_float(decision.get("risk"), 0.0)))
    position_multiplier = max(0.0, min(1.0, _to_float(decision.get("position_multiplier"), 1.0)))
    action = decision.get("action")
    signal = (confidence / 100.0) - (risk / 100.0) + (_action_bias(action) * 0.4)
    signal *= position_multiplier
    return max(-1.0, min(1.0, signal))


def _mode_c_daily_signals(periods):
    daily = {}
    for period in periods or []:
        date_key = str(period.get("date") or "").strip()
        if not date_key:
            start = str(period.get("start") or "")
            if start:
                date_key = start.split("T", 1)[0]
        if not date_key:
            continue
        daily.setdefault(date_key, []).append(_signal_from_period(period))
    return {k: (sum(v) / len(v)) for k, v in daily.items() if v}


def _read_pnl_rows(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            normalized = {str(k or "").strip().lower(): v for k, v in raw.items()}
            date_raw = str(normalized.get("date", "")).strip()
            if not date_raw:
                continue
            try:
                date_key = datetime.strptime(date_raw, "%d/%m/%Y").date().isoformat()
            except ValueError:
                continue

            rel_score_raw = str(normalized.get("relativescore", "")).strip()
            rel_score = _to_float(rel_score_raw, None) if rel_score_raw != "" else None
            net_pnl = _to_float(normalized.get("netpnl"), 0.0)

            actual_score = rel_score if rel_score is not None else net_pnl
            rows.append(
                {
                    "date": date_key,
                    "actual_score": actual_score,
                    "net_pnl": net_pnl,
                    "relative_score": rel_score,
                }
            )
    return rows


def _sign(value, eps=1e-9):
    if value > eps:
        return 1
    if value < -eps:
        return -1
    return 0


def _pearson(x_values, y_values):
    n = len(x_values)
    if n < 2:
        return None
    mean_x = sum(x_values) / n
    mean_y = sum(y_values) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in x_values))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in y_values))
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def _inc(counter, key):
    counter[key] = counter.get(key, 0) + 1


def _dominant(values, default="unknown"):
    if not values:
        return default
    counts = {}
    for v in values:
        k = str(v or default)
        counts[k] = counts.get(k, 0) + 1
    return max(counts.items(), key=lambda kv: kv[1])[0]


def _date_context_map(periods):
    by_date = {}
    for period in periods or []:
        date_key = str(period.get("date") or "").strip()
        if not date_key:
            continue
        by_date.setdefault(date_key, []).append(period)

    context = {}
    for date_key, day_periods in by_date.items():
        actions = []
        nakshatras = []
        top_events = []
        confidences = []
        risks = []
        chandrabala_eighth_flags = []
        focal_11_sav_values = []
        focal_11_sav_bands = []
        risky_nakshatra_penalty_hits = []
        for p in day_periods:
            decision = p.get("decision") or {}
            actions.append(decision.get("action") or "unknown")
            confidences.append(_to_float(decision.get("confidence"), 0.0))
            risks.append(_to_float(decision.get("risk"), 0.0))
            nakshatras.append(p.get("moon_nakshatra") or "unknown")

            trading_gate = p.get("trading_gate") or {}
            chandrabala_eighth_flags.append(bool(trading_gate.get("chandrabala_eighth", False)))
            focal_11_sav_values.append(_to_float(trading_gate.get("focal_11_sav"), 0.0))
            focal_11_sav_bands.append(trading_gate.get("focal_11_sav_band") or "unknown")
            adaptive_overrides = trading_gate.get("adaptive_overrides") or {}
            risky_nakshatra_penalty_hits.append(bool(adaptive_overrides.get("risky_nakshatra_penalty", False)))

            top = p.get("top_events") or []
            if top and isinstance(top[0], (list, tuple)) and len(top[0]) >= 1:
                top_events.append(top[0][0])

        context[date_key] = {
            "dominant_action": _dominant(actions),
            "dominant_moon_nakshatra": _dominant(nakshatras),
            "dominant_top_event": _dominant(top_events),
            "avg_confidence": round(sum(confidences) / max(len(confidences), 1), 2),
            "avg_risk": round(sum(risks) / max(len(risks), 1), 2),
            "chandrabala_8th": any(chandrabala_eighth_flags),
            "avg_focal_11_sav": round(sum(focal_11_sav_values) / max(len(focal_11_sav_values), 1), 2),
            "dominant_focal_11_sav_band": _dominant(focal_11_sav_bands),
            "risky_nakshatra_penalty_hit": any(risky_nakshatra_penalty_hits),
        }

    return context


def _sorted_count_map(counter, limit=25):
    ordered = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)
    return [{"key": k, "count": v} for k, v in ordered[:limit]]


def build_mode_c_alignment_feedback(periods, pnl_csv_path):
    if not pnl_csv_path:
        return {
            "status": "skipped",
            "reason": "No pnl_csv_path provided",
        }

    csv_path = os.path.abspath(pnl_csv_path)
    if not os.path.exists(csv_path):
        return {
            "status": "error",
            "reason": f"PnL CSV not found: {csv_path}",
        }

    daily_signals = _mode_c_daily_signals(periods)
    if not daily_signals:
        return {
            "status": "skipped",
            "reason": "No Mode C periods available for alignment",
            "pnl_csv_path": csv_path,
        }

    pnl_rows = _read_pnl_rows(csv_path)
    day_context = _date_context_map(periods)
    overlap = []
    signal_series = []
    actual_series = []
    aligned_action_counts = {}
    misaligned_action_counts = {}
    aligned_combo_counts = {}
    misaligned_combo_counts = {}

    for row in pnl_rows:
        date_key = row["date"]
        if date_key not in daily_signals:
            continue
        predicted = daily_signals[date_key]
        actual = row["actual_score"]
        pred_sign = _sign(predicted)
        act_sign = _sign(actual)
        aligned = pred_sign == act_sign
        context = day_context.get(date_key, {})
        action = context.get("dominant_action", "unknown")
        combo_key = " | ".join(
            [
                context.get("dominant_top_event", "unknown"),
                context.get("dominant_moon_nakshatra", "unknown"),
                action,
            ]
        )
        if aligned:
            _inc(aligned_action_counts, action)
            _inc(aligned_combo_counts, combo_key)
        else:
            _inc(misaligned_action_counts, action)
            _inc(misaligned_combo_counts, combo_key)

        overlap.append(
            {
                "date": date_key,
                "predicted_signal": round(predicted, 4),
                "actual_score": round(actual, 4),
                "actual_net_pnl": round(row["net_pnl"], 2),
                "actual_relative_score": row["relative_score"],
                "predicted_direction": "up" if pred_sign > 0 else "down" if pred_sign < 0 else "flat",
                "actual_direction": "up" if act_sign > 0 else "down" if act_sign < 0 else "flat",
                "aligned": aligned,
                "context": context,
            }
        )
        signal_series.append(predicted)
        actual_series.append(actual)

    if not overlap:
        return {
            "status": "no_overlap",
            "pnl_csv_path": csv_path,
            "mode_c_days": len(daily_signals),
            "pnl_days": len(pnl_rows),
            "reason": "No overlapping dates between Mode C output and PnL CSV",
        }

    aligned_count = sum(1 for r in overlap if r["aligned"])
    accuracy = aligned_count / len(overlap)
    corr = _pearson(signal_series, actual_series)

    label = "low"
    if accuracy >= 0.7:
        label = "high"
    elif accuracy >= 0.55:
        label = "moderate"

    perfect_actions = {"GO FULL", "CONTROLLED AGGRESSION", "AGGRESSIVE", "TRADE HEAVILY"}
    perfect_combo_candidates = []
    for key, count in aligned_combo_counts.items():
        mis_count = misaligned_combo_counts.get(key, 0)
        if mis_count == 0 and count >= 2:
            action = key.split(" | ")[-1] if " | " in key else "unknown"
            perfect_combo_candidates.append(
                {
                    "combo": key,
                    "aligned_count": count,
                    "recommended_trade_heavy": action not in perfect_actions,
                }
            )
    perfect_combo_candidates.sort(key=lambda x: x["aligned_count"], reverse=True)

    return {
        "status": "ok",
        "pnl_csv_path": csv_path,
        "mode_c_days": len(daily_signals),
        "pnl_days": len(pnl_rows),
        "overlap_days": len(overlap),
        "directional_accuracy": round(accuracy, 4),
        "alignment_label": label,
        "pearson_correlation": None if corr is None else round(corr, 4),
        "aligned_days": aligned_count,
        "misaligned_days": len(overlap) - aligned_count,
        "aligned_action_distribution": _sorted_count_map(aligned_action_counts),
        "misaligned_action_distribution": _sorted_count_map(misaligned_action_counts),
        "top_aligned_combinations": _sorted_count_map(aligned_combo_counts),
        "top_misaligned_combinations": _sorted_count_map(misaligned_combo_counts),
        "perfectly_aligned_combinations": perfect_combo_candidates[:25],
        "daily_alignment": overlap,
    }
