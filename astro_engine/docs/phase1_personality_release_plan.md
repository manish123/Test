# Phase 1 Release Plan — Personality API Symbolic Integration

## Overview

Add symbolic cognition context to the personality API response and OpenAI prompts.
Two changes, both additive, both reversible by removing the added lines.

---

## Exact Changes (2 files, 6 lines total)

### File 1: `personality_api/engine_bridge.py`

**Location:** After `result["dispositional_profile"] = {...}` block (around line 55-60)

**Add:**
```python
        # V3: Symbolic cognition context (additive — does not alter existing output)
        try:
            from orchestration.personality_api_adapter import build_personality_context
            result["symbolic_context"] = build_personality_context(birth_data_dict)
        except Exception as e:
            logger.warning("Symbolic context computation failed (non-fatal): %s", e)
            result["symbolic_context"] = None
```

**Effect:**
- Adds `symbolic_context` key to the engine output dict
- Contains: `{identity, behavioral_core, lifecycle, psychological_os, _routing}`
- Non-fatal: if symbolic layer fails, field is `None` (existing behavior unchanged)
- All existing 7 sections + dispositional_profile remain identical

---

### File 2: `personality_api/openai_client.py`

**Location:** In `_build_structured_user_prompt()`, append after the engine_output JSON dump

**Add:**
```python
    # V3: Append symbolic context for richer interpretation
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
```

Then change the return to append `symbolic_block`:
```python
    return (
        f"INPUT DATA:\n"
        f"Name: {name}\n"
        f"{lang_instruction}\n"
        f"{json.dumps(engine_output, indent=2, default=str)}"
        f"{symbolic_block}"
    )
```

**Effect:**
- Appends 3-4 lines of symbolic context to the OpenAI user prompt
- Only fires if `symbolic_context` is present and valid
- If absent/None, appends empty string (zero change to existing prompt)
- OpenAI response shape is unchanged (still 7 JSON keys)

---

## Payload Fields Injected

| Field | Type | Content | Token Cost |
|-------|------|---------|------------|
| `symbolic_context.identity.primary_archetype` | str | e.g. "The Network Ecosystem Builder" | ~10 |
| `symbolic_context.identity.secondary_archetype` | str | e.g. "The Crisis Capitalist" | ~10 |
| `symbolic_context.identity.fusion_type` | str | single/complementary_dual/tension_dual | ~3 |
| `symbolic_context.lifecycle.phase` | str | e.g. "Mastery and Authority" | ~5 |
| `symbolic_context.lifecycle.stability` | str | high/medium/low/volatile | ~2 |
| `symbolic_context.lifecycle.direction` | str | expanding/contracting/mixed | ~2 |
| `symbolic_context.behavioral_core` | dict | leadership/risk/economic traits | ~60 |
| `symbolic_context.psychological_os` | dict | primary/shadow/failure_modes | ~40 |
| **Total prompt injection** | | 3-4 lines appended | **~35 tokens** |

---

## What Does NOT Change

- All 7 personality sections (atmakaraka through solar_lunar)
- dispositional_profile structure and values
- OpenAI response format (7 JSON keys)
- Life narrative structure (400-700 words)
- Teaser generation (deterministic, no OpenAI)
- Free tier behavior (sections locked, no narrative)
- API request format (ProfileRequest unchanged)
- API response format (ProfileResponse — symbolic_context is optional dict)
- Auth, rate limiting, geocoding, timezone handling

---

## Rollback Plan

**To roll back:** Delete the added lines in both files. No other changes needed.

1. Remove the `try/except` block in `engine_bridge.py` (5 lines)
2. Remove the `symbolic_block` construction in `openai_client.py` (8 lines)
3. Remove the `{symbolic_block}` from the return f-string (1 word)

**Total rollback:** Remove ~14 lines across 2 files. Zero schema changes needed.

---

## Deployment Order

1. **Deploy astro_engine** with symbolic layer to production server
   - This is the TEST repo code (evaluator_base, symbolic/, orchestration/)
   - Must be importable by personality_api

2. **Deploy personality_api** with the 2 changes
   - engine_bridge.py: adds symbolic_context to output
   - openai_client.py: appends symbolic block to prompt

3. **Verify:**
   - Free tier: response unchanged (symbolic_context present but not rendered)
   - Paid tier: narratives are richer (archetype/lifecycle coloring)
   - No errors in logs (symbolic computation is non-fatal)

4. **Monitor:**
   - Check OpenAI token usage (should increase by ~35 tokens per request)
   - Check response latency (symbolic computation adds ~50-100ms)
   - Check narrative quality (should be more specific, less generic)

---

## Pre-Deployment Checklist

- [ ] TEST repo `orchestration/personality_api_adapter.py` passes all 23 tests
- [ ] TEST repo full suite passes (414+ tests)
- [ ] Production astro_engine updated with symbolic layer
- [ ] `build_personality_context()` works with production birth_data_dict format
- [ ] Symbolic computation is wrapped in try/except (non-fatal)
- [ ] OpenAI prompt injection is conditional (only if symbolic_context exists)
- [ ] Free tier response shape unchanged
- [ ] Paid tier response shape unchanged (symbolic_context is additive)
- [ ] Rollback plan documented and tested
