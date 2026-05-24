# Surgery & Medical Events Rules — 5-Layer Semantic Architecture

## Why This Architecture?

Medical crisis prediction is NOT a single question.
It is **5 fundamentally different semantic questions** asked in sequence:

| Layer | File | Question | Timing Precision |
|-------|------|----------|-----------------|
| 1. Dasha | `dasha_rules.json` | **Is medical crisis possible now?** | Broad (years) |
| 2. Transit | `transit_rules.json` | **Is the health window active?** | Medium (months) |
| 3. Fast Trigger | `fast_trigger_rules.json` | **Is this the exact timing?** | Exact (days/weeks) |
| 4. Classical Pattern | `classical_patterns.json` | **Is there a structural health vulnerability?** | None (structural) |
| 5. Outcome/Quality | `outcome_quality.json` | **What kind of medical event?** | None (qualitative) |

---

## The 5-Pass Evaluation Flow

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: DASHA (Gate)                                  │
│  Question: "Is this planetary period health-vulnerable?" │
│  Key: 6th lord, 8th lord, 12th lord, Maraka lords       │
│       (2nd/7th), Mars-Ketu combinations                 │
│  If NO dasha rule fires → STOP. Medical crisis not now. │
│  If YES → opens BROAD WINDOW (1-3 years)                │
└────────────────────────┬────────────────────────────────┘
                         │ window open
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: TRANSIT (Activation)                          │
│  Question: "Are planets activating health houses?"      │
│  Rahu on Mars/8th lord, Saturn on Lagna Sphuta,         │
│  Lagna lord in 6/8/12                                   │
│  If YES → narrows to MEDIUM WINDOW (1-6 months)         │
└────────────────────────┬────────────────────────────────┘
                         │ window narrowed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: FAST TRIGGER (Pinpoint)                       │
│  Question: "What is the exact timing?"                  │
│  Mrityu Bhaga, Vinasha Tara (23rd), Vipat/Pratyak Tara,│
│  Mars Anga Gochara, Ashtakavarga Pinda                  │
│  If YES → narrows to EXACT WINDOW (days to weeks)       │
└────────────────────────┬────────────────────────────────┘
                         │ timing pinpointed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: CLASSICAL PATTERN (Structural Modifier)       │
│  Question: "Does the birth chart confirm health risk?"  │
│  6th+8th lords in Lagna, Saturn-Mars in 6th,            │
│  Moon Papakartari, Mars/Ketu in 6/8                     │
│  MODIFIES confidence, does not create windows           │
└────────────────────────┬────────────────────────────────┘
                         │ confidence adjusted
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: OUTCOME/QUALITY (Classification)              │
│  Question: "What kind of medical event?"                │
│  Mode: surgery/chronic/acute/recovery                   │
│  Quality: life_threatening/manageable/healing           │
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
- Layers 1-3: **WHEN** will the medical event happen?
- Layer 4: **Structural confirmation** (does chart have health vulnerability?)
- Layer 5: **WHAT KIND** of medical event? (surgery vs chronic vs acute)
- Never mix these — a surgery still happens on time regardless of quality

### 3. Provenance Tracking
Every rule carries `source_text` with:
- `work_name`: Classical text (BPHS, Phaladeepika, Jataka Parijata, etc.)
- `chapter`, `verse`, `page`: Exact location
- `quote`: Verbatim text

### 4. Domain Isolation (C1/C2 Split)
- Rules in this directory are domain-specific policies (C2 layer)
- They consume domain-neutral symbolic state from `rules/symbolic/` (C1 layer)
- Medical rules NEVER modify symbolic state — read-only consumers
- Medical rules NEVER leak into trading, career, or relocation domains

### 5. Calibration-Ready
- Each rule has `status`: active / experimental / calibration / deprecated
- Each rule has `interpretation.confidence`: source-level confidence (0-1)
- `calibration_overlay.json` adjusts weights WITHOUT touching classical rules
- Future ML calibration operates per-rule, per-domain

---

## Medical-Specific Semantic Layers

### Layer 1: Dasha (When is medical crisis possible?)
Key planets for medical events:
- **6th Lord** — ruler of disease, illness, enemies to health
- **8th Lord** — ruler of surgery, sudden crisis, chronic ailments, death-like experiences
- **12th Lord** — ruler of hospitalization, bed-ridden states, confinement
- **Maraka Lords (2nd/7th)** — lords of death-inflicting houses
- **Mars** — karaka for surgery, blood, cuts, accidents, inflammation
- **Ketu** — karaka for sudden illness, mysterious diseases, surgical intervention
- **Saturn** — karaka for chronic disease, wasting illness, long hospitalization

### Layer 2: Transit (Is the health window active?)
Key transits:
- **Rahu transit over natal Mars** — inflammation, infection, sudden crisis
- **Saturn transit on Lagna Sphuta** — bodily weakness, systemic breakdown
- **Lagna lord transiting 6/8/12** — self placed in houses of disease/surgery/hospitalization
- **Mars transit over 8th house** — surgical intervention window
- **Saturn-Mars mutual aspect** — chronic inflammation activation

### Layer 3: Fast Trigger (Exact day/week)
Key triggers:
- **Mrityu Bhaga** — degree of death/critical crisis in each sign
- **Vinasha Tara (23rd Nakshatra)** — destruction/annihilation star activation
- **Vipat Tara (3rd)** — danger star, accidents and sudden harm
- **Pratyak Tara (5th)** — obstacles to vitality star
- **Mars Anga Gochara** — Mars limb transit for body-part activation
- **Ashtakavarga Pinda** — lowest-score transit degrees (weakest vitality points)

### Layer 4: Classical Pattern (Natal promise — does chart support health vulnerability?)
Key patterns:
- **6th + 8th lords conjunct in Lagna** — lifetime disease vulnerability
- **Saturn-Mars in 6th house** — chronic inflammatory conditions
- **Moon in Papakartari Yoga** — emotional/mental health affliction
- **Mars/Ketu in 6th or 8th** — surgical destiny, accident-prone
- **Lagna lord in 6/8/12** — weakened vitality from birth
- **All malefics in Kendras** — Sarpa Yoga (health dangers)
- **8th lord in Lagna** — chronic health challenges throughout life

### Layer 5: Outcome/Quality (What kind of medical event?)
Classifications:
- **Mode**: surgery / chronic_disease / acute_illness / hospitalization / recovery / injury
- **Quality**: life_threatening / manageable / healing / critical / routine
- **Body System**: head / chest / abdomen / limbs / nervous / circulatory / reproductive
- **Duration**: acute_episode / chronic_ongoing / recovery_period / emergency
- **Intervention**: surgical / pharmaceutical / natural_recovery / intensive_care

---

## File Layout

```
rules/domains/medical/surgery_and_medical_events/
├── ARCHITECTURE.md               # This document
├── medical_rule.schema.json      # Validation schema
├── dasha_rules.json              # Layer 1: Planetary period gates
├── transit_rules.json            # Layer 2: Slow planet activation
├── fast_trigger_rules.json       # Layer 3: Fast planet exact timing
├── classical_patterns.json       # Layer 4: Structural birth chart patterns
├── outcome_quality.json          # Layer 5: Medical event classification
├── calibration_schema.json       # Schema for calibration overlay
└── calibration_overlay.json      # Empirical tuning (Layer 3 calibration)
```

---

## How the Rule Engine Evaluates

```python
def evaluate_medical_timing(chart_state, transit_state, dasha_state):
    """
    5-pass sequential evaluation.
    Each layer gates the next.
    """
    # Pass 1: Dasha gate
    dasha_results = evaluate_rules(dasha_rules, dasha_state)
    if not any_fired(dasha_results):
        return MedicalResult(status="NOT_NOW", confidence=0)

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
    medical_type = classify_outcome(quality_results)

    # Compose final result
    return MedicalResult(
        status=determine_status(dasha_results, transit_results, trigger_results),
        timing_band=determine_band(window_active, exact_timing),
        confidence=compute_confidence(dasha_results, transit_results,
                                      trigger_results, structural_confidence),
        medical_type=medical_type,
        fired_rules=collect_fired_rules(all_results),
    )
```

---

## Rule Counts

| Layer | File | Rules | Status |
|-------|------|-------|--------|
| Dasha | dasha_rules.json | 10 | Active |
| Transit | transit_rules.json | 6 | Active |
| Fast Trigger | fast_trigger_rules.json | 5 | Active |
| Classical Pattern | classical_patterns.json | 9 | Active |
| Outcome/Quality | outcome_quality.json | 10 | Active |
| **TOTAL** | | **40** | Complete |

---

## Relationship to Other Event Packs

This medical pack follows the identical architecture as:
- `rules/domains/relocation/foreign_settlement/` — relocation timing
- `rules/domains/relationship/marriage/` — marriage timing
- `rules/domains/family/childbirth/` — childbirth timing
- `rules/domains/career/career_profession/` — career change timing
- `rules/domains/business/business_launch/` — business timing

Same engine, same 5-layer logic, different domain-specific rules.

---

## Next Steps

1. ✅ **Rules populated** — 40 rules across all 5 layers
2. **Implement medical_evaluator.py** following relocation_evaluator.py pattern
3. **Add medical-specific sensitive points** (Mrityu Bhaga degrees, 6th+8th lord midpoint, etc.)
4. **Calibrate** with known medical event dates (feedback loop)
5. **Connect to interpreter** (create `rules/domains/medical/interpreter.py`)
