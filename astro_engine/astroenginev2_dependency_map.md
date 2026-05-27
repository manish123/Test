# AstroEngine V2 — Dependency Map

## External Interface Points

The engine is called by 4 external layers:

| Layer | Entry Point | Function | Input | Output |
|-------|-------------|----------|-------|--------|
| **Platform** | `api_bridges/timing_bridge.py` | `get_timing_data(birth_data_dict, eval_date, domain)` | `{date, lat, lon}` + date + domain | `{decision, symbolic_state, domain_reading}` |
| **Profile** | `api_bridges/personality_bridge.py` | `get_personality_data(birth_data_dict, domain)` | `{date, lat, lon}` | `{personality_profile, symbolic_state, domain_reading}` |
| **Timing** | `orchestration/timing_api_adapter.py` | `build_timing_context(birth_data_dict, eval_date)` | `{date, lat, lon}` + date | timing_context payload (≤400 tokens) |
| **UI/LLM** | `orchestration/personality_api_adapter.py` | `build_personality_context(birth_data_dict, eval_date)` | `{date, lat, lon}` + date | personality_context payload (≤600 tokens) |

Additional entry points for past-event prediction:
- `rules/multi_evaluator_runner.py` → `evaluate_all_domains()`, `scan_timeline()`
- `rules/activation_intelligence.py` → `build_activation_profile()`
- `rules/temporal_aggregator.py` → `build_event_prediction()`

---

## Internal Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ ENTRY POINTS                                                     │
│ api_bridges/ | orchestration/ | multi_evaluator_runner            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│ PIPELINE (orchestration only, never interprets)                   │
│ pipeline/astronomy_pipeline → feature_pipeline → rule_pipeline   │
│ → decision_pipeline                                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│ LAYER D — DECISIONS (scoring, confidence, risk, normalization)    │
│ decisions/confidence.py | risk_engine.py | decision_engine.py    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│ LAYER C — RULES (interpretive logic, evaluators, domains)        │
│ rules/evaluator_base.py | *_evaluator.py (×18) | event_engine   │
│ rules/symbolic/ (C1) | rules/domains/ (C2)                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│ LAYER B — FEATURES (classical astrology transforms)              │
│ features/dasha.py | dignity.py | nakshatra.py | houses.py | etc  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│ LAYER A — ASTRONOMY (pure ephemeris computation)                 │
│ astronomy/engine_base.py | config.py | utils.py                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│ SYMBOLIC INTELLIGENCE (additive, never modifies scoring)         │
│ symbolic/ (10A/10B) — archetypes, lifecycle, narrative, coherence│
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│ CONFIGS + DATA                                                   │
│ configs/v2.0.0.yaml | scoring_profiles/*.yaml | symbolic/*.json  │
│ rules/domains/**/dasha_rules.json, transit_rules.json, etc.      │
└─────────────────────────────────────────────────────────────────┘
```

---

## External Pip Dependencies

| Package | Version | Purpose | Critical? |
|---------|---------|---------|-----------|
| `pyswisseph` | ≥2.10 | Swiss Ephemeris (planetary positions) | CRITICAL |
| `numpy` | ≥1.24 | Numerical computation | REQUIRED |
| `pyyaml` | ≥6.0 | Config loading (v2.0.0.yaml, scoring profiles) | REQUIRED |
| `python-dateutil` | ≥2.9 | `relativedelta` in temporal modules | REQUIRED |
| `pandas` | ≥2.0 | Data manipulation (some evaluators) | OPTIONAL (can be removed) |
| `julian` | ≥0.14 | Julian day utilities | OPTIONAL (pyswisseph has julday) |

---

## Zero External File Dependencies

- No `.env` references inside astro_engine/
- No external API calls (pure computation)
- No database connections
- No filesystem writes at runtime
- All `sys.path` manipulations are self-referencing

**astro_engine/ is fully self-contained. It has ZERO runtime dependencies on files outside its folder.**

---

## Data Flow for Each Consumer

### Platform Layer (timing_bridge)
```
birth_data_dict → run_astronomy() → run_features() → run_rules() → run_decisions()
                                                          ↓
                                              build_symbolic_state() → get_domain_interpreter()
                                                          ↓
                                              {decision, symbolic_state, domain_reading}
```

### Profile Layer (personality_bridge)
```
birth_data_dict → run_astronomy() → run_features() → run_rules() → run_decisions()
                                                          ↓
                                              personality_profile + symbolic_state
```

### Timing Layer (timing_api_adapter)
```
birth_data_dict → BaseChartState → build_coherent_state() → route_context("timing_context")
                                                                    ↓
                                                          token-budgeted payload (≤400 tokens)
```

### UI/LLM Layer (personality_api_adapter)
```
birth_data_dict → BaseChartState → build_coherent_state() → route_context("personality_context")
                                                                    ↓
                                                          token-budgeted payload (≤600 tokens)
```

### Past-Event Prediction (activation_intelligence)
```
birth_data_dict → scan_rich_timeline() → compute_activation_density()
                                       → compute_momentum()
                                       → compute_layer_contributions()
                                       → compute_density_confidence()
                                       → build_activation_profile()
                                                    ↓
                                          ActivationProfile (band, peak, confidence, layers)
```
