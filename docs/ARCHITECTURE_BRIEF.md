# 🏗️ ARCHITECTURE BRIEF - Telegram Bot Manager

## 📊 Current State Analysis

### 🔍 Dependency Map
```
src/app.py (1758 LOC) - God Module
├── Flask Web Server (HTTP API + Templates)
├── Authentication & Sessions
├── Bot Management API
├── Marketplace API
├── Auto-update API
└── System Monitoring

src/telegram_bot.py (472 LOC) - Telegram Integration
├── OpenAI Assistant API
├── Voice Processing (Whisper + TTS)
├── Group Context Analysis
└── Message Handling

src/auto_updater.py (574 LOC) - Update System
├── Git Operations
├── Backup Management
├── Process Management
└── Rollback System

src/admin_bot.py (557 LOC) - Admin Bot
├── Telegram Bot Logic
├── System Monitoring
├── Bot Control Interface
└── Notifications

src/bot_manager.py (157 LOC) - Bot Lifecycle
├── Thread Management
├── Start/Stop Operations
└── Status Tracking

src/config_manager.py (167 LOC) - Configuration
├── JSON File Storage
├── Thread-safe Operations
└── Conversation Cache
```

### ⚠️ Hot Spots & Issues

1. **God Module**: `app.py` (1758 LOC) - смешение HTTP API, веб-интерфейса, бизнес-логики
2. **Circular Dependencies**: `bot_manager.py` ↔ `telegram_bot.py` ↔ `config_manager.py`
3. **Mixed Concerns**: Telegram API calls scattered across multiple modules
4. **Hard Dependencies**: Direct imports of external libraries in business logic
5. **No Interface Contracts**: Tight coupling between modules
6. **File-based Storage**: JSON files instead of proper database
7. **Log Files in Git**: Development artifacts polluting repository

### 📈 Quick Wins (3-7 пунктов)

1. **Extract Ports** - Создать интерфейсы для Telegram, Storage, Updater
2. **Split God Module** - Разделить `app.py` на API, Web, Admin entrypoints
3. **Remove Log Files** - Очистить репозиторий от .log файлов
4. **Add Import Contracts** - Настроить import-linter для архитектурных правил
5. **Extract Domain** - Вынести бизнес-сущности (Bot, Config, Update)
6. **Add Type Hints** - Улучшить типизацию для mypy
7. **Setup Quality Tools** - ruff, black, pre-commit hooks

## 🎯 Target Architecture

### 📁 Directory Structure
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

docs/                 # Documentation
├── ARCHITECTURE_BRIEF.md
├── MIGRATION_PLAN.md
└── ADR-*.md
```

### 🔄 Import Rules
```
apps → core.usecases → core.domain
adapters ↔ core.ports (through interfaces)
domain ⊥ frameworks (no Flask, aiogram, etc.)
```

### 🏗️ Architecture Principles

1. **Hexagonal Architecture** - Ports & Adapters pattern
2. **Dependency Inversion** - Depend on abstractions, not concretions
3. **Single Responsibility** - Each module has one reason to change
4. **Open/Closed** - Open for extension, closed for modification
5. **Interface Segregation** - Small, focused interfaces

## 🚀 Migration Strategy

### Phase 1: Foundation (Week 1)
- Create directory structure
- Add quality tools (ruff, black, mypy)
- Setup import contracts
- Extract ports and interfaces

### Phase 2: Adapters (Week 2)
- Extract Telegram adapter
- Extract Storage adapter
- Extract Updater adapter
- Add contract tests

### Phase 3: Domain & Use Cases (Week 3)
- Extract domain entities
- Extract application use cases
- Add unit tests
- Remove business logic from adapters

### Phase 4: Entry Points (Week 4)
- Split app.py into focused entry points
- Add E2E tests
- Update documentation
- Performance optimization

## 📊 Success Metrics

- **Code Quality**: 0 import violations, 100% type coverage
- **Test Coverage**: 90%+ unit tests, 80%+ integration tests
- **Performance**: <2s API response time, <5s bot startup
- **Maintainability**: <500 LOC per module, <3 cyclomatic complexity
- **Deployment**: Zero-downtime updates, automated rollback

## 🔧 Assumptions

1. **Backward Compatibility**: Existing API endpoints must continue working
2. **Gradual Migration**: No big-bang refactoring, iterative approach
3. **Test Coverage**: Maintain existing test suite during migration
4. **Performance**: No degradation in response times
5. **Team Size**: Single developer, but preparing for team growth

