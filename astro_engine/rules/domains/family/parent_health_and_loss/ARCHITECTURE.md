# Parent Health & Loss Rules — 5-Layer Semantic Architecture

## Why This Architecture?

Parental health and loss prediction is NOT a single question.
It is **5 fundamentally different semantic questions** asked in sequence:

| Layer | File | Question | Timing Precision |
|-------|------|----------|-----------------|
| 1. Dasha | `dasha_rules.json` | **Is parental loss possible now?** | Broad (years) |
| 2. Transit | `transit_rules.json` | **Is the parental crisis window active?** | Medium (months) |
| 3. Fast Trigger | `fast_trigger_rules.json` | **Is this the exact event timing?** | Exact (days/weeks) |
| 4. Classical Pattern | `classical_patterns.json` | **Is there structural parental affliction?** | None (structural) |
| 5. Outcome/Quality | `outcome_quality.json` | **What kind of parental event?** | None (qualitative) |

---

## Total Rule Count: 38 Rules

- **Layer 1 (Dasha):** 9 rules — planetary period gates
- **Layer 2 (Transit):** 9 rules — slow planet activation  
- **Layer 3 (Fast Trigger):** 5 rules — exact timing pinpointers
- **Layer 4 (Classical Pattern):** 8 rules — structural natal promise
- **Layer 5 (Outcome/Quality):** 8 rules — event classification

---

## The 5-Pass Evaluation Flow

```
+-----------------------------------------------------------+
|  LAYER 1: DASHA (Gate)                                    |
|  Question: "Is this planetary period parent-loss-active?"  |
|  Key: Ketu-Saturn, Saturn-Rahu, Venus-Sun, Rahu-Moon,     |
|       Jupiter-Moon, Saturn-Moon, Mercury-Jupiter,          |
|       4th lord navamsa dispositor, 1st/4th/9th lords      |
|  If NO dasha rule fires -> STOP. Parental loss not now.   |
|  If YES -> opens BROAD WINDOW (1-3 years)                 |
+---------------------------+-------------------------------+
                            | window open
                            v
+-----------------------------------------------------------+
|  LAYER 2: TRANSIT (Activation)                            |
|  Question: "Are planets activating parental points?"      |
|  Saturn on Sun/Moon (Ashtakavarga), malefics 4th from Sun,|
|  Sun trine D9 lords, sensitive points (Mandi, Yamakantaka)|
|  If YES -> narrows to MEDIUM WINDOW (1-6 months)          |
+---------------------------+-------------------------------+
                            | window narrowed
                            v
+-----------------------------------------------------------+
|  LAYER 3: FAST TRIGGER (Pinpoint)                         |
|  Question: "What is the exact event timing?"              |
|  Moon transit Sun's D9 dispositor, Gandanta pada transit, |
|  Mars 4th from Sun detonator, Sun in Moon's D9 sign      |
|  If YES -> narrows to EXACT WINDOW (days to weeks)        |
+---------------------------+-------------------------------+
                            | timing pinpointed
                            v
+-----------------------------------------------------------+
|  LAYER 4: CLASSICAL PATTERN (Structural Modifier)         |
|  Question: "Does the birth chart confirm parental loss?"  |
|  Moon aspected by 3 malefics, malefics 6/12 or 4/10,     |
|  Sun Papa Kartari 7th, malefics 4th from Moon,            |
|  Sun-Saturn 12th + Moon 7th, Pitru Shapa                  |
|  MODIFIES confidence, does not create windows             |
+---------------------------+-------------------------------+
                            | confidence adjusted
                            v
+-----------------------------------------------------------+
|  LAYER 5: OUTCOME/QUALITY (Classification)                |
|  Question: "What kind of parental event?"                 |
|  Mode: father_death / mother_death / separation /         |
|        emotional_distance / sudden_crisis / abandonment   |
|  Quality: death / chronic / sudden / emotional            |
|  CLASSIFIES the event, never affects timing               |
+-----------------------------------------------------------+
```

---

## Key Planetary Significators

### Father Axis
- **Sun** — Natural karaka (significator) of father
- **9th house** — Father's house (primary)
- **10th house** — Father's house (alternate, Jataka Parijata)
- **Saturn** — Natural maraka (death-dealer) for father
- **4th from Sun** — Death house of father (8th from 9th)

### Mother Axis  
- **Moon** — Natural karaka (significator) of mother
- **4th house** — Mother's house (primary)
- **4th from Moon** — Mother's house in Chandra Lagna
- **Saturn** — Natural maraka for mother (also)
- **Ketu** — Separative planet, emotional distance from mother

### Death/Loss Indicators
- **8th house** — House of death and transformation
- **12th house** — House of loss and separation
- **2nd/7th houses** — Maraka sthanas (killing houses)
- **Mandi/Gulika** — Sub-planet of death timing
- **Yamakantaka** — Sub-planet of Yama (death god)
- **Gandanta points** — Karmic dissolution junctions

---

## Key Design Principles

### 1. Sequential Narrowing (Not Parallel Scoring)
- Layer 1 must fire BEFORE Layer 2 is even evaluated
- Layer 3 only matters if Layer 2 has already narrowed
- This prevents false positives from isolated triggers

### 2. Separation of Timing vs. Quality
- Layers 1-3: **WHEN** will the parental event happen?
- Layer 4: **Structural confirmation** (does chart have parental affliction?)
- Layer 5: **WHAT KIND** of event? (death vs separation vs emotional distance)
- Never mix these — timing is independent of quality

### 3. Father vs. Mother Differentiation
- Father events are primarily tracked through: Sun, 9th house, 10th house
- Mother events are primarily tracked through: Moon, 4th house, 4th from Moon
- Some rules indicate "both parents" (Ketu-Saturn, Saturn-Rahu)

### 4. Provenance Tracking
- Every rule cites its classical source (BPHS, Jataka Parijata, Hora Sara, Phaladeepika)
- No "invented" rules — all derived from recognized Jyotish texts
- Calibration overlay handles empirical adjustments without touching source rules

### 5. Sensitivity & Ethics
- Parental death is the MOST sensitive prediction domain in astrology
- Engine NEVER presents predictions as certainties
- Always frame as "periods of heightened concern"
- Multi-layer confirmation required before any output
- Calibration overlay includes safety_notes for delivery guidance

---

## Sources

| Source | Rules Derived |
|--------|--------------|
| Brihat Parashara Hora Shastra (BPHS) | 22 rules |
| Jataka Parijata | 5 rules |
| Hora Sara | 3 rules |
| Phaladeepika | 3 rules |
| Combined/Mathematical techniques | 5 rules |

---

## Calibration Status

- **Current version:** 0.1.0 (initial creation)
- **Validated cases:** 0 (pending empirical validation)
- **Confidence level:** Theoretical (classical text-derived)
- **Next milestone:** Validate against 10+ known parental loss events
