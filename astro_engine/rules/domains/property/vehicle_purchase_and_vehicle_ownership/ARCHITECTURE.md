# Vehicle Purchase & Vehicle Ownership Rules — 5-Layer Semantic Architecture

## Why This Architecture?

Vehicle purchase prediction is NOT a single question.
It is **5 fundamentally different semantic questions** asked in sequence:

| Layer | File | Question | Timing Precision |
|-------|------|----------|-----------------|
| 1. Dasha | `dasha_rules.json` | **Is vehicle purchase possible now?** | Broad (years) |
| 2. Transit | `transit_rules.json` | **Is the vehicle window active?** | Medium (months) |
| 3. Fast Trigger | `fast_trigger_rules.json` | **Is this the exact timing?** | Exact (days/weeks) |
| 4. Classical Pattern | `classical_patterns.json` | **Is there a structural vehicle yoga?** | None (structural) |
| 5. Outcome/Quality | `outcome_quality.json` | **What kind of vehicle event?** | None (qualitative) |

---

## The 5-Pass Evaluation Flow

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: DASHA (Gate)                                  │
│  Question: "Is this planetary period vehicle-active?"    │
│  Key: Venus karaka, 4th lord, Saturn-Venus, Rahu-Venus  │
│  If NO dasha rule fires → STOP. Vehicle not now.        │
│  If YES → opens BROAD WINDOW (1-3 years)                │
└────────────────────────┬────────────────────────────────┘
                         │ window open
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: TRANSIT (Activation)                          │
│  Question: "Are planets activating vehicle houses?"     │
│  Lagna lord through 4th, Jupiter trine 4th lord,        │
│  Venus karaka conjunct Lagna/Moon lord, benefic 4th     │
│  If YES → narrows to MEDIUM WINDOW (1-6 months)         │
└────────────────────────┬────────────────────────────────┘
                         │ window narrowed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: FAST TRIGGER (Pinpoint)                       │
│  Question: "What is the exact timing?"                  │
│  SBC benefic transit on Janma Nakshatra + name          │
│  consonants alignment in Sarvatobhadra Chakra           │
│  If YES → narrows to EXACT WINDOW (days to weeks)       │
└────────────────────────┬────────────────────────────────┘
                         │ timing pinpointed
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: CLASSICAL PATTERN (Structural Modifier)       │
│  Question: "Does the birth chart confirm vehicle yoga?" │
│  4th-11th exchange, benefic 4th, Moon/Venus + 4th lord  │
│  in Lagna, Jupiter association, Vargottama patterns     │
│  MODIFIES confidence, does not create windows           │
└────────────────────────┬────────────────────────────────┘
                         │ confidence adjusted
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: OUTCOME/QUALITY (Classification)              │
│  Question: "What kind of vehicle event?"                │
│  Mode: luxury/commercial/transport_assets/multiple      │
│  Quality: stable/unstable/debt_heavy/prosperous         │
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
- Layers 1-3: **WHEN** will the vehicle purchase happen?
- Layer 4: **Structural confirmation** (does chart have vehicle yoga?)
- Layer 5: **WHAT KIND** of vehicle event? (luxury vs commercial vs debt-heavy)
- Never mix these — a purchase still happens on time regardless of quality

### 3. Provenance Tracking
Every rule carries `source_text` with:
- `work_name`: Classical text (BPHS, Phaladeepika, Jataka Parijata, Nirayana System, etc.)
- `chapter`, `verse`, `page`: Exact location
- `quote`: Verbatim text

### 4. Domain Isolation (C1/C2 Split)
- Rules in this directory are domain-specific policies (C2 layer)
- They consume domain-neutral symbolic state from `rules/symbolic/` (C1 layer)
- Vehicle rules NEVER modify symbolic state — read-only consumers
- Vehicle rules NEVER leak into medical, career, or relocation domains

### 5. Calibration-Ready
- Each rule has `status`: active / experimental / calibration / deprecated
- Each rule has `interpretation.confidence`: source-level confidence (0-1)
- `calibration_overlay.json` adjusts weights WITHOUT touching classical rules
- Future ML calibration operates per-rule, per-domain

---

## Vehicle Purchase-Specific Semantic Layers

### Layer 1: Dasha (When is vehicle purchase possible?)
Key planets for vehicle purchase:
- **Venus** — Vahana Karaka (natural significator of vehicles, luxuries, conveyances)
- **4th Lord** — ruler of vehicles, home, comforts, immovable/movable assets
- **Jupiter** — expansion, wealth growth, large purchases
- **Saturn** — structures, heavy vehicles, endurance
- **Rahu** — intensification of material desires, foreign vehicles
- **Moon** — comfort, movement, emotional satisfaction from transport

Key Dasha Combinations (9 rules):
1. Venus Mahadasha — primary vehicle karaka gate
2. Rasi Dasha with Jupiter in 4th — sign-based vehicle activation
3. 4th Lord Dasha (dignified + Lagna connection) — direct vehicle ruler
4. Jupiter-Ketu — sudden luxury vehicle acquisition
5. Saturn-Venus — luxury conveyance from Saturnian discipline
6. Saturn-Mars — commercial/heavy transport assets
7. Jupiter-Sun — status elevation vehicle
8. Moon-Mercury — mobility and commercial success vehicles
9. Rahu-Venus — peak materialistic luxury vehicle period

### Layer 2: Transit (Is the vehicle window active?)
Key transits (4 rules):
1. Lagna lord transit through 4th or trine to 4th lord — self enters vehicle house
2. Jupiter trine 4th lord Navamsa position — deep vehicle activation
3. Venus (Vahana Karaka) conjunct natal Lagna lord or Moon lord — karaka activation
4. Benefic planet transit through/aspecting 4th house or lord — general vehicle support

### Layer 3: Fast Trigger (Exact day/week)
Key triggers (1 rule):
1. SBC (Sarvatobhadra Chakra) benefic transit on Janma Nakshatra + name consonants

### Layer 4: Classical Pattern (Natal promise — does chart support vehicle yoga?)
Key patterns (8 rules):
1. 4th-11th Parivartana Yoga — exchange of conveyances and gains
2. Benefic in/aspecting 4th house or lord — happiness from vehicles
3. 4th lord + Mercury in benefic Navamsa — commerce + vehicle combination
4. Moon + 4th lord in Lagna — personal attachment to vehicle
5. Venus + 4th lord in Lagna — royal/luxury vehicle yoga
6. Jupiter + 4th lord — enclosed, protected luxury vehicle
7. 4th lord + Jupiter + Venus in 9th — multiple vehicles yoga
8. Vargottama Lagna lord + 9th lord — golden vehicle / raja yoga

### Layer 5: Outcome/Quality (What kind of vehicle event?)
Classifications (8 rules):
1. 4th lord in Dusthana debilitated — defective/unstable vehicle
2. 4th lord + Jupiter + Venus in 9th — multiple vehicles fleet
3. 4th lord + Jupiter — luxury enclosed vehicle (SUV/sedan)
4. 4th lord + Venus in Lagna — elite luxury vehicle (elephant class)
5. 11th from 6th activation — debt-financed vehicle (car loan)
6. Vargottama raja yoga — golden/ultra-luxury custom vehicle
7. Malefic 4th house without benefic — losses and repeated expenses
8. Sun + Moon + Jupiter in 9th — transport prosperity and richness

---

## File Layout

```
rules/domains/property/vehicle_purchase_and_vehicle_ownership/
├── ARCHITECTURE.md                       # This document
├── vehicle_purchase_rule.schema.json     # Validation schema
├── dasha_rules.json                      # Layer 1: Planetary period gates (9 rules)
├── transit_rules.json                    # Layer 2: Slow planet activation (4 rules)
├── fast_trigger_rules.json               # Layer 3: Fast planet exact timing (1 rule)
├── classical_patterns.json               # Layer 4: Structural birth chart patterns (8 rules)
├── outcome_quality.json                  # Layer 5: Vehicle quality classification (8 rules)
├── calibration_schema.json               # Schema for calibration overlay
└── calibration_overlay.json              # Empirical tuning (Layer 3 calibration)
```

---

## How the Rule Engine Evaluates

```python
def evaluate_vehicle_purchase_timing(chart_state, transit_state, dasha_state):
    """
    5-pass sequential evaluation.
    Each layer gates the next.
    """
    # Pass 1: Dasha gate
    dasha_results = evaluate_rules(dasha_rules, dasha_state)
    if not any_fired(dasha_results):
        return VehicleResult(status="NOT_NOW", confidence=0)

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
    vehicle_type = classify_outcome(quality_results)

    # Compose final result
    return VehicleResult(
        status=determine_status(dasha_results, transit_results, trigger_results),
        timing_band=determine_band(window_active, exact_timing),
        confidence=compute_confidence(dasha_results, transit_results,
                                      trigger_results, structural_confidence),
        vehicle_type=vehicle_type,
        fired_rules=collect_fired_rules(all_results),
    )
```

---

## Rule Counts

| Layer | File | Rules | Status |
|-------|------|-------|--------|
| Dasha | dasha_rules.json | 9 | Active |
| Transit | transit_rules.json | 4 | Active |
| Fast Trigger | fast_trigger_rules.json | 1 | Active |
| Classical Pattern | classical_patterns.json | 8 | Active |
| Outcome/Quality | outcome_quality.json | 8 | Active |
| **TOTAL** | | **30** | Complete |

---

## Karakas & Houses

### Vehicle Purchase Karakas
| Planet | Role | Classical Reference |
|--------|------|-------------------|
| Venus | Vahana Karaka — vehicles, luxuries, conveyances, comforts | Phaladeepika v.12 |
| Jupiter | Expansion, prosperity, large/enclosed vehicles | BPHS Ch.14 |
| Moon | Comfort, movement, emotional satisfaction in transit | BPHS Ch.3 |
| Mercury | Commerce, travel, communication vehicles | Jataka Parijata v.97 |
| Saturn | Heavy/commercial vehicles, durability, structures | BPHS Ch.14 |
| Mars | Kinetic energy, engineering, mechanical vehicles | BPHS v.50-52 |

### Vehicle-Related Houses
| House | Signification |
|-------|--------------|
| 4th | Vehicles, conveyances, movable assets, comforts (primary) |
| 1st | Self — vehicle attached to native's identity |
| 9th | Fortune, luck, dharma — supports vehicle prosperity |
| 11th | Gains — profits and fulfillment of vehicle desires |
| 6th | Debt — car loans, financing, EMI obligations |

---

## Sensitive Points

1. **Vehicle Acquisition Axis**: Venus longitude + 4th lord longitude (sum % 360)
2. **Transport Comfort Axis**: Moon longitude + 4th lord longitude (sum % 360)

---

## Relationship to Other Event Packs

This vehicle purchase pack follows the identical architecture as:
- `rules/domains/property/property_purchase_and_house_acquisition/` — real estate timing
- `rules/domains/finance/ancestral_property_and_inheritance/` — inheritance timing
- `rules/domains/medical/surgery_and_medical_events/` — medical timing
- `rules/domains/relocation/foreign_settlement/` — relocation timing
- `rules/domains/status/fame_and_public_recognition/` — fame timing

Same engine, same 5-layer logic, different domain-specific rules.

---

## Next Steps

1. **Rules populated** — 30 rules across all 5 layers
2. **Implement vehicle_purchase_evaluator.py** following property_purchase_evaluator.py pattern
3. **Calibrate** with known vehicle purchase dates (feedback loop)
4. **Connect to interpreter** (create vehicle purchase interpreter)
