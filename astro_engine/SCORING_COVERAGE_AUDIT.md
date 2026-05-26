# Scoring Coverage Audit — Complete Primitive Inventory

## Executive Summary

All 28 scoring primitives are accounted for. The system is architecturally clean after Phase 9:
- **No contamination found** — trading-specific logic is correctly isolated
- **No duplication with conflicting values** — all primitives have a single source of truth
- **One structural gap identified** — domain evaluators use NONE of the canonical scoring primitives (tara, moorthy, yoga, shadbala, etc.) directly; they rely on transit/house-based scoring only
- **Profile system is fully wired** — all 18 evaluators load their domain profile

---

## Coverage Matrix

| # | Primitive | Type | Source of Truth | Pipeline | Evaluators | Interpreters | Status |
|---|-----------|------|-----------------|----------|------------|--------------|--------|
| 1 | nakshatra_list | Canonical | features/nakshatra.py | ✓ | 16/18 | — | ✅ Complete |
| 2 | nakshatra_lords | Canonical | features/nakshatra.py + evaluator_base.py | — | 18/18 | — | ✅ Complete |
| 3 | nakshatra_weight_overlay | Trading-empirical | rules/nakshatra_weight.py | ✓ (gated) | 0/18 | — | ✅ Correctly isolated |
| 4 | tara_formula | Canonical | rules/evaluator_base.py | ✓ | 0/18 | — | ⚠️ Not used by evaluators |
| 5 | tara_scores | Empirical | rules/evaluator_base.py | ✓ | 0/18 | — | ⚠️ Not used by evaluators |
| 6 | tara_planet_weights | Empirical | rules/evaluator_base.py | ✓ | 0/18 | — | ⚠️ Not used by evaluators |
| 7 | trade_decision_rulebook | Trading-specific | rules/evaluator_base.py | ✓ (gated) | 0/18 | — | ✅ Correctly isolated |
| 8 | moorthy_grading | Canonical+Empirical | rules/moorthy.py | ✓ | 0/18 | 6/7 | ✅ Complete |
| 9 | sign_lords | Canonical | features/dignity.py | ✓ | 18/18 | — | ✅ Complete |
| 10 | dignity_multipliers | Empirical | rules/state_engine.py | ✓ | 0/18 | — | ✅ Pipeline-only (correct) |
| 11 | exaltation/debilitation | Canonical (+ext) | features/dignity.py + 3 evaluators | — | 9/18 | — | ✅ Complete |
| 12 | aspect_constants | Canonical | rules/evaluator_base.py | — | 11/18 | — | ✅ Complete |
| 13 | dasha_periods | Canonical | features/dasha.py | ✓ | 11/18 | — | ✅ Complete |
| 14 | combustion | Canonical | features/combustion.py | ✓ | 0/18 | 1/7 | ✅ Pipeline-only (correct) |
| 15 | house_logic | Canonical | features/houses.py | ✓ | 0/18 | — | ✅ Pipeline-only (correct) |
| 16 | divisional_d9 | Canonical | features/divisional.py + evaluator_base.py | ✓ | 6/18 | — | ✅ Complete |
| 17 | panchang | Canonical | features/panchang.py | ✓ | 0/18 | — | ✅ Pipeline-only (correct) |
| 18 | panchang_risk_weight | Empirical | rules/evaluator_base.py | ✓ | 0/18 | — | ✅ Pipeline-only |
| 19 | vimsopaka | Canonical+Empirical | features/vimsopaka.py | ✓ | 0/18 | — | ✅ Pipeline-only (correct) |
| 20 | shadbala | Canonical | features/shadbala.py | — | 0/18 | — | ✅ Used via state_engine |
| 21 | argala | Canonical | rules/argala.py | ✓ | 0/18 | — | ✅ Pipeline-only |
| 22 | arudha | Canonical | rules/arudha.py | ✓ | 1/18 | — | ✅ Complete |
| 23 | yoga_engine | Canonical | rules/yoga_engine.py | ✓ | 0/18 | — | ✅ Pipeline-only |
| 24 | state_engine | Canonical+Empirical | rules/state_engine.py | ✓ | 0/18 | — | ✅ Pipeline-only |
| 25 | event_scoring_formula | Empirical | rules/event_engine.py | ✓ | 0/18 | — | ✅ Pipeline-only |
| 26 | confidence_formula | Empirical | decisions/confidence.py | ✓ | 0/18 | — | ✅ Pipeline-only |
| 27 | risk_engine | Empirical | decisions/risk_engine.py | ✓ | 0/18 | — | ✅ Pipeline-only |
| 28 | scoring_profiles | Domain-specific | configs/scoring_profiles/*.yaml | ✓ | 18/18 | — | ✅ Complete |

### Trading-Only Primitives (correctly isolated)

| Primitive | Location | Gating Mechanism |
|-----------|----------|-----------------|
| nakshatra_weight_overlay | rules/nakshatra_weight.py | Profile source check + use_trading_event_filter flag |
| trade_decision_rulebook | rules/evaluator_base.py | use_nakshatra_rulebook_bias flag |
| trading_event_filter | rules/evaluator_base.py | use_trading_event_filter flag |
| trading_gate | decisions/trading_gate.py | use_trading_gate flag + profile enabled check |
| risky_nakshatras | decisions/trading_gate.py | Inside trading_gate (double-gated) |
| confidence_calibration | decisions/confidence_calibration.py | calibration_config parameter (None = no-op) |

---

## Domain Interpreter Primitive Usage

| Interpreter | sade_sati | kala_sarpa | moorthy | chandrabala | combustion | dainya |
|-------------|-----------|------------|---------|-------------|------------|--------|
| trading | ✓ | ✓ | ✓ | ✓ | — | ✓ |
| career | ✓ | ✓ | ✓ | ✓ | — | ✓ |
| relationship | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| health | ✓ | — | ✓ | — | — | — |
| spirituality | ✓ | ✓ | — | ✓ | — | ✓ |
| general_life | ✓ | ✓ | ✓ | ✓ | — | ✓ |
| business | ✓ | ✓ | ✓ | ✓ | — | ✓ |

---

## Findings

### Finding 1: Domain evaluators don't use canonical scoring primitives directly

**Observation:** None of the 18 domain evaluators call tara, moorthy, yoga, shadbala, vimsopaka, argala, or panchang directly. They use only:
- Transit house positions (planet_houses_from_lagna/moon)
- Nakshatra offset calculations (Anga Gochara)
- Classical pattern detection (house lord placements)

**Assessment:** This is **architecturally correct**. The domain evaluators implement the 5-layer JSON-driven timing system (dasha → transit → fast trigger → classical → outcome). The canonical scoring primitives are used by the **main pipeline** (`rule_pipeline.py` → `decision_pipeline.py`) which produces the trading/general-life decision. The two systems are intentionally parallel.

**Status:** ✅ Not a bug. By design.

### Finding 2: Moorthy not used in spirituality interpreter

**Observation:** The spirituality interpreter does not reference moorthy grading.

**Assessment:** Intentional. Per DOMAIN_POLICY.md, spirituality has the LOWEST risk sensitivity — moorthy (which affects receptivity) is less relevant when difficulty = opportunity.

**Status:** ✅ Intentional omission.

### Finding 3: Health interpreter uses fewer primitives

**Observation:** Health interpreter only uses sade_sati and moorthy (not kala_sarpa, chandrabala, dainya).

**Assessment:** Likely incomplete — health should probably consider kala_sarpa (concentrated stress) and chandrabala (emotional/physical vulnerability). However, this is a domain interpretation decision, not a scoring bug.

**Status:** ⚠️ Potential enhancement (not a contamination issue).

### Finding 4: No primitive duplication with conflicting values

**Observation:** Every primitive has exactly one source of truth. No file redefines a canonical value with a different number.

**Status:** ✅ Clean.

### Finding 5: Scoring profiles fully wired

**Observation:** All 18 evaluators have `_SCORING_PROFILE` loaded. The pipeline resolves profiles based on `scoring_domain` config key.

**Status:** ✅ Complete.

---

## Contamination / Duplication Findings

| Check | Result |
|-------|--------|
| Trading-derived values in canonical modules | ✅ None found |
| Canonical values overridden by calibration | ✅ None found |
| Duplicate constants with different values | ✅ None found |
| Trading gate active in non-trading paths | ✅ Correctly gated |
| Nakshatra overlay in non-trading paths | ✅ Correctly gated (Phase 9) |
| Confidence calibration active by default | ✅ No-op when config=None |
| GOOD/BAD nakshatra lists in canonical modules | ✅ Only in rules/nakshatra_weight.py (trading) |
| RISKY_NAKSHATRA_SET in canonical modules | ✅ Only in decisions/trading_gate.py |

---

## Priority Items

### High Priority (architectural)
None. The system is clean.

### Medium Priority (enhancement candidates)
1. **Health interpreter** could benefit from kala_sarpa and chandrabala awareness
2. **Domain evaluators** could optionally incorporate tara scoring for timing quality (currently only the main pipeline uses it)
3. **Shadbala** is computed but only used via state_engine multiplier — could be exposed as a standalone quality metric

### Low Priority (documentation)
1. Document why domain evaluators don't use tara/moorthy directly (they use JSON-driven 5-layer timing instead)
2. Add a note to SCORING_CONTRACT.md about the two parallel scoring systems (pipeline vs evaluator)

---

## Summary

The scoring system is **architecturally sound** with:
- 28 primitives fully accounted for
- Zero contamination between trading and non-trading paths
- Zero duplication with conflicting values
- All 18 evaluators wired to domain profiles
- Trading overlays correctly gated behind opt-in flags
- Canonical values frozen and tested (297 tests passing)

The only structural observation is that domain evaluators and the main pipeline are **parallel scoring systems** — the evaluators use JSON-driven 5-layer timing, while the pipeline uses the full canonical scoring stack. This is by design, not a gap.
