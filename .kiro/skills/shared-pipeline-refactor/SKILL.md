---
name: shared-pipeline-refactor
description: Guidelines for refactoring shared pipeline components in astro_engine to reduce duplication and improve maintainability across evaluators.
---
# shared-pipeline-refactor

Guidelines for refactoring shared pipeline components in astro_engine to reduce duplication and improve maintainability across evaluators.

## Core Principle

Extract common pipeline logic into shared base classes and utilities so that astronomy → features → rules → decisions remains a one-way flow, and domain evaluators only implement domain-specific differences.

## When to Apply

- Adding a new evaluator that duplicates existing pipeline steps
- Refactoring existing evaluators to share common logic
- Reducing code duplication across rule_pipeline, feature_pipeline, or decision_pipeline
- Standardizing how evaluators interact with the shared pipeline stages
- Centralizing repeated constants, helpers, and state objects
- Enforcing layer purity and preventing backflow between pipeline stages

## Architecture Rules

- Data must flow only upward through the pipeline:
  astronomy → features → rules → decisions
- Lower layers are read-only inputs for higher layers
- No layer may mutate upstream outputs
- Calibration may adjust weights, thresholds, confidence, or priority only within its own layer
- Domain evaluators must not call sibling evaluators
- Shared helpers must be pure, deterministic, and reusable
- Domain JSON packs remain the source of truth for domain meaning

## Pattern

1. Identify repeated logic across evaluators:
   - time conversion helpers
   - nakshatra and dignity helpers
   - ChartState / TransitState
   - house and aspect logic
   - confidence and scoring helpers
   - Tara scoring and event ranking helpers

2. Extract shared logic into canonical modules such as:
   - `astronomy/utils.py`
   - `features/nakshatra.py`
   - `features/dignity.py`
   - `features/houses.py`
   - `features/divisional.py`
   - `rules/evaluator_base.py` or equivalent shared evaluator utilities

3. Keep domain evaluators thin:
   - inherit shared behavior
   - override only domain-specific methods
   - keep domain meaning inside the domain pack and interpreter

4. Preserve the pipeline contract:
   astronomy → features → rules → decisions

5. Preserve exact behavior:
   - no scoring changes unless explicitly intended
   - no domain semantic changes
   - no JSON rule rewrites unless a bug fix is required

## Shared Refactor Targets

Centralize these if they are duplicated:

- `IST_OFFSET`
- `ist_to_utc`
- `get_jd`
- `SIGN_NAMES`
- `NAKSHATRA_LORDS`
- `NATURAL_BENEFICS`
- `NATURAL_MALEFICS`
- `BENEFIC_HOUSES`
- `MALEFIC_HOUSES`
- `JUPITER_ASPECTS`
- `SATURN_ASPECTS`
- `MARS_ASPECTS`
- `ChartState`
- `TransitState`
- `_get_aspectors_of_house`
- `_get_d9_sign`
- `_compute_d9_lagna`
- `get_house_from_sign`
- Tara scoring helpers
- repeated calibration loader patterns
- repeated window scanning loops

## Refactor Strategy

### Phase 1: Inventory
- Find the canonical implementation of each repeated helper
- Find all copy-pasted duplicates
- Identify which files already import shared infrastructure correctly
- Separate true duplication from intentional domain divergence

### Phase 2: Extract
- Create shared base classes or utility modules
- Move pure shared logic into canonical modules
- Keep existing public APIs stable where possible
- Add compatibility shims if needed

### Phase 3: Replace
- Update evaluator files to import shared logic
- Remove duplicate local definitions
- Leave domain-specific calculations and rule content intact

### Phase 4: Verify
- Run baseline parity checks
- Confirm identical outputs on existing test fixtures
- Confirm layer order is unchanged
- Confirm domain JSON packs are untouched

## Do Not

- Do not merge domain JSON rule packs together
- Do not change meaning, polarity, or output labels across domains
- Do not rewrite calibration values unless the task explicitly requires it
- Do not let lower layers write into higher layers
- Do not let sibling evaluators depend on each other
- Do not refactor everything at once if smaller safe steps are possible

## Acceptance Criteria

The refactor is complete only when:

- shared helpers exist in one canonical place
- evaluator files are reduced to domain-specific logic plus imports
- layer purity is preserved
- no upstream state is mutated by downstream layers
- baseline outputs remain stable
- domain rules remain distinct and readable

## First Run Guidance

Start with a dry-run inventory:
- list duplicates
- map canonical sources
- identify files to update
- propose the smallest safe patch set

Then refactor in this order:
1. pure helpers
2. shared state classes
3. shared scoring helpers
4. evaluator imports
5. parity tests

## Suggested Use

Use this skill whenever refactoring shared astrology pipeline code, especially when a change touches multiple evaluators or pipeline stages.