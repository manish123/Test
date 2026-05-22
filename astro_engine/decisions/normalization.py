MIN_EVENT_SCORE = 0.0
MAX_EVENT_SCORE = 320.0


def _clamp(value, low, high):
    return max(low, min(high, value))


def event_strength_label(normalized_score):
    if normalized_score < 40:
        return "Weak"
    if normalized_score < 65:
        return "Moderate"
    if normalized_score < 85:
        return "Strong"
    return "Extreme"


def normalize_event_score(raw_score, min_score=MIN_EVENT_SCORE, max_score=MAX_EVENT_SCORE):
    span = max(max_score - min_score, 1e-6)
    normalized = ((raw_score - min_score) / span) * 100.0
    return round(_clamp(normalized, 0.0, 100.0), 2)


def normalize_event_scores(event_scores, min_score=MIN_EVENT_SCORE, max_score=MAX_EVENT_SCORE):
    normalized = {}
    for event_name, raw in event_scores.items():
        norm = normalize_event_score(raw, min_score=min_score, max_score=max_score)
        normalized[event_name] = {
            "raw": round(raw, 2),
            "score_100": norm,
            "label": event_strength_label(norm),
        }
    return normalized


def normalize_top_events(top_events, normalized_event_scores):
    normalized_top = []
    for event_name, raw in top_events:
        info = normalized_event_scores.get(event_name)
        if info is None:
            normalized_top.append({
                "event": event_name,
                "raw": round(raw, 2),
                "score_100": normalize_event_score(raw),
                "label": event_strength_label(normalize_event_score(raw)),
            })
            continue
        normalized_top.append(
            {
                "event": event_name,
                "raw": info["raw"],
                "score_100": info["score_100"],
                "label": info["label"],
            }
        )
    return normalized_top
