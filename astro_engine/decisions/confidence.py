def confidence_score(data, penalties=None):
    penalties = penalties or {}

    base_confidence = data.get("event_strength", 0) + data.get("yoga", 0) + data.get("dasha", 0)

    risk = penalties.get("risk")
    if risk is not None:
        # Increased from 0.10 to 0.15 — more meaningful risk penalty on confidence
        risk_adjustment = min(40, risk * 0.15)
        if risk > 120:
            risk_adjustment += 10
    else:
        risk_adjustment = penalties.get("risk_adjustment", 0)
    score = base_confidence - risk_adjustment

    if data.get("promise") == "weak":
        score *= 0.6

    if not data.get("kakshya_active", True):
        score *= 0.7

    return round(max(0.0, min(100.0, score)), 2)
