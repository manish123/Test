# Event Pack Creation Skill

## Purpose

This skill documents the complete **5-Layer Vedic Timing Architecture** pattern used by the Astrolyn astro_engine. Any LLM reading this file can create new event packs that follow the exact same structure, schema, and logic flow used across all 8 existing event packs (254+ rules total).

---

## Architecture Overview

Every event pack in `astro_engine/rules/domains/` follows a **5-layer sequential narrowing** architecture. Each layer answers a fundamentally different semantic question:

| Layer | File | Question | Timing Precision |
|-------|------|----------|-----------------|
| 1. Dasha | `dasha_rules.json` | **Is this event possible now?** | Broad (years) |
| 2. Transit | `transit_rules.json` | **Is the activation window open?** | Medium (months) |
| 3. Fast Trigger | `fast_trigger_rules.json` | **What is the exact timing?** | Exact (days/weeks) |
| 4. Classical Pattern | `classical_patterns.json` | **Does the birth chart confirm it?** | None (structural) |
| 5. Outcome/Quality | `outcome_quality.json` | **What kind of event?** | None (qualitative) |

### Sequential Narrowing Logic

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: DASHA (Gate)                                      │
│  If NO dasha rule fires → STOP. Event not possible now.     │
│  If YES → opens BROAD WINDOW (1-3 years)                    │
└────────────────────────┬────────────────────────────────────┘
                         │ window open
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: TRANSIT (Activation)                              │
│  Slow planets (Jupiter/Saturn) activate the window.         │
│  If YES → narrows to MEDIUM WINDOW (1-6 months)             │
└────────────────────────┬────────────────────────────────────┘
                         │ window narrowed
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: FAST TRIGGER (Pinpoint)                           │
│  Fast planets (Moon/Mars) + Nakshatra pinpoint exact day.   │
│  If YES → narrows to EXACT WINDOW (days to weeks)           │
└────────────────────────┬────────────────────────────────────┘
                         │ timing pinpointed
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: CLASSICAL PATTERN (Structural Modifier)           │
│  Natal promise — MODIFIES confidence, never creates windows │
└────────────────────────┬────────────────────────────────────┘
                         │ confidence adjusted
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 5: OUTCOME/QUALITY (Classification)                  │
│  Classifies the event type/mode/quality. Never affects      │
│  timing — only describes WHAT KIND of event occurs.         │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure (Required for Each Event Pack)

```
astro_engine/rules/domains/{category}/{event_name}/
├── __init__.py                   # Python module with lazy-load accessors
├── ARCHITECTURE.md               # 5-layer design document (this pattern)
├── {event_name}_rule.schema.json # JSON Schema validation
├── dasha_rules.json              # Layer 1: Planetary period gates
├── transit_rules.json            # Layer 2: Slow planet activation
├── fast_trigger_rules.json       # Layer 3: Fast planet exact timing
├── classical_patterns.json       # Layer 4: Structural birth chart patterns
├── outcome_quality.json          # Layer 5: Event classification
├── calibration_schema.json       # Schema for calibration overlay
└── calibration_overlay.json      # Empirical tuning (Layer 3 calibration)
```

---

## Existing Event Packs (8 Total)

| Domain | Pack | Path | Rules |
|--------|------|------|-------|
| relationship | Marriage | `domains/relationship/marriage/` | 31 |
| family | Childbirth | `domains/family/childbirth/` | 31 |
| career | Career/Profession | `domains/career/career_profession/` | 29 |
| business | Business Launch | `domains/business/business_launch/` | 43 |
| medical | Surgery & Medical | `domains/medical/surgery_and_medical_events/` | 31 |
| relocation | Foreign Settlement | `domains/relocation/foreign_settlement/` | 25 |
| status | Fame & Recognition | `domains/status/fame_and_public_recognition/` | 31 |
| finance | Property & Inheritance | `domains/finance/ancestral_property_and_inheritance/` | 33 |

---

## Rule Schema (Universal for All Packs)

Every rule in every JSON file follows this exact schema:

```json
{
  "rule_id": "string — unique, e.g. bphs_dasha_7th_lord_marriage",
  "name": "string — human-readable rule name",
  "description": "string — what this rule detects",
  "source_text": {
    "work_name": "string — classical text name (BPHS, Phaladeepika, etc.)",
    "chapter": "string|null",
    "verse": "string|null",
    "page": "string|null",
    "quote": "string|null — verbatim from source",
    "translation": "string|null — English translation if needed"
  },
  "domain": "string — e.g. relationship, career, medical, finance",
  "event_family": "string — e.g. marriage, surgery, business_launch",
  "event_subtype": ["array of strings — e.g. stable, delayed, sudden"],
  "rule_type": "string — one of: dasha, transit, fast_trigger, classical_pattern, outcome_quality",
  "status": "string — one of: active, experimental, calibration, deprecated",
  "priority": "integer 1-100 — higher = more authoritative",
  "polarity": "string — supportive, obstructive, or modifying",
  "timing_band": "string — broad, medium, exact, structural, qualitative",
  "conditions": {
    "all_of": ["array — ALL must be true"],
    "any_of": ["array — at least ONE must be true"],
    "none_of": ["array — NONE must be true (blockers)"]
  },
  "signals": {
    "dasha": ["array of dasha identifiers"],
    "transit": ["array of transit conditions"],
    "houses": ["array of house numbers as strings"],
    "planets": ["array of planet names"],
    "nakshatra": ["array of nakshatra references"],
    "d9": ["array of D9/Navamsa conditions"],
    "sensitive_points": ["array of sensitive point formulas"]
  },
  "interpretation": {
    "meaning": "string — what firing this rule means",
    "mode": "string — e.g. love, arranged, sudden, gradual",
    "quality": "string — supportive, obstructive, mixed",
    "confidence": "float 0.0-1.0 — source-level confidence"
  },
  "window": {
    "broad_window_days": "integer — dasha window size",
    "exact_window_days": "integer — transit/trigger precision",
    "confidence_decay_days": "integer — how fast confidence fades"
  },
  "weights": {
    "dasha_weight": "float 0.0-1.0",
    "transit_weight": "float 0.0-1.0",
    "fast_trigger_weight": "float 0.0-1.0",
    "classical_weight": "float 0.0-1.0"
  },
  "outputs": {
    "symbolic_label": "string — machine-readable output label",
    "likelihood_band": "string — high, medium, low",
    "timing_band": "string — broad, medium, exact",
    "recommended_action": "string — what to do next in the pipeline"
  },
  "metadata": {
    "notes": "string — implementation notes"
  }
}
```

---

## Key Design Principles

### 1. Sequential Narrowing (NOT Parallel Scoring)
- Layer 1 MUST fire before Layer 2 is evaluated
- Layer 3 only matters if Layer 2 has already narrowed
- This prevents false positives from isolated triggers

### 2. Separation of Timing vs. Quality
- Layers 1-3: **WHEN** will the event occur?
- Layer 4: **Structural confirmation** (does natal chart support it?)
- Layer 5: **WHAT KIND** of event?
- Never mix timing and classification

### 3. Provenance Tracking
Every rule carries `source_text` with classical text attribution:
- `work_name`: BPHS, Phaladeepika, Jataka Parijata, Nirayana System, etc.
- `chapter`, `verse`, `page`: Exact location in source
- `quote`: Verbatim text from classical work
- Enables: audit, calibration, scholarly validation

### 4. Domain Isolation (C1/C2 Architecture)
- Rules in domains are **domain-specific policies** (C2 layer)
- They consume **domain-neutral symbolic state** from `rules/symbolic/` (C1 layer)
- Domains NEVER modify symbolic state — they are read-only consumers
- Event packs NEVER leak rules into other domains

### 5. Calibration-Ready Design
- Each rule has `status`: active / experimental / calibration / deprecated
- Each rule has `interpretation.confidence`: source-level confidence (0.0-1.0)
- `calibration_overlay.json` adjusts weights WITHOUT touching classical rules
- Independent feedback datasets per domain

---

## How to Create a New Event Pack

### Step 1: Identify the Domain and Event Family

Choose from existing domains or create a new one:
- `career`, `relationship`, `health`, `spirituality`, `general_life`, `trading`
- `business`, `medical`, `relocation`, `status`, `finance`, `family`

Pick an event family from `event_ontology.py` (104 events defined) or create a new one.

### Step 2: Create the Directory

```
astro_engine/rules/domains/{domain}/{event_family_name}/
```

### Step 3: Create `__init__.py`

```python
"""
{Event Name} Event Pack — 5-Layer Semantic Architecture

File layout:
  rules/domains/{domain}/{event_name}/
    ARCHITECTURE.md               — 5-layer design document
    {event}_rule.schema.json      — Validation schema
    dasha_rules.json              — Layer 1: Planetary period gates
    transit_rules.json            — Layer 2: Slow planet activation
    fast_trigger_rules.json       — Layer 3: Fast planet exact timing
    classical_patterns.json       — Layer 4: Structural birth chart patterns
    outcome_quality.json          — Layer 5: Event classification
    calibration_schema.json       — Schema for calibration overlay
    calibration_overlay.json      — Empirical tuning

Logic flow:
  Dasha rule fires -> broad window opens
  Transit rule fires -> window becomes active/narrow
  Fast trigger fires -> exact timing narrowed to TARGET_DAY
  Classical pattern -> modifies confidence (natal promise)
  Outcome/quality -> classifies event type/mode/quality
  Decision layer -> outputs BROAD_WINDOW / NARROW_WINDOW / TARGET_DAY
"""

import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_json(filename):
    """Load a JSON rule file from this directory."""
    filepath = os.path.join(_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_dasha_rules():
    """Layer 1: Broad timing — Mahadasha/Antardasha gates."""
    return _load_json("dasha_rules.json")


def get_transit_rules():
    """Layer 2: Medium timing — Jupiter/Saturn transit activation."""
    return _load_json("transit_rules.json")


def get_fast_trigger_rules():
    """Layer 3: Exact timing — Moon/Mars Nakshatra pinpointing."""
    return _load_json("fast_trigger_rules.json")


def get_classical_patterns():
    """Layer 4: Structural — Natal promise patterns."""
    return _load_json("classical_patterns.json")


def get_outcome_quality():
    """Layer 5: Classification — Event type/mode/quality."""
    return _load_json("outcome_quality.json")


def get_calibration_overlay():
    """Empirical calibration overlay for weight/threshold adjustments."""
    return _load_json("calibration_overlay.json")


def get_all_rules():
    """Load all 5 layers concatenated into a single list."""
    return (
        get_dasha_rules()
        + get_transit_rules()
        + get_fast_trigger_rules()
        + get_classical_patterns()
        + get_outcome_quality()
    )


__all__ = [
    "get_dasha_rules",
    "get_transit_rules",
    "get_fast_trigger_rules",
    "get_classical_patterns",
    "get_outcome_quality",
    "get_calibration_overlay",
    "get_all_rules",
]
```

### Step 4: Create Layer JSON Files

Each JSON file is an array of rule objects following the schema above.

**Layer 1 — `dasha_rules.json`** (typically 5-10 rules):
- Focus on which Mahadasha/Antardasha periods activate this event
- `rule_type`: "dasha"
- `timing_band`: "broad"
- `weights.dasha_weight`: 0.9-1.0 (dominant)

**Layer 2 — `transit_rules.json`** (typically 5-8 rules):
- Focus on slow planet (Jupiter, Saturn) transits that narrow the window
- Double transit theory is key here
- `rule_type`: "transit"
- `timing_band`: "medium"
- `weights.transit_weight`: 0.8-0.95 (dominant)

**Layer 3 — `fast_trigger_rules.json`** (typically 5-8 rules):
- Focus on fast planet (Moon, Mars) + Nakshatra exact timing
- Mitra Tara, Sanghatika, Navamsa count techniques
- `rule_type`: "fast_trigger"
- `timing_band`: "exact"
- `weights.fast_trigger_weight`: 0.85-0.95 (dominant)

**Layer 4 — `classical_patterns.json`** (typically 6-12 rules):
- Focus on natal chart structural patterns (yogas, house lords, etc.)
- These MODIFY confidence, never create timing windows
- `rule_type`: "classical_pattern"
- `timing_band`: "structural"
- `weights.classical_weight`: 0.7-0.9 (dominant)

**Layer 5 — `outcome_quality.json`** (typically 6-10 rules):
- Focus on classifying event quality/mode/type
- These CLASSIFY only, never affect timing
- `rule_type`: "outcome_quality"
- `timing_band`: "qualitative"
- All weights typically 0.0 except specialized

### Step 5: Create ARCHITECTURE.md

Follow the pattern from any existing event pack's ARCHITECTURE.md (e.g., `business_launch/ARCHITECTURE.md`). Document:
- Why this architecture for this domain
- Domain-specific semantic layers
- Key planets, houses, and transits for each layer
- Rule counts table
- Evaluation flow pseudocode

### Step 6: Create Schema and Calibration Files

**`{event}_rule.schema.json`**: Copy from existing pack, update:
- `$id` URL
- `title`
- `domain` enum value
- Domain-specific enum values

**`calibration_schema.json`**: Standard calibration overlay schema.

**`calibration_overlay.json`**: Start with empty adjustments:
```json
{
  "version": "1.0.0",
  "domain": "{domain}",
  "event_family": "{event_family}",
  "adjustments": [],
  "notes": "Initial calibration overlay — no empirical adjustments yet."
}
```

### Step 7: Register in Domain `__init__.py`

Update `astro_engine/rules/domains/{domain}/__init__.py` to export the new pack.

---

## Evaluation Engine Integration

The event engine at `astro_engine/rules/event_engine.py` processes rules using this flow:

```python
def evaluate_event_timing(chart_state, transit_state, dasha_state):
    """5-pass sequential evaluation. Each layer gates the next."""

    # Pass 1: Dasha gate
    dasha_results = evaluate_rules(dasha_rules, dasha_state)
    if not any_fired(dasha_results):
        return EventResult(status="NOT_NOW", confidence=0)

    # Pass 2: Transit activation (only if dasha opened)
    transit_results = evaluate_rules(transit_rules, transit_state)
    window_active = any_fired(transit_results)

    # Pass 3: Fast trigger (only if transit narrowed)
    if window_active:
        trigger_results = evaluate_rules(fast_trigger_rules, transit_state)
        exact_timing = any_fired(trigger_results)
    else:
        exact_timing = False

    # Pass 4: Classical pattern (structural modifier — always evaluated)
    pattern_results = evaluate_rules(classical_patterns, chart_state)
    structural_confidence = aggregate_confidence(pattern_results)

    # Pass 5: Outcome classification (independent — always evaluated)
    quality_results = evaluate_rules(outcome_quality, chart_state)
    event_type = classify_outcome(quality_results)

    # Compose final result
    return EventResult(
        status=determine_status(dasha_results, transit_results, trigger_results),
        timing_band=determine_band(window_active, exact_timing),
        confidence=compute_confidence(dasha_results, transit_results,
                                      trigger_results, structural_confidence),
        event_type=event_type,
        fired_rules=collect_fired_rules(all_results),
    )
```

---

## Event Ontology Reference

The system defines 104 events across 6 categories in `event_ontology.py`:
- A. Career & Enterprise (24 events)
- B. Relationships & Family (16 events)
- C. Health & Wellbeing (16 events)
- D. Spiritual & Learning (15 events)
- E. Life Shifts & Assets (21 events)
- F. Trading & Market Operations (12 events)

Available domains: `trading`, `career`, `relationship`, `health`, `spirituality`, `general_life`, `business`, `medical`, `relocation`, `status`, `finance`, `family`

---

## Classical Sources Used

Rules derive from these Vedic astrology texts (provenance tracked per-rule):
- **BPHS** (Brihat Parashara Hora Shastra) — foundational timing rules
- **Phaladeepika** — transit and yoga interpretations
- **Jataka Parijata** — event timing and classification
- **Nirayana System** — structural patterns and yogas
- **Transit texts** — Jupiter/Saturn activation windows
- **SBC (Sarvatobhadra Chakra)** — Nakshatra-based fast triggers
- **JYOTHISHI** — modern compilation of classical timing rules

---

## Checklist for New Event Pack

- [ ] Directory created at `domains/{category}/{event_name}/`
- [ ] `__init__.py` with lazy-load accessors
- [ ] `ARCHITECTURE.md` documenting 5-layer design
- [ ] `{event}_rule.schema.json` with validation schema
- [ ] `dasha_rules.json` — 5-10 rules, Layer 1
- [ ] `transit_rules.json` — 5-8 rules, Layer 2
- [ ] `fast_trigger_rules.json` — 5-8 rules, Layer 3
- [ ] `classical_patterns.json` — 6-12 rules, Layer 4
- [ ] `outcome_quality.json` — 6-10 rules, Layer 5
- [ ] `calibration_schema.json` — calibration overlay schema
- [ ] `calibration_overlay.json` — empty initial calibration
- [ ] Domain `__init__.py` updated to export new pack
- [ ] All rules have valid `source_text` provenance
- [ ] All rules have correct `rule_type` matching their layer
- [ ] All rules follow the universal schema exactly
- [ ] Total rules per pack: 25-45 (typical range)

---

## Common Mistakes to Avoid

1. **Mixing timing layers** — Never put transit logic in dasha rules
2. **Skipping provenance** — Every rule MUST cite a classical source
3. **Parallel scoring** — The 5 layers are SEQUENTIAL, not parallel
4. **Quality affecting timing** — Layer 5 never changes when, only what kind
5. **Cross-domain leakage** — Each pack is isolated to its own domain
6. **Missing structural rules** — Layer 4 must exist even if fewer rules
7. **Ignoring calibration** — Always include empty calibration_overlay.json
8. **Wrong rule_type field** — Must match the layer the rule belongs to
