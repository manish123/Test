---
name: event-pack-creation
description: Guidelines for creating and extending astro_engine domain event packs after the shared-pipeline refactor.
---
# Event Pack Creation Skill

## Purpose

This skill documents the complete **5-Layer Vedic Timing Architecture** pattern used by the Astrolyn astro_engine. Any LLM reading this file can create new event packs that follow the exact same structure, schema, and logic flow used across all 8 existing event packs (254+ rules total).

---

## Refactor-Aware Rules

After the shared-pipeline refactor, all new event packs must follow these constraints:

- **Import shared infrastructure from canonical base modules.** Use `rules/evaluator_base.py` for `BaseChartState`, `BaseTransitState`, `IST_OFFSET`, `ist_to_utc`, `get_jd`, `SIGN_NAMES`, `NAKSHATRA_LORDS`, `NATURAL_BENEFICS/MALEFICS`, `BENEFIC/MALEFIC_HOUSES`, `JUPITER/SATURN/MARS_ASPECTS`, tara scoring helpers, and `load_calibration()`.
- **Do not duplicate** `ChartState`, `TransitState`, time helpers, nakshatra lists, aspect constants, or scoring helpers. If you need them, import them.
- **Domain packs must stay domain-specific.** Shared plumbing must stay shared. Domain-specific constants (e.g., `MEDICAL_KARAKAS`, `BUSINESS_HOUSES`) belong in the evaluator file, not in `evaluator_base.py`.
- **Keep the pipeline one-way:** `astronomy → features → rules → decisions`. No backflow.
- **Lower layers are read-only inputs for higher layers.** JSON packs define meaning; Python only orchestrates.
- **Subclass, don't copy.** New evaluator `ChartState` classes must inherit from `BaseChartState` and add only domain-specific house lords and sensitive points in their `__init__`.
- **Use `load_calibration(path, fallback_defaults)`** from `evaluator_base` instead of writing a new `_load_calibration()` function from scratch.

---

## Layer Purity Rule

This is the single most important architectural constraint:

```
astronomy  NEVER imports features
features   NEVER imports rules
rules      NEVER imports decisions
Only orchestration (pipeline/ and main.py) can see everything.
```

Additionally:
- **JSON packs define meaning** (what a rule says, what it detects, what it recommends).
- **Python code orchestrates** (loads JSON, evaluates conditions, computes scores).
- **No layer may mutate upstream state.** A transit evaluator must not modify the natal chart. A scoring function must not alter planet positions.
- **Calibration adjusts weights and thresholds only** — it never rewrites classical rules.

---

## Single-Chart vs Dual-Chart Decision Rule

Before creating a new event pack, decide which chart model applies:

| Model | When to use | Examples |
|-------|-------------|----------|
| **Single-chart** | Event concerns one person's life trajectory | Career, health, property, relocation, fame, financial crisis |
| **Dual-chart** | Event requires comparing two birth charts or validating against a partner | Marriage compatibility, childbirth (mother + child), synastry |

**Default to single-chart.** Only use dual-chart when the domain logic genuinely requires cross-person comparison. Most life events are single-chart.

For dual-chart domains:
- The primary chart is always the querent's natal chart
- The secondary chart (partner, child) is loaded separately
- Cross-chart aspects are computed in the evaluator, not in `BaseChartState`
- The JSON rules still describe conditions in terms of one chart at a time

---

## NotebookLM Extraction Checklist

When extracting rules from classical texts (via NotebookLM, PDF reading, or manual research), capture these fields for each rule:

- [ ] **Source text** — exact quote, work name, chapter/verse/page
- [ ] **Event family** — which life event does this rule predict?
- [ ] **House activations** — which houses (1-12) are involved?
- [ ] **Planets** — which planets are significators or triggers?
- [ ] **Timing windows** — broad (years), medium (months), or exact (days)?
- [ ] **Quality/mode labels** — what kind of event? (e.g., sudden, gradual, stable, volatile)
- [ ] **Recommended actions** — what should the system do when this fires?
- [ ] **Polarity** — supportive, obstructive, or mixed?
- [ ] **Conditions** — what must be true (all_of), what alternatives exist (any_of), what blocks it (none_of)?

Map each extracted rule to exactly one layer:
- If it's about dasha periods → Layer 1
- If it's about Jupiter/Saturn transits → Layer 2
- If it's about Moon/Mars exact timing → Layer 3
- If it's about natal chart structure → Layer 4
- If it's about event classification → Layer 5

---

## Domain Expansion Guidance

When adding new domains to the system:

1. **Start with single-chart life events.** These are simpler, testable with one birth chart, and cover 90% of use cases.
2. **Build cross-person domains only when the logic truly requires it.** Marriage compatibility needs two charts; career promotion does not.
3. **Reuse the existing ontology.** Check `event_ontology.py` (104 events) before inventing new event IDs. Your domain may already have events defined there.
4. **Follow the existing directory convention:** `domains/{category}/{event_name}/`
5. **Register in the domain registry** at `domains/registry.py` so the dispatcher can find your interpreter.
6. **Create a thin evaluator file** at `rules/{domain}_evaluator.py` that:
   - Imports from `evaluator_base` (not from `marriage_evaluator`)
   - Subclasses `BaseChartState` with domain-specific lords
   - Subclasses `BaseTransitState` (usually a pass-through)
   - Implements the 5-layer evaluation functions
   - Loads calibration via `load_calibration()`

**Planned future domains** (from DOMAIN_POLICY.md): entrepreneurship, parenting, leadership, politics, education, creativity, healing/recovery, social influence. All should reuse the same astronomy, symbolic states, and event ontology while applying different optimization goals.

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

### Step 0: Decide Chart Model and Check Ontology

1. **Single-chart or dual-chart?** (See decision rule above)
2. **Check `event_ontology.py`** — does your event already exist in the 104-event V3 model?
3. **Check `event_engine.py` EVENT_MAP** — does it already have a scoring entry for this event?
4. **Choose your domain category** from the existing structure

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

### Step 7: Create the Evaluator File (Post-Refactor Pattern)

Create `astro_engine/rules/{event_name}_evaluator.py` following this pattern:

```python
"""
{Event Name} Rule Evaluator — 5-Layer Sequential Engine
Domain: {Domain Name}
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from features.dasha import get_current_vimshottari, _generate_md_periods, _generate_ad_periods
from features.dignity import SIGN_LORDS, get_sign
from features.nakshatra import get_nakshatra

# ── Shared infrastructure (from evaluator_base) ──────────────
from rules.evaluator_base import (
    IST_OFFSET, ist_to_utc, get_jd,
    SIGN_NAMES, NAKSHATRA_LORDS,
    NATURAL_BENEFICS, NATURAL_MALEFICS, BENEFIC_HOUSES, MALEFIC_HOUSES,
    JUPITER_ASPECTS, SATURN_ASPECTS, MARS_ASPECTS,
    BaseChartState, BaseTransitState,
    load_calibration,
)

# ═══════════════════════════════════════════════════════════════
# DOMAIN-SPECIFIC CONSTANTS (only what's unique to this domain)
# ═══════════════════════════════════════════════════════════════
RULES_DIR = Path(__file__).resolve().parent / "domains" / "{category}" / "{event_name}"

{DOMAIN}_KARAKAS = {"Planet1", "Planet2", ...}
{DOMAIN}_HOUSES = {1, 2, ...}

# ═══════════════════════════════════════════════════════════════
# CALIBRATION
# ═══════════════════════════════════════════════════════════════
CALIBRATION = load_calibration(
    RULES_DIR / "calibration_overlay.json",
    fallback_defaults={...}  # domain-specific defaults
)

# ═══════════════════════════════════════════════════════════════
# CHART STATE (thin subclass — only domain-specific lords)
# ═══════════════════════════════════════════════════════════════
class ChartState(BaseChartState):
    def __init__(self, birth_dt, lat, lon, alt=0):
        super().__init__(birth_dt, lat, lon, alt)
        # Add only domain-specific house lords here
        self.{relevant}_sign = ((self.asc_sign + N - 1) % 12) + 1
        self.{relevant}_lord = SIGN_LORDS[self.{relevant}_sign]

# ═══════════════════════════════════════════════════════════════
# TRANSIT STATE (usually just a pass-through)
# ═══════════════════════════════════════════════════════════════
class TransitState(BaseTransitState):
    pass

# Then implement: evaluate_dasha_layer, evaluate_transit_layer,
# evaluate_fast_trigger_layer, evaluate_classical_layer,
# evaluate_outcome_layer, and the scan_*_windows function.
```

### Step 8: Register in Domain `__init__.py`

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
- [ ] Evaluator file imports from `evaluator_base` (not copy-pasted)
- [ ] `ChartState` subclasses `BaseChartState` (not standalone)
- [ ] `TransitState` subclasses `BaseTransitState`
- [ ] No duplicated constants (IST_OFFSET, SIGN_NAMES, etc.)
- [ ] Single-chart vs dual-chart decision documented
- [ ] Registered in `domains/registry.py`

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
9. **Copy-pasting ChartState** — Always subclass `BaseChartState`, never copy the full class
10. **Redefining shared constants** — Import from `evaluator_base`, never redefine locally
11. **Importing from sibling evaluators** — Import from `evaluator_base`, not from `marriage_evaluator` or other domain evaluators (except for backward-compatible legacy code)
12. **Mutating upstream state** — Transit evaluators must not modify natal chart data
13. **Defaulting to dual-chart** — Use single-chart unless cross-person logic is genuinely required
