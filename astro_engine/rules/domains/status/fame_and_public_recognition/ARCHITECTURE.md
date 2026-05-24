# Fame & Public Recognition Rules — 5-Layer Semantic Architecture

## Why This Architecture?

Fame/public recognition prediction is NOT a single question.
It is **5 fundamentally different semantic questions** asked in sequence:

| Layer | File | Question | Timing Precision |
|-------|------|----------|-----------------|
| 1. Dasha | `dasha_rules.json` | **Is fame/recognition possible now?** | Broad (years) |
| 2. Transit | `transit_rules.json` | **Is the recognition window active?** | Medium (months) |
| 3. Fast Trigger | `fast_trigger_rules.json` | **Is this the exact recognition day?** | Exact (days/weeks) |
| 4. Classical Pattern | `classical_patterns.json` | **Is there a structural fame signature?** | None (structural) |
| 5. Outcome/Quality | `outcome_quality.json` | **What kind of fame?** | None (qualitative) |

---

## The 5-Pass Evaluation Flow

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: DASHA (Gate)                                  │
│  Question: "Is this planetary period fame-capable?"     │
│  Key: Sun, 10th lord, 1st lord, Jupiter periods         │
│  If NO dasha rule fires → STOP. Fame not now.          │
│  If YES → opens BROAD WINDOW (1-3 years)               │
└────────────────────────┬────────────────────────────────┘
                         │ window open
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: TRANSIT (Activation)                          │
│  Question: "Are slow planets activating fame houses?"   │
│  Jupiter conjunct Sun, Jupiter Return, benefics in 10th │
│  If YES → narrows to MEDIUM WINDOW (1-6 months)        │
└────────────────────────┬────────────────────────────────┘
                         │ window narrowed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: FAST TRIGGER (Pinpoint)                       │
│  Question: "What is the exact recognition day?"         │
│  Moon on Abhishek Tara (28th nakshatra from birth Moon) │
│  If YES → narrows to EXACT WINDOW (days)               │
└────────────────────────┬────────────────────────────────┘
                         │ timing pinpointed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: CLASSICAL PATTERN (Structural Modifier)       │
│  Question: "Does the birth chart confirm fame?"         │
│  Amala Yoga, Vargottama Moon, Sun in 10th, etc.        │
│  MODIFIES confidence, does not create windows          │
└────────────────────────┬────────────────────────────────┘
                         │ confidence adjusted
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: OUTCOME/QUALITY (Classification)              │
│  Question: "What kind of fame?"                         │
│  Political/artistic/spiritual/controversial/mass        │
│  Stable/unstable/charismatic/scandal-prone              │
│  Local/national/international scale                    │
│  CLASSIFIES the event, never affects timing            │
└─────────────────────────────────────────────────────────┘
```

---

## Key Design Principles

### 1. Sequential Narrowing (Not Parallel Scoring)
- Layer 1 must fire BEFORE Layer 2 is even evaluated
- Layer 3 only matters if Layer 2 has already narrowed
- This prevents false positives from isolated triggers

### 2. Separation of Timing vs. Quality
- Layers 1-3: **WHEN** will fame/recognition happen?
- Layer 4: **Structural confirmation** (does chart support fame?)
- Layer 5: **WHAT KIND** of fame? (political vs artistic vs spiritual)
- Never mix these — controversial fame still happens on time

### 3. Provenance Tracking
Every rule carries `source_text` with:
- `work_name`: Classical text (BPHS, Phaladeepika, Jataka Parijata, etc.)
- `chapter`, `verse`, `page`: Exact location
- `quote`: Verbatim text

### 4. Domain Isolation (C1/C2 Split)
- Rules in this directory are domain-specific policies (C2 layer)
- They consume domain-neutral symbolic state from `rules/symbolic/` (C1 layer)
- Fame rules NEVER modify symbolic state — read-only consumers
- Fame rules NEVER leak into medical, career, or relocation domains

### 5. Calibration-Ready
- Each rule has `status`: active / experimental / calibration / deprecated
- Each rule has `interpretation.confidence`: source-level confidence (0-1)
- `calibration_overlay.json` adjusts weights WITHOUT touching classical rules
- Future ML calibration operates per-rule, per-domain

---

## Fame-Specific Semantic Layers

### Layer 1: Dasha (When is fame possible?)
Key planets for fame:
- **Sun** — natural karaka for fame, authority, public standing, government honor
- **Jupiter** — karaka for wisdom-fame, spiritual recognition, Gaja Kesari
- **Moon** — karaka for public popularity, mass appeal, emotional connection
- **Venus** — karaka for artistic fame, beauty, entertainment recognition
- **Rahu** — karaka for mass influence, sudden fame, unconventional recognition

Key houses:
- **1st house** — self, personality, public image
- **5th house** — creativity, intelligence, past-life merit
- **9th house** — dharma, luck, guru's blessing
- **10th house** — karma, career, public action, government
- **11th house** — gains, fulfillment of desires, large networks

### Layer 2: Transit (Is the fame window active?)
Key transits:
- **Jupiter conjunct natal Sun** — fame activation (strongest single transit)
- **Jupiter Return** (to natal position) — wisdom/dharma recognition cycle
- **Benefics transit 10th house** — public action window
- **Abhishek Tara (28th nakshatra)** transit — coronation/recognition

### Layer 3: Fast Trigger (Exact recognition day)
Key triggers:
- **Moon on Abhishek Tara (28th)** — coronation/recognition day
- **Mars on Abhishek Tara (28th)** — action-fame day (awards, announcements)

### Layer 4: Classical Pattern (Natal promise — does chart support fame?)
Key patterns:
- **Amala Yoga** — benefic in 10th from Moon (spotless fame)
- **1st-10th lord exchange** (Parivartana) — self and career intertwined
- **Moon in 10th with trinal 10th lord** — public popularity
- **Sun in 10th** — political/government fame
- **10th lord with benefics** — honored reputation
- **Vargottama Moon** — international recognition
- **Malefics in 3/6/11** — competitive victory, overcoming enemies

### Layer 5: Outcome/Quality (What kind of fame?)
Classifications:
- **Mode**: political_fame / artistic_fame / spiritual_fame / controversial / mass_influence
- **Quality**: stable / unstable / charismatic / scandal_prone
- **Scale**: local / national / international

---

## File Layout

```
rules/domains/status/fame_and_public_recognition/
├── ARCHITECTURE.md               # This document
├── fame_rule.schema.json         # Validation schema
├── dasha_rules.json              # Layer 1: Planetary period gates (7 rules)
├── transit_rules.json            # Layer 2: Slow planet activation (4 rules)
├── fast_trigger_rules.json       # Layer 3: Fast planet exact timing (1 rule)
├── classical_patterns.json       # Layer 4: Structural birth chart patterns (10 rules)
├── outcome_quality.json          # Layer 5: Fame classification (9 rules)
├── calibration_schema.json       # Schema for calibration overlay
└── calibration_overlay.json      # Empirical tuning (Layer 3 calibration)
```

---

## How the Rule Engine Evaluates

```python
def evaluate_fame_timing(chart_state, transit_state, dasha_state):
    """
    5-pass sequential evaluation.
    Each layer gates the next.
    """
    # Pass 1: Dasha gate
    dasha_results = evaluate_rules(dasha_rules, dasha_state)
    if not any_fired(dasha_results):
        return FameResult(status="NOT_NOW", confidence=0)

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
    fame_type = classify_outcome(quality_results)

    # Compose final result
    return FameResult(
        status=determine_status(dasha_results, transit_results, trigger_results),
        timing_band=determine_band(window_active, exact_timing),
        confidence=compute_confidence(dasha_results, transit_results,
                                      trigger_results, structural_confidence),
        fame_type=fame_type,
        fired_rules=collect_fired_rules(all_results),
    )
```

---

## Rule Counts

| Layer | File | Rules | Status |
|-------|------|-------|--------|
| Dasha | dasha_rules.json | 7 | Active |
| Transit | transit_rules.json | 4 | Active |
| Fast Trigger | fast_trigger_rules.json | 1 | Active |
| Classical Pattern | classical_patterns.json | 10 | Active |
| Outcome/Quality | outcome_quality.json | 9 | Active |
| **TOTAL** | | **31** | All layers populated |

---

## Relationship to Other Event Packs

This fame pack follows the identical architecture as:
- `rules/domains/relationship/marriage/` — marriage timing
- `rules/domains/family/childbirth/` — childbirth timing
- `rules/domains/career/career_profession/` — career change timing
- `rules/domains/business/business_launch/` — business timing
- `rules/domains/relocation/foreign_settlement/` — relocation timing

Same engine, same 5-layer logic, different domain-specific rules.

---

## Next Steps

1. ✅ **Rules populated** — 31 rules across 5 layers
2. ✅ **fame_evaluator.py** implemented following medical/relocation pattern
3. **Calibrate** with known fame events (feedback loop)
4. **Connect to interpreter** (create `rules/domains/status/interpreter.py`)
