EVENT_FAMILY = {
    "finance": "wealth",
    "property": "wealth",
    "career": "profession",
    "job": "profession",
    "business": "profession",
    "authority": "profession",
    "retirement": "lifecycle",
    "achievement": "profession",
    "legal": "risk",
    "litigation": "risk",
    "loss": "risk",
    "inheritance": "wealth",
    "bankruptcy": "sensitive",
    "health": "wellbeing",
    "health_scare": "wellbeing",
    "accident": "risk",
    "hospitalization": "risk",
    "surgery": "risk",
    "criminal_record": "sensitive",
    "education": "development",
    "studies": "development",
    "examination": "development",
    "creative_milestone": "development",
    "belief_shift": "development",
    "children": "family",
    "child_birth": "family",
    "grandchildren": "family",
    "spiritual": "development",
    "travel_foreign": "mobility",
    "relocation": "mobility",
    "citizenship": "mobility",
    "relationship": "relationship",
    "marriage": "relationship",
    "divorce": "risk",
    "extra_marital": "sensitive",
    "parents_death": "lifecycle",
    "sibling_death": "lifecycle",
    "spouse_bereavement": "lifecycle",
    "behavior_risk": "behavior",
    "behavior_discipline": "behavior",
    "addiction_recovery": "behavior",
}


PROFILE_CONFIG = {
    "professional": {
        "family_caps": {
            "sensitive": 0.55,
            "behavior": 0.80,
            "relationship": 0.85,
            "lifecycle": 0.75,
        },
        "event_boost": {
            "career": 1.15,
            "job": 1.15,
            "business": 1.15,
            "finance": 1.10,
            "authority": 1.10,
            "achievement": 1.15,
            "retirement": 1.05,
        },
    },
    "personal": {
        "family_caps": {
            "profession": 0.90,
            "sensitive": 0.65,
            "risk": 0.80,
        },
        "event_boost": {
            "relationship": 1.15,
            "marriage": 1.20,
            "children": 1.15,
            "child_birth": 1.20,
            "grandchildren": 1.15,
            "retirement": 1.15,
            "relocation": 1.10,
            "health": 1.10,
            "health_scare": 1.10,
            "education": 1.10,
            "studies": 1.12,
            "examination": 1.12,
            "creative_milestone": 1.10,
            "belief_shift": 1.10,
        },
    },
    "risk_control": {
        "family_caps": {
            "sensitive": 0.45,
            "behavior": 0.70,
            "relationship": 0.80,
        },
        "event_boost": {
            "loss": 1.15,
            "legal": 1.10,
            "litigation": 1.20,
            "divorce": 1.25,
            "health": 1.10,
            "health_scare": 1.15,
            "accident": 1.20,
            "hospitalization": 1.15,
            "surgery": 1.10,
            "bankruptcy": 1.20,
            "criminal_record": 1.20,
            "parents_death": 1.10,
            "sibling_death": 1.10,
            "spouse_bereavement": 1.15,
            "behavior_risk": 1.15,
            "addiction_recovery": 1.15,
        },
    },
    "adult_sensitive": {
        "family_caps": {
            "sensitive": 1.00,
            "behavior": 0.90,
            "lifecycle": 0.90,
        },
        "event_boost": {
            "relationship": 1.10,
            "extra_marital": 1.30,
            "divorce": 1.20,
            "health_scare": 1.05,
            "behavior_risk": 1.10,
        },
    },
}

SENSITIVE_EVENTS = {"extra_marital", "bankruptcy", "criminal_record"}


def apply_event_governance(event_scores, profile="professional", context=None, allow_adult_insights=False):
    context = context or {}
    cfg = PROFILE_CONFIG.get(profile, PROFILE_CONFIG["professional"])
    age_years = context.get("age_years", 0)
    is_adult_eligible = bool(age_years >= 18)
    is_adult_profile = profile == "adult_sensitive"
    adult_access_enabled = (not is_adult_profile) or (allow_adult_insights and is_adult_eligible)

    governed = {k: float(v) for k, v in event_scores.items()}
    caps_applied = {}
    boosts_applied = {}
    gated_events = []

    for event_name, mult in cfg.get("event_boost", {}).items():
        if event_name in governed:
            governed[event_name] *= mult
            boosts_applied[event_name] = mult

    for event_name, score in list(governed.items()):
        family = EVENT_FAMILY.get(event_name)
        cap = cfg.get("family_caps", {}).get(family)
        if cap is not None:
            governed[event_name] = score * cap
            caps_applied[event_name] = cap

    yoga_score = context.get("yoga_score", 0)
    transit_strength = context.get("transit_strength", 0)

    for event_name in SENSITIVE_EVENTS:
        if event_name not in governed:
            continue

        sensitive_score = governed[event_name]
        is_strong_signal = sensitive_score >= 160 and yoga_score >= 8 and transit_strength >= 0.5
        if not adult_access_enabled:
            governed[event_name] = 0.0
            gated_events.append(event_name)
            continue
        if not is_strong_signal:
            governed[event_name] = sensitive_score * 0.45
            gated_events.append(event_name)

    return governed, {
        "profile": profile,
        "caps_applied": caps_applied,
        "boosts_applied": boosts_applied,
        "gated_events": gated_events,
        "adult_sensitive": {
            "consent_required": is_adult_profile,
            "consent_granted": bool(allow_adult_insights),
            "adult_eligible": is_adult_eligible,
            "active": is_adult_profile and adult_access_enabled,
        },
    }
