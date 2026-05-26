---
name: technology-agnostic-framework
description: Universal project structure and setup that works with any programming language, framework, or technology stack while enabling progressive technology selection.
---
# technology-agnostic-framework

Universal project structure and setup that works with any programming language, framework, or technology stack while enabling progressive technology selection.

## Core Principle

Structure your project around concerns, not technologies. The foundation should be independent of tech choices, allowing you to add or replace technologies without rewriting your architecture.

## When to Apply

- Starting a new project or repository
- Migrating tech stack while retaining domain logic
- Building project templates or scaffolds
- Designing a monorepo structure

## The Technology-Agnostic Structure

```
project/
├── src/                              # Core implementation
│   ├── core/                         # Business logic, domain models
│   ├── api/                          # Interfaces (HTTP, CLI, RPC)
│   ├── infrastructure/               # External integrations
│   └── utils/                        # Shared helpers
├── tests/                            # Test files
│   ├── unit/                         # Unit tests (fast, isolated)
│   ├── integration/                  # Integration tests (with dependencies)
│   └── e2e/                          # End-to-end tests (full flow)
├── docs/                             # Documentation (loaded on-demand)
├── config/                           # Configuration
│   ├── environment/                  # Environment-specific configs
│   └── schema/                       # Config validation schema
├── scripts/                          # Automation scripts
│   ├── build/                        # Build automation
│   ├── test/                         # Test runners
│   └── deploy/                       # Deployment helpers
└── .kiro/                            # AI agent configuration
    ├── skills/                       # Agent skills
    ├── steering/                     # Project-specific guidance
    └── agent-settings.json           # Agent configuration
```

## Layer Principles

### Layer 1: Core (Technology-Free)

**Purpose:** Business logic, domain models, rules

**Characteristics:**
- No framework-specific imports
- No external dependencies
- Pure functions where possible
- Testable without setup

```python
# src/core/users/user.py
class User:
    def __init__(self, id, email, name):
        self.id = id
        self.email = email
        self.name = name
    
    def can_vote(self):
        return self.age >= 18
    
    def update_email(self, new_email):
        if not self._is_valid_email(new_email):
            raise ValueError("Invalid email")
        self.email = new_email
    
    def _is_valid_email(self, email):
        return "@" in email and "." in email.split("@")[-1]
```

**Language-agnostic pattern:**
- Domain models live in src/core/domain/
- Business rules live in src/core/domains/service.py
- No framework imports allowed

### Layer 2: Interfaces (Adapter-Friendly)

**Purpose:** HTTP endpoints, CLI commands, message handlers

**Characteristics:**
- Know about protocol, not business logic
- Translate external formats to domain objects
- Validate inputs, call core, return results

```python
# src/api/http/users_routes.py
def create_user_route(request):
    try:
        data = parse_and_validate(request.json, CreateUserSchema)
        
        user = User(
            id=None,
            email=data.email,
            name=data.name,
            age=data.age
        )
        
        user_service = UserService()
        user = user_service.create(user)
        
        return success_response(user.to_dict())
    except ValueError as e:
        return error_response(400, str(e))
```

**Language-agnostic pattern:**
- HTTP routes in src/api/http/
- CLI commands in src/api/cli/
- Message handlers in src/api/messages/

### Layer 3: Infrastructure (External-Only)

**Purpose:** Database, external APIs, file system, 3rd party services

**Characteristics:**
- Implements interfaces from core
- Knows about external systems
- Contains adapter code only
- No business logic

```python
# src/infrastructure/database/user_repository.py
class PostgreSQLUserRepository(UserRepository):
    def __init__(self, db_pool):
        self.pool = db_pool
    
    def find_by_id(self, user_id):
        row = self.pool.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        return User.from_dict(row) if row else None
```

**Language-agnostic pattern:**
- Database implementations in src/infrastructure/database/
- API adapters in src/infrastructure/api/
- File operations in src/infrastructure/files/

### Layer 4: Configuration (Externalized)

**Purpose:** All configuration, not hardcoded

**Characteristics:**
- Environment-specific configs
- Secret management
- Runtime configuration
- Schema validation

```yaml
# config/environment/development.yaml
server:
  host: localhost
  port: 3000
  debug: true

database:
  type: postgresql
  host: localhost
  port: 5432
  database: app_dev

integrations:
  email_provider: sendgrid
  payment_provider: stripe
```

## Project Configuration Files

### .kiro/agent-settings.json

```json
{
  "agent_name": "project-dev",
  "skills": [
    "#kiro/skills/token-optimization/README.md",
    "#kiro/skills/coding-standards/README.md",
    "#kiro/skills/design-patterns/README.md",
    "#kiro/skills/product-integration/README.md"
  ],
  "default_technology": "python",
  "enable_self_learning": true
}
```

### .kiro/steering/project-standards.md

```markdown
# Project Standards

This project follows these conventions:

1. **Technology-Agnostic Structure** - Layers separated by concern
2. **Coding Standards** - See skill: coding-standards
3. **Design Patterns** - See skill: design-patterns
4. **Integration Patterns** - See skill: product-integration

## Technology Selection

New technologies should be:

1. Well-maintained with active community
2. Good documentation
3. Adhere to open standards
4. Compatible with our integration patterns

## Testing Requirements

- Unit tests: 80%+ coverage
- Integration tests: critical paths
- E2E tests: user-facing flows
- Tests must be fast (<100ms each)
```

## Language-agnostic Patterns

### Domain Modeling (Any Language)

```
Java: src/core/java/package/model/
Python: src/core/python/model/
JavaScript: src/core/typescript/models/
Ruby: src/core/ruby/models/
```

### Repository Pattern (Any Language)

```java
// Java interface
public interface UserRepository {
    User findbyId(String id);
    void save(User user);
}
```

```python
# Python interface
class UserRepository:
    def find_by_id(self, user_id) -> User: ...
    def save(self, user) -> None: ...
```

```typescript
// TypeScript interface
interface UserRepository {
    findById(id: string): User | null
    save(user: User): void
}
```

## Progressive Tech Stack Selection

### Phase 1: Foundation (Technology-Free)

```
1. Define domain models
2. Implement core business logic
3. Define interfaces (adapter contracts)
4. Write unit tests
```

### Phase 2: Technology Selection

```
1. Choose database (SQL, NoSQL, in-memory)
2. Choose web framework
3. Choose messaging system
4. Choose monitoring tools
```

### Phase 3: Implementation

```
1. Implement infrastructure adapters
2. Implement API layers
3. Write integration tests
4. Deploy and monitor
```

## Cross-Project Consistency

### Monorepo Structure

```
monorepo/
├── packages/
│   ├── core/               # Shared domain logic
│   ├── auth/               # Authentication service
│   ├── billing/            # Billing service
│   └── api-gateway/        # API gateway
├── shared/
│   ├── config/             # Shared configs
│   ├── testing/            # Shared test utilities
│   └── scripts/            # Shared automation
└── .kiro/
    ├── skills/             # Shared skills
    └── steering/           # Shared standards
```

## Technology Agnostic Success Indicators

Your structure is technology-agnostic when:

1. **Tech Swapping:** Can replace database with <10 file changes
2. **No Tech Lock-in:** Core code has zero external imports
3. **Language Independence:** Same structure works for Java, Python, TS
4. **Team agnostic:** New language skills can join without relearning structure
5. **Progressive:** Add technology when you need it, not upfront

## Migration Path

### From Tech-Locked to Technology-Agnostic

```
Step 1: Extract domain models (no external deps)
Step 2: Create interfaces for all external calls
Step 3: Implement adapters (external specific)
Step 4: Update code to use interfaces
Step 5: Remove direct external imports
```

**Rule:** One component at a time. Do not rewrite everything.