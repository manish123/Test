"""
Phase 1 Production Simulation Tests

Simulates the exact production personality_api behavior AFTER the Phase 1 patch:
1. Engine bridge produces existing output + symbolic_context
2. Prompt injection appends symbolic block
3. Existing payload is unchanged
4. Backward compatibility maintained
5. Non-fatal failure handling works

These tests validate the integration WITHOUT touching production code.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from copy import deepcopy

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ═══════════════════════════════════════════════════════════════
# SIMULATE PRODUCTION ENGINE BRIDGE
# ═══════════════════════════════════════════════════════════════

def _simulate_engine_bridge_output(birth_data_dict: dict) -> dict:
    """
    Simulate what production engine_bridge.get_personality_data() returns
    AFTER the Phase 1 patch is applied.

    This mimics the production flow:
    1. Existing 7 sections (mocked as dicts)
    2. dispositional_profile (mocked)
    3. NEW: symbolic_context from adapter
    """
    # Mock existing production output (7 sections)
    existing_output = {
        "atmakaraka": {"atmakaraka": "Jupiter", "soul_nature": "benefic", "retrograde": False},
        "karakamsha": {"karakamsha_sign": 9, "dharma_axis": ["Jupiter"]},
        "persona_d1_d9": {"hidden_strength": ["Mercury"], "hidden_weakness": [], "public_private_matrix": [{"d1_public": "optimistic"}]},
        "guna_tattva": {"dominant_tattva": "Fire", "dominant_guna": "Sattva"},
        "lajjitaadi": [{"planet": "Mars", "states": ["garvita"]}],
        "ethics_behavior": {"second_house": {"honesty_index": 72}, "professional_behavior": {"ambition_score": 68}},
        "solar_lunar": {"archetype": "solar", "solar_score": 65, "lunar_score": 35},
        "dispositional_profile": {
            "traits": {"risk_taking": 0.6, "resilience": 0.7, "emotional_volatility": 0.4},
            "dominant_orientation": "achievement_oriented",
            "processing_style": "analytical",
        },
    }

    # Phase 1 addition: symbolic_context
    try:
        from orchestration.personality_api_adapter import build_personality_context
        existing_output["symbolic_context"] = build_personality_context(birth_data_dict)
    except Exception:
        existing_output["symbolic_context"] = None

    return existing_output


def _simulate_prompt_injection(engine_output: dict) -> str:
    """
    Simulate what the OpenAI user prompt looks like AFTER Phase 1 patch.
    """
    name = "Test User"
    base_prompt = f"INPUT DATA:\nName: {name}\n\n{json.dumps(engine_output, indent=2, default=str)}"

    # Phase 1 addition: symbolic block
    symbolic = engine_output.get("symbolic_context")
    if symbolic and isinstance(symbolic, dict):
        identity = symbolic.get("identity", {})
        lifecycle = symbolic.get("lifecycle", {})
        symbolic_block = (
            f"\n\nSYMBOLIC CONTEXT (use to color interpretations):\n"
            f"- Primary Archetype: {identity.get('primary_archetype', 'unknown')}\n"
            f"- Life Phase: {lifecycle.get('phase', 'unknown')} ({lifecycle.get('stability', '')})\n"
            f"- Direction: {lifecycle.get('direction', 'unknown')}\n"
        )
    else:
        symbolic_block = ""

    return base_prompt + symbolic_block


# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

BIRTH_DATA = {"date": datetime(1975, 7, 22, 18, 15), "lat": 21.2094, "lon": 81.4285}
EVAL_DATE = datetime(2025, 6, 1)


class TestExistingPayloadUnchanged:
    """All existing 7 sections must remain identical after Phase 1."""

    def test_atmakaraka_present(self):
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        assert "atmakaraka" in result
        assert result["atmakaraka"]["atmakaraka"] == "Jupiter"

    def test_all_seven_sections_present(self):
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        for section in ["atmakaraka", "karakamsha", "persona_d1_d9", "guna_tattva",
                       "lajjitaadi", "ethics_behavior", "solar_lunar"]:
            assert section in result, f"Missing section: {section}"

    def test_dispositional_profile_present(self):
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        assert "dispositional_profile" in result
        assert result["dispositional_profile"]["dominant_orientation"] == "achievement_oriented"

    def test_existing_sections_not_mutated(self):
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        # Verify specific values haven't changed
        assert result["guna_tattva"]["dominant_tattva"] == "Fire"
        assert result["solar_lunar"]["solar_score"] == 65
        assert result["ethics_behavior"]["second_house"]["honesty_index"] == 72


class TestSymbolicContextAdded:
    """symbolic_context must be present and correctly shaped."""

    def test_symbolic_context_present(self):
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        assert "symbolic_context" in result
        assert result["symbolic_context"] is not None

    def test_symbolic_context_has_identity(self):
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        ctx = result["symbolic_context"]
        assert "identity" in ctx
        assert ctx["identity"]["primary_archetype"] != "undetermined"

    def test_symbolic_context_has_lifecycle(self):
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        ctx = result["symbolic_context"]
        assert "lifecycle" in ctx
        assert ctx["lifecycle"]["phase"] != "unknown"

    def test_symbolic_context_has_behavioral_core(self):
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        ctx = result["symbolic_context"]
        assert "behavioral_core" in ctx


class TestPromptInjection:
    """Prompt must include symbolic block when context is present."""

    def test_prompt_contains_symbolic_block(self):
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        prompt = _simulate_prompt_injection(result)
        assert "SYMBOLIC CONTEXT" in prompt
        assert "Primary Archetype:" in prompt
        assert "Life Phase:" in prompt

    def test_prompt_still_contains_original_data(self):
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        prompt = _simulate_prompt_injection(result)
        assert "INPUT DATA:" in prompt
        assert "atmakaraka" in prompt
        assert "Jupiter" in prompt

    def test_prompt_without_symbolic_context(self):
        """If symbolic_context is None, prompt is unchanged."""
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        result["symbolic_context"] = None
        prompt = _simulate_prompt_injection(result)
        assert "SYMBOLIC CONTEXT" not in prompt
        assert "INPUT DATA:" in prompt


class TestNonFatalFailure:
    """Symbolic computation failure must not break the API."""

    def test_invalid_birth_data_returns_none(self):
        """If symbolic layer fails, symbolic_context should be None."""
        bad_data = {"date": "not_a_datetime", "lat": 0, "lon": 0}
        # Simulate the try/except in engine_bridge
        try:
            from orchestration.personality_api_adapter import build_personality_context
            ctx = build_personality_context(bad_data)
        except Exception:
            ctx = None
        assert ctx is None

    def test_none_context_doesnt_break_prompt(self):
        """None symbolic_context produces empty symbolic_block."""
        result = {"symbolic_context": None, "atmakaraka": {"test": True}}
        prompt = _simulate_prompt_injection(result)
        assert "SYMBOLIC CONTEXT" not in prompt
        assert "INPUT DATA:" in prompt


class TestBackwardCompatibility:
    """Response shape must be backward-compatible with existing web/platform."""

    def test_response_is_dict(self):
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        assert isinstance(result, dict)

    def test_no_removed_keys(self):
        """No existing keys should be removed."""
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        required_keys = {"atmakaraka", "karakamsha", "persona_d1_d9", "guna_tattva",
                        "lajjitaadi", "ethics_behavior", "solar_lunar", "dispositional_profile"}
        assert required_keys.issubset(set(result.keys()))

    def test_symbolic_context_is_optional(self):
        """Web/platform should handle missing symbolic_context gracefully."""
        result = _simulate_engine_bridge_output(BIRTH_DATA)
        # Simulate old behavior (no symbolic_context)
        del result["symbolic_context"]
        # Should still be a valid response
        assert "atmakaraka" in result
        assert len(result) >= 7


class TestDeterminism:
    """Same input must produce same symbolic_context."""

    def test_deterministic(self):
        r1 = _simulate_engine_bridge_output(BIRTH_DATA)
        r2 = _simulate_engine_bridge_output(BIRTH_DATA)
        # Compare symbolic_context (excluding _routing which has tokens_used)
        ctx1 = deepcopy(r1["symbolic_context"])
        ctx2 = deepcopy(r2["symbolic_context"])
        if ctx1: ctx1.pop("_routing", None)
        if ctx2: ctx2.pop("_routing", None)
        assert ctx1 == ctx2
