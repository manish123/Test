# Semantic Orchestration — Contract Specification

## Overview

This document defines the stable semantic interfaces between astro_engine's
symbolic cognition layer and future API/LLM consumers.

## Architecture

```
astro_engine symbolic cognition
    ↓
orchestration/context_router.py (routes to target contract)
    ↓
orchestration/token_budget.py (enforces budget)
    ↓
orchestration/prompt_sections.py (structures injection order)
    ↓
orchestration/payload_builder.py (produces final payload)
    ↓
Future: Personality API / Timing API / Career API / OpenAI
```

## Contracts

| Contract | Budget | Compression | Primary Use |
|----------|--------|-------------|-------------|
| minimal_context | 80 tokens | extreme | Chat snippets, quick lookups |
| prediction_context | 250 tokens | high | Weekly/monthly predictions |
| timing_context | 400 tokens | moderate | Timing API responses |
| relationship_context | 450 tokens | moderate | Partnership analysis |
| career_context | 500 tokens | moderate | Career API responses |
| personality_context | 600 tokens | moderate | Full personality profiles |
| full_symbolic_context | 1200 tokens | minimal | Advanced orchestration |

## Semantic Priority (per contract)

| Contract | Priority Order |
|----------|---------------|
| personality | identity → behavioral_core → psychological_os → lifecycle |
| timing | lifecycle → coherence → conflicts → narratives |
| career | identity → economic_style → leadership → lifecycle |
| prediction | narratives → lifecycle → conflicts → identity |
| relationship | conflicts → suppression → behavioral_core → identity |

## Prompt Injection Sections

| # | Section | Always Include | Max Tokens |
|---|---------|---------------|------------|
| 1 | Core Identity | ✓ | 80 |
| 2 | Behavioral Operating System | ✓ | 120 |
| 3 | Current Life Phase | ✓ | 60 |
| 4 | Active Symbolic Conflicts | — | 80 |
| 5 | Causal Explanations | — | 100 |
| 6 | Opportunity Vectors | — | 60 |
| 7 | Suppression Vectors | — | 60 |
| 8 | Risk Vectors | — | 60 |

## Token Budget Strategy

1. Required sections (identity + behavioral + lifecycle) = ~260 tokens minimum
2. Remaining budget distributed proportionally to optional sections
3. If over budget: prune in reverse priority order (risk → suppression → opportunity → narratives → conflicts)
4. Never prune identity or lifecycle (always required)

## Future Integration Map

| API | Contract | Integration Point |
|-----|----------|-------------------|
| Personality API | personality_context | Inject into system prompt as "subject profile" |
| Timing API | timing_context | Inject as "current phase context" for timing interpretation |
| Career API | career_context | Inject as "career intelligence" for guidance generation |
| Weekly Predictions | prediction_context | Inject as "symbolic backdrop" for narrative generation |
| Chat/Assistant | full_symbolic_context | Inject as persistent context in conversation memory |
| Relationship | relationship_context | Inject as "emotional/partnership dynamics" |
