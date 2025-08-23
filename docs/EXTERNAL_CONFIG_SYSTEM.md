# Professional External Configuration System

## 🎯 Overview

This document describes the new professional external configuration system for Telegram Bot Manager that provides:

- **🔒 Security**: Secrets stored separately from configs
- **🔄 Version Management**: Automatic config migrations between versions  
- **📦 External Storage**: Configs stored outside project directory
- **💾 Backup System**: Automatic backups with retention policies
- **🛡️ Validation**: JSON schema validation for all configs
- **🔧 Professional CLI**: Command-line management tools

## 📁 Directory Structure

```
/home/nick/.telegram-bot-manager/
├── configs/
│   ├── bots.json           # Main bot configurations
│   └── version.json        # Version tracking
├── secrets/
│   └── secrets.env         # Encrypted secrets (chmod 600)
├── backups/
│   ├── auto_backup_*/      # Automatic backups
│   ├── migration_backup_*/ # Pre-migration backups
│   └── manual_backup_*/    # Manual backups
└── schemas/
    ├── bot_config_schema.json  # Configuration validation schema
    └── secrets_schema.json     # Secrets validation schema
```

## 🔧 CLI Usage

### Initialize System
```bash
# Initialize external config system
python scripts/config_manager_cli.py init

# Force reinitialize
python scripts/config_manager_cli.py init --force
```

### Migration
```bash
# Migrate from internal project configs
python scripts/config_manager_cli.py migrate --from ./bot_configs.json

# Dry run migration (preview changes)
python scripts/config_manager_cli.py migrate --from ./bot_configs.json --dry-run
```

### Configuration Management
```bash
# Show configuration summary
python scripts/config_manager_cli.py show

# Show specific bot
python scripts/config_manager_cli.py show --bot-id 1

# Show as JSON
python scripts/config_manager_cli.py show --format json
```

### Bot Management
```bash
# Update bot configuration
python scripts/config_manager_cli.py update-bot --id 1 --name "New Bot Name"
python scripts/config_manager_cli.py update-bot --id 1 --enable-ai true
python scripts/config_manager_cli.py update-bot --id 1 --context-limit 20
```

### Secrets Management
```bash
# Add/update secret
python scripts/config_manager_cli.py secret --add bot_1_token "1234567890:ABCD..."

# List secrets (keys only)
python scripts/config_manager_cli.py secret --list

# Remove secret
python scripts/config_manager_cli.py secret --remove old_bot_token
```

### Backup Management
```bash
# Create manual backup
python scripts/config_manager_cli.py backup --create --type manual

# List available backups
python scripts/config_manager_cli.py backup --list

# Clean up old backups (older than 30 days)
python scripts/config_manager_cli.py backup --cleanup 30
```

### Restore Operations
```bash
# Restore from backup
python scripts/config_manager_cli.py restore --backup /path/to/backup --confirm
```

### Validation
```bash
# Validate current configuration
python scripts/config_manager_cli.py validate
```

## 🔄 Migration Process

### Version 1.x → 2.0.0 Migration

The migration process automatically:

1. **Creates Backup**: Pre-migration backup is created
2. **Extracts Secrets**: Moves tokens/API keys to secure storage
3. **Updates Structure**: Converts to new schema format
4. **Validates Config**: Ensures all required fields exist
5. **Generates Report**: Detailed migration report

### Migration Report Example
```
=== CONFIGURATION MIGRATION REPORT ===
Version: 1.0.0 -> 2.0.0
Bots migrated: 1 -> 1
Secrets extracted: 2 items

=== SECURITY IMPROVEMENTS ===
- bot_1_telegram_token: Telegram bot token
- bot_1_openai_key: API key

=== VALIDATION PASSED ===
No issues detected in migration.
```

## 🔒 Security Features

### Secret Storage
- **Separate Files**: Secrets stored in separate `.env` file
- **File Permissions**: Secrets file has `chmod 600` (owner read/write only)
- **Reference System**: Configs contain references, not actual secrets
- **Schema Validation**: Secrets validated against schema

### Token References
Old format (insecure):
```json
{
  "telegram_token": "1234567890:ABCD...",
  "openai_api_key": "sk-proj-..."
}
```

New format (secure):
```json
{
  "telegram_token_ref": "bot_1_telegram_token",
  "openai_api_key_ref": "bot_1_openai_key"
}
```

## 📋 Configuration Schema

### Bot Configuration Schema v2.0.0
```json
{
  "version": "2.0.0",
  "bots": {
    "1": {
      "id": 1,
      "config": {
        "bot_name": "@diosybot",
        "telegram_token_ref": "bot_1_telegram_token",
        "openai_api_key_ref": "bot_1_openai_key",
        "assistant_id": "asst_EiyeubCPOqOJQ4MSLT17Cm7M",
        "group_context_limit": 15,
        "enable_ai_responses": true,
        "enable_voice_responses": false,
        "voice_model": "tts-1",
        "voice_type": "alloy",
        "marketplace": {
          "enabled": false,
          "title": "",
          "description": "",
          "category": "other"
        },
        "features": {
          "auto_responses": true,
          "command_handling": true,
          "file_processing": true,
          "image_generation": false,
          "web_search": false
        },
        "created_at": "2025-01-22T18:23:38",
        "updated_at": "2025-01-22T18:23:38"
      },
      "status": "running"
    }
  },
  "global_settings": {
    "max_bots": 10,
    "log_level": "INFO",
    "auto_backup": true,
    "backup_retention_days": 30
  },
  "admin_bot": {
    "enabled": false,
    "token_ref": "admin_bot_token",
    "admin_users": [],
    "notifications": {
      "bot_status": true,
      "high_cpu": true,
      "errors": true,
      "weekly_stats": true
    }
  }
}
```

## 💾 Backup System

### Automatic Backups
- **Pre-Save**: Before each configuration save
- **Pre-Migration**: Before version migrations
- **Scheduled**: Daily/weekly automated backups

### Backup Types
- **`auto`**: Automatic system backups
- **`manual`**: User-initiated backups  
- **`migration`**: Pre-migration backups
- **`pre_save`**: Pre-configuration save backups

### Retention Policy
- **Default**: 30 days retention
- **Configurable**: Via `backup_retention_days` setting
- **Manual Cleanup**: CLI command for cleanup

## 🔄 Update Process (Production Safe)

### 1. Project Update
```bash
# Update project code
git pull origin main

# External configs remain untouched
# No configuration loss during updates!
```

### 2. Configuration Migration (if needed)
```bash
# Check if migration is needed
python scripts/config_manager_cli.py validate

# Migrate if required
python scripts/config_manager_cli.py migrate --from ./old_config.json
```

### 3. Restart Application
```bash
# Restart with new code + preserved configs
python src/app.py
```

## 🔧 Integration with Legacy Code

### Automatic Compatibility
The system includes a legacy adapter that:
- **Detects** existing configs automatically
- **Migrates** on first use
- **Maintains** backward compatibility
- **Preserves** existing code functionality

### Legacy Code Example
```python
# Existing code continues to work unchanged
from src.config_manager import load_configs, save_configs

configs = load_configs()  # Automatically uses external system
save_configs(configs)     # Saves to external system
```

## 🛡️ Validation & Error Handling

### Schema Validation
- **JSON Schema**: All configs validated against schema
- **Type Checking**: Proper data types enforced
- **Required Fields**: Missing fields detected
- **Range Validation**: Numeric ranges validated

### Error Recovery
- **Backup Restore**: Automatic rollback on errors
- **Graceful Degradation**: Falls back to legacy system if needed
- **Detailed Logging**: Comprehensive error reporting

## 📊 Monitoring & Health Checks

### Configuration Health
```bash
# Check system health
python scripts/config_manager_cli.py validate

# Get status information
python -c "
from core.config.legacy_adapter import get_adapter
print(get_adapter().get_config_status())
"
```

### Status Fields
- **`using_external`**: Whether external system is active
- **`external_initialized`**: External system initialization status
- **`migration_attempted`**: Migration attempt status
- **`config_directory`**: Path to external configs

## 🚀 Benefits for Production

### Security
- ✅ **Secrets Protected**: Separate encrypted storage
- ✅ **Access Control**: File permissions properly set
- ✅ **No Git Exposure**: Secrets never in repository

### Reliability  
- ✅ **Update Safe**: Configs survive project updates
- ✅ **Backup Protected**: Multiple backup layers
- ✅ **Validation**: Schema validation prevents corruption

### Maintenance
- ✅ **Professional CLI**: Easy management tools
- ✅ **Migration Path**: Smooth version upgrades
- ✅ **Monitoring**: Health checks and status reports

### Scalability
- ✅ **External Storage**: Independent of project size
- ✅ **Schema Evolution**: Structured migration system
- ✅ **Multiple Environments**: Per-environment configs

## 🔮 Future Enhancements

### Planned Features
- **🔐 Encryption**: Encrypt entire config files
- **☁️ Cloud Sync**: Sync configs across deployments
- **📱 Web UI**: Web-based configuration management
- **🔄 Real-time**: Live config reloading
- **🏢 Multi-tenant**: Support for multiple bot collections

### Environment Support
- **Development**: Local config overrides
- **Staging**: Staging-specific settings
- **Production**: Production-hardened configs
- **Testing**: Isolated test configurations

---

## 🆘 Support & Troubleshooting

### Common Issues

**Migration Failed**
```bash
# Check source file exists
ls -la ./bot_configs.json

# Try dry-run first
python scripts/config_manager_cli.py migrate --from ./bot_configs.json --dry-run
```

**Validation Errors**
```bash
# Validate specific components
python scripts/config_manager_cli.py validate
```

**Backup/Restore Issues**
```bash
# List available backups
python scripts/config_manager_cli.py backup --list

# Create manual backup
python scripts/config_manager_cli.py backup --create
```

### Emergency Recovery
```bash
# Restore from latest backup
python scripts/config_manager_cli.py restore --backup $(ls -t /home/nick/.telegram-bot-manager/backups/ | head -1)

# Force fallback to legacy system
rm -rf /home/nick/.telegram-bot-manager/
```

---

*Professional External Configuration System - Telegram Bot Manager v2.0.0*




