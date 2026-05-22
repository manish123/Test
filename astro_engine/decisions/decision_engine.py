def generate_decision(top_events, risk, confidence, av_vulnerability=0):
    event_name, score = top_events[0]

    if confidence >= 70 and risk < 45:
        action = "GO FULL"
    elif confidence >= 60 and score > 120:
        action = "CONTROLLED AGGRESSION"
    elif confidence >= 50 and risk < 75:
        action = "MODERATE"
    elif 75 <= risk <= 130:
        action = "LOW SIZE / WAIT"
    else:
        action = "AVOID"

    phase = "NORMAL"
    if risk > 120 and confidence < 30 and av_vulnerability > 70:
        phase = "DESTRUCTIVE"
        action = "SURVIVE"

    return {
        "top_event": event_name,
        "score": score,
        "confidence": confidence,
        "risk": risk,
        "phase": phase,
        "action": action,
    }
