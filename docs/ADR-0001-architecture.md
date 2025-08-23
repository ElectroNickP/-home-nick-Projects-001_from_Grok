# ADR-0001: Hexagonal Architecture Implementation

## Status
Accepted

## Context
The Telegram Bot Manager project has grown to a complex system with multiple responsibilities:
- Telegram bot management and communication
- OpenAI API integration
- Web interface and API endpoints
- Auto-update system
- Configuration management
- File-based storage

The current monolithic structure in `src/` directory has several issues:
1. **God Module**: `app.py` (1758 LOC) contains web server, API, authentication, and business logic
2. **Circular Dependencies**: Modules import each other creating tight coupling
3. **Mixed Concerns**: External API calls are scattered across multiple modules
4. **Hard Dependencies**: Business logic directly depends on external libraries (Flask, aiogram, OpenAI)
5. **No Interface Contracts**: Modules are tightly coupled without clear interfaces
6. **Testing Difficulties**: Hard to test business logic in isolation

## Decision
We will implement **Hexagonal Architecture** (Ports and Adapters pattern) to:
- Separate business logic from external concerns
- Make the system testable and maintainable
- Enable easy replacement of external dependencies
- Provide clear boundaries and interfaces

## Consequences

### Positive
- **Testability**: Business logic can be tested without external dependencies
- **Maintainability**: Clear separation of concerns makes code easier to understand
- **Flexibility**: External dependencies can be replaced without changing business logic
- **Scalability**: New features can be added without affecting existing code
- **Team Development**: Multiple developers can work on different layers independently

### Negative
- **Complexity**: More files and directories to manage
- **Learning Curve**: Team needs to understand hexagonal architecture principles
- **Migration Effort**: Significant refactoring required
- **Performance**: Additional abstraction layers may add minimal overhead

## Implementation

### Directory Structure
```
apps/                    # Entry points
├── api/                # HTTP API server
├── admin/              # Web admin interface
├── bots/               # Bot entry points
└── workers/            # Background workers

core/                   # Business logic (no IO)
├── domain/            # Entities, Value Objects, Policies
├── usecases/          # Application scenarios
└── ports/             # Interface contracts (Protocols)

adapters/              # External integrations
├── telegram/          # Telegram API implementation
├── updater/           # Auto-update implementation
├── storage/           # File/DB storage implementation
└── web/               # Flask templates & static files

infra/                 # Infrastructure concerns
├── config/            # Configuration management
├── logging/           # Logging setup
└── scripts/           # Dev/Ops scripts

tests/                 # Test suite
├── unit/             # Domain & Use Cases
├── integration/      # Adapters
├── e2e/              # End-to-end scenarios
└── contract/         # Port contract tests
```

### Import Rules
```
apps → core.usecases → core.domain
adapters ↔ core.ports (through interfaces)
domain ⊥ frameworks (no Flask, aiogram, etc.)
```

### Ports (Interfaces)
- **TelegramPort**: For Telegram API operations
- **ConfigStoragePort**: For configuration storage operations
- **AutoUpdaterPort**: For auto-update operations

### Migration Strategy
1. **Phase 1**: Create ports and contract tests
2. **Phase 2**: Extract adapters from existing code
3. **Phase 3**: Extract domain entities and use cases
4. **Phase 4**: Split entry points and add E2E tests

## Alternatives Considered

### 1. Clean Architecture
- **Pros**: Well-established pattern, comprehensive
- **Cons**: Over-engineered for our needs, complex layers

### 2. Domain-Driven Design (DDD)
- **Pros**: Rich domain model, business-focused
- **Cons**: Complex for our use case, requires domain expertise

### 3. Microservices
- **Pros**: Independent deployment, technology diversity
- **Cons**: Overkill for current scale, operational complexity

### 4. Keep Current Structure
- **Pros**: No migration effort, familiar to team
- **Cons**: Technical debt will grow, harder to maintain

## References
- [Hexagonal Architecture by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Ports and Adapters Pattern](https://martinfowler.com/articles/microservices.html#Decouple)

## Related ADRs
- ADR-0002: Database Migration Strategy (future)
- ADR-0003: Testing Strategy (future)
- ADR-0004: Deployment Strategy (future)

