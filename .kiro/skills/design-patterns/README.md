# design-patterns

Reusable architectural patterns that solve common problems while keeping code maintainable and testable.

## Core Principle

Patterns are solutions to recurring problems, not templates to force. Use the simplest pattern that solves your problem. Patterns should make code clearer, not more complex.

## When to Apply

- Identifying recurring problem patterns in your codebase
- Architecting new features or services
- Refactoring legacy code into maintainable structure
- Designing system boundaries and responsibilities

## The Pattern Selection Framework

### Step 1: Identify the Problem Type

| Problem | Typical Pattern | When to Avoid |
|---------|----------------|---------------|
| Object creation | Factory, Builder | Single concrete type |
| Behavior variation | Strategy, Command | Single implementation |
| State change | State, Observer | Fixed behavior |
| Composition | Composite, Decorator | Simple hierarchy |
| Access control | Proxy, Adapter | Direct access sufficient |

### Step 2: Evaluate Pattern Cost

| Factor | Low Cost | High Cost |
|--------|----------|-----------|
| Classes | 1-2 | 4+ |
| Indirection | Minimal | Multiple layers |
| Testing | Easy mocks | Complex setup |
| Learning curve | Familiar | Specialized |

## Essential Patterns

### 1. Repository Pattern

**Purpose:** Separate data access from business logic

```python
# Interface
class UserRepository:
    def get_by_id(self, user_id): ...
    def save(self, user): ...
    def find_active(self): ...

# Implementation
class DatabaseUserRepository(UserRepository):
    def get_by_id(self, user_id):
        return db.query(User).filter_by(id=user_id).first()
```

**When to use:** Any service that needs data access
**Avoid when:** Simple CRUD with no business logic

### 2. Service Layer Pattern

**Purpose:** Encapsulate business operations

```python
class OrderService:
    def __init__(self, order_repo, payment_processor):
        self.orders = order_repo
        self.payments = payment_processor
    
    def place_order(self, order_data):
        # Business logic flows here
        order = self.orders.create(order_data)
        self.payments.process(order)
        return order
```

**When to use:** Multi-step business operations
**Avoid when:** Simple data access only

### 3. Factory Pattern

**Purpose:** Hide object creation complexity

```python
class NotificationFactory:
    def create(self, channel):
        if channel == "email":
            return EmailNotification()
        elif channel == "sms":
            return SMSNotification()
        raise ValueError(f"Unknown channel: {channel}")
```

**When to use:** Multiple implementations, creation complexity
**Avoid when:** Single constructor, no variation

### 4. Strategy Pattern

**Purpose:** Select algorithm at runtime

```python
class PricingStrategy:
    def calculate(self, items): raise NotImplementedError

class BulkPricing(PricingStrategy):
    def calculate(self, items):
        return sum(items) * 0.8

class RegularPricing(PricingStrategy):
    def calculate(self, items):
        return sum(items)
```

**When to use:** Multiple algorithms, switching behavior
**Avoid when:** Single fixed algorithm

### 5. Observer Pattern

**Purpose:** Notify interested parties of changes

```python
class OrderPublisher:
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        self._observers.append(observer)
    
    def notify(self, order):
        for observer in self._observers:
            observer.update(order)
```

**When to use:** Event systems, coupled but not direct
**Avoid when:** Simple synchronous calls

## Clean Architecture Pattern

**Purpose:** Separate concerns into independent layers

```
┌─────────────────────────────────────┐
│           Presentation              │  ← Routers, CLI, UI
├─────────────────────────────────────┤
│           Application               │  ← Use cases, orchestration
├─────────────────────────────────────┤
│             Domain                  │  ← Entities, business rules
├─────────────────────────────────────┤
│          Infrastructure             │  ← Database, HTTP, external APIs
└─────────────────────────────────────┘
```

**Rules:**
- Dependencies point inward (outer depends on inner)
- Domain has no external dependencies
- Interfaces defined in inner layers, implemented in outer
- Each layer testable in isolation

**When to use:** Complex systems with multiple interfaces
**Avoid when:** Simple CRUD applications

## DDD Bounded Context Pattern

**Purpose:** Define clear boundaries for domain models

```
UserContext:
  - User entity
  - Registration service
  - Authentication service

OrderContext:
  - Order entity
  - Order fulfillment service
  - Payment coordination
```

**When to use:** Large domains with distinct subdomains
**Avoid when:** Single cohesive domain

## Anti-Patterns to Avoid

| Pattern | Anti-Pattern | Symptom | Fix |
|---------|--------------|---------|-----|
| Factory | God Factory | 100+ methods, switch statement | Split into specific factories |
| Service | God Service | 200+ methods | Extract domain services |
| Repository | Table Module | Business logic in repo | Move to domain layer |
| Observer | Event Soup | No clear message types | Define explicit event types |
| Composite | Recursive Maze | Unbounded nesting | Add termination conditions |

## Pattern Combinations to Know

### Service + Repository + Factory

```python
class OrderService:
    def __init__(self, repo_factory, payment_factory):
        self.orders = repo_factory.create()
        self.payments = payment_factory.create()
```

**Use for:** Testable service layer with configurable dependencies

### Strategy + Factory

```python
class PricingEngine:
    def __init__(self, strategy_factory):
        self.strategy_factory = strategy_factory
    
    def get_pricing(self, customer_type):
        strategy = self.strategy_factory.create(customer_type)
        return strategy.calculate(self.items)
```

**Use for:** Selectable algorithms with varying parameters

## Success Indicators

Patterns are working when:

1. Adding a new feature requires <3 new files
2. Each class fits in one screen (~200 lines)
3. Tests have no mocks
4. New devs can understand the structure in <1 hour
5. Changes in one layer do not require changes in others

## Pattern Selection Flow

```
Problem → Identify Type → Evaluate Options → Choose Simplest
              ↓
Is there one obvious solution? → No → Consider Composition
              ↓                            ↓
Yes → Use Simple Pattern → Is complexity growing? → Yes → Evolve Pattern