# Property Purchase & House Acquisition Rules — 5-Layer Semantic Architecture

## Why This Architecture?

Property purchase prediction is NOT a single question.
It is **5 fundamentally different semantic questions** asked in sequence:

| Layer | File | Question | Timing Precision |
|-------|------|----------|-----------------|
| 1. Dasha | `dasha_rules.json` | **Is property purchase possible now?** | Broad (years) |
| 2. Transit | `transit_rules.json` | **Is the property window active?** | Medium (months) |
| 3. Fast Trigger | `fast_trigger_rules.json` | **Is this the exact timing?** | Exact (days/weeks) |
| 4. Classical Pattern | `classical_patterns.json` | **Is there a structural property yoga?** | None (structural) |
| 5. Outcome/Quality | `outcome_quality.json` | **What kind of property event?** | None (qualitative) |

---

## The 5-Pass Evaluation Flow

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: DASHA (Gate)                                  │
│  Question: "Is this planetary period property-active?"   │
│  Key: 4th lord, Mars-Jupiter, Saturn-Mars, Moon combos  │
│  If NO dasha rule fires → STOP. Property not now.       │
│  If YES → opens BROAD WINDOW (1-3 years)                │
└────────────────────────┬────────────────────────────────┘
                         │ window open
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: TRANSIT (Activation)                          │
│  Question: "Are planets activating property houses?"    │
│  Jupiter 4th/9th, Lagna lord through 4th,               │
│  Mars karaka conjunct Lagna/Moon lord                   │
│  If YES → narrows to MEDIUM WINDOW (1-6 months)         │
└────────────────────────┬────────────────────────────────┘
                         │ window narrowed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: FAST TRIGGER (Pinpoint)                       │
│  Question: "What is the exact timing?"                  │
│  SBC house entry, Lagna-4th lord conjunction,           │
│  Mars conjunct Lagna/Moon lord exact                    │
│  If YES → narrows to EXACT WINDOW (days to weeks)       │
└────────────────────────┬────────────────────────────────┘
                         │ timing pinpointed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: CLASSICAL PATTERN (Structural Modifier)       │
│  Question: "Does the birth chart confirm property yoga?"│
│  4th house residential comforts, Karakamsa patterns,    │
│  10th-4th lord mansions, 5th lord dignity, 9th-4th      │
│  MODIFIES confidence, does not create windows           │
└────────────────────────┬────────────────────────────────┘
                         │ confidence adjusted
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: OUTCOME/QUALITY (Classification)              │
│  Question: "What kind of property event?"               │
│  Mode: house_purchase/land/construction/luxury/invest   │
│  Quality: stable/unstable/profitable/debt/disputed      │
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
- Layers 1-3: **WHEN** will the property purchase happen?
- Layer 4: **Structural confirmation** (does chart have property yoga?)
- Layer 5: **WHAT KIND** of property event? (house vs land vs construction)
- Never mix these — a purchase still happens on time regardless of quality

### 3. Provenance Tracking
Every rule carries `source_text` with:
- `work_name`: Classical text (BPHS, Phaladeepika, Jataka Parijata, etc.)
- `chapter`, `verse`, `page`: Exact location
- `quote`: Verbatim text

### 4. Domain Isolation (C1/C2 Split)
- Rules in this directory are domain-specific policies (C2 layer)
- They consume domain-neutral symbolic state from `rules/symbolic/` (C1 layer)
- Property rules NEVER modify symbolic state — read-only consumers
- Property rules NEVER leak into medical, career, or relocation domains

### 5. Calibration-Ready
- Each rule has `status`: active / experimental / calibration / deprecated
- Each rule has `interpretation.confidence`: source-level confidence (0-1)
- `calibration_overlay.json` adjusts weights WITHOUT touching classical rules
- Future ML calibration operates per-rule, per-domain

---

## Property Purchase-Specific Semantic Layers

### Layer 1: Dasha (When is property purchase possible?)
Key planets for property purchase:
- **4th Lord** — ruler of property, home, land, immovable assets
- **Mars** — Bhumi Karaka (natural significator of land and property)
- **Moon** — home, comfort, emotional security, residence
- **Jupiter** — expansion, wealth growth, big investments
- **Saturn** — structures, construction, old buildings
- **Venus** — luxury property, beautiful homes, comforts

Key Dasha Combinations (10 rules):
1. 4th lord MD/AD — primary property gate
2. Moon-Moon — home and comfort period
3. Sun-Mars — house through authority/land
4. Mars-Jupiter — land acquisition expansion
5. Mars-Venus — village/luxury property
6. Saturn-Mars — construction and structure building
7. Moon-Venus — agricultural/comfort property
8. Mercury-Moon — construction through planning
9. Moon-Jupiter — property expansion/big home
10. Jupiter-Saturn — large lands/institutional property

### Layer 2: Transit (Is the property window active?)
Key transits (4 rules):
1. Jupiter transit 4th/9th from Lagna — property blessings activated
2. Lagna lord through 4th house — self enters property house
3. Jupiter trine 4th lord navamsa position — deep property activation
4. Mars (Bhumi Karaka) conjunct Lagna lord or Moon lord — land action

### Layer 3: Fast Trigger (Exact day/week)
Key triggers (3 rules):
1. SBC (Sarvatobhadra Chakra) benefic house entry on Janma Nakshatra
2. Lagna lord + 4th lord conjunction (exact within 3°)
3. Mars conjunct Lagna lord or Moon lord (exact within 2°)

### Layer 4: Classical Pattern (Natal promise — does chart support property yoga?)
Key patterns (7 rules):
1. 4th house with benefics — residential comforts from birth
2. 10th lord + 4th lord in kendras — mansions, large properties
3. Karakamsa with benefic in 4th — palatial residence
4. Karakamsa with Saturn in 4th — stone/cement house
5. Karakamsa with Mars in 4th — brick/clay house
6. 5th lord dignified + connected to 4th — lands through intelligence
7. 9th lord + 4th lord connection — wealth from fortune for property

### Layer 5: Outcome/Quality (What kind of property event?)
Classifications (8 rules):
1. Saturn drishti on 4th — unstable property
2. Mars in 4th — conflict over property
3. 4th lord with benefics — comfortable property acquisition
4. 11th from 6th house activation — mortgage/loan property
5. 5th from 4th activation — value appreciation
6. Malefic in 4th — destruction/renovation needed
7. Saturn-Mars neecha bhanga — unexpected property through hardship
8. Exalted Jupiter aspecting 4th — premium real estate

---

## File Layout

```
rules/domains/property/property_purchase_and_house_acquisition/
├── ARCHITECTURE.md                       # This document
├── property_purchase_rule.schema.json    # Validation schema
├── dasha_rules.json                      # Layer 1: Planetary period gates (10 rules)
├── transit_rules.json                    # Layer 2: Slow planet activation (4 rules)
├── fast_trigger_rules.json               # Layer 3: Fast planet exact timing (3 rules)
├── classical_patterns.json               # Layer 4: Structural birth chart patterns (7 rules)
├── outcome_quality.json                  # Layer 5: Property purchase classification (8 rules)
├── calibration_schema.json               # Schema for calibration overlay
└── calibration_overlay.json              # Empirical tuning (Layer 3 calibration)
```

---

## How the Rule Engine Evaluates

```python
def evaluate_property_purchase_timing(chart_state, transit_state, dasha_state):
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
| Dasha | dasha_rules.json | 10 | Active |
| Transit | transit_rules.json | 4 | Active |
| Fast Trigger | fast_trigger_rules.json | 3 | Active |
| Classical Pattern | classical_patterns.json | 7 | Active |
| Outcome/Quality | outcome_quality.json | 8 | Active |
| **TOTAL** | | **32** | Complete |

---

## Karakas & Houses

### Property Purchase Karakas
| Planet | Role | Classical Reference |
|--------|------|-------------------|
| Mars | Bhumi Karaka — land, real estate, physical property | BPHS Ch.3 |
| Moon | Home, comfort, emotional security, residence | BPHS Ch.3 |
| Venus | Luxury property, beautiful homes, comforts | BPHS Ch.3 |
| Jupiter | Expansion, wealth growth, big investments | BPHS Ch.3 |
| Saturn | Structures, construction, old buildings | BPHS Ch.3 |

### Property Houses
| House | Signification |
|-------|--------------|
| 4th | Property, home, land, immovable assets (primary) |
| 2nd | Accumulated wealth, family resources for purchase |
| 9th | Fortune, luck, father's support for property |
| 10th | Career property, commercial real estate |
| 11th | Gains, profits from property |

---

## Sensitive Points

1. **Property Axis**: 4th lord longitude + Mars longitude (sum % 360)
2. **Home Comfort Axis**: Moon longitude + 4th lord longitude (sum % 360)

---

## Relationship to Other Event Packs

This property purchase pack follows the identical architecture as:
- `rules/domains/finance/ancestral_property_and_inheritance/` — inheritance timing
- `rules/domains/medical/surgery_and_medical_events/` — medical timing
- `rules/domains/relocation/foreign_settlement/` — relocation timing
- `rules/domains/status/fame_and_recognition/` — fame timing
- `rules/domains/career/career_profession/` — career change timing

Same engine, same 5-layer logic, different domain-specific rules.

---

## Next Steps

1. ✅ **Rules populated** — 32 rules across all 5 layers
2. ✅ **Implement property_purchase_evaluator.py** following property_evaluator.py pattern
3. **Calibrate** with known property purchase dates (feedback loop)
4. **Connect to interpreter** (create property purchase interpreter)
