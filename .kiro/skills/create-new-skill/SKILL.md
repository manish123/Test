---
name: create-new-skill
description: Guidelines for creating reusable skills from coding insights and patterns discovered during development.
---
# create-new-skill

Guidelines for creating reusable skills from coding insights and patterns discovered during development.

## Creating a New Skill

When you identify an effective pattern, approach, or solution during development, consider turning it into a reusable skill.

### When to Create a Skill

- Reusable pattern that solves a recurring problem
- Proven solution that improves code quality or development speed
- Abstracted best practice that applies beyond a single use case
- Insight that reduced complexity or prevented bugs

### Skill File Structure

Create a new directory in `.\kiro/skills/` with:

```
.\kiro/skills/skill-name/
  README.md      # The skill documentation
  steering.md    # Optional: steering rules referencing this skill
```

### Skill README.md Format

```markdown
# skill-name

Brief description of what this skill addresses.

## Core Principle

One-sentence statement of the guiding insight.

## When to Apply

List situations where this approach is beneficial.

## Pattern/Template

Concrete code patterns or structural guidance.

## Example

Specific example from your work that demonstrates effectiveness.

## Why It Works

Explanation of why this approach is effective.
```

## Example: Skill Creation Process

**Discovery Phase:**
- During code review, notice you consistently refactor X pattern
- Document the pattern and its benefits

**Skill Creation:**
- Create `.\kiro/skills/refactor-x-pattern/README.md`
- Include the pattern code, when to use, and why it works
- Push to repository for team sharing

**Future Application:**
- In new projects, reference the skill with `#[[file:.kiro/skills/refactor-x-pattern/README.md]]`
- Adapt the pattern to new contexts with confidence
