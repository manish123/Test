# Domain Policy — Interpretation Profiles (v2.0)

## Core Principle

The same planetary state means different things depending on what the user is optimizing for.

**One neutral sky model → six separate domain interpreters.**

Domains NEVER modify symbolic states. They are read-only consumers.
New domains can be added without touching astronomy, features, or symbolic states.

---

## Domain Registry

```python
from rules.domains import get_domain_interpreter

interpreter = get_domain_interpreter("trading")   # or career, relationship, health, spirituality, general_life
reading = interpreter.interpret(symbolic_state)
```

---

## The Six Domains

### 1. Trading

| Property | Value |
|----------|-------|
| **Module** | `rules/domains/trading/interpreter.py` |
| **Optimization Goal** | Capital preservation + execution timing |
| **Risk Sensitivity** | HIGHEST — amplifies all risk signals |
| **Action Vocabulary** | AVOID, LOW SIZE, MODERATE, FULL EXECUTION |
| **Feedback Source** | PnL data, directional accuracy, drawdown metrics |

**What it watches for:**
- Whipsaw potential (Kala Sarpa = concentrated volatility)
- Emotional decision-making pressure (Sade Sati)
- Hard execution blocks (Chandrabala 8th, Tara no-trade)
- Environmental resistance (Moorthy Loha)
- Capital/resource stress (Dainya yoga)

**Key characteristic:** Aggressively blocks entries under uncertainty. A single bad day can erase a week of gains, so false negatives (missing a trade) are preferred over false positives (taking a losing trade).

---

### 2. Career

| Property | Value |
|----------|-------|
| **Module** | `rules/domains/career/interpreter.py` |
| **Optimization Goal** | Professional growth, authority, achievement |
| **Risk Sensitivity** | MODERATE — restructuring seen as opportunity |
| **Action Vocabulary** | EXPAND, ADVANCE, STEADY EFFORT, CONSOLIDATE, PAUSE |
| **Feedback Source** | Career milestones, promotions, role changes |

**What it watches for:**
- Focused ambition axis (Kala Sarpa = deep single-minded professional focus)
- Organizational restructuring (Sade Sati = rebuild opportunity)
- Visibility periods (Sun amplified, 10th/11th house activation)
- Unconventional career paths (Node pressure)
- Mentorship availability (Jupiter state)

**Key characteristic:** Interprets pressure as restructuring opportunity, not danger. Saturn pressure in career = "time to rebuild from stronger foundation." The same condition that blocks trading can accelerate career pivots.

---

### 3. Relationship

| Property | Value |
|----------|-------|
| **Module** | `rules/domains/relationship/interpreter.py` |
| **Optimization Goal** | Emotional connection, partnership depth, family harmony |
| **Risk Sensitivity** | MODERATE — testing seen as deepening |
| **Action Vocabulary** | DEEPEN, ENGAGE, GENTLE EFFORT, PATIENCE, SPACE |
| **Feedback Source** | Relationship quality, emotional satisfaction, conflict resolution |

**What it watches for:**
- Karmic bond patterns (Kala Sarpa = intense fated connections)
- Commitment testing (Sade Sati = relationships that survive become unshakeable)
- Emotional receptivity (Moorthy grade, Moon state)
- Venus condition (key relationship signifier)
- Deep emotional transformation (Chandrabala 8th = vulnerability, not avoidance)

**Key characteristic:** "Difficult" conditions are often doorways to deeper connection. Chandrabala 8th in trading = "DO NOT TRADE." In relationships = "hidden feelings surfacing, deep honesty possible."

---

### 4. Health

| Property | Value |
|----------|-------|
| **Module** | `rules/domains/health/interpreter.py` |
| **Optimization Goal** | Physical vitality, recovery, longevity |
| **Risk Sensitivity** | HIGH — Mars/Sun dormancy = real physical concern |
| **Action Vocabulary** | THRIVE, ACTIVE, MODERATE, CAUTION, REST |
| **Feedback Source** | Symptom cycles, energy levels, recovery patterns |

**What it watches for:**
- Physical energy (Mars intensity — amplified vs dormant)
- Vitality and immunity (Sun state)
- Chronic fatigue patterns (Sade Sati peak)
- Hidden health issues surfacing (Ashtama Shani)
- Body-environment friction (Moorthy Loha)
- Sudden health events (high node pressure)

**Key characteristic:** Takes physical indicators seriously. Mars/Sun dormant combined with Sade Sati peak = genuine health concern, not just "bad day." The only domain where "AVOID physical exertion" may literally apply.

---

### 5. Spirituality

| Property | Value |
|----------|-------|
| **Module** | `rules/domains/spirituality/interpreter.py` |
| **Optimization Goal** | Inner awareness, detachment, awakening |
| **Risk Sensitivity** | LOWEST — difficulty = opportunity for growth |
| **Action Vocabulary** | EXPAND, PRACTICE, CONTEMPLATE, SURRENDER, STILLNESS |
| **Feedback Source** | Meditation quality, insight frequency, detachment growth |

**What it watches for:**
- Karmic acceleration (Kala Sarpa = concentrated processing, ideal for deep practice)
- Tapas and maturation (Sade Sati = ego dissolution through discipline)
- Death/rebirth of patterns (Chandrabala 8th = excellent for occult study)
- Natural detachment (Ketu state)
- Guru access (Jupiter availability)
- Past-life resolution (node energy)

**Key characteristic:** INVERTS the risk interpretation of other domains. What trading calls "extreme danger," spirituality often calls "profound opportunity." Sade Sati peak in trading = AVOID. In spirituality = "profound maturation through tapas — this is the work."

---

### 6. General Life

| Property | Value |
|----------|-------|
| **Module** | `rules/domains/general_life/interpreter.py` |
| **Optimization Goal** | Balanced adaptation, growth, and meaning |
| **Risk Sensitivity** | NEUTRAL — describes without prescribing a single axis |
| **Action Vocabulary** | FLOURISH, ENGAGE, ADJUST, NAVIGATE, ADAPT |
| **Feedback Source** | Overall life satisfaction, multi-domain balance |

**What it watches for:**
- Overall energy characterization (which planets are amplified vs dormant)
- Life phase transitions (Sade Sati, dasha sandhi)
- Environmental support (Moorthy grade)
- Balance across all domains simultaneously
- Whether restructuring or stability dominates

**Key characteristic:** Uses DESCRIPTIVE language, not prescriptive. Instead of "BAD PERIOD" → says "HIGH INSTABILITY / HIGH TRANSFORMATION." The user decides what to optimize — this domain just describes what is.

---

## Domain Selection Rules

| API Service | Default Domain | Rationale |
|-------------|---------------|-----------|
| `personality_api` | `general_life` | Personality is not domain-specific |
| `timing_api` (career endpoint) | `career` | Career timing optimization |
| `timing_api` (trading endpoint) | `trading` | Capital preservation |
| Future: relationship API | `relationship` | Emotional connection |
| Future: health API | `health` | Vitality tracking |
| Future: spiritual API | `spirituality` | Inner growth |

---

## Adding a New Domain

1. Create `rules/domains/new_domain/__init__.py` and `interpreter.py`
2. Inherit from `BaseDomainInterpreter`
3. Implement `interpret(symbolic_state)` → returns standardized reading dict
4. Register in `rules/domains/registry.py`
5. Add to `AVAILABLE_DOMAINS` list

**What you touch:** Only `rules/domains/` directory.
**What you never touch:** astronomy, features, symbolic states, contracts, pipeline.

---

## Interpreter Output Contract

Every `interpret()` call returns:

```python
{
    "domain": str,              # which domain lens was applied
    "optimization_goal": str,   # what this domain optimizes for
    "summary": str,             # one-line domain-specific reading
    "intensity": str,           # overall intensity level
    "themes": list[str],        # active life themes in this domain
    "opportunities": list[str], # what's favorable in this domain
    "challenges": list[str],    # what requires attention
    "action_guidance": str,     # what to do (domain-specific vocabulary)
    "risk_level": str,          # low / moderate / elevated / high / extreme
    "risk_points": float,       # accumulated risk score
    "risk_factors": list[str],  # specific risks in this domain
}
```

---

## The Semantic Neutrality Rule

Symbolic layer (`rules/symbolic/`) must NEVER use:

- ❌ "good" / "bad"
- ❌ "avoid" / "go" / "block"
- ❌ "dangerous" / "safe"
- ❌ "favorable" / "unfavorable"

It must ONLY use:

- ✅ "active" / "inactive"
- ✅ "amplified" / "subdued" / "dormant"
- ✅ "restructuring" / "transition" / "stable"
- ✅ "concentrated" / "distributed"
- ✅ "internalized" / "externalized"
- ✅ Descriptive phrases: "energy flowing along one channel"

Domain interpreters decide whether that's good or bad for their optimization goal.

---

## Cross-Domain Corruption Prevention

**Rule:** Domains NEVER modify symbolic states.

**Rule:** No domain's risk weights leak into another domain's interpreter.

**Rule:** Domain calibration uses SEPARATE feedback datasets:
- Trading → PnL data
- Career → milestone tracking
- Relationship → satisfaction surveys
- Health → symptom logs
- Spirituality → practice quality metrics

**Rule:** A domain can be added, removed, or recalibrated without affecting any other domain or the symbolic layer.

---

## Future: Per-Domain ML Calibration

Once symbolic states are stable, each domain can independently learn:

```
trading_policy    + PnL feedback         → optimized trading weights
career_policy     + career outcomes      → optimized career weights
health_policy     + symptom cycles       → optimized health weights
relationship_pol  + satisfaction data    → optimized relationship weights
spirituality_pol  + practice quality     → optimized spiritual weights
```

This is possible BECAUSE domains are isolated. One domain's learning never contaminates another.
