# token-optimization

Guide for managing token budgets effectively in AI agent workflows to optimize performance and cost.

## Core Principle

Token budgeting is about attention management - your context window is limited RAM. Every token competes for attention with the most important information.

## When to Apply

- Multi-step tasks that span many tool calls
- Workflows involving multiple files or complex context
- Long-running sessions where context grows unbounded
- When facing token limits or slow response times

## Token Budget Framework

### Three-Tier System

| Tier | Purpose | Target Size | Load Frequency |
|------|---------|-------------|----------------|
| **Bootstrap** | Core identity & rules | 50-100% of budget | Every turn |
| **Working Memory** | Current task context | 30-40% of budget | Active phase |
| **Long-term** | Reference & history | 0% (on-demand) | As needed |

### The 70-20-10 Rule

- **70%** for current task (what you are actively working on)
- **20%** for working context (related files, recent changes)
- **10%** for agent identity & rules (what you are and how to behave)

## Token Efficiency Patterns

### 1. Lazy Loading

```
DON'T: Load all docs upfront
DO: Load only what the next tool call needs
```

### 2. Distillation

```
DON'T: Keep raw session logs in context
DO: Extract key facts -> promote to MEMORY.md
```

### 3. Compression

```
DON'T: Verbose explanations in code comments
DO: Use naming that encodes intent
```

### 4. Chunking

```
DON'T: Read entire file when you need one function
DO: Grep first, read ranges
```

## Token Budget Metrics

| Metric | Action Level | Response |
|--------|-------------|----------|
| 70%+ used | Warning | Start distilling, move to long-term |
| 85%+ used | Critical | Commit work, start new session |
| 95%+ used | Emergency | /clear, restart with minimal context |

## Workspace File Optimization

| File | Target | Truncation Threshold |
|------|--------|---------------------|
| AGENTS.md | 10K chars | 20K chars |
| SOUL.md | 10K chars | 20K chars |
| TOOLS.md | 5K chars | 10K chars |
| MEMORY.md | 10K chars | 20K chars |
| Daily logs | 5K chars | 10K chars |

## Skill Activation Patterns

### When to Load Skills Selectively

| Scenario | Approach |
|----------|----------|
| Working on Python project | Load only -py skills |
| Single API integration | Load specific service skill |
| General development | Load only core skills |
| Multi-step task | Load task-specific planning skill |

### Unload Patterns

```
After completing a task phase:
1. Keep: Current file contents, active goals
2. Move to long-term: Process notes, intermediate results
3. Unload: Temporary files, completed phases
```

## Self-Audit Checklist

Before starting complex work:

- [ ] What is the 1-sentence goal?
- [ ] Which files will I modify?
- [ ] Which docs do I need?
- [ ] What skills apply?

## Anti-Patterns

| Pattern | Problem | Solution |
|---------|---------|----------|
| Load all skills | Context rot, conflated patterns | Select skills by domain |
| Keep raw session logs | Wasted tokens, slow responses | Distill to MEMORY.md |
| Read entire files | Excessive token use | Grep first, read ranges |
| Duplicated rules | Confusion, budget bloat | Single source of truth |
| Stale content | Wasted attention | Regular audit & cleanup |

## Token-Saving Tactics

### 1. Naming as Documentation

```
DON'T: userData, processData
DO: userPreferences, processPaymentTransaction
```

### 2. Compression via Abstraction

```
DON'T: Repeated auth patterns in every file
DO: authHelper.py with reusable functions
```

### 3. Selective Loading

```
DON'T: Load React docs when working on backend
DO: Load only current SDK docs as needed
```

### 4. Chunked Processing

```
DON'T: Ask for entire codebase review
DO: Review authentication flow only + follow-ups
```

## Success Metrics

You have done token optimization well when:

- Context window never hits 85% during active work
- Files load in <200ms
- Agent questions are precise
- New sessions start with <30% context used