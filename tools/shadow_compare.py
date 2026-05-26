"""
Shadow Comparison Harness — Compare baseline vs symbolic-enhanced OpenAI outputs.

Runs locally using .env keys. No production systems touched.

Usage:
    python tools/shadow_compare.py

Produces reports in reports/ directory.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from copy import deepcopy

# Setup paths
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "astro_engine"))

# Load .env
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.7
MAX_TOKENS = 1500

# ═══════════════════════════════════════════════════════════════
# SUBJECT LOADING
# ═══════════════════════════════════════════════════════════════

def load_subjects():
    with open(ROOT / "data" / "subjects.json") as f:
        return json.load(f)


def subject_to_birth_data(subject: dict) -> dict:
    """Convert subject fixture to birth_data_dict format."""
    parts = subject["date_of_birth"].split("-")
    time_parts = subject["time_of_birth"].split(":")
    birth_dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]),
                       int(time_parts[0]), int(time_parts[1]))
    return {
        "date": birth_dt,
        "lat": subject["lat"],
        "lon": subject["lon"],
        "alt": subject.get("alt", 0),
    }


# ═══════════════════════════════════════════════════════════════
# SYMBOLIC CONTEXT GENERATION
# ═══════════════════════════════════════════════════════════════

def get_symbolic_contexts(birth_data: dict, eval_date: datetime = None):
    """Generate all symbolic contexts for a subject."""
    if eval_date is None:
        eval_date = datetime.now()

    from orchestration.personality_api_adapter import build_personality_context, build_prompt_injection
    from orchestration.timing_api_adapter import build_timing_context, build_weekly_prediction_injection
    from orchestration.career_api_adapter import build_career_context, build_career_prompt_injection

    return {
        "personality_context": build_personality_context(birth_data, eval_date),
        "personality_injection": build_prompt_injection(birth_data, eval_date),
        "timing_context": build_timing_context(birth_data, eval_date),
        "timing_injection": build_weekly_prediction_injection(birth_data, eval_date),
        "career_context": build_career_context(birth_data, eval_date),
        "career_injection": build_career_prompt_injection(birth_data, eval_date),
    }


# ═══════════════════════════════════════════════════════════════
# OPENAI CALLS
# ═══════════════════════════════════════════════════════════════

def _call_openai(system_prompt: str, user_prompt: str) -> dict:
    """Make a single OpenAI call. Returns {content, tokens_used, model}."""
    if not OPENAI_API_KEY:
        return {"content": "[SKIPPED — no API key]", "tokens_used": 0, "model": MODEL}

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return {
        "content": response.choices[0].message.content.strip(),
        "tokens_used": response.usage.total_tokens if response.usage else 0,
        "model": MODEL,
    }


# ═══════════════════════════════════════════════════════════════
# PROMPT TEMPLATES
# ═══════════════════════════════════════════════════════════════

PERSONALITY_SYSTEM = """You are a Vedic astrology expert. Generate a 3-paragraph personality profile.
Focus on: core identity, leadership style, and hidden challenges.
Be specific, psychologically realistic, and avoid generic statements.
Write in second person ("you"). 150-250 words."""

CAREER_SYSTEM = """You are a Vedic astrology career strategist. Generate a 3-paragraph career analysis.
Focus on: natural career archetype, wealth generation style, and scaling strategy.
Be specific about the TYPE of career/business that fits. 150-250 words."""

TIMELINE_SYSTEM = """You are a Vedic astrology timing expert. Generate a past-event timeline analysis.
Given the birth data, identify 3-5 likely major life events and their approximate timing.
Focus on: career milestones, relationship events, relocations, and financial shifts.
Be specific about WHEN and WHAT. 150-250 words."""


def build_personality_prompt(subject: dict, symbolic_injection: str = "") -> str:
    """Build personality user prompt."""
    base = f"Name: {subject['name']}\nBirth: {subject['date_of_birth']} {subject['time_of_birth']}\nCity: {subject['city_of_birth']}"
    if symbolic_injection:
        return f"{base}\n\n{symbolic_injection}"
    return base


def build_career_prompt(subject: dict, symbolic_injection: str = "") -> str:
    """Build career user prompt."""
    base = f"Name: {subject['name']}\nBirth: {subject['date_of_birth']} {subject['time_of_birth']}\nCity: {subject['city_of_birth']}"
    if symbolic_injection:
        return f"{base}\n\n{symbolic_injection}"
    return base


def build_timeline_prompt(subject: dict, symbolic_injection: str = "") -> str:
    """Build timeline user prompt."""
    base = f"Name: {subject['name']}\nBirth: {subject['date_of_birth']} {subject['time_of_birth']}\nCity: {subject['city_of_birth']}\nCurrent year: 2025"
    if symbolic_injection:
        return f"{base}\n\n{symbolic_injection}"
    return base


# ═══════════════════════════════════════════════════════════════
# COMPARISON ENGINE
# ═══════════════════════════════════════════════════════════════

def run_comparison(subject: dict, eval_date: datetime = None) -> dict:
    """Run baseline vs enhanced comparison for one subject."""
    if eval_date is None:
        eval_date = datetime(2025, 6, 1)

    birth_data = subject_to_birth_data(subject)
    symbolic = get_symbolic_contexts(birth_data, eval_date)

    results = {"subject": subject["id"], "name": subject["name"], "tracks": {}}

    # Track 1: Personality
    print(f"  [{subject['id']}] Personality baseline...")
    baseline_personality = _call_openai(PERSONALITY_SYSTEM, build_personality_prompt(subject))
    time.sleep(1)
    print(f"  [{subject['id']}] Personality enhanced...")
    enhanced_personality = _call_openai(PERSONALITY_SYSTEM, build_personality_prompt(subject, symbolic["personality_injection"]))
    time.sleep(1)

    results["tracks"]["personality"] = {
        "baseline": baseline_personality,
        "enhanced": enhanced_personality,
        "injection_used": symbolic["personality_injection"],
    }

    # Track 2: Career
    print(f"  [{subject['id']}] Career baseline...")
    baseline_career = _call_openai(CAREER_SYSTEM, build_career_prompt(subject))
    time.sleep(1)
    print(f"  [{subject['id']}] Career enhanced...")
    enhanced_career = _call_openai(CAREER_SYSTEM, build_career_prompt(subject, symbolic["career_injection"]))
    time.sleep(1)

    results["tracks"]["career"] = {
        "baseline": baseline_career,
        "enhanced": enhanced_career,
        "injection_used": symbolic["career_injection"],
    }

    # Track 3: Timeline
    print(f"  [{subject['id']}] Timeline baseline...")
    baseline_timeline = _call_openai(TIMELINE_SYSTEM, build_timeline_prompt(subject))
    time.sleep(1)
    print(f"  [{subject['id']}] Timeline enhanced...")
    enhanced_timeline = _call_openai(TIMELINE_SYSTEM, build_timeline_prompt(subject, symbolic["timing_injection"]))

    results["tracks"]["timeline"] = {
        "baseline": baseline_timeline,
        "enhanced": enhanced_timeline,
        "injection_used": symbolic["timing_injection"],
    }

    return results


# ═══════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_report(all_results: list) -> dict:
    """Generate the comparison report."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "model": MODEL,
        "temperature": TEMPERATURE,
        "subjects": [],
    }

    for result in all_results:
        subject_report = {
            "id": result["subject"],
            "name": result["name"],
            "tracks": {},
        }
        for track_name, track_data in result["tracks"].items():
            baseline_tokens = track_data["baseline"].get("tokens_used", 0)
            enhanced_tokens = track_data["enhanced"].get("tokens_used", 0)
            subject_report["tracks"][track_name] = {
                "baseline_tokens": baseline_tokens,
                "enhanced_tokens": enhanced_tokens,
                "token_delta": enhanced_tokens - baseline_tokens,
                "injection_length": len(track_data["injection_used"]),
                "baseline_output": track_data["baseline"]["content"][:500],
                "enhanced_output": track_data["enhanced"]["content"][:500],
            }
        report["subjects"].append(subject_report)

    return report


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  SHADOW COMPARISON HARNESS")
    print(f"  Model: {MODEL} | Temp: {TEMPERATURE}")
    print("=" * 70)

    subjects = load_subjects()
    all_results = []

    for subject in subjects:
        print(f"\n  Processing: {subject['name']}")
        result = run_comparison(subject)
        all_results.append(result)

    # Save full results
    results_path = ROOT / "reports" / "shadow_compare_results.json"
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Full results saved: {results_path}")

    # Save report
    report = generate_report(all_results)
    report_path = ROOT / "reports" / "shadow_compare_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved: {report_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    for subject_report in report["subjects"]:
        print(f"\n  {subject_report['name']}:")
        for track, data in subject_report["tracks"].items():
            print(f"    {track}: baseline={data['baseline_tokens']}tok, enhanced={data['enhanced_tokens']}tok (+{data['token_delta']})")

    print("\n  Done.")


if __name__ == "__main__":
    main()
