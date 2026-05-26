# Scoring Profiles — v3.0.0 Specification

## Purpose

This directory holds per-domain scoring profiles that allow each domain to evolve
its confidence formula, thresholds, and calibration weights independently — without
contaminating canonical Vedic scoring or other domains.

## Architecture

```
configs/scoring_profiles/
├── README.md                  ← this file
├── canonical.yaml             ← frozen Vedic scoring inputs (NEVER changes)
├── trading.yaml               ← trading-specific confidence + thresholds
├── career.yaml                ← career-specific confidence + thresholds
├── relationship.yaml          ← relationship-specific
├── health.yaml                ← health-specific
├── spirituality.yaml          ← spirituality-specific
├── general_life.yaml          ← balanced default
└── finance.yaml               ← wealth/property/financial crisis
```

## Design Rules

1. **Canonical inputs are frozen.** `canonical.yaml` documents the Vedic scoring
   primitives that NEVER change. No profile may override these.

2. **Each domain profile is independent.** Changing `trading.yaml` cannot affect
   `career.yaml` or any other domain.

3. **Profiles only adjust the EMPIRICAL layer.** They may change:
   - Confidence formula weights
   - Risk penalty factors
   - Likelihood thresholds
   - Event boost/damp multipliers
   - Promise multipliers

4. **Profiles MUST NOT change:**
   - Tara formula (get_tara)
   - Moorthy house→grade mapping
   - Dignity classification (SIGN_LORDS, exaltation signs)
   - Aspect rules
   - Dasha periods
   - Nakshatra sequence

5. **Trading gates remain opt-in.** They are loaded only when the trading profile
   is active and `use_trading_gate=True`.

## Profile Schema

```yaml
version: "3.0.0"
domain: "trading"  # or career, relationship, health, etc.

confidence:
  base_components:
    event_strength_cap: 80       # max contribution from event score
    yoga_cap: 25                 # max contribution from yoga
    dasha_cap: 35                # max contribution from dasha alignment
  risk_penalty:
    factor: 0.15                 # risk × factor = penalty
    cap: 40                      # max penalty from risk
    high_risk_threshold: 120     # above this, extra penalty applies
    high_risk_extra: 10          # extra penalty when risk > threshold
  promise_multipliers:
    weak: 0.6
    moderate: 1.0
    strong: 1.1
  kakshya_multiplier:
    active: 1.0
    inactive: 0.7

thresholds:
  very_high: 55
  high: 40
  moderate: 25
  low: 15

layer_weights:
  dasha_weight: 0.35
  transit_weight: 0.30
  fast_trigger_weight: 0.20
  classical_weight: 0.15

# Trading-only section (ignored by other domains)
trading_gate:
  enabled: true
  sav_pass: 28
  sav_fail: 20
  kas_composite_pass: 197
  chandrabala_8th_block: true
  risky_nakshatras: ["Dhanishta", "Ashlesha", "Ashwini", "Mrigashira", "Jyeshtha"]
```

## Migration Plan

### Current State (v2.0.0)
- Single confidence formula in `decisions/confidence.py`
- Single set of thresholds shared across all domains
- Trading-specific logic mixed into rule_pipeline via flags
- Per-domain evaluators use their own `calibration_overlay.json` for layer weights

### Target State (v3.0.0)
- `load_scoring_profile(domain)` returns the domain's profile
- Confidence formula reads weights from the profile, not hardcoded values
- Each domain evaluator passes its profile to the scoring function
- Canonical inputs remain frozen and profile-independent
- Trading gate loads from `trading.yaml`, not from code constants

### Migration Steps
1. ✅ Create `configs/scoring_profiles/` directory with spec (this file)
2. ✅ Create `canonical.yaml` freezing Vedic inputs
3. Create per-domain YAML profiles (start with trading + general_life)
4. Add `load_scoring_profile()` to evaluator_base
5. Update confidence_score() to accept profile dict
6. Update domain evaluators to pass their profile
7. Verify parity: same inputs → same outputs with profile loaded
8. Remove hardcoded values from confidence.py (replaced by profile lookup)

### Backward Compatibility
- If no profile is loaded, the current hardcoded values are used (fallback)
- Existing tests continue to pass without any profile files present
- The migration is incremental — one domain at a time
