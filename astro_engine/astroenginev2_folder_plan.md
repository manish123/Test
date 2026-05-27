# AstroEngine V2 — Portable Folder Plan

## Proposed Structure

```
astro_engine_v2/
├── __init__.py                          ← Package root (new, minimal)
├── main.py                              ← Legacy entry point
├── requirements.txt                     ← Pip dependencies
│
├── api_bridges/                         ← External consumer entry points
│   ├── __init__.py
│   ├── timing_bridge.py                 ← Platform/timing layer calls this
│   └── personality_bridge.py            ← Profile layer calls this
│
├── astronomy/                           ← Layer A — Pure ephemeris
│   ├── __init__.py
│   ├── engine_base.py                   ← Swiss Ephemeris wrapper
│   ├── config.py                        ← Versioned config loader
│   ├── birth_data.py
│   ├── ephemeris.py
│   ├── planets.py
│   └── utils.py
│
├── features/                            ← Layer B — Classical features
│   ├── __init__.py
│   ├── dasha.py                         ← Vimshottari dasha periods
│   ├── dignity.py                       ← Sign lords, planetary status
│   ├── nakshatra.py                     ← Nakshatra computation
│   ├── houses.py                        ← House system
│   ├── ashtakavarga.py
│   ├── chara_dasha.py
│   ├── combustion.py
│   ├── divisional.py
│   ├── panchang.py
│   ├── planet_builder.py
│   ├── planet_enrichment.py
│   ├── planetary_calculator.py
│   ├── planetary_positions.py
│   ├── rahu_ketu.py
│   ├── shadbala.py
│   ├── time_decay.py
│   ├── transit.py
│   ├── vimsopaka.py
│   └── yogini.py
│
├── rules/                               ← Layer C — Interpretive rules
│   ├── __init__.py
│   ├── evaluator_base.py                ← Shared infrastructure (BaseChartState, BaseTransitState)
│   ├── multi_evaluator_runner.py        ← Cross-domain timeline scanner
│   ├── activation_intelligence.py       ← Density-based temporal scoring
│   ├── temporal_aggregator.py           ← Multi-resolution rollups
│   │
│   ├── marriage_evaluator.py            ← 18 domain evaluators
│   ├── childbirth_evaluator.py
│   ├── career_evaluator.py
│   ├── career_authority_evaluator.py
│   ├── business_evaluator.py
│   ├── relocation_evaluator.py
│   ├── foreign_migration_evaluator.py
│   ├── property_evaluator.py
│   ├── property_purchase_evaluator.py
│   ├── parent_loss_evaluator.py
│   ├── medical_evaluator.py
│   ├── fame_evaluator.py
│   ├── financial_crisis_evaluator.py
│   ├── vehicle_purchase_evaluator.py
│   ├── wealth_evaluator.py
│   ├── social_network_evaluator.py
│   ├── creative_output_evaluator.py
│   ├── litigation_evaluator.py
│   │
│   ├── event_engine.py                  ← 40+ event scoring
│   ├── event_ontology.py
│   ├── event_registry.py
│   ├── yoga_engine.py
│   ├── governance.py
│   ├── personality_engine.py
│   ├── state_engine.py
│   ├── argala.py
│   ├── arudha.py
│   ├── aspects.py
│   ├── avastha.py
│   ├── badhakesh.py
│   ├── graha_yuddha.py
│   ├── kakshya.py
│   ├── longevity.py
│   ├── maraka.py
│   ├── moorthy.py
│   ├── multi_planet.py
│   ├── nakshatra_weight.py
│   ├── neechabhanga.py
│   ├── rasi_drishti.py
│   ├── retrograde.py
│   ├── sade_sati.py
│   ├── sbc.py
│   ├── vedha.py
│   │
│   ├── symbolic/                        ← Layer C1 — Universal symbolic states
│   │   ├── __init__.py
│   │   └── planetary_conditions.py
│   │
│   └── domains/                         ← Layer C2 — Domain interpreters + JSON rules
│       ├── __init__.py
│       ├── base.py
│       ├── registry.py
│       ├── trading/
│       ├── career/
│       ├── relationship/
│       ├── health/
│       ├── spirituality/
│       ├── general_life/
│       ├── business/
│       ├── medical/
│       ├── property/
│       ├── relocation/
│       ├── finance/
│       ├── family/
│       └── status/
│
├── decisions/                           ← Layer D — Scoring & governance
│   ├── __init__.py
│   ├── confidence.py
│   ├── confidence_calibration.py
│   ├── decision_engine.py
│   ├── feedback.py
│   ├── normalization.py
│   ├── priority.py
│   ├── risk_engine.py
│   └── trading_gate.py
│
├── contracts/                           ← Typed data boundaries
│   ├── __init__.py
│   ├── astronomy_result.py
│   ├── decision_result.py
│   ├── engine_snapshot.py
│   ├── feature_result.py
│   ├── rule_result.py
│   └── symbolic_result.py
│
├── pipeline/                            ← Orchestration (typed pipeline)
│   ├── __init__.py
│   ├── astronomy_pipeline.py
│   ├── feature_pipeline.py
│   ├── rule_pipeline.py
│   └── decision_pipeline.py
│
├── symbolic/                            ← Symbolic intelligence (10A/10B)
│   ├── __init__.py
│   ├── symbolic_state_engine.py         ← Master aggregator
│   ├── coherent_state_builder.py        ← Phase 10B orchestrator
│   ├── archetype_engine.py
│   ├── archetype_prioritizer.py
│   ├── arbitration_engine.py
│   ├── coherence_engine.py
│   ├── lifecycle_engine.py
│   ├── narrative_engine.py
│   ├── narrative_ranker.py
│   ├── planetary_behavior_engine.py
│   ├── prompt_context_builder.py
│   ├── registry_loader.py
│   └── semantic_compressor.py
│
├── orchestration/                       ← API payload builders
│   ├── __init__.py
│   ├── personality_api_adapter.py
│   ├── timing_api_adapter.py
│   ├── career_api_adapter.py
│   ├── context_contracts.py
│   ├── context_router.py
│   ├── payload_builder.py
│   ├── prompt_sections.py
│   └── token_budget.py
│
└── configs/                             ← Runtime configuration data
    ├── v2.0.0.yaml                      ← Master config
    ├── scoring_profiles/
    │   ├── canonical.yaml
    │   ├── career.yaml
    │   ├── finance.yaml
    │   ├── general_life.yaml
    │   ├── health.yaml
    │   ├── relationship.yaml
    │   ├── spirituality.yaml
    │   └── trading.yaml
    └── symbolic/
        ├── arbitration_rules.json
        ├── business_archetypes.json
        ├── causal_narratives.json
        ├── lifecycle_transitions.json
        └── planetary_behaviors.json
```

---

## Interface Contract (Minimal Coupling)

The production repo only needs to know these 4 functions:

```python
# Timing layer
from astro_engine_v2.api_bridges.timing_bridge import get_timing_data
result = get_timing_data({"date": dt, "lat": 21.2, "lon": 81.4}, eval_date, "career")

# Profile layer
from astro_engine_v2.api_bridges.personality_bridge import get_personality_data
result = get_personality_data({"date": dt, "lat": 21.2, "lon": 81.4})

# Symbolic context (for LLM injection)
from astro_engine_v2.orchestration.timing_api_adapter import build_timing_context
ctx = build_timing_context({"date": dt, "lat": 21.2, "lon": 81.4}, eval_date)

# Past-event prediction
from astro_engine_v2.rules.activation_intelligence import build_activation_profile
profile = build_activation_profile(birth_dt, lat, lon, alt, "marriage", center_date)
```

---

## Migration Steps

1. **Copy** the entire `astro_engine/` folder to production as `astro_engine_v2/`
2. **Add** a root `__init__.py` with version info
3. **Install** dependencies: `pip install pyswisseph numpy pyyaml python-dateutil`
4. **Update** production imports from `astro_engine` → `astro_engine_v2`
5. **Remove** optional files (tests/, docs/, *.md, legacy scripts)

---

## What to Exclude (not needed in production)

| Path | Reason |
|------|--------|
| `tests/` | Test-only benchmarks and fixtures |
| `docs/` | Documentation (keep in repo, not in deployed package) |
| `*.md` (in root) | Architecture docs |
| `run_test.py` | Dev utility |
| `verify_drik.py` | Dev utility |
| `marriage_analysis.py` | Legacy standalone script |
| `guideline_for_marriage.txt` | Reference text |
| `__pycache__/` | Bytecode cache |
| `.pytest_cache/` | Test cache |

---

## Safety Checklist

| Check | Status |
|-------|--------|
| Zero external file dependencies | ✓ (no .env, no DB, no API calls) |
| All imports are internal | ✓ (only pip packages + self-references) |
| No sys.path hacks needed if installed as package | ✓ (add root __init__.py) |
| Configs are relative to module root | ✓ (Path(__file__).parent patterns) |
| No mutable global state | ✓ (config cached but read-only) |
| Deterministic for same inputs | ✓ (pure computation) |
| Thread-safe | ⚠️ (swisseph is not thread-safe — use process isolation) |

---

## Size Estimate

| Category | Files | Approx Size |
|----------|-------|-------------|
| Python modules | ~95 | ~250 KB |
| JSON rule data | ~120 | ~400 KB |
| YAML configs | ~10 | ~30 KB |
| **Total** | **~225** | **~680 KB** |

The entire engine fits in under 1 MB.
