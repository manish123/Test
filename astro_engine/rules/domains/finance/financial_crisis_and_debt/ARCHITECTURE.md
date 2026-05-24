# Financial Crisis & Debt Rules — 5-Layer Semantic Architecture

## Why This Architecture?

Financial crisis prediction is NOT a single question.
It is **5 fundamentally different semantic questions** asked in sequence:

| Layer | File | Question | Timing Precision |
|-------|------|----------|-----------------|
| 1. Dasha | `dasha_rules.json` | **Is financial crisis possible now?** | Broad (years) |
| 2. Transit | `transit_rules.json` | **Is the crisis window active?** | Medium (months) |
| 3. Fast Trigger | `fast_trigger_rules.json` | **Is this the exact crisis timing?** | Exact (days/weeks) |
| 4. Classical Pattern | `classical_patterns.json` | **Is there a structural poverty/debt yoga?** | None (structural) |
| 5. Outcome/Quality | `outcome_quality.json` | **What kind of financial crisis?** | None (qualitative) |

---

## The 5-Pass Evaluation Flow

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: DASHA (Gate)                                  │
│  Question: "Is this planetary period crisis-active?"    │
│  Key: 8th lord, Rahu dusthana, Saturn-Mars, Venus 6/8  │
│  If NO dasha rule fires → STOP. Crisis not now.        │
│  If YES → opens BROAD WINDOW (1-3 years)                │
└────────────────────────┬────────────────────────────────┘
                         │ window open
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: TRANSIT (Activation)                          │
│  Question: "Are planets activating crisis houses?"      │
│  Saturn on Sun, Jupiter 8/9/12 from Moon,              │
│  Rahu adverse from Moon, malefic left-leg nakshatras   │
│  If YES → narrows to MEDIUM WINDOW (1-6 months)         │
└────────────────────────┬────────────────────────────────┘
                         │ window narrowed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: FAST TRIGGER (Pinpoint)                       │
│  Question: "What is the exact crisis timing?"           │
│  Mars left-hand nakshatras, Sanghatika (16th),         │
│  Vinasha (23rd) from Janma nakshatra                   │
│  If YES → narrows to EXACT WINDOW (days to weeks)       │
└────────────────────────┬────────────────────────────────┘
                         │ timing pinpointed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: CLASSICAL PATTERN (Structural Modifier)       │
│  Question: "Does the birth chart confirm poverty yoga?" │
│  2nd+11th lords in dusthana, Mars-Rahu insolvency,     │
│  1st-12th exchange, Lagna lord+Ketu 8th, Moon nodes    │
│  MODIFIES confidence, does not create windows           │
└────────────────────────┬────────────────────────────────┘
                         │ confidence adjusted
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: OUTCOME/QUALITY (Classification)              │
│  Question: "What kind of financial crisis?"             │
│  Mode: bankruptcy/asset_seizure/speculative_collapse/   │
│        hidden_liability/loan_dependency/destitution     │
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
- Layers 1-3: **WHEN** will the financial crisis happen?
- Layer 4: **Structural confirmation** (does chart have poverty/debt yoga?)
- Layer 5: **WHAT KIND** of crisis? (bankruptcy vs asset seizure vs chronic debt)
- Never mix these — a crisis still happens on time regardless of classification

### 3. Provenance Tracking
Every rule carries `source_text` with:
- `work_name`: Classical text (BPHS, Jataka Parijata, Nirayana System, etc.)
- `chapter`, `verse`, `page`: Exact location
- `quote`: Verbatim text

### 4. Domain Isolation (C1/C2 Split)
- Rules in this directory are domain-specific policies (C2 layer)
- They consume domain-neutral symbolic state from `rules/symbolic/` (C1 layer)
- Financial crisis rules NEVER modify symbolic state — read-only consumers
- Financial crisis rules NEVER leak into medical, career, or property domains

### 5. Calibration-Ready
- Each rule has `status`: active / experimental / calibration / deprecated
- Each rule has `interpretation.confidence`: source-level confidence (0-1)
- `calibration_overlay.json` adjusts weights WITHOUT touching classical rules
- Future ML calibration operates per-rule, per-domain

---

## Financial Crisis-Specific Semantic Layers

### Layer 1: Dasha (When is financial crisis possible?)
Key planets for financial crisis:
- **8th Lord** — sudden destruction, bankruptcy, hidden collapses
- **Rahu** — deception, speculation failure, illusory wealth
- **Saturn** — restriction, denial, chronic poverty, debt accumulation
- **Mars** — aggressive loss, litigation, impulsive destruction
- **Venus in Dusthana** — business failure, commercial collapse
- **Mercury in Dusthana** — poor judgment, asset liquidation

Key Dasha Combinations (8 rules):
1. Planet associated with 6th/8th/12th lords — financial harm gate
2. 8th Lord Mahadasha — sudden financial crisis gate
3. Rahu in 8th/12th or debilitated — bankruptcy gate
4. Venus in Dusthana — business loss gate
5. Rahu in 2nd house — capital drain gate
6. Jupiter-Saturn adverse alignment — industrial loss gate
7. Mercury in Dusthana — asset loss gate
8. Saturn-Mars adverse — debt accumulation gate

### Layer 2: Transit (Is the crisis window active?)
Key transits (4 rules):
1. Saturn on natal Sun — sudden loss through authority collapse
2. Jupiter in 8th/9th/12th from Moon — false optimism financial loss
3. Rahu in 2nd/5th/7th/9th/12th from Moon — deception-driven instability
4. Saturn/Rahu/Ketu in 9-11th nakshatra from Janma (left leg SBC) — financial destruction

### Layer 3: Fast Trigger (Exact day/week)
Key triggers (3 rules):
1. Mars in 12-15th nakshatra from Janma (left hand SBC) — poverty trigger
2. Moon/Mars on 16th nakshatra (Sanghatika) — forced debt trigger
3. Moon/Mars on 23rd nakshatra (Vinasha) — asset destruction trigger

### Layer 4: Classical Pattern (Natal promise — does chart support poverty/debt yoga?)
Key patterns (8 rules):
1. 2nd + 11th lords in evil houses — structural poverty yoga
2. 2nd + 11th lords with Mars/Rahu — insolvency yoga
3. Ascendant-12th exchange — self-created poverty
4. Ascendant lord in 8th with Ketu — hidden poverty
5. 5th + 9th lords in 6th/12th — speculative loss yoga
6. Mars-Saturn in 2nd — wealth destruction yoga
7. Moon with Rahu/Ketu + malefic — chronic poverty
8. Moon weak + Jupiter in Dusthana — no wealth retention

### Layer 5: Outcome/Quality (What kind of financial crisis?)
Classifications (10 rules):
1. Sun afflicted in wealth houses — government asset seizure
2. Strong 8th lord afflicting wealth — sudden bankruptcy from prosperity
3. 5th + 9th lords in Dusthana — speculative collapse
4. Jupiter in 12th from Arudha — tax burden outcome
5. Mercury in 12th from Arudha — litigation drain outcome
6. Moon-Mars in 8th — hidden liability emergence
7. 11th from 6th active — chronic loan dependency
8. Saturn in 2nd hostile — financial dysfunction
9. Sun in 6th — bad loans and bribery losses
10. Weak 10th + afflicted 3rd/9th — complete destitution

---

## File Layout

```
rules/domains/finance/financial_crisis_and_debt/
├── ARCHITECTURE.md                       # This document
├── financial_crisis_rule.schema.json     # Validation schema
├── dasha_rules.json                      # Layer 1: Planetary period gates (8 rules)
├── transit_rules.json                    # Layer 2: Slow planet activation (4 rules)
├── fast_trigger_rules.json               # Layer 3: Fast planet exact timing (3 rules)
├── classical_patterns.json               # Layer 4: Structural birth chart patterns (8 rules)
├── outcome_quality.json                  # Layer 5: Financial crisis classification (10 rules)
├── calibration_schema.json               # Schema for calibration overlay
└── calibration_overlay.json              # Empirical tuning (Layer 3 calibration)
```

---

## How the Rule Engine Evaluates

```python
def evaluate_financial_crisis_timing(chart_state, transit_state, dasha_state):
    """
    5-pass sequential evaluation.
    Each layer gates the next.
    """
    # Pass 1: Dasha gate
    dasha_results = evaluate_rules(dasha_rules, dasha_state)
    if not any_fired(dasha_results):
        return CrisisResult(status="NOT_NOW", confidence=0)

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
    crisis_type = classify_outcome(quality_results)

    # Compose final result
    return CrisisResult(
        status=determine_status(dasha_results, transit_results, trigger_results),
        timing_band=determine_band(window_active, exact_timing),
        confidence=compute_confidence(dasha_results, transit_results,
                                      trigger_results, structural_confidence),
        crisis_type=crisis_type,
        fired_rules=collect_fired_rules(all_results),
    )
```

---

## Rule Counts

| Layer | File | Rules | Status |
|-------|------|-------|--------|
| Dasha | dasha_rules.json | 8 | Active |
| Transit | transit_rules.json | 4 | Active |
| Fast Trigger | fast_trigger_rules.json | 3 | Active |
| Classical Pattern | classical_patterns.json | 8 | Active |
| Outcome/Quality | outcome_quality.json | 10 | Active |
| **TOTAL** | | **33** | Complete |

---

## Karakas & Houses

### Financial Crisis Karakas
| Planet | Role | Classical Reference |
|--------|------|-------------------|
| Saturn | Restriction, denial, chronic poverty, debt | BPHS Ch.14 |
| Rahu | Deception, speculation failure, illusion | BPHS Rahu Dasha |
| Mars | Aggression, litigation, impulsive destruction | BPHS Ch.42 |
| 8th Lord | Sudden destruction, bankruptcy, hidden collapse | BPHS Ch.48 |
| 6th Lord | Debt, enemies, chronic obligations | BPHS Ch.42 |
| 12th Lord | Loss, expenditure, drainage, hidden expenses | BPHS Ch.42 |

### Financial Crisis-Related Houses
| House | Signification |
|-------|--------------|
| 2nd | Savings, accumulated wealth, family resources (primary target) |
| 6th | Debt, obligations, enemies, litigation (crisis source) |
| 8th | Sudden events, destruction, bankruptcy, hidden losses (crisis trigger) |
| 11th | Income, gains, fulfillment (disrupted during crisis) |
| 12th | Expenditure, loss, drainage, foreign losses (crisis expression) |

---

## Relationship to Other Event Packs

This financial crisis pack follows the identical architecture as:
- `rules/domains/property/vehicle_purchase_and_vehicle_ownership/` — vehicle timing
- `rules/domains/property/property_purchase_and_house_acquisition/` — real estate timing
- `rules/domains/finance/ancestral_property_and_inheritance/` — inheritance timing
- `rules/domains/medical/surgery_and_medical_events/` — medical timing
- `rules/domains/relocation/foreign_settlement/` — relocation timing

Same engine, same 5-layer logic, different domain-specific rules.

---

## Next Steps

1. **Rules populated** — 33 rules across all 5 layers (8+4+3+8+10)
2. **Implement financial_crisis_evaluator.py** following vehicle_purchase_evaluator.py pattern
3. **Calibrate** with known financial crisis dates (feedback loop)
4. **Connect to interpreter** (create financial crisis interpreter)
