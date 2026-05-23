# Business Launch Rules — 5-Layer Semantic Architecture

## Why This Architecture?

Business timing prediction (launch, expansion, pivot, exit) is NOT a single question.
It is **5 fundamentally different semantic questions** asked in sequence:

| Layer | File | Question | Timing Precision |
|-------|------|----------|-----------------|
| 1. Dasha | `dasha_rules.json` | **Is business success possible now?** | Broad (years) |
| 2. Transit | `transit_rules.json` | **Is the commercial window active?** | Medium (months) |
| 3. Fast Trigger | `fast_trigger_rules.json` | **Is this the exact timing?** | Exact (days/weeks) |
| 4. Classical Pattern | `classical_patterns.json` | **Is there a structural business signature?** | None (structural) |
| 5. Outcome/Quality | `outcome_quality.json` | **What kind of business outcome?** | None (qualitative) |

These are **fundamentally different semantic layers**. Mixing them into a single scoring function
loses the sequential narrowing logic that makes Vedic timing work.

---

## The 5-Pass Evaluation Flow

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: DASHA (Gate)                                  │
│  Question: "Is this planetary period business-capable?"  │
│  If NO dasha rule fires → STOP. Business success not now│
│  If YES → opens BROAD WINDOW (1-3 years)                │
└────────────────────────┬────────────────────────────────┘
                         │ window open
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: TRANSIT (Activation)                          │
│  Question: "Are slow planets activating commerce?"      │
│  Double transit, Jupiter on 11th, Saturn on 10th...     │
│  If YES → narrows to MEDIUM WINDOW (1-6 months)         │
└────────────────────────┬────────────────────────────────┘
                         │ window narrowed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: FAST TRIGGER (Pinpoint)                       │
│  Question: "What is the exact timing?"                  │
│  Moon Mitra Tara, Mars head gains, Navamsa count...     │
│  If YES → narrows to EXACT WINDOW (days to weeks)       │
└────────────────────────┬────────────────────────────────┘
                         │ timing pinpointed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: CLASSICAL PATTERN (Structural Modifier)       │
│  Question: "Does the birth chart confirm business?"     │
│  Speculative yogas, Mercury in 10th, Lagnesha in 3rd...│
│  MODIFIES confidence, does not create windows           │
└────────────────────────┬────────────────────────────────┘
                         │ confidence adjusted
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: OUTCOME/QUALITY (Classification)              │
│  Question: "What kind of business outcome?"             │
│  Solo/partnership, sector alignment, scale, risk...     │
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
- Layers 1-3: **WHEN** will business success/failure occur?
- Layer 4: **Structural confirmation** (does chart support entrepreneurship?)
- Layer 5: **WHAT KIND** of business outcome?
- Never mix these — a partnership business still launches on time regardless of solo/joint classification

### 3. Provenance Tracking
Every rule carries `source_text` with:
- `work_name`: Classical text (BPHS, Phaladeepika, Jataka Parijata, Nirayana System, etc.)
- `chapter`, `verse`, `page`: Exact location
- `quote`: Verbatim text
- This enables: audit, calibration, scholarly validation

### 4. Domain Isolation (C1/C2 Split)
- Rules in this directory are **domain-specific policies** (C2 layer)
- They consume **domain-neutral symbolic state** from `rules/symbolic/` (C1 layer)
- Domains NEVER modify symbolic state — read-only consumers
- Business rules NEVER leak into trading, career, or other domains

### 5. Calibration-Ready
- Each rule has `status`: active / experimental / calibration / deprecated
- Each rule has `interpretation.confidence`: source-level confidence (0-1)
- `calibration_overlay.json` adjusts weights WITHOUT touching classical rules
- Future ML calibration operates per-rule, per-domain
- Independent feedback datasets per domain

---

## Business-Specific Semantic Layers

### Layer 1: Dasha (When is business success/failure possible?)
Key planets for business:
- **Mercury** — natural karaka for commerce, trade, intellect
- **Jupiter** — expansion, funding, growth, wisdom
- **Rahu** — massive scale, foreign elements, unconventional ventures
- **Saturn** — structure, discipline, long-term operations
- **Mars** — execution energy, aggressive action (but overextension risk)

### Layer 2: Transit (Is the commercial window active?)
Key transits:
- **Double Transit** (Jupiter + Saturn) on 7th/10th/11th — most reliable manifestation trigger
- **Jupiter transit 11th from Moon** — network expansion, customer growth
- **Saturn transit 11th from Moon** — structural gains, funding secured
- **Jupiter conjunct natal Mercury** — commercial expansion window
- **Saturn transit 12th from Moon** — business drain, restructuring needed

### Layer 3: Fast Trigger (Exact day/week)
Key triggers:
- **Mitra Tara (8th Nakshatra)** — partnership/funding day
- **Param Mitra Tara (9th Nakshatra)** — co-founder/investor day
- **Moon 25th-27th Nakshatra (Right Hand)** — wealth acquisition day
- **Mars 16th-17th Nakshatra (Head)** — aggressive gains window
- **Sanghatika (16th Star)** — business crisis trigger
- **Navamsa count** — exact day of deal completion

### Layer 4: Classical Pattern (Natal promise)
Key patterns:
- **5th-11th lord connection** — speculative business acumen
- **Chandra-Mangala in 11th** — viral/network business
- **Mercury alone in 10th** — merchant/trader archetype
- **Lagnesha in 3rd** — born business administrator
- **Venus strong in 7th** — luxury/partnership business
- **5th-8th Parivartana** — large-scale market investments
- **Mars Navamsa** — technology/engineering business

### Layer 5: Outcome/Quality (What kind?)
Classifications:
- **Mode**: solo_proprietorship / partnership / family_business / franchise / speculative
- **Scale**: micro / small / medium / large / enterprise
- **Sector**: commerce / technology / services / manufacturing / finance
- **Quality**: stable / volatile / litigation_prone / debt_heavy / scalable
- **Risk**: conservative / moderate / aggressive / speculative

---

## File Layout

```
rules/domains/business/business_launch/
├── ARCHITECTURE.md               # This document
├── business_rule.schema.json     # Validation schema
├── dasha_rules.json              # Layer 1: Planetary period gates
├── transit_rules.json            # Layer 2: Slow planet activation
├── fast_trigger_rules.json       # Layer 3: Fast planet exact timing
├── classical_patterns.json       # Layer 4: Structural birth chart patterns
├── outcome_quality.json          # Layer 5: Business classification
├── calibration_schema.json       # Schema for calibration overlay
└── calibration_overlay.json      # Empirical tuning (Layer 3 calibration)
```

---

## How the Rule Engine Evaluates

```python
def evaluate_business_timing(chart_state, transit_state, dasha_state):
    """
    5-pass sequential evaluation.
    Each layer gates the next.
    """
    # Pass 1: Dasha gate
    dasha_results = evaluate_rules(dasha_rules, dasha_state)
    if not any_fired(dasha_results):
        return BusinessResult(status="NOT_NOW", confidence=0)

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
    business_type = classify_outcome(quality_results)

    # Compose final result
    return BusinessResult(
        status=determine_status(dasha_results, transit_results, trigger_results),
        timing_band=determine_band(window_active, exact_timing),
        confidence=compute_confidence(dasha_results, transit_results,
                                      trigger_results, structural_confidence),
        business_type=business_type,
        fired_rules=collect_fired_rules(all_results),
    )
```

---

## Rule Counts (Current State)

| Layer | File | Rules | Sources |
|-------|------|-------|---------|
| Dasha | dasha_rules.json | 9 | BPHS, Jataka Parijata |
| Transit | transit_rules.json | 6 | Phaladeepika, Transit texts |
| Fast Trigger | fast_trigger_rules.json | 7 | Phala Deepika, SBC, Jataka Parijata |
| Classical Pattern | classical_patterns.json | 11 | BPHS, Nirayana System, Jataka Parijata |
| Outcome/Quality | outcome_quality.json | 10 | Nirayana System, Jataka Parijata, BPHS |
| **TOTAL** | | **43** | |

---

## Relationship to Other Event Packs

This business_launch pack follows the identical architecture as:
- `rules/domains/relationship/marriage/` — marriage timing
- `rules/domains/family/childbirth/` — childbirth timing
- `rules/domains/career/career_profession/` — career change timing

Same engine, same 5-layer logic, different domain-specific rules.

---

## Next Steps

1. **Implement business_evaluator.py** in `rules/` following marriage_evaluator.py pattern
2. **Add business-specific sensitive points** (Mercury+10th lord longitude sum, etc.)
3. **Calibrate** with known business launch/exit dates (feedback loop)
4. **Add sub-event packs**: business_exit, business_pivot, business_partnership
5. **Connect to interpreter** (`rules/domains/business/interpreter.py`)
