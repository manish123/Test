# Ancestral Property & Inheritance Rules — 5-Layer Semantic Architecture

## Why This Architecture?

Ancestral property/inheritance prediction is NOT a single question.
It is **5 fundamentally different semantic questions** asked in sequence:

| Layer | File | Question | Timing Precision |
|-------|------|----------|-----------------|
| 1. Dasha | `dasha_rules.json` | **Is property/inheritance possible now?** | Broad (years) |
| 2. Transit | `transit_rules.json` | **Is the property window active?** | Medium (months) |
| 3. Fast Trigger | `fast_trigger_rules.json` | **Is this the exact property day?** | Exact (days/weeks) |
| 4. Classical Pattern | `classical_patterns.json` | **Is there a structural property signature?** | None (structural) |
| 5. Outcome/Quality | `outcome_quality.json` | **What kind of property event?** | None (qualitative) |

---

## The 5-Pass Evaluation Flow

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: DASHA (Gate)                                      │
│  Question: "Is this planetary period property-capable?"     │
│  Key: 4th lord, 8th lord, 9th lord, Mars, Saturn periods    │
│  If NO dasha rule fires → STOP. Property not now.           │
│  If YES → opens BROAD WINDOW (1-3 years)                    │
└────────────────────────┬────────────────────────────────────┘
                         │ window open
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: TRANSIT (Activation)                              │
│  Question: "Are slow planets activating property houses?"   │
│  Jupiter on 4th/9th/8th, Saturn on Mars, Jupiter 2nd Moon   │
│  If YES → narrows to MEDIUM WINDOW (1-6 months)            │
└────────────────────────┬────────────────────────────────────┘
                         │ window narrowed
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: FAST TRIGGER (Pinpoint)                           │
│  Question: "What is the exact property transfer day?"       │
│  Jati Tara (26th nak), Moon right hand (25-27th),           │
│  Moon two eyes (9-10th), Mars head (16-17th)                │
│  If YES → narrows to EXACT WINDOW (days)                    │
└────────────────────────┬────────────────────────────────────┘
                         │ timing pinpointed
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: CLASSICAL PATTERN (Structural Modifier)           │
│  Question: "Does the birth chart confirm property?"         │
│  Benefic 8th, strong 4th, strong 2nd, 12th paternal, 3rd   │
│  MODIFIES confidence, does not create windows               │
└────────────────────────┬────────────────────────────────────┘
                         │ confidence adjusted
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 5: OUTCOME/QUALITY (Classification)                  │
│  Question: "What kind of property event?"                   │
│  smooth_inheritance / disputed_property / sudden_gain /     │
│  karmic_pattern / inherited_debt                            │
│  Asset: land / liquid_wealth / luxury_assets / inaccessible │
│  CLASSIFIES the event, never affects timing                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Design Principles

### 1. Sequential Narrowing (Not Parallel Scoring)
- Layer 1 must fire BEFORE Layer 2 is even evaluated
- Layer 3 only matters if Layer 2 has already narrowed
- This prevents false positives from isolated triggers

### 2. Separation of Timing vs. Quality
- Layers 1-3: **WHEN** will property/inheritance happen?
- Layer 4: **Structural confirmation** (does chart support property gains?)
- Layer 5: **WHAT KIND** of property? (smooth vs disputed vs sudden)
- Never mix these — disputed inheritance still happens on time

### 3. Provenance Tracking
Every rule carries `source_text` with:
- `work_name`: Classical text (BPHS, Phaladeepika, Jataka Parijata, etc.)
- `chapter`, `verse`, `page`: Exact location
- `quote`: Verbatim text

### 4. Domain Isolation (C1/C2 Split)
- Rules in this directory are domain-specific policies (C2 layer)
- They consume domain-neutral symbolic state from `rules/symbolic/` (C1 layer)
- Property rules NEVER modify symbolic state — read-only consumers
- Property rules NEVER leak into medical, career, or fame domains

### 5. Calibration-Ready
- Each rule has `status`: active / experimental / calibration / deprecated
- Each rule has `interpretation.confidence`: source-level confidence (0-1)
- `calibration_overlay.json` adjusts weights WITHOUT touching classical rules
- Future ML calibration operates per-rule, per-domain

---

## Property-Specific Semantic Layers

### Layer 1: Dasha (When is property/inheritance possible?)
Key planets (Property Karakas):
- **Mars** — natural karaka for land, real estate, physical property
- **Saturn** — karaka for structures, old property, ancestral buildings
- **Jupiter** — karaka for expansion, wealth growth, blessings
- **Moon** — karaka for home, comfort, emotional security through property
- **Venus** — karaka for luxury assets, vehicles, beautiful homes

Key houses:
- **2nd house** — family wealth, accumulated assets, movable property
- **4th house** — immovable property, land, home, vehicles, happiness
- **8th house** — inheritance, sudden gains, hidden wealth, legacy
- **9th house** — father's property, fortune, dharma, paternal legacy
- **11th house** — gains, fulfillment of desires, income from property
- **12th house** — paternal property (father's loss = child's gain), distant property

Key lords:
- **4th lord** — direct property ownership
- **8th lord** — inheritance matters (positive = smooth, afflicted = disputes)
- **9th lord** — father/fortune connection, paternal legacy
- **2nd lord** — family wealth accumulation
- **12th lord** — paternal property transfer

### Layer 2: Transit (Is the property window active?)
Key transits:
- **Jupiter transit 4th from Moon** — property acquisition activation
- **Jupiter transit 9th from Moon** — father's property/fortune
- **Jupiter transit 8th from Moon** — inheritance activation
- **Jupiter conjunct natal Sun** — father's wealth transfer
- **Saturn conjunct natal Mars** — property loss/disputes
- **Saturn transit 9th from Moon** — father/legacy matters

### Layer 3: Fast Trigger (Exact property day)
Key triggers:
- **Jati Tara (26th nakshatra from birth Moon)** — ancestral property day
- **Moon right hand (25-27th nakshatra)** — property transfer moment
- **Moon two eyes (9-10th nakshatra)** — visibility of assets
- **Mars head (16-17th nakshatra)** — land/real estate action day

### Layer 4: Classical Pattern (Natal promise — does chart support property?)
Key patterns:
- **Benefic in 8th** — smooth inheritance, hidden wealth surfaces
- **8th hostile drishti** — disputed property, litigation
- **Strong 4th house** — inherited land, ancestral property
- **Strong 2nd house** — family money, accumulated wealth
- **12th house activation** — paternal property transfer
- **3rd house activation** — sudden windfalls, brother's property

### Layer 5: Outcome/Quality (What kind of property event?)
Classifications:
- **Mode**: smooth_inheritance / disputed_property / sudden_gain / karmic_pattern / inherited_debt
- **Quality**: supportive / challenging / mixed
- **Asset type**: land / liquid_wealth / luxury_assets / inaccessible

---

## File Layout

```
rules/domains/finance/ancestral_property_and_inheritance/
├── ARCHITECTURE.md               # This document
├── property_rule.schema.json     # Validation schema
├── dasha_rules.json              # Layer 1: Planetary period gates (8 rules)
├── transit_rules.json            # Layer 2: Slow planet activation (6 rules)
├── fast_trigger_rules.json       # Layer 3: Fast planet exact timing (4 rules)
├── classical_patterns.json       # Layer 4: Structural birth chart patterns (9 rules)
├── outcome_quality.json          # Layer 5: Property classification (6 rules)
├── calibration_schema.json       # Schema for calibration overlay
└── calibration_overlay.json      # Empirical tuning (Layer 3 calibration)
```

---

## How the Rule Engine Evaluates

```python
def evaluate_property_timing(chart_state, transit_state, dasha_state):
    """
    5-pass sequential evaluation.
    Each layer gates the next.
    """
    # Pass 1: Dasha gate
    dasha_results = evaluate_rules(dasha_rules, dasha_state)
    if not any_fired(dasha_results):
        return PropertyResult(status="NOT_NOW", confidence=0)

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
    property_type = classify_outcome(quality_results)

    # Compose final result
    return PropertyResult(
        status=determine_status(dasha_results, transit_results, trigger_results),
        timing_band=determine_band(window_active, exact_timing),
        confidence=compute_confidence(dasha_results, transit_results,
                                      trigger_results, structural_confidence),
        property_type=property_type,
        fired_rules=collect_fired_rules(all_results),
    )
```

---

## Rule Counts

| Layer | File | Rules | Status |
|-------|------|-------|--------|
| Dasha | dasha_rules.json | 8 | Active |
| Transit | transit_rules.json | 6 | Active |
| Fast Trigger | fast_trigger_rules.json | 4 | Active |
| Classical Pattern | classical_patterns.json | 9 | Active |
| Outcome/Quality | outcome_quality.json | 6 | Active |
| **TOTAL** | | **33** | All layers populated |

---

## Relationship to Other Event Packs

This property pack follows the identical architecture as:
- `rules/domains/status/fame_and_public_recognition/` — fame timing
- `rules/domains/relationship/marriage/` — marriage timing
- `rules/domains/medical/surgery_medical_procedure/` — medical timing
- `rules/domains/relocation/foreign_settlement/` — relocation timing
- `rules/domains/career/career_profession/` — career change timing

Same engine, same 5-layer logic, different domain-specific rules.

---

## Next Steps

1. ✅ **Rules populated** — 33 rules across 5 layers
2. ✅ **property_evaluator.py** implemented following fame/medical pattern
3. **Calibrate** with known property events (feedback loop)
4. **Connect to interpreter** (create `rules/domains/finance/interpreter.py`)
