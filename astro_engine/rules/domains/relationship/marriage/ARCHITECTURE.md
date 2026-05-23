# Marriage Rules — 5-Layer Semantic Architecture

## Why This Architecture?

Marriage prediction (and all life-event prediction) is NOT a single question.
It is **5 fundamentally different semantic questions** asked in sequence:

| Layer | File | Question | Timing Precision |
|-------|------|----------|-----------------|
| 1. Dasha | `dasha_rules.json` | **Is marriage possible now?** | Broad (years) |
| 2. Transit | `transit_rules.json` | **Is the window active?** | Medium (months) |
| 3. Fast Trigger | `fast_trigger_rules.json` | **Is this the exact timing?** | Exact (days/weeks) |
| 4. Classical Pattern | `classical_patterns.json` | **Is there a structural timing signature?** | None (structural) |
| 5. Outcome/Quality | `outcome_quality.json` | **What kind of marriage will it be?** | None (qualitative) |

These are **fundamentally different semantic layers**. Mixing them into a single scoring function
loses the sequential narrowing logic that makes Vedic timing work.

---

## The 5-Pass Evaluation Flow

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: DASHA (Gate)                                  │
│  Question: "Is this planetary period marriage-capable?"  │
│  If NO dasha rule fires → STOP. Marriage not now.       │
│  If YES → opens BROAD WINDOW (1-3 years)                │
└────────────────────────┬────────────────────────────────┘
                         │ window open
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: TRANSIT (Activation)                          │
│  Question: "Are slow planets activating the axis?"      │
│  Double transit, Jupiter trine, sensitive points...     │
│  If YES → narrows to MEDIUM WINDOW (1-6 months)         │
└────────────────────────┬────────────────────────────────┘
                         │ window narrowed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: FAST TRIGGER (Pinpoint)                       │
│  Question: "What is the exact timing?"                  │
│  Moon 72-day, Mars 2-month, Jupiter degree hits...      │
│  If YES → narrows to EXACT WINDOW (days to weeks)       │
└────────────────────────┬────────────────────────────────┘
                         │ timing pinpointed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: CLASSICAL PATTERN (Structural Modifier)       │
│  Question: "Does the birth chart confirm timing?"       │
│  Early/normal/delayed indicators, age-based rules...    │
│  MODIFIES confidence, does not create windows           │
└────────────────────────┬────────────────────────────────┘
                         │ confidence adjusted
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: OUTCOME/QUALITY (Classification)              │
│  Question: "What kind of marriage?"                     │
│  Love/arranged, stable/volatile, first/second...        │
│  CLASSIFIES the event, never affects timing             │
└─────────────────────────────────────────────────────────┘
```

---

## Key Design Principles

### 1. Sequential Narrowing (Not Parallel Scoring)
- Layer 1 must fire BEFORE Layer 2 is even evaluated
- Layer 3 only matters if Layer 2 has already narrowed
- This prevents false positives from isolated triggers

### 2. Separation of Timing vs. Quality
- Layers 1-3: **WHEN** will it happen?
- Layer 4: **Structural confirmation** (does chart agree?)
- Layer 5: **WHAT KIND** will it be?
- Never mix these — a painful marriage still happens on time

### 3. Provenance Tracking
Every rule carries `source_text` with:
- `work_name`: Classical text (BPHS, Phaladeepika, Jataka Parijata, etc.)
- `chapter`, `verse`, `page`: Exact location
- `quote`: Verbatim text
- This enables: audit, calibration, scholarly validation

### 4. Domain Isolation (C1/C2 Split)
- Rules in this directory are **domain-specific policies** (C2 layer)
- They consume **domain-neutral symbolic state** from `rules/symbolic/` (C1 layer)
- Domains NEVER modify symbolic state — read-only consumers
- This prevents cross-domain semantic corruption

### 5. Calibration-Ready
- Each rule has `status`: active / experimental / calibration / deprecated
- Each rule has `interpretation.confidence`: source-level confidence (0-1)
- Future ML calibration operates per-rule, per-domain
- Independent feedback datasets per domain

---

## Universal Extraction Framework

The same 5-layer architecture applies to ALL life events:

### Marriage (this implementation)
| Layer | Question |
|-------|----------|
| Dasha | Is marriage possible now? |
| Transit | Is the window active? |
| Fast Trigger | Is this the exact timing? |
| Classical Pattern | Is there a legacy timing signature? |
| Outcome/Quality | What kind of marriage will it be? |

### Career Change
| Layer | Question |
|-------|----------|
| Dasha | Is career change possible now? (10th lord, Sun, Saturn periods) |
| Transit | Is the window active? (Jupiter/Saturn on 10th, 6th, 11th) |
| Fast Trigger | Is this the exact timing? (Mars over 10th, Sun over 10th lord) |
| Classical Pattern | Is there a structural signature? (Rajayoga activation, etc.) |
| Outcome/Quality | What kind? (Promotion vs stress vs authority vs entrepreneurship) |

### Childbirth
| Layer | Question |
|-------|----------|
| Dasha | Is childbirth possible now? (5th lord, Jupiter, putrakaraka periods) |
| Transit | Is the window active? (Jupiter/Saturn on 5th, 9th) |
| Fast Trigger | Is this the exact timing? (Moon over 5th, Mars activation) |
| Classical Pattern | Is there a structural signature? (Saptamsa activation, etc.) |
| Outcome/Quality | What kind? (Easy/complicated, gender indications, multiple births) |

### Surgery / Health Crisis
| Layer | Question |
|-------|----------|
| Dasha | Is health event possible now? (6th/8th lord, Mars, maraka periods) |
| Transit | Is the window active? (Saturn on 6th/8th, Mars on 8th) |
| Fast Trigger | Is this the exact timing? (Moon over 8th, Mars exact degree hit) |
| Classical Pattern | Is there a structural signature? (Maraka activation, longevity) |
| Outcome/Quality | What kind? (Elective vs emergency, recovery speed, chronic vs acute) |

### Business Launch
| Layer | Question |
|-------|----------|
| Dasha | Is business launch possible now? (7th lord for partnership, 10th, 11th) |
| Transit | Is the window active? (Jupiter on 11th, Saturn on 10th) |
| Fast Trigger | Is this the exact timing? (Mercury/Mars activation) |
| Classical Pattern | Is there a structural signature? (Dhana yoga, Rajayoga) |
| Outcome/Quality | What kind? (Solo vs partnership, scale, sector alignment) |

### Relocation
| Layer | Question |
|-------|----------|
| Dasha | Is relocation possible now? (4th lord, 12th lord, Rahu periods) |
| Transit | Is the window active? (Saturn/Jupiter on 4th/9th/12th) |
| Fast Trigger | Is this the exact timing? (Mars/Moon over 4th/12th) |
| Classical Pattern | Is there a structural signature? (Foreign settlement yogas) |
| Outcome/Quality | What kind? (Domestic vs international, temporary vs permanent) |

---

## File Layout Pattern (Reusable for All Events)

```
rules/domains/{domain}/{event_family}/
├── {event}_rule.schema.json      # Validation schema
├── dasha_rules.json              # Layer 1: Planetary period gates
├── transit_rules.json            # Layer 2: Slow planet activation
├── fast_trigger_rules.json       # Layer 3: Fast planet exact timing
├── classical_patterns.json       # Layer 4: Structural birth chart patterns
├── outcome_quality.json          # Layer 5: Event classification
└── ARCHITECTURE.md               # This document
```

### Examples:
```
rules/domains/relationship/marriage/       ← THIS (implemented)
rules/domains/career/job_switch/           ← NEXT
rules/domains/career/promotion/
rules/domains/health/surgery/
rules/domains/health/chronic_onset/
rules/domains/family/childbirth/
rules/domains/finance/business_launch/
rules/domains/spirituality/initiation/
rules/domains/relocation/foreign_move/
```

---

## How the Rule Engine Evaluates

```python
def evaluate_marriage_timing(chart_state, transit_state, dasha_state):
    """
    5-pass sequential evaluation.
    Each layer gates the next.
    """
    # Pass 1: Dasha gate
    dasha_results = evaluate_rules(dasha_rules, dasha_state)
    if not any_fired(dasha_results):
        return MarriageResult(status="NOT_NOW", confidence=0)

    # Pass 2: Transit activation (only if dasha opened)
    transit_results = evaluate_rules(transit_rules, transit_state)
    window_active = any_fired(transit_results)

    # Pass 3: Fast trigger (only if transit narrowed)
    if window_active:
        trigger_results = evaluate_rules(fast_trigger_rules, transit_state)
        exact_timing = any_fired(trigger_results)
    else:
        exact_timing = False

    # Pass 4: Classical pattern (structural modifier)
    pattern_results = evaluate_rules(classical_patterns, chart_state)
    structural_confidence = aggregate_confidence(pattern_results)

    # Pass 5: Outcome classification (independent)
    quality_results = evaluate_rules(outcome_quality, chart_state)
    marriage_type = classify_outcome(quality_results)

    # Compose final result
    return MarriageResult(
        status=determine_status(dasha_results, transit_results, trigger_results),
        timing_band=determine_band(window_active, exact_timing),
        confidence=compute_confidence(dasha_results, transit_results, 
                                      trigger_results, structural_confidence),
        marriage_type=marriage_type,
        fired_rules=collect_fired_rules(all_results),
    )
```

---

## Signal Extraction Requirements

The `signals` field in each rule declares what data the engine must extract:

| Signal Axis | What It Means | Source Layer |
|-------------|---------------|-------------|
| `dasha` | Which dasha lords/references are needed | features/dasha.py |
| `transit` | Which transiting planets to track | astronomy/engine_base.py |
| `houses` | Which house numbers are relevant | features/houses.py |
| `planets` | Specific planets referenced | astronomy/engine_base.py |
| `nakshatra` | Nakshatra references | features/nakshatra.py |
| `d9` | Navamsa chart references | features/divisional.py |
| `sensitive_points` | Calculated mathematical points | NEW: to be implemented |

This allows the engine to pre-compute ONLY the data needed for active rules,
avoiding unnecessary calculation overhead.

---

## Rule Counts (Current State)

| Layer | File | Rules | Sources |
|-------|------|-------|---------|
| Dasha | dasha_rules.json | 5 | JYOTHISHI, Jataka Parijata, Phaladeepika |
| Transit | transit_rules.json | 7 | JYOTHISHI, Phaladeepika, Nakshatras study |
| Fast Trigger | fast_trigger_rules.json | 4 | Transit Astrology, Nakshatras study |
| Classical Pattern | classical_patterns.json | 6 | BPHS, Phaladeepika |
| Outcome/Quality | outcome_quality.json | 9 | JYOTHISHI, Phaladeepika, BPHS, AstroSight, Harness |
| **TOTAL** | | **31** | |

---

## Next Steps

1. **Implement rule evaluator** in `rules/event_engine.py` that follows 5-pass logic
2. **Add sensitive point calculator** for mathematical longitude sums
3. **Add D9 (Navamsa) lagna calculator** to features/divisional.py
4. **Replicate pattern** for career/job_switch as next event pack
5. **Calibrate** with known marriage dates (feedback loop)
