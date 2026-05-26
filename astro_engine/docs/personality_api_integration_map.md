# Personality API Integration Map

## Executive Summary

The production `personality_api` currently consumes a 7-section engine output from
`personality/personality_engine.py` (atmakaraka, karakamsha, persona_d1_d9, guna_tattva,
lajjitaadi, ethics_behavior, solar_lunar) plus a V2 `dispositional_profile`.

The TEST repo's symbolic cognition layer produces a richer, more structured output
(archetypes, behavioral profiles, lifecycle state, arbitration, narratives) that can
**augment** the existing personality API without replacing it.

The integration is **additive** — the existing 7-section engine output continues to work.
The symbolic layer provides additional context for OpenAI prompt enrichment.

---

## 1. Production personality_api Architecture

```
POST /profile
    → auth (API key → tier: free/paid)
    → rate_limiter
    → geocode (city → lat/lon)
    → timezone_utils (local time → IST datetime)
    → engine_bridge.get_personality_data(birth_data_dict)
        → personality/personality_engine.build_personality_profile()
        → personality/dispositional_traits.compute_dispositional_traits()
    → teasers.build_teaser() (deterministic, per section)
    → openai_client.get_narratives() (Call 1: structured JSON, 7 sections)
    → openai_client.get_life_narrative() (Call 2: 400-700 word prose)
    → ProfileResponse
```

### What engine_bridge currently expects:

**Input:** `{"date": datetime_IST, "lat": float, "lon": float}`

**Output:** dict with 7 section keys + optional `dispositional_profile`:
```python
{
    "atmakaraka": {...},      # soul significator data
    "karakamsha": {...},      # life purpose axes
    "persona_d1_d9": {...},   # public vs private self
    "guna_tattva": {...},     # elemental nature
    "lajjitaadi": [...],      # psychological complexes (list)
    "ethics_behavior": {...}, # ethics & ambition
    "solar_lunar": {...},     # solar-lunar archetype
    "dispositional_profile": {  # V2 addition
        "traits": {trait_name: float_0_to_1},
        "dominant_orientation": str,
        "processing_style": str,
        "event_alignment": {event: {alignment, color}},
    }
}
```

### What openai_client currently expects as prompt context:

**Call 1 (Structured):** Full engine_output dict (all 7 sections + dispositional_profile)
- Injected as JSON into user prompt
- System prompt instructs GPT to produce 7 narrative strings

**Call 2 (Life Narrative):** The 7 narrative strings from Call 1 + dispositional_profile
- System prompt instructs GPT to write 400-700 word prose
- Dispositional traits (HIGH/LOW) are highlighted for specificity

### What the endpoint currently returns:

```json
{
    "name": "...",
    "birth_data": {"date", "time", "city", "lat", "lon"},
    "tier": "free|paid",
    "sections": [{"id", "title", "teaser", "locked", "data?", "narrative?"}],
    "structured_profile": {"section_id": "narrative_string", "dispositional_profile": {...}},
    "life_narrative": "400-700 word prose",
    "ai_narrative_available": bool
}
```

---

## 2. TEST Repo Symbolic Output (what we now produce)

From `symbolic/coherent_state_builder.build_coherent_state()`:

```python
{
    "core_identity": {"primary", "secondary", "fusion_type", "stability"},
    "dominant_archetypes": [{"id", "name", "match_score", "source_confidence", "composite_score"}],
    "suppressed_archetypes": [...],
    "behavioral_core": {"leadership": [...], "risk": [...], "economic": [...]},
    "primary_lifecycle_state": {"current_state", "age_years", "probable_next_states", "expansion_indicators"},
    "primary_conflicts": [{"type", "dominant", "subordinate", "resolution"}],
    "resolved_manifestation_path": {...},
    "top_causal_narratives": [{"narrative_id", "core_cause", "relevance", "rank_score"}],
    "semantic_coherence_score": float,
    "prompt_ready_context": {compact payload for LLM injection},
}
```

From `orchestration/payload_builder.build_payload(state, "personality_context")`:

```python
{
    "identity": {"primary_archetype", "secondary_archetype", "fusion_type", "stability"},
    "behavioral_core": {"leadership": [2 traits], "risk": [2 traits], "economic": [2 traits]},
    "lifecycle": {"phase", "stability", "direction"},
    "primary_conflicts": [{"type", "resolution"}],
    "top_narratives": [{"cause", "relevance"}],
    "coherence": {"score", "fragmentation"},
}
```

---

## 3. Gap Analysis

| Current Production Input | TEST Repo Equivalent | Gap |
|--------------------------|---------------------|-----|
| `atmakaraka` section | Not directly produced | **Gap**: symbolic layer doesn't replicate personality_engine sections |
| `karakamsha` section | Not directly produced | **Gap**: same |
| `persona_d1_d9` section | Not directly produced | **Gap**: same |
| `guna_tattva` section | Not directly produced | **Gap**: same |
| `lajjitaadi` section | Not directly produced | **Gap**: same |
| `ethics_behavior` section | Not directly produced | **Gap**: same |
| `solar_lunar` section | Partially: `behavioral_profile.dominant_planets` | Partial overlap |
| `dispositional_profile.traits` | `behavioral_core` (different schema) | **Reshape needed** |
| `dispositional_profile.dominant_orientation` | `core_identity.primary` | Direct map |
| `dispositional_profile.processing_style` | `lifecycle.stability` | Approximate |
| — (not in production) | `core_identity` | **New field** |
| — (not in production) | `dominant_archetypes` | **New field** |
| — (not in production) | `lifecycle_state` | **New field** |
| — (not in production) | `primary_conflicts` | **New field** |
| — (not in production) | `causal_narratives` | **New field** |
| — (not in production) | `prompt_ready_context` | **New field** |

### Key Insight:

The TEST repo symbolic layer does NOT replace the existing 7-section personality engine.
It **augments** it by providing:
1. Archetype context (who they ARE symbolically)
2. Behavioral operating system (how they FUNCTION)
3. Lifecycle phase (where they ARE in life)
4. Conflict resolution (what's SUPPRESSED vs AMPLIFIED)
5. Causal narratives (WHY things manifest the way they do)

The integration path is to **inject the symbolic context into the OpenAI prompts**
alongside the existing engine output, making the AI narratives richer and more specific.

---

## 4. Mapping Table: Old Input → New Symbolic Payload

| Production Field | Symbolic Payload Field | Mapping Type |
|-----------------|----------------------|--------------|
| `engine_output` (7 sections) | Unchanged — keep as-is | Pass-through |
| `dispositional_profile.dominant_orientation` | `core_identity.primary` | Direct |
| `dispositional_profile.traits.risk_taking` | `behavioral_core.risk[0]` | Reshape |
| `dispositional_profile.traits.resilience` | Inferred from `lifecycle.stability` | Approximate |
| — | `prompt_ready_context` (full payload) | **NEW: inject into system prompt** |
| — | `core_identity.primary_archetype` | **NEW: add to narrative prompt** |
| — | `lifecycle.phase` | **NEW: add to narrative prompt** |
| — | `primary_conflicts[0].resolution` | **NEW: add to narrative prompt** |

---

## 5. Recommended Integration Sequence

### Phase 1: Personality Context Only (lowest risk)

1. In TEST repo, create `personality_api_adapter.py` that:
   - Takes `birth_data_dict` (same as engine_bridge expects)
   - Calls `BaseChartState(birth_dt, lat, lon)`
   - Calls `build_coherent_state(chart, eval_date)`
   - Returns `prompt_ready_context` shaped for personality_context contract
2. In production (FUTURE): add one line to `engine_bridge.py`:
   ```python
   result["symbolic_context"] = get_symbolic_context(birth_data_dict)
   ```
3. In production (FUTURE): append symbolic context to OpenAI user prompt

### Phase 2: Timeline/Past Events (after Phase 1 validated)

1. Use `multi_evaluator_runner.scan_timeline()` to produce 10-year event timeline
2. Shape as `timing_context` contract payload
3. Inject into timing_api prompts

### Phase 3: Weekly Predictions (after Phase 2 validated)

1. Use `prediction_context` contract (250 tokens)
2. Inject lifecycle + narratives + conflicts into weekly prediction prompts

---

## 6. Files That Must Remain Untouched in Production (for now)

| File | Reason |
|------|--------|
| `personality_api/main.py` | App entry point — no changes needed |
| `personality_api/models.py` | Request/response schemas — extend later, don't modify |
| `personality_api/auth.py` | Authentication — unrelated |
| `personality_api/rate_limiter.py` | Rate limiting — unrelated |
| `personality_api/geocoder.py` | Geocoding — unrelated |
| `personality_api/timezone_utils.py` | Timezone — unrelated |
| `personality_api/teasers.py` | Deterministic teasers — keep as-is |
| `personality_api/routers/health.py` | Health check — unrelated |
| `personality_api/openai_client.py` | Modify LAST (prompt injection point) |
| `personality_api/engine_bridge.py` | Modify SECOND (add symbolic context call) |
| `personality_api/routers/profile.py` | Modify THIRD (pass symbolic to response) |

---

## 7. Next Implementation Step (TEST repo only)

Create `astro_engine/orchestration/personality_api_adapter.py` that:

1. Accepts the same `birth_data_dict` format as production engine_bridge
2. Builds `BaseChartState` from it
3. Runs `build_coherent_state()`
4. Returns the `personality_context` contract payload (≤600 tokens)
5. Includes a `build_prompt_injection()` method that formats the symbolic context
   as a string block suitable for appending to the OpenAI system/user prompt

This adapter is the **single integration point** — production only needs to call
one function to get the symbolic enrichment.
