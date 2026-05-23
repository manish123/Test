# EVENT_ONTOLOGY.md

## Philosophy

Astralyn does **not** treat astrology as a fixed prediction engine.

The architecture is:

```text
Sky State
→ Symbolic Conditions
→ Event Possibilities
→ Domain Interpretation
→ Decision / Guidance
```

The same symbolic condition may produce different meanings depending on the domain.

Example:

```text
Kala Sarpa + Saturn pressure
```

may mean:
- trading → volatility risk
- spirituality → karmic concentration
- career → intense ambition
- relationship → emotional pressure

Therefore:
- events are neutral
- domains interpret meaning
- decisions are domain-specific

---

# 1. EVENT MODEL

Each event in Astralyn follows this schema:

```json
{
  "event_id": "business_start",
  "title": "Business Start",
  "category": "career_enterprise",
  "domains": ["career", "general_life", "trading"],
  "houses": [10, 6, 11],
  "planetary_significators": ["Mercury", "Jupiter", "Saturn"],
  "timing_triggers": [
    "dasha",
    "transit",
    "nakshatra",
    "house_activation"
  ],
  "polarity": "mixed",
  "intensity_range": [3, 10],
  "repeatable": true,
  "life_stage_sensitive": true,
  "requires_confirmation": true
}
```

---

# 2. EVENT CATEGORIES

## A. CAREER & ENTERPRISE

### Role Transitions
- `job_entry`
- `job_switch_lateral`
- `job_switch_promotion`
- `job_switch_demotion`
- `sector_change`
- `voluntary_exit`
- `involuntary_loss`
- `retirement`

### Enterprise Ventures
- `business_start`
- `business_launch`
- `partnership_formed`
- `business_expansion`
- `business_pivot`
- `business_closure`
- `merger_acquisition`
- `business_exit`

### Growth & Authority
- `promotion`
- `responsibility_escalation`
- `leadership_role`
- `team_building`
- `project_ownership`
- `certification_completion`
- `recognition_award`
- `skill_mastery`

## B. RELATIONSHIPS & FAMILY

### Partnership Events
- `meeting_significant_person`
- `commitment_deepens`
- `marriage_union`
- `cohabitation`
- `trust_breach`
- `separation_divorce`
- `reconciliation`
- `relationship_renewal`

### Family Events
- `pregnancy_awareness`
- `childbirth`
- `first_child`
- `child_milestone`
- `sibling_birth`
- `parent_health_event`
- `parent_loss`
- `grandchild_arrival`

## C. HEALTH & WELLBEING

### Physical Health
- `injury_accident`
- `surgery_procedure`
- `illness_onset`
- `chronic_diagnosis`
- `recovery_period`
- `hospitalization`
- `medication_change`
- `vitality_surge`

### Mental & Behavioral
- `stress_burnout`
- `anxiety_episode`
- `depression_onset`
- `addiction_cycle`
- `therapy_counseling`
- `habit_breaking`
- `confidence_shift`
- `sleep_disruption`

## D. SPIRITUAL & LEARNING

### Practice & Study
- `meditation_begins`
- `vedic_study_starts`
- `formal_training`
- `retreat_intensive`
- `teacher_meeting`
- `discipline_period`
- `sadhana_shift`
- `study_completion`

### Insight & Realization
- `breakthrough_realization`
- `belief_shift`
- `perspective_change`
- `purpose_clarity`
- `release_surrender`
- `cosmic_alignment`
- `identity_dissolution`

## E. LIFE SHIFTS & ASSETS

### Property & Assets
- `home_purchase`
- `property_sale`
- `ancestral_property`
- `inheritance`
- `asset_acquisition`
- `asset_loss`
- `property_legal_dispute`

### Movement & Travel
- `relocation_move`
- `city_change`
- `country_change`
- `long_journey`
- `visa_permit`
- `immigration`
- `homecoming`

### Financial & Legal
- `debt_incurred`
- `debt_cleared`
- `bankruptcy`
- `lawsuit_litigation`
- `criminal_charge`
- `windfall_bonus`
- `tax_event`

### Start & End Cycles
- `project_start`
- `project_end`
- `phase_begin`
- `phase_close`
- `relationship_cycle_complete`
- `educational_year_transition`
- `seasonal_transition`

## F. TRADING & MARKET OPERATIONS

### Execution States
- `high_conviction_window`
- `capital_preservation_phase`
- `high_volatility_phase`
- `whipsaw_risk`
- `overtrading_risk`
- `execution_block`

### Portfolio States
- `expansion_phase`
- `risk_off_phase`
- `sector_rotation`
- `liquidity_stress`
- `momentum_alignment`
- `timing_window`

---

# 3. EVENT PRINCIPLES

## Events are neutral
The ontology stores:
- WHAT may happen
- NOT whether it is “good” or “bad”

Meaning is assigned by domains.

## Events are probabilistic
Events represent:
- increased likelihood
- timing windows
- symbolic activation

NOT deterministic guarantees.

## Events are domain-aware
One event may belong to multiple domains.

## Events support calibration
Every event stores:
- confidence
- trigger conditions
- calibration history
- feedback alignment
