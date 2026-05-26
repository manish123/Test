---
name: self-learning
description: Framework for AI agents to discover, document, and reuse effective patterns during development.
---
# self-learning

Framework for AI agents to discover, document, and reuse effective patterns during development.

## Core Principle

Every discovery should become reusable knowledge. When you find a pattern that improves code quality, development speed, or reduces bugs, document it as a skill for future use.

## When to Apply

- After completing a complex task that reveals a reusable approach
- When you detect a recurring problem pattern
- After resolving a bug that suggests a better architecture
- When your workflow shows repeated patterns

## The Self-Learning Loop

```
Discover → Document → Store → Reuse → Improve
    ←---------------------------------------┘
```

### Step 1: Discover Pattern

Indicators that you have found something worth documenting:

| Signal | Example |
|--------|---------|
| **Repeated code** | Same pattern in 3+ files |
| **Repeated thinking** | You ask the same clarifying questions |
| **Recurring bugs** | Same type of error multiple times |
| **Uncovering docs** | You read the same API docs repeatedly |
| **Complex workflows** | Multi-step process that does not fit in context |

### Step 2: Document as Skill

Create .kiro/skills/pattern-name/README.md:

```markdown
# pattern-name

Brief description of what this pattern solves.

## Core Principle

One-sentence statement of the insight.

## When to Apply

List situations where this approach is beneficial.

## Pattern Template

Concrete code patterns or structural guidance.

## Example

Specific example that demonstrates effectiveness.

## Why It Works

Explanation of why this approach is effective.
```

### Step 3: Store and Share

**Location:** .kiro/skills/<skill-name>/README.md

**Version control:** Commit to repository for team sharing

**Trigger:** Reference in new projects with #[[file:.kiro/skills/pattern-name/README.md]]

### Step 4: Reuse

In a new project:

```
Use the pattern-name skill when [situation].
```

The skill loads, providing consistent guidance across projects.

### Step 5: Improve

After using the skill:

- Add new examples
- Update anti-patterns
- Add metrics for success
- Cross-reference related skills

## Self-Learning Checklist

Use this checklist when you suspect you have found something reusable:

### Discovery Checklist

- [ ] Did I write similar code 3+ times?
- [ ] Did I have to research the same thing repeatedly?
- [ ] Did I make a similar mistake multiple times?
- [ ] Is there a multi-step workflow that I am replicating?

### Documentation Checklist

- [ ] Is the title descriptive and searchable?
- [ ] Is the principle one sentence?
- [ ] Are use cases explicit and testable?
- [ ] Is there at least one concrete example?
- [ ] Does it explain why it works?

### Quality Checklist

- [ ] Can I use it without asking questions?
- [ ] Would another skill use this pattern?
- [ ] Is it language/framework agnostic?
- [ ] Can I verify it worked?

## Pattern Categories

### Architecture Patterns

| Category | Example Skills |
|----------|----------------|
| Project Structure | clean-architecture, layered-architecture |
| Component Design | repository-pattern, factory-pattern |
| Data Flow | event-driven, cqrs |

### Coding Patterns

| Category | Example Skills |
|----------|----------------|
| Error Handling | fail-fast-pattern, circuit-breaker |
| Validation | guard-clauses, build-dont-validate |
| Testing | test-first-pattern, test-data-builders |

### Process Patterns

| Category | Example Skills |
|----------|----------------|
| Development | tdd, planning-with-files |
| Debugging | systematic-debugging, diagnose |
| Refactoring | surgical-changes, refactor-when-green |

## Self-Learning Examples

### Example 1: Error Handling Pattern

**Discovery:**
```
I keep writing the same error handling pattern:
if validation_fails:
    raise ValueError(message)
return result
```

**Created Skill:** error-handling-pattern/README.md

### Example 2: Planning Workflow

**Discovery:**
```
Always create:
1. task_plan.md - phases and goals
2. findings.md - research and discoveries  
3. progress.md - session log

Before complex tasks.
```

**Created Skill:** planning-with-files/README.md

### Example 3: Code Review Pattern

**Discovery:**
```
Before merge, check:
- Single responsibility
- Error handling explicit
- Dependencies passed
- Names self-explanatory
```

**Created Skill:** coding-standards/README.md

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Document too late | Memory fades, details lost | Document immediately after discovery |
| Too specific | Not reusable | Generalize the pattern |
| Too abstract | Impossible to apply | Add concrete examples |
| No success criteria | Cannot verify | Define measurable outcomes |
| Single example | Hard to apply | Multiple varied examples |

## Metrics for Skill Quality

A good skill is:

- **Actionable:** Can be applied immediately
- **Verifiable:** Success criteria are clear
- **Transferable:** Works across projects
- **Maintainable:** Easy to update
- **Discoverable:** Searchable by problem type

## Integration with Existing Skills

Your self-learning skills should integrate with:

- **Karpathy guidelines:** Follow those principles when creating new skills
- **Token optimization:** Keep skills under 500 lines
- **Coding standards:** Follow naming and style conventions
- **Design patterns:** Use patterns when documenting solutions

## Success Indicators

Your self-learning is working when:

- New code follows established patterns without training
- Bugs of a type have not reoccurred in 3 months
- New team members can find relevant skills by searching
- Skills are used automatically, not just when asked
- You create 1-2 new skills per complex project