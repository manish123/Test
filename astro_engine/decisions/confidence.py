def confidence_score(data, penalties=None, profile_params=None):
    """
    Compute confidence score from event strength, yoga, dasha, and risk.

    Parameters
    ----------
    data : dict
        Keys: event_strength, yoga, dasha, promise, kakshya_active
    penalties : dict, optional
        Keys: risk (float) or risk_adjustment (float)
    profile_params : dict, optional
        If provided, overrides hardcoded defaults with profile-specific values.
        Keys: risk_penalty_factor, risk_penalty_cap, high_risk_threshold,
              high_risk_extra, weak_promise_multiplier, kakshya_inactive_multiplier
        If None, uses current hardcoded defaults (backward compatible).

    Returns
    -------
    float : confidence score clamped to [0, 100]
    """
    penalties = penalties or {}

    # Extract profile params or use hardcoded defaults
    if profile_params:
        risk_factor = profile_params.get("risk_penalty_factor", 0.15)
        risk_cap = profile_params.get("risk_penalty_cap", 40)
        high_risk_thresh = profile_params.get("high_risk_threshold", 120)
        high_risk_extra = profile_params.get("high_risk_extra", 10)
        weak_mult = profile_params.get("weak_promise_multiplier", 0.6)
        kakshya_mult = profile_params.get("kakshya_inactive_multiplier", 0.7)
    else:
        risk_factor = 0.15
        risk_cap = 40
        high_risk_thresh = 120
        high_risk_extra = 10
        weak_mult = 0.6
        kakshya_mult = 0.7

    base_confidence = data.get("event_strength", 0) + data.get("yoga", 0) + data.get("dasha", 0)

    risk = penalties.get("risk")
    if risk is not None:
        risk_adjustment = min(risk_cap, risk * risk_factor)
        if risk > high_risk_thresh:
            risk_adjustment += high_risk_extra
    else:
        risk_adjustment = penalties.get("risk_adjustment", 0)
    score = base_confidence - risk_adjustment

    if data.get("promise") == "weak":
        score *= weak_mult

    if not data.get("kakshya_active", True):
        score *= kakshya_mult

    return round(max(0.0, min(100.0, score)), 2)
