# product-integration

Framework for seamlessly integrating external systems, APIs, and services into your product while maintaining testability and flexibility.

## Core Principle

Integration layers should be thin, adapters should be explicit, and dependencies should flow inward. Keep your product logic independent of external dependencies.

## When to Apply

- Adding new API or service integration
- Replacing an existing integration
- Setting up new product dependencies
- Designing system boundaries for external systems

## The Integration Framework

### Four Integration Layers

```
┌─────────────────────────────────────┐
│           Product Logic             │  ← business rules, core models
├─────────────────────────────────────┤
│         Integration Interface       │  ← defined by you, lives in product
├─────────────────────────────────────┤
│          Adapter Layer              │  ← translates to external API
├─────────────────────────────────────┤
│         External Service            │  ← third-party or external
└─────────────────────────────────────┘
```

**Rules:**
- Product logic knows about interface, not implementation
- Adapter implements interface and knows about external API
- External service is untouched (black box)
- Dependencies point LEFT (product → adapters, not right)

## Integration Patterns

### Pattern 1: Repository Pattern

**Use for:** Database, API, file-based data

```python
# Interface (in product)
class UserRepository:
    def get_by_id(self, user_id) -> User: ...
    def save(self, user) -> None: ...
    def find_by_email(self, email) -> User | None: ...

# Adapter (external-specific)
class PostgreSQLUserRepository(UserRepository):
    def __init__(self, db_pool):
        self.pool = db_pool
    
    def get_by_id(self, user_id):
        row = self.pool.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return User.from_dict(row) if row else None
```

**Benefits:**
- Product logic never imports external SDK
- Easy to swap databases
- Easy to test (mock the interface)

### Pattern 2: Adapter Pattern

**Use for:** External HTTP APIs, webhooks, web services

```python
# Interface (in product)
class PaymentProcessor:
    def charge(self, amount, currency, card_token) -> PaymentResult: ...
    def refund(self, payment_id) -> RefundResult: ...

# Adapter (external-specific)
class StripePaymentProcessor(PaymentProcessor):
    def __init__(self, api_key):
        self.stripe = stripe.API(api_key)
    
    def charge(self, amount, currency, card_token):
        result = self.stripe.charges.create(
            amount=amount,
            currency=currency,
            source=card_token
        )
        return PaymentResult(
            id=result.id,
            status=result.status,
            amount=result.amount
        )
```

**Benefits:**
- Product code never mentions Stripe
- Easy to switch payment providers
- Can implement mock for testing

### Pattern 3: Client Pattern

**Use for:** Third-party services (email, auth, storage)

```python
# Interface (in product)
class EmailService:
    def send(self, to, subject, body, html=False) -> bool: ...
    def batch_send(self, recipients, subject, body) -> list[bool]: ...

# Adapter (external-specific)
class SendGridEmailService(EmailService):
    def __init__(self, api_key):
        self.client = sendgrid.SendGridClient(api_key)
    
    def send(self, to, subject, body, html=False):
        message = sendgrid.Mail(
            to=to,
            subject=subject,
            html=body if html else None,
            text=body if not html else None
        )
        return self.client.send(message) == 200
```

**Benefits:**
- Email implementation hidden
- Easy to test without real email
- Can swap providers

## Integration Quality Checklist

Before production integration:

### Functionality

- [ ] Integration handles success case correctly
- [ ] Integration handles all error cases explicitly
- [ ] Integration has appropriate timeouts
- [ ] Integration has retry logic for transient failures

### Observability

- [ ] Integration has logging (success, failure, timing)
- [ ] Integration has metrics (latency, error rate)
- [ ] Integration has health checks (when applicable)

### Maintainability

- [ ] Interface is stable
- [ ] Adapter is isolated (easy to replace)
- [ ] No external SDK imports leak into product logic
- [ ] Configuration is external (not hardcoded)

### Security

- [ ] Credentials are stored securely (env vars, secrets manager)
- [ ] No sensitive data logged
- [ ] Proper error messages (no leaks)
- [ ] Rate limiting is respected

## Common Integration Types

### Database Integration

**Pattern:** Repository + Unit of Work

```python
class UnitOfWork:
    def __init__(self, session_factory):
        self.session = session_factory()
        self.users = UserRepository(self.session)
        self.orders = OrderRepository(self.session)
    
    def commit(self):
        self.session.commit()
    
    def rollback(self):
        self.session.rollback()
```

**Best for:** Relational or document databases
**Avoid:** Direct SQL/ORM in business logic

### HTTP API Integration

**Pattern:** Adapter with Circuit Breaker

```python
class ExternalAPIClient:
    def __init__(self, base_url, timeout=5):
        self.base_url = base_url
        self.timeout = timeout
        self.circuit_breaker = CircuitBreaker()
    
    def get(self, path, params=None):
        return self.circuit_breaker.call(
            lambda: requests.get(
                f"{self.base_url}{path}",
                params=params,
                timeout=self.timeout
            )
        )
```

**Best for:** REST, GraphQL APIs
**Avoid:** Direct HTTP client in product code

### Message Queue Integration

**Pattern:** Publisher/Subscriber

```python
# Interface
class MessagePublisher:
    def publish(self, queue, message): ...
    def publish_batch(self, queue, messages): ...

# Adapter
class RabbitMQPublisher(MessagePublisher):
    def __init__(self, connection_string):
        self.conn = amqp.Connection(connection_string)
    
    def publish(self, queue, message):
        channel = self.conn.channel()
        channel.basic_publish(exchange='', routing_key=queue, body=message)
```

**Best for:** Async processing, decoupled services
**Avoid:** Synchronous calls through message queues

### Authentication/Authorization

**Pattern:** Service Adapter

```python
# Interface
class AuthService:
    def authenticate(self, credentials) -> AuthResult: ...
    def create_token(self, user_id) -> str: ...
    def validate_token(self, token) -> UserContext: ...

# Adapter
class Auth0AuthService(AuthService):
    def __init__(self, domain, audience):
        self.domain = domain
        self.audience = audience
    
    def authenticate(self, credentials):
        # Auth0 specific auth flow
        ...
```

**Best for:** Multi-provider auth support
**Avoid:** Auth SDK directly in controllers

## Integration Testing Strategy

### Unit Tests (with mocks)

```python
def test_user_registration_with_email(NotificationServiceMock):
    mock = NotificationServiceMock()
    service = RegistrationService(notifier=mock)
    
    service.register("user@example.com")
    
    mock.send.assert_called_once_with(
        "user@example.com",
        "Welcome!"
    )
```

### Integration Tests (with real adapter)

```python
def test_email_delivery(SendGridEmailService):
    service = SendGridEmailService(api_key=os.environ["SENDGRID_API_KEY"])
    
    result = service.send("test@example.com", "Test", "Body")
    
    assert result == True  # Real email sent
```

### Contract Tests (between service and adapter)

```python
def test_payment_adapter_contracts(PaymentProcessor):
    # Verify adapter satisfies interface
    assert isinstance(PaymentProcessor, PaymentProcessor)
    assert hasattr(PaymentProcessor, "charge")
    assert hasattr(PaymentProcessor, "refund")
```

## Integration Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Direct SDK in product | Tightly coupled, hard to test | Extract interface + adapter |
| Multiple adapters in one class | Violates single responsibility | Separate adapters |
| Logic in adapter | Hard to test | Move logic to product |
| Hardcoded config | Environment-specific | Externalize configuration |
| No error handling | Silent failures | Explicit error handling |
| Shared client instance | Concurrency issues | Use dependency injection |

## Configuration Strategy

```yaml
# config.yaml (not in code)
integrations:
  payment:
    provider: stripe
    stripe:
      api_key: ${STRIPE_API_KEY}
      webhook_secret: ${STRIPE_WEBHOOK_SECRET}
  email:
    provider: sendgrid
    sendgrid:
      api_key: ${SENDGRID_API_KEY}
```

**Best practices:**
- Use environment variables for secrets
- Externalize configuration (config files, env, secrets manager)
- Prefer provider-based config (do not hardcode provider names)
- Default to development adapters for easy local testing

## Success Indicators

Integration is working well when:

- Adding a new integration requires <3 files
- No product code imports external SDKs
- Integration tests run in <1 second (mocked)
- Can swap providers without changing product code
- External failures are handled gracefully
- Logs clearly show integration boundaries