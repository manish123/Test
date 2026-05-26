# Shadow Comparison Harness

Local-only tool for comparing baseline vs symbolic-enhanced OpenAI outputs.

## Purpose

Runs the same OpenAI prompts with and without symbolic context injection from the astro_engine cognition layer, then compares the results for personality, career, and past-event timeline generation.

## Prerequisites

```bash
# From repo root
.venv/bin/pip install python-dotenv openai
```

Ensure `.env` at repo root contains:
```
OPENAI_API_KEY=sk-...
```

## Usage

```bash
# Run the full comparison (makes 12 OpenAI API calls: 2 subjects × 3 tracks × 2 modes)
.venv/bin/python tools/shadow_compare.py
```

## What It Does

For each of the 2 test subjects (defined in `data/subjects.json`):

1. **Personality track** — baseline vs symbolic-enhanced personality profile
2. **Career track** — baseline vs symbolic-enhanced career analysis
3. **Timeline track** — baseline vs symbolic-enhanced past-event timeline

The only difference between baseline and enhanced is the injection of symbolic context from the astro_engine cognition layer into the user prompt.

## Output

Results are saved to `reports/` (gitignored):
- `reports/shadow_compare_results.json` — full raw results
- `reports/shadow_compare_report.json` — summary with token usage and output previews

## Test Subjects

| ID | Birth | City | Notes |
|----|-------|------|-------|
| subject_a | 22 Jul 1975, 18:15 | Bhilai | Technology professional, foreign settlement |
| subject_b | 30 Nov 1983, 21:20 | Ambikapur | Strong authority trajectory |

## Running Tests

```bash
.venv/bin/pytest tests/test_shadow_compare.py -v
```

Tests use mocked OpenAI calls — no API key needed for testing.

## Rubric Dimensions (for manual evaluation)

- Psychological specificity
- Internal consistency
- Archetype resonance
- Narrative coherence
- Contradiction reduction
- Lifecycle realism
- Strategic usefulness
- Emotional realism
- Memorability
- Genericness reduction

## Safety

- No production systems touched
- No Firestore, Razorpay, or external persistence
- All outputs stay local in `reports/` (gitignored)
- Same model, temperature, max_tokens for both paths
