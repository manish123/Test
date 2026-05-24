# Relocation & Foreign Settlement Rules — 5-Layer Semantic Architecture

## Why This Architecture?

Relocation/foreign settlement prediction is NOT a single question.
It is **5 fundamentally different semantic questions** asked in sequence:

| Layer | File | Question | Timing Precision |
|-------|------|----------|-----------------|
| 1. Dasha | `dasha_rules.json` | **Is relocation/foreign move possible now?** | Broad (years) |
| 2. Transit | `transit_rules.json` | **Is the relocation window active?** | Medium (months) |
| 3. Fast Trigger | `fast_trigger_rules.json` | **Is this the exact timing?** | Exact (days/weeks) |
| 4. Classical Pattern | `classical_patterns.json` | **Is there a structural foreign settlement signature?** | None (structural) |
| 5. Outcome/Quality | `outcome_quality.json` | **What kind of relocation?** | None (qualitative) |

---

## The 5-Pass Evaluation Flow

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: DASHA (Gate)                                  │
│  Question: "Is this planetary period relocation-capable?"│
│  Key: 4th lord, 12th lord, 9th lord, Rahu periods       │
│  If NO dasha rule fires → STOP. Relocation not now.     │
│  If YES → opens BROAD WINDOW (1-3 years)                │
└────────────────────────┬────────────────────────────────┘
                         │ window open
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: TRANSIT (Activation)                          │
│  Question: "Are slow planets activating move houses?"   │
│  Double transit on 4/9/12, Saturn on 4th, Jupiter on 9th│
│  If YES → narrows to MEDIUM WINDOW (1-6 months)         │
└────────────────────────┬────────────────────────────────┘
                         │ window narrowed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: FAST TRIGGER (Pinpoint)                       │
│  Question: "What is the exact timing?"                  │
│  Moon over 4th/12th, Mars activation, Rahu degree hits  │
│  If YES → narrows to EXACT WINDOW (days to weeks)       │
└────────────────────────┬────────────────────────────────┘
                         │ timing pinpointed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: CLASSICAL PATTERN (Structural Modifier)       │
│  Question: "Does the birth chart confirm foreign move?" │
│  Rahu in 1/7/9/12, 4th lord in 12th, foreign yogas     │
│  MODIFIES confidence, does not create windows           │
└────────────────────────┬────────────────────────────────┘
                         │ confidence adjusted
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: OUTCOME/QUALITY (Classification)              │
│  Question: "What kind of relocation?"                   │
│  Domestic/international, temporary/permanent,           │
│  career-driven/family-driven, voluntary/forced          │
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
- Layers 1-3: **WHEN** will relocation happen?
- Layer 4: **Structural confirmation** (does chart support foreign settlement?)
- Layer 5: **WHAT KIND** of move? (domestic vs foreign, temporary vs permanent)
- Never mix these — a forced relocation still happens on time

### 3. Provenance Tracking
Every rule carries `source_text` with:
- `work_name`: Classical text (BPHS, Phaladeepika, Jataka Parijata, etc.)
- `chapter`, `verse`, `page`: Exact location
- `quote`: Verbatim text

### 4. Domain Isolation (C1/C2 Split)
- Rules in this directory are domain-specific policies (C2 layer)
- They consume domain-neutral symbolic state from `rules/symbolic/` (C1 layer)
- Relocation rules NEVER modify symbolic state — read-only consumers
- Relocation rules NEVER leak into trading, career, or business domains

### 5. Calibration-Ready
- Each rule has `status`: active / experimental / calibration / deprecated
- Each rule has `interpretation.confidence`: source-level confidence (0-1)
- `calibration_overlay.json` adjusts weights WITHOUT touching classical rules
- Future ML calibration operates per-rule, per-domain

---

## Relocation-Specific Semantic Layers

### Layer 1: Dasha (When is relocation possible?)
Key planets for relocation:
- **Rahu** — natural karaka for foreign lands, border-crossing, unconventional paths
- **4th Lord** — ruler of home, land, roots (its period = home changes)
- **12th Lord** — ruler of foreign lands, faraway places, loss of familiar
- **9th Lord** — ruler of long journeys, fortune abroad, dharma in distant lands
- **Moon** — karaka for mind, emotions, settling (its period = emotional uprooting)
- **Saturn** — karaka for displacement, exile, slow permanent changes
- **Ketu** — karaka for leaving behind, detachment from homeland

### Layer 2: Transit (Is the relocation window active?)
Key transits:
- **Double Transit** (Jupiter + Saturn) on 4th/9th/12th — most reliable
- **Saturn transit over 4th house** — uprooting, change of residence
- **Jupiter transit 9th or 12th** — long-distance opportunity opens
- **Rahu transit over natal Moon** — mental restlessness, desire to move
- **Saturn/Rahu transit 4th from Moon** — emotional displacement

### Layer 3: Fast Trigger (Exact day/week)
Key triggers:
- **Moon over 4th/12th house** — emotional readiness day
- **Mars over 3rd/12th** — action/initiative for travel
- **Rahu degree hits** on sensitive points — foreign activation
- **Nakshatra triggers** (Ardra, Swati, Shatabhisha — air/movement stars)

### Layer 4: Classical Pattern (Natal promise — does chart support foreign settlement?)
Key patterns:
- **Rahu in 1/7/9/12** — foreign connection lifetime signature
- **4th lord in 12th** — home in foreign land (strongest single indicator)
- **12th lord in 4th** — foreign influence ON home (exile pattern)
- **9th lord in 12th** — fortune found far from birthplace
- **Ketu in 4th** — detachment from motherland
- **Moon in 12th** — mind settled in foreign environment
- **Multiple planets in 12th** — life energy directed toward foreign lands

### Layer 5: Outcome/Quality (What kind of relocation?)
Classifications:
- **Distance**: domestic_city_change / domestic_state_change / international
- **Duration**: temporary / semi_permanent / permanent_settlement / citizenship
- **Driver**: career_driven / education_driven / family_driven / forced / spiritual
- **Direction**: east / west / north / south (from sign/house calculations)
- **Quality**: smooth / challenging / sudden / gradual / repeated

---

## File Layout

```
rules/domains/relocation/foreign_settlement/
├── ARCHITECTURE.md               # This document
├── relocation_rule.schema.json   # Validation schema
├── dasha_rules.json              # Layer 1: Planetary period gates
├── transit_rules.json            # Layer 2: Slow planet activation
├── fast_trigger_rules.json       # Layer 3: Fast planet exact timing
├── classical_patterns.json       # Layer 4: Structural birth chart patterns
├── outcome_quality.json          # Layer 5: Relocation classification
├── calibration_schema.json       # Schema for calibration overlay
└── calibration_overlay.json      # Empirical tuning (Layer 3 calibration)
```

---

## How the Rule Engine Evaluates

```python
def evaluate_relocation_timing(chart_state, transit_state, dasha_state):
    """
    5-pass sequential evaluation.
    Each layer gates the next.
    """
    # Pass 1: Dasha gate
    dasha_results = evaluate_rules(dasha_rules, dasha_state)
    if not any_fired(dasha_results):
        return RelocationResult(status="NOT_NOW", confidence=0)

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
    relocation_type = classify_outcome(quality_results)

    # Compose final result
    return RelocationResult(
        status=determine_status(dasha_results, transit_results, trigger_results),
        timing_band=determine_band(window_active, exact_timing),
        confidence=compute_confidence(dasha_results, transit_results,
                                      trigger_results, structural_confidence),
        relocation_type=relocation_type,
        fired_rules=collect_fired_rules(all_results),
    )
```

---

## Rule Counts (Awaiting Population)

| Layer | File | Rules | Status |
|-------|------|-------|--------|
| Dasha | dasha_rules.json | 0 | Awaiting rules |
| Transit | transit_rules.json | 0 | Awaiting rules |
| Fast Trigger | fast_trigger_rules.json | 0 | Awaiting rules |
| Classical Pattern | classical_patterns.json | 0 | Awaiting rules |
| Outcome/Quality | outcome_quality.json | 0 | Awaiting rules |
| **TOTAL** | | **0** | Structure ready |

---

## Relationship to Other Event Packs

This relocation pack follows the identical architecture as:
- `rules/domains/relationship/marriage/` — marriage timing
- `rules/domains/family/childbirth/` — childbirth timing
- `rules/domains/career/career_profession/` — career change timing
- `rules/domains/business/business_launch/` — business timing

Same engine, same 5-layer logic, different domain-specific rules.

---

## Next Steps

1. **Populate rules** — user will provide JSON rules one by one
2. **Implement relocation_evaluator.py** following marriage_evaluator.py pattern
3. **Add relocation-specific sensitive points** (4th lord + 12th lord longitude sum, etc.)
4. **Calibrate** with known relocation dates (feedback loop)
5. **Connect to interpreter** (create `rules/domains/relocation/interpreter.py`)
