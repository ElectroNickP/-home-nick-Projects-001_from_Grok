# 📋 MIGRATION PLAN - Telegram Bot Manager Refactoring

## 🎯 Overview

**Goal**: Transform current monolithic structure into modular, scalable hexagonal architecture
**Timeline**: 4 weeks, 2-3 iterations per week
**Approach**: Iterative refactoring with zero behavior changes
**Success Criteria**: All tests pass, no performance degradation

## 📅 Iteration Schedule

### Week 1: Foundation Setup
- **T1.1** (2h): Directory structure + quality tools
- **T1.2** (2h): Ports extraction + contract tests
- **T1.3** (2h): Import contracts + CI setup

### Week 2: Adapter Extraction
- **T2.1** (2h): Telegram adapter
- **T2.2** (2h): Storage adapter  
- **T2.3** (2h): Updater adapter

### Week 3: Domain & Use Cases
- **T3.1** (2h): Domain entities
- **T3.2** (2h): Application use cases
- **T3.3** (2h): Unit test coverage

### Week 4: Entry Points & Polish
- **T4.1** (2h): API entry point
- **T4.2** (2h): Admin entry point
- **T4.3** (2h): E2E tests + documentation

## 🔧 Detailed Iterations

### T1.1: Directory Structure + Quality Tools (2h)

**Goal**: Create new architecture foundation without breaking existing code

**Tasks**:
```bash
# 1. Create directory structure
mkdir -p apps/{api,admin,bots,workers}
mkdir -p core/{domain,usecases,ports}
mkdir -p adapters/{telegram,updater,storage,web}
mkdir -p infra/{config,logging,scripts}
mkdir -p tests/{unit,integration,e2e,contract}
mkdir -p docs

# 2. Move existing files to temporary locations
cp src/app.py apps/api/app.py.backup
cp src/telegram_bot.py adapters/telegram/telegram_bot.py.backup
cp src/config_manager.py adapters/storage/config_manager.py.backup
cp src/auto_updater.py adapters/updater/auto_updater.py.backup
```

**Files to create**:
- `pyproject.toml` - Quality tools configuration
- `.importlinter` - Import contract rules
- `.pre-commit-config.yaml` - Pre-commit hooks
- `infra/scripts/dev-setup.sh` - Development environment

**Success Criteria**:
- ✅ New directory structure exists
- ✅ Quality tools installed and configured
- ✅ All existing tests still pass
- ✅ No import errors

**Rollback Plan**: Delete new directories, restore original structure

---

### T1.2: Ports Extraction + Contract Tests (2h)

**Goal**: Define interface contracts for external dependencies

**Tasks**:
```python
# core/ports/telegram.py
from typing import Protocol, Any

class TelegramPort(Protocol):
    async def set_webhook(self, url: str, secret: str | None = None) -> None: ...
    async def send_message(self, chat_id: str, text: str, **opts: Any) -> str: ...
    async def send_voice(self, chat_id: str, source: str, **opts: Any) -> str: ...
    async def get_me(self) -> dict: ...
    async def validate_token(self, token: str) -> bool: ...

# core/ports/storage.py
class ConfigStoragePort(Protocol):
    def read_config(self) -> dict: ...
    def write_config(self, patch: dict) -> None: ...
    def get_bot_config(self, bot_id: int) -> dict | None: ...
    def update_bot_config(self, bot_id: int, config: dict) -> None: ...
    def delete_bot_config(self, bot_id: int) -> None: ...

# core/ports/updater.py
class AutoUpdaterPort(Protocol):
    def check_updates(self) -> dict: ...
    def apply_update(self, version: str) -> bool: ...
    def create_backup(self) -> str: ...
    def restore_backup(self, backup_id: str) -> bool: ...
```

**Files to create**:
- `core/ports/__init__.py`
- `core/ports/telegram.py`
- `core/ports/storage.py`
- `core/ports/updater.py`
- `tests/contract/test_telegram_port.py`
- `tests/contract/test_storage_port.py`
- `tests/contract/test_updater_port.py`

**Success Criteria**:
- ✅ All ports defined with proper type hints
- ✅ Contract tests pass with mock implementations
- ✅ No breaking changes to existing code

---

### T1.3: Import Contracts + CI Setup (2h)

**Goal**: Enforce architectural boundaries through import rules

**Tasks**:
```ini
# .importlinter
[importlinter]
root_package = .

[contract:layers]
name = Layered architecture
layers =
    apps
    core.usecases
    core.domain
containers = .

[contract:ports]
name = Port contracts
source_modules = core.ports
forbidden_modules = adapters
```

**Files to create**:
- `.importlinter`
- `.github/workflows/ci.yml`
- `infra/scripts/lint-imports.sh`

**Success Criteria**:
- ✅ Import-linter catches violations
- ✅ CI pipeline runs successfully
- ✅ No import violations in existing code

---

### T2.1: Telegram Adapter (2h)

**Goal**: Extract Telegram API calls into dedicated adapter

**Tasks**:
```python
# adapters/telegram/telegram_adapter.py
from core.ports.telegram import TelegramPort
from aiogram import Bot, Dispatcher

class AiogramTelegramAdapter(TelegramPort):
    def __init__(self, token: str):
        self.bot = Bot(token)
        self.dp = Dispatcher()
    
    async def send_message(self, chat_id: str, text: str, **opts: Any) -> str:
        result = await self.bot.send_message(chat_id, text, **opts)
        return str(result.message_id)
```

**Files to modify**:
- Extract from `src/telegram_bot.py`
- Create `adapters/telegram/__init__.py`
- Update imports in existing modules

**Success Criteria**:
- ✅ All Telegram API calls go through adapter
- ✅ Contract tests pass with real implementation
- ✅ Existing bot functionality unchanged

---

### T2.2: Storage Adapter (2h)

**Goal**: Extract configuration storage into dedicated adapter

**Tasks**:
```python
# adapters/storage/json_storage.py
from core.ports.storage import ConfigStoragePort
import json
import threading

class JsonConfigAdapter(ConfigStoragePort):
    def __init__(self, config_file: str):
        self.config_file = config_file
        self._lock = threading.Lock()
    
    def read_config(self) -> dict:
        with self._lock:
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                return {}
```

**Files to modify**:
- Extract from `src/config_manager.py`
- Create `adapters/storage/__init__.py`
- Update imports in existing modules

**Success Criteria**:
- ✅ All config operations go through adapter
- ✅ Thread safety maintained
- ✅ Existing functionality unchanged

---

### T2.3: Updater Adapter (2h)

**Goal**: Extract auto-update logic into dedicated adapter

**Tasks**:
```python
# adapters/updater/git_updater.py
from core.ports.updater import AutoUpdaterPort
import subprocess
import shutil

class GitUpdaterAdapter(AutoUpdaterPort):
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
    
    def check_updates(self) -> dict:
        # Git fetch and compare logic
        pass
    
    def apply_update(self, version: str) -> bool:
        # Git pull and restart logic
        pass
```

**Files to modify**:
- Extract from `src/auto_updater.py`
- Create `adapters/updater/__init__.py`
- Update imports in existing modules

**Success Criteria**:
- ✅ All update operations go through adapter
- ✅ Backup/rollback functionality maintained
- ✅ Existing update process unchanged

---

### T3.1: Domain Entities (2h)

**Goal**: Extract business entities from existing code

**Tasks**:
```python
# core/domain/bot.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Bot:
    id: int
    name: str
    telegram_token: str
    openai_api_key: str
    assistant_id: str
    status: str = "stopped"
    created_at: datetime = None
    
    def start(self) -> None:
        self.status = "running"
    
    def stop(self) -> None:
        self.status = "stopped"

# core/domain/config.py
@dataclass
class BotConfig:
    bot_id: int
    settings: dict
    metadata: dict
```

**Files to create**:
- `core/domain/__init__.py`
- `core/domain/bot.py`
- `core/domain/config.py`
- `core/domain/update.py`

**Success Criteria**:
- ✅ Business entities extracted
- ✅ No framework dependencies in domain
- ✅ Rich domain model with behavior

---

### T3.2: Application Use Cases (2h)

**Goal**: Extract application scenarios from existing code

**Tasks**:
```python
# core/usecases/bot_management.py
from core.domain.bot import Bot
from core.ports.telegram import TelegramPort
from core.ports.storage import ConfigStoragePort

class BotManagementUseCase:
    def __init__(self, telegram: TelegramPort, storage: ConfigStoragePort):
        self.telegram = telegram
        self.storage = storage
    
    def start_bot(self, bot_id: int) -> bool:
        config = self.storage.get_bot_config(bot_id)
        if not config:
            return False
        
        bot = Bot(**config)
        bot.start()
        # Start bot logic
        return True
```

**Files to create**:
- `core/usecases/__init__.py`
- `core/usecases/bot_management.py`
- `core/usecases/update_management.py`
- `core/usecases/config_management.py`

**Success Criteria**:
- ✅ Application logic extracted
- ✅ Use cases orchestrate domain and ports
- ✅ No direct adapter dependencies

---

### T3.3: Unit Test Coverage (2h)

**Goal**: Add comprehensive unit tests for domain and use cases

**Tasks**:
```python
# tests/unit/test_bot_management.py
import pytest
from unittest.mock import Mock
from core.usecases.bot_management import BotManagementUseCase

def test_start_bot_success():
    telegram_mock = Mock()
    storage_mock = Mock()
    storage_mock.get_bot_config.return_value = {
        "id": 1, "name": "TestBot", "telegram_token": "token"
    }
    
    use_case = BotManagementUseCase(telegram_mock, storage_mock)
    result = use_case.start_bot(1)
    
    assert result is True
    storage_mock.get_bot_config.assert_called_once_with(1)
```

**Files to create**:
- `tests/unit/test_bot.py`
- `tests/unit/test_bot_management.py`
- `tests/unit/test_update_management.py`

**Success Criteria**:
- ✅ 90%+ test coverage for domain
- ✅ 80%+ test coverage for use cases
- ✅ All tests pass

---

### T4.1: API Entry Point (2h)

**Goal**: Split app.py into focused API entry point

**Tasks**:
```python
# apps/api/app.py
from flask import Flask
from core.usecases.bot_management import BotManagementUseCase
from adapters.telegram.aiogram_adapter import AiogramTelegramAdapter
from adapters.storage.json_adapter import JsonConfigAdapter

app = Flask(__name__)

# Dependency injection
telegram_adapter = AiogramTelegramAdapter()
storage_adapter = JsonConfigAdapter("config.json")
bot_use_case = BotManagementUseCase(telegram_adapter, storage_adapter)

@app.route("/api/bots", methods=["POST"])
def create_bot():
    # Use case orchestration
    pass
```

**Files to modify**:
- Extract API routes from `src/app.py`
- Create `apps/api/__init__.py`
- Update imports and dependencies

**Success Criteria**:
- ✅ API functionality extracted
- ✅ All existing endpoints work
- ✅ Clean separation of concerns

---

### T4.2: Admin Entry Point (2h)

**Goal**: Extract admin interface into separate entry point

**Tasks**:
```python
# apps/admin/app.py
from flask import Flask, render_template
from core.usecases.bot_management import BotManagementUseCase

app = Flask(__name__, template_folder='../../adapters/web/templates')

@app.route("/")
def admin_dashboard():
    # Admin interface logic
    pass
```

**Files to modify**:
- Extract admin routes from `src/app.py`
- Move templates to `adapters/web/templates/`
- Create `apps/admin/__init__.py`

**Success Criteria**:
- ✅ Admin interface extracted
- ✅ Templates properly organized
- ✅ Authentication maintained

---

### T4.3: E2E Tests + Documentation (2h)

**Goal**: Add end-to-end tests and update documentation

**Tasks**:
```python
# tests/e2e/test_bot_lifecycle.py
import pytest
from apps.api.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_bot_lifecycle(client):
    # Create bot
    response = client.post('/api/bots', json={
        'name': 'TestBot',
        'telegram_token': 'test_token'
    })
    assert response.status_code == 201
    
    # Start bot
    bot_id = response.json['id']
    response = client.post(f'/api/bots/{bot_id}/start')
    assert response.status_code == 200
```

**Files to create**:
- `tests/e2e/test_bot_lifecycle.py`
- `tests/e2e/test_update_process.py`
- `docs/API.md`
- `docs/DEPLOYMENT.md`

**Success Criteria**:
- ✅ E2E tests cover main scenarios
- ✅ Documentation updated
- ✅ All tests pass

## 🔍 Quality Gates

### After Each Iteration
- ✅ All existing tests pass
- ✅ No import violations
- ✅ No performance regression
- ✅ Code coverage maintained

### Final Acceptance Criteria
- ✅ Zero import violations
- ✅ 90%+ unit test coverage
- ✅ <500 LOC per module
- ✅ All E2E scenarios pass
- ✅ Documentation complete

## 🚨 Risk Mitigation

### Technical Risks
- **Breaking Changes**: Each iteration maintains backward compatibility
- **Performance Issues**: Continuous monitoring and benchmarks
- **Test Failures**: Comprehensive test suite with rollback capability

### Process Risks
- **Scope Creep**: Strict timeboxing (2h per iteration)
- **Quality Degradation**: Automated quality gates
- **Team Coordination**: Clear documentation and handoffs

## 📊 Progress Tracking

### Metrics to Track
- Import violations count
- Test coverage percentage
- Module size (LOC)
- Performance benchmarks
- Technical debt score

### Weekly Reviews
- Architecture compliance check
- Performance regression analysis
- Test coverage review
- Documentation completeness

## 🎯 Success Definition

**Complete when**:
1. All code follows hexagonal architecture
2. Zero import violations
3. 90%+ test coverage
4. All existing functionality preserved
5. Performance maintained or improved
6. Documentation complete and accurate

