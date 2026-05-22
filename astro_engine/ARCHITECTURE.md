# Astro Engine — Architecture (v2.0)

## The Boundary Rule

```
astronomy  → depends on NOTHING above it
features   → depends only on astronomy
rules      → depends on astronomy + features
decisions  → depends on everything below it
main.py    → orchestrates only, never interprets
```

## The Semantic Rule

```
astronomy = computation    (where is the body?)
features  = derived facts  (what sign? what nakshatra? what dignity?)
rules     = meaning        (what does this combination mean?)
decisions = action         (what do we do about it?)
```

## Layer Structure

```
astro_engine/
├── astronomy/              Layer A — Pure computation
│   ├── engine_base.py          Swiss Ephemeris: positions, speeds, retro, cusps
│   ├── ephemeris.py            Ayanamsa config (reads from configs/v2.0.0.yaml)
│   ├── utils.py                normalize_lon()
│   ├── planets.py              Planet ID constants
│   ├── birth_data.py           Input data
│   └── config.py               Versioned YAML config loader
│
├── features/               Layer B — Classical feature extraction
│   ├── dignity.py              SIGN_LORDS, get_planet_status() — pure data + classification
│   ├── planet_builder.py       Build planet dict from longitude
│   ├── planet_enrichment.py    Enrich raw positions with nakshatra + dignity + relationship
│   ├── nakshatra.py            Longitude → nakshatra (pure division)
│   ├── houses.py               Cusps → planet-in-house (calls Layer A for cusps)
│   ├── panchang.py             Tithi/karana/yoga scoring (pure math from longitudes)
│   ├── ashtakavarga.py         BAV/SAV computation
│   ├── vimsopaka.py            Vimsopaka bala
│   ├── dasha.py                Vimshottari dasha periods
│   ├── chara_dasha.py          Jaimini Chara dasha
│   ├── yogini.py               Yogini dasha
│   ├── transit.py              Double transit (Jupiter/Saturn) strength
│   ├── time_decay.py           Orb-based time decay probability
│   ├── divisional.py           D1/D2/D3/D7/D9/D10/D12/D60 signs
│   ├── shadbala.py             Six-fold planetary strength
│   ├── combustion.py           Sun proximity → damping factor
│   ├── rahu_ketu.py            Kala Sarpa detection, node aspects
│   └── planetary_calculator.py Composite enrichment API (Layer A + B combined)
│
├── rules/                  Layer C — Interpretive rules
│   ├── symbolic/           Layer C1 — UNIVERSAL SYMBOLIC STATES (domain-neutral)
│   │   ├── planetary_conditions.py
│   │   │     describe_dignity()         → neutral: "at peak expression"
│   │   │     describe_retrograde()      → neutral: "internalized expression"
│   │   │     describe_combustion()      → neutral: "merged with solar authority"
│   │   │     describe_kala_sarpa()      → neutral: "concentrated karmic channel"
│   │   │     describe_sade_sati()       → neutral: "restructuring pressure"
│   │   │     describe_chandrabala()     → neutral: "8th from Moon — transformation axis"
│   │   │     describe_moorthy()         → neutral: "iron receptivity"
│   │   │     build_symbolic_state()     → extracts full neutral snapshot
│   │   └── __init__.py
│   │
│   ├── domains/            Layer C2 — DOMAIN INTERPRETATION PROFILES
│   │   ├── base.py              BaseDomainInterpreter protocol
│   │   ├── registry.py          get_domain_interpreter(domain_name) dispatcher
│   │   ├── trading/             Capital preservation + execution timing
│   │   ├── career/              Professional growth + authority
│   │   ├── relationship/        Emotional connection + partnerships
│   │   ├── health/              Physical vitality + recovery
│   │   ├── spirituality/        Inner awareness + detachment
│   │   └── general_life/        Balanced multi-domain overview
│   │
│   ├── state_engine.py     Planet state processing (combustion, retro, graha yuddha)
│   ├── event_engine.py     40+ event scoring (EVENT_MAP)
│   ├── yoga_engine.py      Yoga detection (Mahapurusha, Dainya, Dhana, Bhanga)
│   ├── governance.py       Profile-based event filtering
│   ├── personality_engine.py  Personality rules (atmakaraka, guna, tattva)
│   └── ... (other rule modules)
│
├── decisions/              Layer D — Scoring & governance
│   ├── confidence.py           Confidence formula
│   ├── confidence_calibration.py  Post-hoc calibration
│   ├── decision_engine.py      Action generation
│   ├── trading_gate.py         3-level trading gate
│   ├── risk_engine.py          Risk aggregation
│   ├── normalization.py        Score normalization
│   ├── priority.py             Event ranking
│   └── feedback.py             PnL alignment
│
├── contracts/              Immutable typed boundaries
│   ├── astronomy_result.py     AstronomyResult (frozen dataclass)
│   ├── feature_result.py       FeatureResult (frozen dataclass)
│   ├── rule_result.py          RuleResult (frozen dataclass)
│   ├── decision_result.py      DecisionResult (frozen dataclass)
│   └── engine_snapshot.py      EngineSnapshot (versioned traceability)
│
├── pipeline/               Orchestration (calls stages in sequence)
│   ├── astronomy_pipeline.py   run_astronomy() → AstronomyResult
│   ├── feature_pipeline.py     run_features() → FeatureResult
│   ├── rule_pipeline.py        run_rules() → RuleResult
│   └── decision_pipeline.py    run_decisions() → DecisionResult
│
├── configs/
│   └── v2.0.0.yaml             Versioned config (ayanamsa, thresholds, weights)
│
└── main.py                 Entry point (orchestrates only, never interprets)
    ├── _run_single()           Legacy API (production, full logic)
    ├── run()                   Mode selector (A/B/C)
    └── run_pipeline()          v2.0 Pipeline API (typed, traced)
```

---

## The Domain Separation (C1 / C2 Split)

### The Problem It Solves

Trading-specific calibration logic was leaking into general life interpretation:

- "node crisis" → interpreted as "danger" everywhere (but in spirituality = karmic acceleration)
- "Chandrabala 8th" → "hard block" everywhere (but in relationships = deep emotional honesty)
- "Kala Sarpa" → "whipsaw risk" everywhere (but in career = focused ambition axis)

### The Solution

```
Layer C1 — Universal Symbolic States
  Describes WHAT IS HAPPENING. No judgment.
  "Saturn conjunct natal Moon = restructuring pressure on emotional foundations"

Layer C2 — Domain Interpretation Profiles
  Decides WHAT IT MEANS for a specific life area.
  Same state → different meaning depending on optimization goal.
```

### How It Works

```python
from rules.symbolic.planetary_conditions import build_symbolic_state
from rules.domains import get_domain_interpreter

# Step 1: Extract neutral symbolic state (same for everyone)
symbolic = build_symbolic_state(engine_result)

# Step 2: Apply domain-specific interpretation
trading_reading = get_domain_interpreter("trading").interpret(symbolic)
career_reading = get_domain_interpreter("career").interpret(symbolic)
spiritual_reading = get_domain_interpreter("spirituality").interpret(symbolic)
```

### Domain Comparison (same planetary state)

| Condition | Trading | Career | Spirituality |
|-----------|---------|--------|-------------|
| Kala Sarpa | whipsaw risk → REDUCE SIZE | focused ambition → USE IT | karmic acceleration → MEDITATE |
| Sade Sati peak | grinding losses → AVOID | restructuring → REBUILD | tapas → DEEPENING |
| Chandrabala 8th | DO NOT TRADE | low visibility day | excellent for past-life work |
| Dainya yoga | resources under stress | growth through adversity | karma yoga activation |
| Moorthy Loha | environment resists → FLAT | extra effort needed | n/a |
| Node crisis | unpredictable → STAY FLAT | unconventional paths opening | ancestral clearing |

### Available Domains

| Domain | Optimization Goal | Risk Sensitivity |
|--------|------------------|-----------------|
| `trading` | Capital preservation | HIGHEST — amplifies all risk signals |
| `career` | Professional growth | MODERATE — restructuring seen as opportunity |
| `relationship` | Emotional connection | MODERATE — testing seen as deepening |
| `health` | Physical vitality | HIGH — Mars/Sun dormancy = real concern |
| `spirituality` | Inner awareness | LOWEST — difficulty = opportunity |
| `general_life` | Balanced adaptation | NEUTRAL — describes without prescribing |

---

## Immutable Contracts

Every pipeline stage produces a frozen dataclass:

```
AstronomyResult  → raw coordinates, speeds, cusps (never changes)
FeatureResult    → dignities, nakshatras, dashas (deterministic)
RuleResult       → yogas, events, risks (interpretive)
DecisionResult   → confidence, risk, action (final)
EngineSnapshot   → version + hash + timestamp (traceability)
```

These prevent layer contamination at the data level.

---

## Configuration

Ayanamsa and all thresholds are externalized in `configs/v2.0.0.yaml`:

```yaml
ayanamsa: "LAHIRI"       # Change without touching code
```

To switch ayanamsa: edit one line. No code changes needed.

---

## The One Rule That Prevents All Future Drift

```
astronomy NEVER imports features
features NEVER imports rules
rules NEVER imports decisions
Only orchestration (pipeline/ and main.py) can see everything.
```

This one principle preserves the engine for years.
