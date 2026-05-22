# Calibration Policy — Parameter Classification & Provenance (v2.0)

## Core Principle

Every numeric value in this engine falls into exactly one of three categories:

| Category | Source | Can change? | Scope |
|----------|--------|-------------|-------|
| **Classical** | Vedic canon (2000+ years) | Never | Universal |
| **Empirical** | Backtested on historical data | With evidence | Domain-specific |
| **Domain-Specific** | Optimized for one domain's feedback | Freely per domain | Single domain |

**Rule:** Classical parameters are NEVER modified by calibration or ML.
**Rule:** Empirical parameters require evidence (backtest, correlation) to change.
**Rule:** Domain parameters can be tuned independently per domain without affecting others.

---

## Category 1: Classical (Vedic Canon)

These are timeless astronomical and astrological constants. They come from classical texts
(Brihat Parashara Hora Shastra, Jaimini Sutras, Phaladeepika, Saravali).

**They are NEVER tuned, calibrated, or domain-adjusted.**

### Astronomical Constants

| Parameter | Value | Source |
|-----------|-------|--------|
| Nakshatra size | 13°20' (360/27) | Geometric division |
| Sign size | 30° (360/12) | Geometric division |
| Pada size | 3°20' (13.33/4) | Geometric division |
| Navamsha division | 3°20' per navamsha | Geometric |
| Ayanamsa | Lahiri (externalized in config) | Convention (switchable) |

### Dignity Tables

| Parameter | Source | Location |
|-----------|--------|----------|
| SIGN_LORDS (12 entries) | BPHS Ch. 1 | `features/dignity.py` |
| EXALTATION signs (7 entries) | BPHS Ch. 3 | `features/dignity.py` |
| DEBILITATION signs (7 entries) | BPHS Ch. 3 | `features/dignity.py` |
| MOOLATRIKONA signs (7 entries) | BPHS Ch. 3 | `features/dignity.py` |
| NATURAL_FRIENDS / ENEMIES | BPHS Ch. 3 | `features/dignity.py` |

### Nakshatra Lordship

| Parameter | Source | Location |
|-----------|--------|----------|
| 27 nakshatra sequence | Vedic canon | `features/nakshatra.py` |
| Nakshatra lords (Ketu→Mercury cycle) | Vimshottari scheme | `features/nakshatra.py` |

### Dasha Periods

| Parameter | Value | Source | Location |
|-----------|-------|--------|----------|
| Vimshottari total | 120 years | BPHS | `features/dasha.py` |
| Ketu period | 7 years | BPHS | `features/dasha.py` |
| Venus period | 20 years | BPHS | `features/dasha.py` |
| Sun period | 6 years | BPHS | `features/dasha.py` |
| Moon period | 10 years | BPHS | `features/dasha.py` |
| Mars period | 7 years | BPHS | `features/dasha.py` |
| Rahu period | 18 years | BPHS | `features/dasha.py` |
| Jupiter period | 16 years | BPHS | `features/dasha.py` |
| Saturn period | 19 years | BPHS | `features/dasha.py` |
| Mercury period | 17 years | BPHS | `features/dasha.py` |

### Ashtakavarga Rules

| Parameter | Source | Location |
|-----------|--------|----------|
| PLANET_OFFSET_RULES (7 planets) | Classical BAV tables | `features/ashtakavarga.py` |
| Trikona groups | Classical | `features/ashtakavarga.py` |
| Ekadhipatya pairs | Classical | `features/ashtakavarga.py` |

### Aspect Rules

| Parameter | Source | Location |
|-----------|--------|----------|
| Mars special aspects (4th, 7th, 8th) | BPHS | `rules/aspects.py` |
| Jupiter special aspects (5th, 7th, 9th) | BPHS | `rules/aspects.py` |
| Saturn special aspects (3rd, 7th, 10th) | BPHS | `rules/aspects.py` |
| All planets 7th aspect | Universal | `rules/aspects.py` |

### Combustion Thresholds (degrees)

| Planet | Threshold | Source |
|--------|-----------|--------|
| Moon | 12° | Phaladeepika |
| Mars | 17° | Phaladeepika |
| Mercury (direct) | 14° | Phaladeepika |
| Mercury (retro) | 12° | Phaladeepika |
| Jupiter | 11° | Phaladeepika |
| Venus (direct) | 10° | Phaladeepika |
| Venus (retro) | 8° | Phaladeepika |
| Saturn | 15° | Phaladeepika |

### Moorthy Classification

| House from natal Moon | Grade | Source |
|-----------------------|-------|--------|
| 1, 6, 11 | Swarna (Gold) | Classical Gochar |
| 2, 5, 9 | Rajata (Silver) | Classical Gochar |
| 3, 7, 10 | Taamra (Copper) | Classical Gochar |
| 4, 8, 12 | Loha (Iron) | Classical Gochar |

---

## Category 2: Empirical (Backtested)

These parameters were derived from historical correlation analysis.
They require EVIDENCE to change — either new backtest results, or correlation improvement.

**Current calibration dataset:** 519 trading days (Apr 2022–Mar 2026), Nifty/BankNifty.

### Dignity Multipliers

| Status | Multiplier | Provenance |
|--------|-----------|------------|
| exalted | 1.5 | Backtest: exalted planets correlate 50% stronger with positive events |
| own | 1.2 | Backtest: own-sign planets correlate 20% stronger |
| great_friend | 1.15 | Interpolated between own and friend |
| friend | 1.05 | Minimal but measurable positive correlation |
| neutral | 1.0 | Baseline (definition) |
| enemy | 0.9 | Backtest: 10% signal reduction in adverse environment |
| bitter_enemy | 0.75 | Backtest: 25% signal reduction |
| debilitated | 0.5 | Backtest: 50% signal reduction, rarely actionable |

**Config path:** `planet_state.dignity_multipliers`
**Evidence required to change:** Backtest on 500+ data points showing improved directional accuracy.

### Event Scoring Weights

| Parameter | Value | Provenance |
|-----------|-------|------------|
| planet_base_per_unit | 25 | Empirical: scales planet contribution to 0-250 range |
| vimsopaka_per_unit | 2 | Empirical: vimsopaka adds 0-40 points per planet |
| exalted_bonus | 15 | Empirical: exalted planets outperform by ~15 score units |
| debilitated_penalty | -10 | Empirical: debilitated planets underperform by ~10 |
| house_bonus (tier_strong) | 20 | Empirical: strong-house planets contribute +20 per house hit |

**Config path:** `event_scoring.*`
**Evidence required to change:** Correlation analysis showing new weights improve event prediction accuracy.

### Risk Caps

| Factor | Cap | Provenance |
|--------|-----|------------|
| saturn_pressure | 12 | Empirical: beyond 12 points, additional Saturn pressure has diminishing marginal effect |
| node_crisis | 15 | Empirical: node effects saturate at 15 |
| sade_sati_peak | 20 | Empirical: Sade Sati peak contributes max 20 risk points |
| maraka_score | 20 | Empirical: maraka contribution capped |
| maraka_trigger | 25 | Empirical: trigger events capped |
| av_vulnerability | 25 | Empirical: ashtakavarga vulnerability saturates |
| dasha_sandhi | 15 | Empirical: sandhi risk contribution capped |

**Config path:** `risk.*_cap`
**Evidence required to change:** New backtest showing improved risk prediction with different caps.

### Confidence Formula

| Parameter | Value | Provenance |
|-----------|-------|------------|
| base_multiplier | 60 | Empirical: scales confidence to 0-100 range |
| yoga_weight | 0.30 | Empirical: yoga contribution to confidence |
| yoga_cap | 15 | Empirical: yoga effect saturates |
| tara_weight | 1.5 | Empirical: tara multiplier on confidence |
| sandhi_vimshottari_multiplier | 0.60 | Empirical: 40% confidence reduction during sandhi |
| vimsopaka_weak_multiplier | 0.60 | Empirical: weak promise reduces confidence 40% |

**Config path:** `confidence.*`
**Evidence required to change:** Improved Pearson correlation between confidence and actual PnL.

### Reference Weights (Lagna vs Moon)

| Domain | Lagna Weight | Moon Weight | Provenance |
|--------|-------------|-------------|------------|
| Wealth | 0.60 | 0.40 | Empirical: lagna reference slightly better for wealth events |
| Profession | 0.60 | 0.40 | Empirical |
| Health_Risk | 0.65 | 0.35 | Empirical: lagna more predictive for health |
| Relationship | 0.40 | 0.60 | Empirical: Moon reference better for emotional events |
| Family | 0.45 | 0.55 | Empirical |

**Config path:** `reference_weights.*`
**Evidence required to change:** Split backtest showing improved per-domain accuracy with different weights.

---

## Category 3: Domain-Specific (Freely Tunable Per Domain)

These parameters are calibrated for ONE domain and can be changed without affecting others.
Each domain may have completely different values for the same conceptual parameter.

### Trading Domain Parameters

| Parameter | Value | Location | Rationale |
|-----------|-------|----------|-----------|
| trading_event_boost | 1.15 | `multipliers.trading_filter` | Boosts trading-relevant events |
| non_trading_damp | 0.35 | `multipliers.trading_filter` | Suppresses non-trading events |
| sav_pass threshold | 28 | `trading_gate.sav_pass` | SAV ≥28 = expansion signal |
| sav_fail threshold | 20 | `trading_gate.sav_fail` | SAV <20 = contraction signal |
| kas_composite_pass | 197 | `trading_gate.kas_composite_pass` | Intraday readiness threshold |
| no_trade_nakshatras | [Dhanishta, Ashlesha, Ashwini, Mrigashira, Jyeshtha] | `trading_gate` | Empirical: these nakshatras correlate with losses |
| chandrabala_8th_block | true | Trading interpreter | Hard block for 8th from Moon |
| kala_sarpa_risk_weight | 1.3 | Trading interpreter | Amplified risk for concentrated energy |
| dainya_risk_weight | 1.4 | Trading interpreter | Amplified risk for resource stress |

**Tuning authority:** Trading PnL feedback loop only.
**Never applies to:** career, relationship, health, spirituality, general_life.

### Nakshatra Lists

| List | Content | Provenance | Scope |
|------|---------|-----------|-------|
| GOOD_NAK | Rohini, Pushya, Anuradha, Vishakha | Empirical (trading backtest) | Trading domain only |
| BAD_NAK | Mrigashira, Ardra, Ashlesha, Jyeshtha, Dhanishta | Empirical (trading backtest) | Trading domain only |
| RISKY_NAKSHATRA_SET | Dhanishta, Ashlesha, Ashwini, Mrigashira, Jyeshtha | Empirical (adaptive_lite_plus) | Trading domain only |

**Critical note:** These lists were derived from TRADING performance correlation.
They do NOT mean these nakshatras are "bad" for health, career, or spirituality.
A nakshatra "bad" for trading may be excellent for meditation or creative work.

### Decision Thresholds

| Parameter | Value | Scope |
|-----------|-------|-------|
| go_full: confidence ≥70, risk <45 | Trading | `decision.go_full` |
| controlled_aggression: confidence ≥60, score >120 | Trading | `decision.controlled_aggression` |
| moderate: confidence ≥50, risk <75 | Trading | `decision.moderate` |
| low_size_wait: risk 75-130 | Trading | `decision.low_size_wait` |
| destructive: risk >120, confidence <30, av_vuln >70 | Trading | `decision.destructive` |

**These thresholds are TRADING-NATIVE.** They should NOT be applied to career advice,
relationship guidance, or spiritual readings. Each domain will develop its own
decision thresholds based on its own feedback dataset.

---

## Versioning Rules

1. **Config file is versioned:** `configs/v2.0.0.yaml` — bump version when any parameter changes.
2. **Every engine run records config hash:** via `EngineSnapshot.config_hash`.
3. **Classical parameters are documented but NOT in YAML** — they live in code as constants (e.g., `DASHA_YEARS`, `SIGN_LORDS`). They never change.
4. **Empirical parameters live in YAML** — they CAN change but require evidence.
5. **Domain parameters will eventually live in per-domain config files:**
   - `configs/domains/trading.yaml`
   - `configs/domains/career.yaml`
   - `configs/domains/relationship.yaml`
   - (not yet implemented — currently in code)

---

## Change Control Process

### To change a Classical parameter:
**Answer: You don't.** These are mathematical or canonical facts. If you think one is wrong, verify against BPHS or the relevant classical text.

### To change an Empirical parameter:
1. State the hypothesis ("changing X from 0.6 to 0.7 will improve accuracy")
2. Run backtest on ≥500 data points
3. Show improved metric (directional accuracy, Pearson correlation, or drawdown reduction)
4. Document in commit message: old value, new value, evidence
5. Bump config version

### To change a Domain parameter:
1. Identify which domain it affects
2. Verify it does NOT leak into other domains
3. Test with domain-specific feedback data
4. Change freely — no cross-domain approval needed
5. Bump config version

---

## Migration Path: From Global to Per-Domain

### Current state (v2.0.0):
All parameters in one `configs/v2.0.0.yaml`. Domain-specific values mixed with universal ones.

### Target state (v3.0.0):
```
configs/
├── v3.0.0.yaml              # Universal: ayanamsa, classical reference, empirical base weights
├── domains/
│   ├── trading.yaml         # Trading-specific: gate thresholds, nakshatra lists, risk weights
│   ├── career.yaml          # Career-specific: opportunity thresholds, growth weights
│   ├── relationship.yaml    # Relationship-specific: Venus weights, emotional receptivity
│   ├── health.yaml          # Health-specific: Mars/Sun vitality weights
│   ├── spirituality.yaml    # Spirituality-specific: Ketu weights, transformation bonuses
│   └── general_life.yaml    # General: balanced, no single axis
```

Each domain config is:
- Independently versioned
- Independently calibratable
- Loaded only when that domain is requested
- Never affects other domains

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Dangerous | Correct Approach |
|--------------|-------------------|-----------------|
| Tuning SIGN_LORDS for better accuracy | Destroys astronomical correctness | Never modify classical data |
| Using trading nakshatra lists for health | Cross-domain contamination | Each domain has own lists |
| Changing dignity multipliers without backtest | Uncontrolled drift | Require 500+ point evidence |
| Hardcoding thresholds in interpreter code | Prevents versioned calibration | Move to domain config |
| Same risk caps for all domains | Trading bias infects everything | Per-domain risk profiles |
| Optimizing for one domain's metric globally | Silent corruption of other domains | Isolated feedback loops |

---

## Summary Table

| Parameter Family | Category | Can Change? | Who Decides? | Scope |
|-----------------|----------|-------------|--------------|-------|
| Sign lords, exaltation signs | Classical | Never | Canon | Universal |
| Nakshatra sequence, dasha years | Classical | Never | Canon | Universal |
| Combustion thresholds | Classical | Never | Canon | Universal |
| Aspect rules | Classical | Never | Canon | Universal |
| Dignity multipliers (1.5, 1.2, etc.) | Empirical | With evidence | Backtest | Universal base |
| Risk caps | Empirical | With evidence | Backtest | Universal base |
| Confidence formula weights | Empirical | With evidence | Backtest | Universal base |
| Lagna/Moon reference splits | Empirical | With evidence | Backtest | Per-event-family |
| Trading gate thresholds | Domain | Freely | Trading PnL | Trading only |
| Nakshatra good/bad lists | Domain | Freely | Domain feedback | Per-domain |
| Domain risk multipliers | Domain | Freely | Domain feedback | Per-domain |
| Decision action thresholds | Domain | Freely | Domain feedback | Per-domain |
