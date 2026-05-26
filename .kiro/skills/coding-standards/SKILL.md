---
name: coding-standards
description: Code style conventions that make your codebase AI-friendly, maintainable, and self-documenting.
---
# coding-standards

Code style conventions that make your codebase AI-friendly, maintainable, and self-documenting.

## Core Principle

Code is communication first, execution second. Write for the human who will read it next month, not for the compiler today.

## When to Apply

- Starting new codebase or project
- Adding features to existing code
- Refactoring or cleanup
- Code review

## The 4-Pillar Standard

### 1. Naming as Specification

| Pattern | Bad | Good |
|---------|-----|------|
| Variable | data, temp, x | userPreferences, pendingOrders |
| Function | doStuff(), handle(), process() | validateUserInput(), fetchOrderHistory() |
| Class | Manager, Handler, Utilities | OrderFulfillmentService, SessionManager |

**Rule:** If you need a comment to explain what a name means, the name is wrong.

### 2. Single Responsibility

```python
# BAD: Does three things
def process_user_data(data):
    # validate
    # transform
    # save
    pass

# GOOD: Each function does one thing
def validate_user_data(data): ...
def transform_user_data(data): ...
def save_user_data(data): ...
```

**Rule:** A function should fit in your working memory (~20 lines). If it is longer, it is doing too much.

### 3. Explicit Dependencies

```python
# BAD: Hidden dependency on global state
user_cache = {}

def get_user(user_id):
    if user_id in user_cache:
        return user_cache[user_id]
    user = db.find_user(user_id)
    user_cache[user_id] = user
    return user

# GOOD: Dependencies are parameters
def get_user(db, cache, user_id):
    if user_id in cache:
        return cache[user_id]
    user = db.find_user(user_id)
    cache[user_id] = user
    return user
```

**Rule:** If a function uses it, it should be passed in. No global state, no hidden lookups.

### 4. Fail Fast, Fail Explicit

```python
# BAD: Silent failure
def calculate_discount(price, rate):
    if not price or not rate:
        return 0
    return price * rate

# GOOD: Explicit error handling
def calculate_discount(price: float, rate: float) -> float:
    if price < 0:
        raise ValueError("Price cannot be negative")
    if not (0 <= rate <= 1):
        raise ValueError("Rate must be between 0 and 1")
    return price * rate
```

**Rule:** If data is invalid, signal failure immediately.

## AI-Friendly Conventions

### 1. Structure for Navigation

```python
# Organize imports
import stdlib
import external
import local

# Organize class members
class Service:
    # Constants (top)
    MAX_RETRIES = 3
    
    # Public methods
    def process(self): ...
    
    # Private helpers (bottom)
    def _validate(self): ...
```

### 2. Consistent Error Handling

| Pattern | Use When |
|---------|----------|
| ValueError | Invalid arguments |
| RuntimeError | System state issue |
| NotImplementedError | Missing implementation |

### 3. Type Annotations

```python
# BAD
def find_users(status):
    ...

# GOOD
from typing import List

def find_users(status: str) -> List[User]:
    ...
```

## Language-Agnostic Standards

### File Organization

```
project/
├── src/               # Implementation
│   ├── core/          # Business logic, domain models
│   ├── api/           # HTTP/CLI interfaces
│   ├── infrastructure/# DB, external APIs
│   └── utils/         # Shared helpers
├── tests/             # Test files mirror src structure
├── docs/              # Documentation (loaded on-demand)
└── config/            # Configuration files
```

### Comment Principles

```python
# BAD: Says what code does
# Loop through users
for user in users:

# GOOD: Explains why
# Filter to active users only - inactive users are archived
active_users = [u for u in users if u.is_active()]
```

**Rule:** Comments explain **why**. Code should explain **what**.

## Common Anti-Patterns

| Pattern | Why It is Bad | Fix |
|---------|---------------|-----|
| try: pass / except: pass | Swallows errors silently | Log and re-raise |
| if not x: return None | Silent failure on edge cases | Validate + raise |
| global keyword | Hidden state, hard to test | Pass as parameter |
| Magic strings/numbers | Unclear meaning | Constants with names |
| Deep nesting | Hard to follow | Extract functions early |

## Code Review Checklist

Before merge, verify:

- [ ] Function/variable names are self-explanatory
- [ ] Each function does one thing
- [ ] All dependencies are passed as parameters
- [ ] Errors are explicit, not silent
- [ ] Types are annotated
- [ ] Comments explain why, not what
- [ ] No duplicate logic
- [ ] No commented-out code

## Success Manifesto

You know coding standards are working when:

1. A new developer can understand the codebase in <1 hour
2. Code reviews focus on logic, not style
3. Bugs are caught by the type/naming system, not tests
4. "What does this do?" is answered by reading the name