"""
Unit тесты для config_manager.py
"""

import json
import os

# Импортируем модуль для тестирования
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, "src")
import config_manager as cm


@pytest.mark.unit
class TestConfigManager:
    """Тесты для config_manager"""

    def test_load_configs_success(self, temp_config_file):
        """Тест успешной загрузки конфигураций"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            # Проверяем, что конфигурации загружены
            assert hasattr(cm, "BOT_CONFIGS")
            assert isinstance(cm.BOT_CONFIGS, dict)
            assert "1" in cm.BOT_CONFIGS

            bot_config = cm.BOT_CONFIGS["1"]
            assert bot_config["id"] == 1
            assert bot_config["config"]["bot_name"] == "Test Bot 1"

    def test_load_configs_file_not_exists(self):
        """Тест загрузки конфигураций при отсутствии файла"""
        with patch.object(cm, "CONFIG_FILE", "/nonexistent/file.json"):
            cm.load_configs()
            assert cm.BOT_CONFIGS == {}

    def test_load_configs_invalid_json(self):
        """Тест загрузки конфигураций с невалидным JSON"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json}')
            temp_file = f.name

        try:
            with patch.object(cm, "CONFIG_FILE", temp_file):
                cm.load_configs()
                assert cm.BOT_CONFIGS == {}
        finally:
            os.unlink(temp_file)

    def test_save_configs_success(self, temp_config_file):
        """Тест успешного сохранения конфигураций"""
        test_configs = {
            "bots": {
                "1": {
                    "id": 1,
                    "config": {
                        "bot_name": "Test Bot",
                        "telegram_token": "test_token",
                        "openai_api_key": "test_key",
                        "assistant_id": "test_assistant",
                        "enable_ai_responses": True,
                        "enable_voice_responses": False,
                        "group_context_limit": 15,
                    },
                    "status": "stopped",
                }
            }
        }

        cm.BOT_CONFIGS = test_configs["bots"]

        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.save_configs()

            # Проверяем, что файл сохранен
            assert os.path.exists(temp_config_file)

            with open(temp_config_file) as f:
                saved_data = json.load(f)

            assert saved_data == test_configs

    def test_save_configs_async(self, temp_config_file):
        """Тест асинхронного сохранения конфигураций"""
        test_configs = {"1": {"id": 1, "config": {"bot_name": "Test Bot"}, "status": "stopped"}}

        cm.BOT_CONFIGS = test_configs

        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.save_configs_async()

            # Проверяем, что файл сохранен
            assert os.path.exists(temp_config_file)

    def test_get_bot_config_success(self, temp_config_file):
        """Тест получения конфигурации бота"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            bot_config = cm.get_bot_config(1)
            assert bot_config is not None
            assert bot_config["config"]["bot_name"] == "Test Bot 1"

    def test_get_bot_config_not_found(self, temp_config_file):
        """Тест получения конфигурации несуществующего бота"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            bot_config = cm.get_bot_config(999)
            assert bot_config is None

    def test_update_bot_config_success(self, temp_config_file):
        """Тест обновления конфигурации бота"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            new_config = {
                "bot_name": "Updated Bot",
                "telegram_token": "updated_token",
                "openai_api_key": "updated_key",
                "assistant_id": "updated_assistant",
                "enable_ai_responses": False,
                "enable_voice_responses": True,
                "group_context_limit": 20,
            }

            success = cm.update_bot_config(1, new_config)
            assert success is True

            # Проверяем, что конфигурация обновлена
            updated_config = cm.get_bot_config(1)
            assert updated_config["config"]["bot_name"] == "Updated Bot"
            assert updated_config["config"]["enable_ai_responses"] is False

    def test_update_bot_config_not_found(self, temp_config_file):
        """Тест обновления конфигурации несуществующего бота"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            new_config = {"bot_name": "Updated Bot"}
            success = cm.update_bot_config(999, new_config)
            assert success is False

    def test_delete_bot_config_success(self, temp_config_file):
        """Тест удаления конфигурации бота"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            # Проверяем, что бот существует
            assert "1" in cm.BOT_CONFIGS

            success = cm.delete_bot_config(1)
            assert success is True

            # Проверяем, что бот удален
            assert "1" not in cm.BOT_CONFIGS

    def test_delete_bot_config_not_found(self, temp_config_file):
        """Тест удаления несуществующей конфигурации бота"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            success = cm.delete_bot_config(999)
            assert success is False

    def test_add_bot_config_success(self, temp_config_file):
        """Тест добавления новой конфигурации бота"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            new_bot_config = {
                "bot_name": "New Bot",
                "telegram_token": "new_token",
                "openai_api_key": "new_key",
                "assistant_id": "new_assistant",
                "enable_ai_responses": True,
                "enable_voice_responses": False,
                "group_context_limit": 15,
            }

            bot_id = cm.add_bot_config(new_bot_config)
            assert bot_id is not None

            # Проверяем, что бот добавлен
            added_config = cm.get_bot_config(bot_id)
            assert added_config is not None
            assert added_config["config"]["bot_name"] == "New Bot"

    def test_get_all_bot_configs(self, temp_config_file):
        """Тест получения всех конфигураций ботов"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            all_configs = cm.get_all_bot_configs()
            assert isinstance(all_configs, dict)
            assert len(all_configs) > 0
            assert "1" in all_configs

    def test_get_bot_status_success(self, temp_config_file):
        """Тест получения статуса бота"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            status = cm.get_bot_status(1)
            assert status == "stopped"

    def test_get_bot_status_not_found(self, temp_config_file):
        """Тест получения статуса несуществующего бота"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            status = cm.get_bot_status(999)
            assert status is None

    def test_set_bot_status_success(self, temp_config_file):
        """Тест установки статуса бота"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            success = cm.set_bot_status(1, "running")
            assert success is True

            # Проверяем, что статус обновлен
            status = cm.get_bot_status(1)
            assert status == "running"

    def test_set_bot_status_not_found(self, temp_config_file):
        """Тест установки статуса несуществующего бота"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            success = cm.set_bot_status(999, "running")
            assert success is False

    def test_get_running_bots(self, temp_config_file):
        """Тест получения списка работающих ботов"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            # Добавляем работающий бот
            cm.set_bot_status(1, "running")

            running_bots = cm.get_running_bots()
            assert isinstance(running_bots, list)
            assert len(running_bots) > 0
            assert 1 in running_bots

    def test_get_stopped_bots(self, temp_config_file):
        """Тест получения списка остановленных ботов"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            # Устанавливаем статус остановленного бота
            cm.set_bot_status(1, "stopped")

            stopped_bots = cm.get_stopped_bots()
            assert isinstance(stopped_bots, list)
            assert len(stopped_bots) > 0
            assert 1 in stopped_bots

    def test_validate_bot_config_success(self):
        """Тест валидации корректной конфигурации бота"""
        valid_config = {
            "bot_name": "Test Bot",
            "telegram_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz",
            "assistant_id": "asst_test1234567890abcdefghijklmnopqrstuvwxyz",
            "enable_ai_responses": True,
            "enable_voice_responses": False,
            "group_context_limit": 15,
        }

        # Проверяем, что валидация проходит (если функция существует)
        if hasattr(cm, "validate_bot_config"):
            result = cm.validate_bot_config(valid_config)
            assert result is True

    def test_validate_bot_config_missing_fields(self):
        """Тест валидации конфигурации с отсутствующими полями"""
        invalid_config = {
            "bot_name": "Test Bot"
            # Отсутствуют обязательные поля
        }

        # Проверяем, что валидация не проходит (если функция существует)
        if hasattr(cm, "validate_bot_config"):
            result = cm.validate_bot_config(invalid_config)
            assert result is False

    def test_backup_configs(self, temp_config_file):
        """Тест создания резервной копии конфигураций"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            # Создаем резервную копию
            backup_path = cm.backup_configs()

            # Проверяем, что файл резервной копии создан
            assert os.path.exists(backup_path)

            # Проверяем содержимое резервной копии
            with open(backup_path) as f:
                backup_data = json.load(f)

            assert backup_data == {"bots": cm.BOT_CONFIGS}

            # Очистка
            os.unlink(backup_path)

    def test_restore_configs_from_backup(self, temp_config_file):
        """Тест восстановления конфигураций из резервной копии"""
        with patch.object(cm, "CONFIG_FILE", temp_config_file):
            cm.load_configs()

            # Создаем резервную копию
            backup_path = cm.backup_configs()

            # Изменяем конфигурацию
            cm.update_bot_config(1, {"bot_name": "Modified Bot"})

            # Восстанавливаем из резервной копии
            success = cm.restore_configs_from_backup(backup_path)
            assert success is True

            # Проверяем, что конфигурация восстановлена
            restored_config = cm.get_bot_config(1)
            assert restored_config["config"]["bot_name"] == "Test Bot 1"

            # Очистка
            os.unlink(backup_path)

    def test_restore_configs_invalid_backup(self):
        """Тест восстановления из невалидной резервной копии"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json}')
            invalid_backup = f.name

        try:
            success = cm.restore_configs_from_backup(invalid_backup)
            assert success is False
        finally:
            os.unlink(invalid_backup)
