from rules.sade_sati import sade_sati_phase
from rules.maraka import maraka_score, maraka_trigger_risk
from features.rahu_ketu import node_crisis_score


def build_risk_context(
    planets,
    moon_sign,
    saturn_sign,
    sign_lords=None,
    lagna_sign=None,
    dasha_sandhi=False,
    av_vulnerability=0,
    maraka_trigger_data=None,
):
    phase, sade_risk = sade_sati_phase(moon_sign, saturn_sign)
    rahu_house = next((p.get("house") for p in planets if p["name"] == "Rahu"), None)
    node_risk = node_crisis_score(rahu_house) if rahu_house else 0
    favorable = node_risk < 0
    if favorable:
        node_risk -= 10
    maraka_trigger_data = maraka_trigger_data or {}
    maraka_trigger_points, maraka_level = maraka_trigger_risk(
        maraka_trigger_data.get("md_lord", ""),
        maraka_trigger_data.get("ad_lord", ""),
        maraka_trigger_data.get("maraka_lords", set()),
        maraka_trigger_data.get("age_years", 0),
        maraka_trigger_data.get("longevity_bracket", (72, 120)),
        maraka_trigger_data.get("planet_in_8th", False),
    )

    return {
        "sade_sati": sade_risk,
        "saturn_pressure": sade_risk > 0,
        "node_crisis": node_risk,
        "maraka": maraka_score(planets, sign_lords=sign_lords, lagna_sign=lagna_sign),
        "maraka_trigger": maraka_trigger_points,
        "maraka_level": maraka_level,
        "av_vulnerability": av_vulnerability,
        "ashtama_shani": 25 if phase == "ashtama" else 0,
        "tara_risk": 0,
        "dasha_sandhi": 25 if dasha_sandhi else 0,
        "badhakesh": 0,
        "gochar_vedha": 0,
        "panchang_adverse": 0,
        "sbc_vedha": 0,
        "sade_sati_phase": phase,
    }


def calculate_risk(factors):
    risk = 0

    if factors.get("saturn_pressure"):
        risk += 12

    risk += min(15, max(0, factors.get("node_crisis", 0)))

    if factors.get("sade_sati"):
        phase = factors.get("sade_sati_phase")
        phase_weight = {
            "rising": 10,
            "peak": 20,
            "setting": 15,
            "ashtama": 25,
        }
        risk += phase_weight.get(phase, 10)

    risk += min(20, factors.get("maraka", 0) * 0.5)
    risk += min(25, factors.get("maraka_trigger", 0) * 0.4)
    risk += min(25, factors.get("av_vulnerability", 0) * 0.3125)
    risk += min(10, factors.get("ashtama_shani", 0) * 0.4)
    risk += min(10, factors.get("sbc_vedha", 0))
    risk += min(10, factors.get("tara_risk", 0) * 0.5)
    risk += min(15, factors.get("dasha_sandhi", 0) * 0.6)
    risk += min(12, factors.get("badhakesh", 0) * 0.6)
    risk += min(10, factors.get("gochar_vedha", 0) * 0.67)
    risk += min(10, factors.get("panchang_adverse", 0) * 0.5)

    return min(150, max(0, round(risk, 2)))
