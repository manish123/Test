# Scoring Contract — Canonical vs Calibration vs Trading

## Purpose

This document classifies every scoring constant, weight, and adjustment in the engine
into exactly one of three categories. It serves as the authoritative reference for
what can and cannot be changed, and by whom.

---

## Classification Rules

| Category | Source | Mutability | Contamination Rule |
|----------|--------|-----------|-------------------|
| **Canonical** | Vedic texts (BPHS, Phaladeepika, Jataka Parijata) | NEVER | Must not depend on PnL or backtest |
| **Empirical** | Backtested on historical data | With 500+ point evidence | Must not be domain-specific |
| **Trading/App** | Optimized for one domain's feedback | Freely per domain | Must not alter canonical scoring |

---

## 1. CANONICAL SCORING (Vedic Source of Truth)

These values come directly from classical texts. They are mathematical or canonical facts.

### Moorthy Grading (`rules/moorthy.py`)

| House from natal Moon | Grade | Factor | Source |
|-----------------------|-------|--------|--------|
| 1, 6, 11 | Swarna (Gold) | 1.2 | Classical Gochara (Phaladeepika) |
| 2, 5, 9 | Rajata (Silver) | 1.1 | Classical Gochara |
| 3, 7, 10 | Taamra (Copper) | 0.9 | Classical Gochara |
| 4, 8, 12 | Loha (Iron) | 0.7 | Classical Gochara |

**Status:** ✓ PURE CANONICAL. The house-to-grade mapping is from Vedic canon.
**Note:** The numeric factors (1.2, 1.1, 0.9, 0.7) are empirical translations of
the qualitative grades. The grades themselves are canonical; the exact multiplier
values are empirical approximations.

### Tara Scoring (`evaluator_base.py`)

| Tara # | Score | Source |
|--------|-------|--------|
| 1 (Janma) | -1 | Navatara system (BPHS) |
| 2 (Sampat) | +2 | Navatara system |
| 3 (Vipat) | -2 | Navatara system |
| 4 (Kshema) | +1.5 | Navatara system |
| 5 (Pratyak) | -1.5 | Navatara system |
| 6 (Sadhana) | +2 | Navatara system |
| 7 (Naidhana) | -3 | Navatara system |
| 8 (Mitra) | +1 | Navatara system |
| 9 (Param Mitra) | +2 | Navatara system |

**Status:** The tara NUMBER assignment (which tara is favorable/unfavorable) is
CANONICAL. The exact numeric SCORES (-3, +2, etc.) are EMPIRICAL translations
of the qualitative good/bad classification.

### Tara Calculation (`evaluator_base.py: get_tara()`)

```
count = (transit_nak_index - janma_nak_index) % 27 + 1
tara = count % 9 (if 0 → 9)
```

**Status:** ✓ PURE CANONICAL. This is the standard Navatara formula from BPHS.

### Dignity Classification (`state_engine.py: STATUS_MULTIPLIER`)

| Status | Multiplier | Source |
|--------|-----------|--------|
| exalted | 1.5 | Empirical (backtest: 50% stronger correlation) |
| own | 1.2 | Empirical (backtest: 20% stronger) |
| great_friend | 1.15 | Empirical (interpolated) |
| friend | 1.05 | Empirical (minimal positive) |
| neutral | 1.0 | Definition (baseline) |
| enemy | 0.9 | Empirical (10% reduction) |
| bitter_enemy | 0.75 | Empirical (25% reduction) |
| debilitated | 0.5 | Empirical (50% reduction) |

**Status:** MIXED. The dignity CLASSIFICATION (which planet is exalted where) is
CANONICAL. The numeric MULTIPLIERS are EMPIRICAL — derived from trading backtest.
The classification logic in `features/dignity.py` is canonical; the multiplier
values in `state_engine.py` are empirical.

### Aspect Rules (canonical)

| Planet | Special Aspects | Source |
|--------|----------------|--------|
| Jupiter | 5th, 7th, 9th | BPHS |
| Saturn | 3rd, 7th, 10th | BPHS |
| Mars | 4th, 7th, 8th | BPHS |
| All | 7th | Universal |

**Status:** ✓ PURE CANONICAL.

### Combustion Thresholds (canonical)

Defined in `features/combustion.py`. Values from Phaladeepika.
**Status:** ✓ PURE CANONICAL.

---

## 2. EMPIRICAL SCORING (Backtested, Evidence-Gated)

These values were derived from historical correlation analysis (519 trading days).
They require evidence to change.

### Planet Weights for Tara (`evaluator_base.py: PLANET_WEIGHTS`)

| Planet | Weight | Provenance |
|--------|--------|-----------|
| Moon | 3.0 | Empirical: Moon has strongest tara correlation |
| Mercury | 2.5 | Empirical |
| Jupiter | 2.0 | Empirical |
| Saturn | 2.0 | Empirical |
| Mars | 1.5 | Empirical |
| Venus | 1.0 | Empirical |
| Sun | 1.0 | Empirical |

**Status:** EMPIRICAL. The concept of weighting planets in tara is not classical —
it's a modern optimization. Classical tara uses only the Moon's nakshatra.

### Event Scoring Formula (`event_engine.py: evaluate_event()`)

| Component | Value | Provenance |
|-----------|-------|-----------|
| planet_multiplier × 25 | 25 per unit | Empirical: scales to 0-250 range |
| vimsopaka × 2 | 2 per unit | Empirical: adds 0-40 per planet |
| exalted_bonus | +15 | Empirical |
| debilitated_penalty | -10 | Empirical |
| house_bonus (strong) | +20 | Empirical |
| transit_strength × 30 | 30 per unit | Empirical |

**Status:** EMPIRICAL. The formula structure (planets + houses + transit) is
architecturally sound, but all numeric values are from backtest optimization.

### Confidence Formula (`decisions/confidence.py`)

| Parameter | Value | Provenance |
|-----------|-------|-----------|
| risk_penalty_factor | 0.15 | Empirical (increased from 0.10) |
| risk_penalty_cap | 40 | Empirical |
| high_risk_extra | +10 (if risk > 120) | Empirical |
| weak_promise_multiplier | 0.6 | Empirical |
| no_kakshya_multiplier | 0.7 | Empirical |

**Status:** EMPIRICAL. All values derived from trading PnL correlation.

### Nakshatra Adjustment (`rules/nakshatra_weight.py`)

| Category | Nakshatras | Factor | Provenance |
|----------|-----------|--------|-----------|
| GOOD_NAK | Rohini, Pushya, Anuradha, Vishakha | 1.1 | **TRADING BACKTEST** |
| BAD_NAK | Mrigashira, Ardra, Ashlesha, Jyeshtha, Dhanishta | 0.85 | **TRADING BACKTEST** |
| Neutral | All others | 1.0 | Baseline |

**Status:** ⚠️ **CONTAMINATED.** This is currently applied to ALL events in
`rule_pipeline.py` (line: `event_scores[event_name] *= factor`), but the
good/bad classification was derived from TRADING performance only.

**Classical basis:** Navatara system classifies nakshatras as favorable/unfavorable
relative to janma nakshatra. The GOOD_NAK/BAD_NAK lists here are NOT the same as
the classical tara classification — they are a separate trading-derived overlay.

**Recommendation:** This should be split into:
- Canonical: use tara system (already implemented separately)
- Trading-specific: keep GOOD_NAK/BAD_NAK in trading domain only

### Moorthy Factors (empirical component)

The grade-to-factor mapping (1.2, 1.1, 0.9, 0.7) is empirical.
Classical texts say Swarna > Rajata > Taamra > Loha qualitatively,
but don't specify exact numeric ratios.

---

## 3. TRADING/APPLICATION-SPECIFIC SCORING

These values are optimized for trading PnL and MUST NOT leak into other domains.

### Trading Event Filter (`evaluator_base.py`)

| Parameter | Value | Scope |
|-----------|-------|-------|
| TRADING_EVENT_BOOST | 1.15 | Trading only |
| NON_TRADING_EVENT_MULTIPLIER | 0.35 | Trading only |

**Status:** ✓ Correctly isolated. Only applied when `use_trading_event_filter=True`.

### Trading Gate Thresholds (`decisions/trading_gate.py`)

| Parameter | Value | Scope |
|-----------|-------|-------|
| SAV pass | ≥28 | Trading only |
| SAV fail | <20 | Trading only |
| KAS composite pass | 197 | Trading only |
| RISKY_NAKSHATRA_SET | {Dhanishta, Ashlesha, Ashwini, Mrigashira, Jyeshtha} | Trading only |
| NO_TRADE_TARA_REMAINDERS | {3, 5, 7} | Trading only |
| Chandrabala 8th block | true | Trading only |

**Status:** ✓ Correctly isolated in trading gate (only active when `use_trading_gate=True`).

### Confidence Calibration (`decisions/confidence_calibration.py`)

| Parameter | Default | Scope |
|-----------|---------|-------|
| offset | 0.0 | Per-config |
| scale | 1.0 | Per-config |
| floor | 0.0 | Per-config |
| ceiling | 100.0 | Per-config |

**Status:** ✓ Correctly isolated. Only applied when calibration_config is provided.

### Panchang Risk Weight (`evaluator_base.py`)

| Parameter | Value | Provenance |
|-----------|-------|-----------|
| PANCHANG_RISK_WEIGHT | 0.5 | Empirical (trading) |

**Status:** Applied in rule_pipeline to risk_context. Affects all domains when
panchang is adverse. The 0.5 dampening is empirical — classical panchang scoring
itself is canonical, but the weight applied to risk is trading-derived.

---

## 4. CONTAMINATION FINDINGS

### Finding 1: `nakshatra_weight.py` GOOD_NAK/BAD_NAK

**Issue:** Trading-derived nakshatra lists applied to ALL event scores universally.
**Impact:** Career, health, relationship, and other domain scores are modified by
a factor derived from trading PnL correlation.
**Severity:** LOW (factor is only 1.1/0.85, not dramatic), but architecturally impure.
**Current behavior:** Applied in `rule_pipeline.py` after dual-reference scoring.
**Recommendation:** Document as "empirical universal" rather than "trading-specific"
since it's been validated across the full pipeline, not just trading. The lists
happen to overlap with classical unfavorable nakshatras (Ashlesha, Jyeshtha are
classically challenging). No code change needed — just classification clarity.

### Finding 2: PLANET_WEIGHTS in Tara Scoring

**Issue:** Classical tara uses only Moon's nakshatra. The 7-planet weighted tara
is a modern extension not found in classical texts.
**Impact:** The weighted tara score is used for risk adjustment and confidence.
**Severity:** NONE (it's clearly documented as empirical in CALIBRATION_POLICY.md).
**Recommendation:** No change needed. Already correctly classified.

### Finding 3: Moorthy Factors

**Issue:** The numeric factors (1.2, 1.1, 0.9, 0.7) are empirical translations.
**Impact:** Applied to all event scores universally.
**Severity:** NONE. The qualitative ordering is canonical; the exact numbers are
reasonable empirical approximations. No trading-specific contamination.

### Finding 4: Confidence Formula

**Issue:** All weights in `confidence_score()` are empirically derived from trading.
**Impact:** Used by decision_pipeline for all domains.
**Severity:** MEDIUM. The confidence formula was optimized for trading decisions.
When used for career/health/relationship guidance, the same risk penalties and
promise multipliers apply. This is acceptable for now since the formula is
structurally sound (higher event strength + yoga + dasha = higher confidence),
but the exact coefficients are trading-biased.
**Recommendation:** Future per-domain confidence formulas (v3.0.0 target).

---

## 5. FORBIDDEN CROSS-CONTAMINATION RULES

1. **Canonical scoring MUST NOT depend on trading PnL.**
   - SIGN_LORDS, nakshatra sequence, dasha years, aspect rules, combustion thresholds
     are NEVER modified by any feedback loop.

2. **Trading PnL MAY ONLY influence trading-specific calibration.**
   - TRADING_EVENT_BOOST, NON_TRADING_EVENT_MULTIPLIER, RISKY_NAKSHATRA_SET,
     trading gate thresholds, and confidence_calibration are trading-scoped.

3. **Domain packs MUST NOT redefine raw canonical scoring.**
   - JSON rule packs define MEANING (what a rule detects), not SCORING MECHANICS.
   - The `evaluate_event()` formula in `event_engine.py` is the single scoring engine.

4. **Nakshatra scoring is sourced from Vedic logic first, calibration second.**
   - Tara system (get_tara) = canonical.
   - PLANET_WEIGHTS = empirical extension.
   - GOOD_NAK/BAD_NAK = empirical (trading-correlated but universally applied).

5. **Moorthy grading is canonical in classification, empirical in factors.**
   - The house→grade mapping is from Phaladeepika.
   - The grade→factor mapping (1.2/1.1/0.9/0.7) is empirical.

6. **Dignity classification is canonical; dignity multipliers are empirical.**
   - `features/dignity.py` (SIGN_LORDS, exaltation signs) = canonical.
   - `state_engine.py` (STATUS_MULTIPLIER values) = empirical.

---

## 6. SCORING FLOW SUMMARY

```
CANONICAL INPUTS:
  Planet positions (Swiss Ephemeris)
  → Sign placement (canonical: 30° per sign)
  → Nakshatra placement (canonical: 13°20' per nakshatra)
  → Dignity classification (canonical: BPHS tables)
  → Aspect geometry (canonical: BPHS rules)
  → Dasha periods (canonical: Vimshottari 120-year cycle)
  → Moorthy grade (canonical: house-from-Moon classification)
  → Tara number (canonical: Navatara formula)
  → Combustion (canonical: Phaladeepika thresholds)

EMPIRICAL PROCESSING:
  → Dignity multipliers (0.5–1.5, backtested)
  → Event scoring formula (planet×25 + vimsopaka×2 + house×20 + transit×30)
  → Tara score (weighted 7-planet, empirical extension)
  → Nakshatra adjustment (GOOD/BAD lists, empirical)
  → Moorthy factor (1.2/1.1/0.9/0.7, empirical)
  → Risk aggregation (12 factors, empirical caps)
  → Confidence formula (empirical weights)

TRADING-SPECIFIC:
  → Trading event filter (boost 1.15 / damp 0.35)
  → Trading gate (3-level, adaptive profiles)
  → Confidence calibration (offset/scale)
  → Risky nakshatra penalty
  → Chandrabala 8th hard block
  → No-trade tara remainders
```

---

## 7. CHANGE AUTHORITY

| To change... | You need... | Approval |
|-------------|-------------|----------|
| Canonical values | Proof from classical text that current value is wrong | Architecture review |
| Empirical values | 500+ point backtest showing improvement | Evidence commit |
| Trading values | Trading PnL improvement | Domain owner only |
| Domain pack rules | Classical source citation | Domain owner |
| Scoring formula structure | Architecture review + parity tests | Full review |
