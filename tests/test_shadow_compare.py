"""
Tests for the shadow comparison harness.

Validates:
- No mutation of input subject data
- Both paths run successfully (mocked OpenAI)
- Outputs are persisted locally
- Enhanced path includes symbolic context
- Baseline path does not include symbolic context
- Diff report is generated
"""

import json
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "astro_engine"))

from tools.shadow_compare import (
    load_subjects,
    subject_to_birth_data,
    get_symbolic_contexts,
    build_personality_prompt,
    build_career_prompt,
    build_timeline_prompt,
    run_comparison,
    generate_report,
    PERSONALITY_SYSTEM,
    CAREER_SYSTEM,
    TIMELINE_SYSTEM,
)


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def subjects():
    return load_subjects()


@pytest.fixture
def subject_a(subjects):
    return subjects[0]


@pytest.fixture
def subject_b(subjects):
    return subjects[1]


@pytest.fixture
def birth_data_a(subject_a):
    return subject_to_birth_data(subject_a)


@pytest.fixture
def eval_date():
    return datetime(2025, 6, 1)


# ═══════════════════════════════════════════════════════════════
# INPUT IMMUTABILITY TESTS
# ═══════════════════════════════════════════════════════════════

class TestInputImmutability:
    """Verify that no function mutates the input subject data."""

    def test_subject_to_birth_data_no_mutation(self, subject_a):
        original = deepcopy(subject_a)
        subject_to_birth_data(subject_a)
        assert subject_a == original

    def test_get_symbolic_contexts_no_mutation(self, subject_a, eval_date):
        original = deepcopy(subject_a)
        birth_data = subject_to_birth_data(subject_a)
        bd_original = deepcopy(birth_data)
        get_symbolic_contexts(birth_data, eval_date)
        assert subject_a == original
        assert birth_data == bd_original

    def test_build_personality_prompt_no_mutation(self, subject_a):
        original = deepcopy(subject_a)
        build_personality_prompt(subject_a, "some injection")
        assert subject_a == original

    def test_build_career_prompt_no_mutation(self, subject_a):
        original = deepcopy(subject_a)
        build_career_prompt(subject_a, "some injection")
        assert subject_a == original

    def test_build_timeline_prompt_no_mutation(self, subject_a):
        original = deepcopy(subject_a)
        build_timeline_prompt(subject_a, "some injection")
        assert subject_a == original


# ═══════════════════════════════════════════════════════════════
# SYMBOLIC CONTEXT TESTS
# ═══════════════════════════════════════════════════════════════

class TestSymbolicContexts:
    """Verify symbolic context generation works for both subjects."""

    def test_symbolic_contexts_subject_a(self, subject_a, eval_date):
        birth_data = subject_to_birth_data(subject_a)
        ctx = get_symbolic_contexts(birth_data, eval_date)
        assert "personality_context" in ctx
        assert "personality_injection" in ctx
        assert "timing_context" in ctx
        assert "timing_injection" in ctx
        assert "career_context" in ctx
        assert "career_injection" in ctx

    def test_symbolic_contexts_subject_b(self, subject_b, eval_date):
        birth_data = subject_to_birth_data(subject_b)
        ctx = get_symbolic_contexts(birth_data, eval_date)
        assert "personality_context" in ctx
        assert "personality_injection" in ctx

    def test_personality_injection_is_string(self, subject_a, eval_date):
        birth_data = subject_to_birth_data(subject_a)
        ctx = get_symbolic_contexts(birth_data, eval_date)
        assert isinstance(ctx["personality_injection"], str)
        assert len(ctx["personality_injection"]) > 0

    def test_career_injection_is_string(self, subject_a, eval_date):
        birth_data = subject_to_birth_data(subject_a)
        ctx = get_symbolic_contexts(birth_data, eval_date)
        assert isinstance(ctx["career_injection"], str)
        assert len(ctx["career_injection"]) > 0

    def test_timing_injection_is_string(self, subject_a, eval_date):
        birth_data = subject_to_birth_data(subject_a)
        ctx = get_symbolic_contexts(birth_data, eval_date)
        assert isinstance(ctx["timing_injection"], str)
        assert len(ctx["timing_injection"]) > 0

    def test_deterministic_output(self, subject_a, eval_date):
        birth_data = subject_to_birth_data(subject_a)
        ctx1 = get_symbolic_contexts(birth_data, eval_date)
        ctx2 = get_symbolic_contexts(birth_data, eval_date)
        assert ctx1["personality_injection"] == ctx2["personality_injection"]
        assert ctx1["career_injection"] == ctx2["career_injection"]
        assert ctx1["timing_injection"] == ctx2["timing_injection"]


# ═══════════════════════════════════════════════════════════════
# PROMPT CONSTRUCTION TESTS
# ═══════════════════════════════════════════════════════════════

class TestPromptConstruction:
    """Verify baseline vs enhanced prompt differences."""

    def test_baseline_personality_no_symbolic(self, subject_a):
        prompt = build_personality_prompt(subject_a)
        assert "SYMBOLIC" not in prompt
        assert subject_a["name"] in prompt

    def test_enhanced_personality_has_symbolic(self, subject_a):
        prompt = build_personality_prompt(subject_a, "SYMBOLIC CONTEXT:\n- Archetype: Visionary")
        assert "SYMBOLIC CONTEXT" in prompt
        assert "Archetype" in prompt

    def test_baseline_career_no_symbolic(self, subject_a):
        prompt = build_career_prompt(subject_a)
        assert "SYMBOLIC" not in prompt

    def test_enhanced_career_has_symbolic(self, subject_a):
        prompt = build_career_prompt(subject_a, "SYMBOLIC CAREER CONTEXT:\n- Leadership: Bold")
        assert "SYMBOLIC CAREER CONTEXT" in prompt

    def test_baseline_timeline_no_symbolic(self, subject_a):
        prompt = build_timeline_prompt(subject_a)
        assert "SYMBOLIC" not in prompt

    def test_enhanced_timeline_has_symbolic(self, subject_a):
        prompt = build_timeline_prompt(subject_a, "SYMBOLIC TIMING CONTEXT:\n- Phase: Peak")
        assert "SYMBOLIC TIMING CONTEXT" in prompt


# ═══════════════════════════════════════════════════════════════
# COMPARISON ENGINE TESTS (MOCKED OPENAI)
# ═══════════════════════════════════════════════════════════════

def _mock_openai_response(content="Mock response"):
    """Create a mock OpenAI response."""
    return {"content": content, "tokens_used": 100, "model": "gpt-4o-mini"}


class TestComparisonEngine:
    """Test the comparison engine with mocked OpenAI calls."""

    @patch("tools.shadow_compare._call_openai")
    def test_run_comparison_both_paths(self, mock_call, subject_a, eval_date):
        mock_call.return_value = _mock_openai_response("Test output")
        result = run_comparison(subject_a, eval_date)

        assert result["subject"] == "subject_a"
        assert "personality" in result["tracks"]
        assert "career" in result["tracks"]
        assert "timeline" in result["tracks"]

        # Both baseline and enhanced should be called
        assert mock_call.call_count == 6  # 3 tracks × 2 (baseline + enhanced)

    @patch("tools.shadow_compare._call_openai")
    def test_baseline_calls_without_injection(self, mock_call, subject_a, eval_date):
        mock_call.return_value = _mock_openai_response("Baseline")
        run_comparison(subject_a, eval_date)

        # First call for each track is baseline (no symbolic injection in user prompt)
        baseline_calls = [mock_call.call_args_list[i] for i in [0, 2, 4]]
        for call in baseline_calls:
            user_prompt = call[0][1]  # second positional arg
            assert "SYMBOLIC" not in user_prompt

    @patch("tools.shadow_compare._call_openai")
    def test_enhanced_calls_with_injection(self, mock_call, subject_a, eval_date):
        mock_call.return_value = _mock_openai_response("Enhanced")
        run_comparison(subject_a, eval_date)

        # Second call for each track is enhanced (has symbolic injection)
        enhanced_calls = [mock_call.call_args_list[i] for i in [1, 3, 5]]
        for call in enhanced_calls:
            user_prompt = call[0][1]
            assert "SYMBOLIC" in user_prompt or "symbolic" in user_prompt.lower()

    @patch("tools.shadow_compare._call_openai")
    def test_injection_stored_in_results(self, mock_call, subject_a, eval_date):
        mock_call.return_value = _mock_openai_response("Output")
        result = run_comparison(subject_a, eval_date)

        for track_name, track_data in result["tracks"].items():
            assert "injection_used" in track_data
            assert len(track_data["injection_used"]) > 0


# ═══════════════════════════════════════════════════════════════
# REPORT GENERATION TESTS
# ═══════════════════════════════════════════════════════════════

class TestReportGeneration:
    """Test report generation from comparison results."""

    @patch("tools.shadow_compare._call_openai")
    def test_report_structure(self, mock_call, subject_a, eval_date):
        mock_call.return_value = _mock_openai_response("Test output")
        result = run_comparison(subject_a, eval_date)
        report = generate_report([result])

        assert "generated_at" in report
        assert "model" in report
        assert "subjects" in report
        assert len(report["subjects"]) == 1

    @patch("tools.shadow_compare._call_openai")
    def test_report_tracks_present(self, mock_call, subject_a, eval_date):
        mock_call.return_value = _mock_openai_response("Test output")
        result = run_comparison(subject_a, eval_date)
        report = generate_report([result])

        subject_report = report["subjects"][0]
        assert "personality" in subject_report["tracks"]
        assert "career" in subject_report["tracks"]
        assert "timeline" in subject_report["tracks"]

    @patch("tools.shadow_compare._call_openai")
    def test_report_token_tracking(self, mock_call, subject_a, eval_date):
        mock_call.return_value = _mock_openai_response("Test output")
        result = run_comparison(subject_a, eval_date)
        report = generate_report([result])

        for track_data in report["subjects"][0]["tracks"].values():
            assert "baseline_tokens" in track_data
            assert "enhanced_tokens" in track_data
            assert "token_delta" in track_data
            assert "injection_length" in track_data


# ═══════════════════════════════════════════════════════════════
# SUBJECT LOADING TESTS
# ═══════════════════════════════════════════════════════════════

class TestSubjectLoading:
    """Test subject fixture loading."""

    def test_load_two_subjects(self, subjects):
        assert len(subjects) == 2

    def test_subject_a_fields(self, subject_a):
        assert subject_a["id"] == "subject_a"
        assert subject_a["lat"] == 21.2094
        assert subject_a["lon"] == 81.4285

    def test_subject_b_fields(self, subject_b):
        assert subject_b["id"] == "subject_b"
        assert subject_b["lat"] == 23.1186
        assert subject_b["lon"] == 83.1960

    def test_birth_data_conversion(self, subject_a):
        bd = subject_to_birth_data(subject_a)
        assert "date" in bd
        assert "lat" in bd
        assert "lon" in bd
        assert isinstance(bd["date"], datetime)
        assert bd["lat"] == 21.2094
