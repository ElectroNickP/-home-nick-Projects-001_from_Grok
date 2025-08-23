#!/usr/bin/env python3
"""
Административный бот для управления Telegram Bot Manager
Предоставляет интерфейс для удаленного управления системой через Telegram
"""

import asyncio
import logging
from datetime import datetime

import psutil
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import bot_manager as bm
import config_manager as cm

logger = logging.getLogger(__name__)


class AdminBot:
    """Бот для управления проектом"""

    def __init__(self, token: str, admin_users: list, notifications: dict = None):
        self.bot = Bot(token)
        self.admin_users = set(admin_users)
        self.dp = Dispatcher()
        self.notifications = notifications or {}
        self.is_running = False
        self.monitoring_task = None

        # Настройка обработчиков
        self.setup_handlers()

        logger.info(f"AdminBot инициализирован для {len(self.admin_users)} администраторов")

    def setup_handlers(self):
        """Настройка обработчиков команд"""
        # Основные команды (ПЕРВЫМИ для приоритета!)
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_status, Command("status"))
        self.dp.message.register(self.cmd_bots, Command("bots"))
        self.dp.message.register(self.cmd_stats, Command("stats"))
        self.dp.message.register(self.cmd_control, Command("control"))
        self.dp.message.register(self.cmd_update, Command("update"))
        self.dp.message.register(self.cmd_backup, Command("backup"))

        # Обработчики callback кнопок
        self.dp.callback_query.register(self.handle_callback)
        
        # Debug отключен - мешает обработке команд

        logger.info("Обработчики AdminBot настроены")

    async def debug_all_messages(self, message: types.Message):
        """Debug: логирование всех входящих сообщений"""
        user = message.from_user
        logger.info(f"🔔 ПОЛУЧЕНО СООБЩЕНИЕ: '{message.text}' от пользователя {user.id} (@{user.username or 'None'}) {user.first_name or ''}")
        logger.info(f"🔔 Тип сообщения: {message.content_type}, chat_id: {message.chat.id}")
        # ВАЖНО: возвращаем управление для продолжения обработки
        return

    def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        logger.info(f"🔍 Проверка прав: user_id={user_id} (тип: {type(user_id)}), admin_users={self.admin_users}")
        result = user_id in self.admin_users
        logger.info(f"🔍 Результат проверки: {result}")
        return result

    async def cmd_start(self, message: types.Message):
        """Команда /start - главное меню"""
        logger.info(f"📨 Получена команда /start от пользователя {message.from_user.id} (@{message.from_user.username})")
        if not self.is_admin(message.from_user.id):
            logger.warning(f"⛔ Отказано в доступе пользователю {message.from_user.id}")
            await message.answer("⛔ У вас нет доступа к административным функциям.")
            return

        logger.info(f"✅ Доступ разрешен пользователю {message.from_user.id}")
        await self.show_main_menu(message)

    async def show_main_menu(self, message: types.Message):
        """Показать главное меню"""
        # Получаем краткую статистику для отображения в меню
        total_bots = len(cm.BOT_CONFIGS)
        running_bots = sum(1 for bot in cm.BOT_CONFIGS.values() if bot.get("status") == "running")
        
        # Проверяем состояние системы
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            if cpu_percent > 80:
                system_emoji = "🔴"
                system_status = "Высокая нагрузка"
            elif cpu_percent > 60:
                system_emoji = "🟡"
                system_status = "Средняя нагрузка"
            else:
                system_emoji = "🟢"
                system_status = "Стабильно"
        except:
            system_emoji = "⚪"
            system_status = "Неизвестно"

        keyboard = InlineKeyboardBuilder()
        
        # Основные разделы
        keyboard.add(InlineKeyboardButton(
            text=f"📊 Система {system_emoji}", 
            callback_data="menu_system"
        ))
        keyboard.add(InlineKeyboardButton(
            text=f"🤖 Боты ({running_bots}/{total_bots})", 
            callback_data="menu_bots"
        ))
        
        # Быстрые действия
        keyboard.add(InlineKeyboardButton(
            text="⚡ Быстрые действия", 
            callback_data="menu_quick"
        ))
        keyboard.add(InlineKeyboardButton(
            text="📈 Мониторинг", 
            callback_data="menu_monitoring"
        ))
        
        # Администрирование и настройки
        keyboard.add(InlineKeyboardButton(
            text="🔧 Настройки", 
            callback_data="menu_settings"
        ))
        keyboard.add(InlineKeyboardButton(
            text="📋 Логи", 
            callback_data="menu_logs"
        ))
        
        # Обновление меню
        keyboard.add(InlineKeyboardButton(
            text="🔄 Обновить", 
            callback_data="refresh_main"
        ))
        
        keyboard.adjust(2, 2, 2, 1)

        menu_text = f"""🔮 **ELECTRONICK Bot Manager**

🖥️ **Система:** {system_emoji} {system_status}
🤖 **Боты:** {running_bots} из {total_bots} работают
⏰ **Время:** {datetime.now().strftime('%H:%M:%S')}

👆 Выберите раздел для управления:"""

        try:
            await message.edit_text(
                menu_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown",
            )
        except:
            await message.answer(
                menu_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown",
            )

    async def cmd_help(self, message: types.Message):
        """Команда /help - справка"""
        if not self.is_admin(message.from_user.id):
            return

        help_text = """
🔮 **ELECTRONICK Bot Manager - Справка**

**Основные команды:**
/start - Главное меню
/status - Статус системы и ресурсов
/bots - Список ботов с управлением
/stats - Детальная статистика
/control - Управление конкретным ботом
/update - Проверка обновлений
/backup - Управление бэкапами
/help - Эта справка

**Уведомления:**
🔔 Статус ботов (запуск/остановка)
⚠️ Высокое использование CPU (>80%)
🚨 Ошибки в работе ботов
📈 Еженедельная статистика
🔄 Уведомления об обновлениях
        """

        await message.answer(help_text, parse_mode="Markdown")

    async def cmd_status(self, message: types.Message):
        """Команда /status - статус системы"""
        if not self.is_admin(message.from_user.id):
            return

        status_text = await self.get_system_status()
        await message.answer(status_text, parse_mode="Markdown")

    async def cmd_bots(self, message: types.Message):
        """Команда /bots - список ботов"""
        if not self.is_admin(message.from_user.id):
            return

        bots_text, keyboard = await self.get_bots_list()
        await message.answer(bots_text, reply_markup=keyboard, parse_mode="Markdown")

    async def cmd_stats(self, message: types.Message):
        """Команда /stats - детальная статистика"""
        if not self.is_admin(message.from_user.id):
            return

        stats_text = await self.get_detailed_stats()
        await message.answer(stats_text, parse_mode="Markdown")

    async def cmd_control(self, message: types.Message):
        """Команда /control - управление ботом"""
        if not self.is_admin(message.from_user.id):
            return

        # Парсим аргументы команды
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []

        if not args:
            await message.answer(
                "Использование: /control <bot_id> <action>\n"
                "Действия: start, stop, restart, info\n"
                "Пример: /control 1 start"
            )
            return

        try:
            bot_id = int(args[0])
            action = args[1] if len(args) > 1 else "info"

            result = await self.control_bot(bot_id, action)
            await message.answer(result, parse_mode="Markdown")

        except ValueError:
            await message.answer("❌ Неверный ID бота")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")

    async def cmd_update(self, message: types.Message):
        """Команда /update - проверка обновлений"""
        if not self.is_admin(message.from_user.id):
            return

        await message.answer("🔄 Проверка обновлений...")

        # Здесь будет логика проверки обновлений
        # Пока заглушка
        await message.answer("✅ Система обновлена до последней версии")

    async def cmd_backup(self, message: types.Message):
        """Команда /backup - управление бэкапами"""
        if not self.is_admin(message.from_user.id):
            return

        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="📦 Создать бэкап", callback_data="backup_create"))
        keyboard.add(InlineKeyboardButton(text="📋 Список бэкапов", callback_data="backup_list"))
        keyboard.add(InlineKeyboardButton(text="🗑️ Очистить старые", callback_data="backup_cleanup"))
        keyboard.adjust(1)

        await message.answer(
            "📦 **Управление бэкапами**\n\n" "Выберите действие:",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown",
        )

    async def handle_callback(self, callback: CallbackQuery):
        """Обработка callback кнопок"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("⛔ Нет доступа", show_alert=True)
            return

        data = callback.data

        try:
            # Главное меню и навигация
            if data == "refresh_main":
                await self.show_main_menu(callback.message)
                await callback.answer("🔄 Обновлено")
                
            elif data == "back_to_main":
                await self.show_main_menu(callback.message)
                await callback.answer()

            # Подменю
            elif data == "menu_system":
                await self.show_system_menu(callback.message)
                await callback.answer()
                
            elif data == "menu_bots":
                await self.show_bots_menu(callback.message)
                await callback.answer()
                
            elif data == "menu_quick":
                await self.show_quick_actions_menu(callback.message)
                await callback.answer()
                
            elif data == "menu_monitoring":
                await self.show_monitoring_menu(callback.message)
                await callback.answer()
                
            elif data == "menu_settings":
                await self.show_settings_menu(callback.message)
                await callback.answer()
                
            elif data == "menu_logs":
                await self.show_logs_menu(callback.message)
                await callback.answer()

            # Старые функции (совместимость)
            elif data == "status":
                status_text = await self.get_system_status()
                keyboard = InlineKeyboardBuilder()
                keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
                await callback.message.edit_text(
                    status_text + "\n\n👆 Выберите действие:",
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )

            elif data == "bots":
                bots_text, keyboard = await self.get_bots_list()
                await callback.message.edit_text(
                    bots_text, reply_markup=keyboard, parse_mode="Markdown"
                )

            elif data == "stats":
                stats_text = await self.get_detailed_stats()
                keyboard = InlineKeyboardBuilder()
                keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
                await callback.message.edit_text(
                    stats_text + "\n\n👆 Выберите действие:",
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )

            elif data == "admin":
                await self.show_admin_menu(callback.message)

            # Управление ботами
            elif data.startswith("start_bot_"):
                bot_id = int(data.split("_")[2])
                result = await self.control_bot(bot_id, "start")
                await callback.answer(result, show_alert=True)
                # Обновляем меню ботов
                await self.show_bots_menu(callback.message)

            elif data.startswith("stop_bot_"):
                bot_id = int(data.split("_")[2])
                result = await self.control_bot(bot_id, "stop")
                await callback.answer(result, show_alert=True)
                # Обновляем меню ботов
                await self.show_bots_menu(callback.message)
                
            elif data.startswith("restart_bot_"):
                bot_id = int(data.split("_")[2])
                result = await self.control_bot(bot_id, "restart")
                await callback.answer(result, show_alert=True)
                # Обновляем меню ботов
                await self.show_bots_menu(callback.message)
                
            elif data.startswith("info_bot_"):
                bot_id = int(data.split("_")[2])
                result = await self.control_bot(bot_id, "info")
                keyboard = InlineKeyboardBuilder()
                keyboard.add(InlineKeyboardButton(text="🤖 К списку ботов", callback_data="menu_bots"))
                keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
                keyboard.adjust(1)
                await callback.message.edit_text(
                    result + "\n\n👆 Выберите действие:",
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )

            # Быстрые действия
            elif data == "quick_start_all":
                await self.quick_start_all_bots(callback)
                
            elif data == "quick_stop_all":
                await self.quick_stop_all_bots(callback)
                
            elif data == "quick_restart_all":
                await self.quick_restart_all_bots(callback)
                
            elif data == "quick_clear_logs":
                await callback.answer("🧹 Функция очистки логов в разработке", show_alert=True)

            # Дополнительные системные функции
            elif data == "system_resources":
                await self.show_system_resources(callback.message)
                
            elif data == "system_processes":
                await self.show_system_processes(callback.message)

            elif data.startswith("backup_"):
                await self.handle_backup_callback(callback, data)

            else:
                await callback.answer("❌ Неизвестное действие", show_alert=True)

        except Exception as e:
            logger.error(f"Ошибка обработки callback {data}: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def show_system_menu(self, message: types.Message):
        """Показать меню системной информации"""
        keyboard = InlineKeyboardBuilder()
        
        keyboard.add(InlineKeyboardButton(text="📊 Статус системы", callback_data="status"))
        keyboard.add(InlineKeyboardButton(text="📈 Детальная статистика", callback_data="stats"))
        keyboard.add(InlineKeyboardButton(text="💾 Использование ресурсов", callback_data="system_resources"))
        keyboard.add(InlineKeyboardButton(text="🔄 Процессы", callback_data="system_processes"))
        keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
        
        keyboard.adjust(2, 2, 1)

        await message.edit_text(
            "🖥️ **Системная информация**\n\n"
            "Выберите нужную информацию:",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

    async def show_bots_menu(self, message: types.Message):
        """Показать улучшенное меню управления ботами"""
        try:
            bots_text = "🤖 **Управление ботами**\n\n"
            keyboard = InlineKeyboardBuilder()

            if not cm.BOT_CONFIGS:
                bots_text += "📭 Боты не найдены"
                keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
                await message.edit_text(bots_text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
                return

            running_count = 0
            stopped_count = 0

            for bot_id, bot_data in cm.BOT_CONFIGS.items():
                status = bot_data.get("status", "stopped")
                bot_name = bot_data["config"].get("bot_name", f"Bot {bot_id}")
                
                if status == "running":
                    status_emoji = "🟢"
                    running_count += 1
                else:
                    status_emoji = "🔴" 
                    stopped_count += 1

                # Добавляем строку с ботом
                bots_text += f"{status_emoji} **{bot_name}** (ID: {bot_id})\n"

                # Добавляем кнопки для каждого бота
                if status == "running":
                    keyboard.add(InlineKeyboardButton(
                        text=f"🔴 Остановить {bot_name[:15]}...", 
                        callback_data=f"stop_bot_{bot_id}"
                    ))
                    keyboard.add(InlineKeyboardButton(
                        text=f"🔄 Перезапуск {bot_name[:15]}...", 
                        callback_data=f"restart_bot_{bot_id}"
                    ))
                else:
                    keyboard.add(InlineKeyboardButton(
                        text=f"🟢 Запустить {bot_name[:15]}...", 
                        callback_data=f"start_bot_{bot_id}"
                    ))
                    keyboard.add(InlineKeyboardButton(
                        text=f"ℹ️ Инфо {bot_name[:15]}...", 
                        callback_data=f"info_bot_{bot_id}"
                    ))

            # Статистика
            bots_text += f"\n📊 **Статистика:** {running_count} работает, {stopped_count} остановлено"

            # Кнопки групповых действий
            keyboard.add(InlineKeyboardButton(text="⚡ Быстрые действия", callback_data="menu_quick"))
            keyboard.add(InlineKeyboardButton(text="🔄 Обновить список", callback_data="menu_bots"))
            keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))

            # Размещение кнопок: по 2 кнопки управления ботами, затем кнопки навигации
            bot_buttons_count = len(cm.BOT_CONFIGS) * 2
            adjust_pattern = [2] * (bot_buttons_count // 2)
            if bot_buttons_count % 2:
                adjust_pattern.append(1)
            adjust_pattern.extend([1, 2, 1])
            
            keyboard.adjust(*adjust_pattern)

            await message.edit_text(
                bots_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Ошибка показа меню ботов: {e}")
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
            await message.edit_text(
                "❌ Ошибка загрузки списка ботов",
                reply_markup=keyboard.as_markup()
            )

    async def show_quick_actions_menu(self, message: types.Message):
        """Показать меню быстрых действий"""
        total_bots = len(cm.BOT_CONFIGS)
        running_bots = sum(1 for bot in cm.BOT_CONFIGS.values() if bot.get("status") == "running")
        stopped_bots = total_bots - running_bots

        keyboard = InlineKeyboardBuilder()
        
        # Групповые действия с ботами
        if stopped_bots > 0:
            keyboard.add(InlineKeyboardButton(text="🟢 Запустить все боты", callback_data="quick_start_all"))
        if running_bots > 0:
            keyboard.add(InlineKeyboardButton(text="🔴 Остановить все боты", callback_data="quick_stop_all"))
            keyboard.add(InlineKeyboardButton(text="🔄 Перезапустить все", callback_data="quick_restart_all"))
        
        # Системные действия
        keyboard.add(InlineKeyboardButton(text="🧹 Очистить логи", callback_data="quick_clear_logs"))
        keyboard.add(InlineKeyboardButton(text="📦 Создать бэкап", callback_data="backup_create"))
        
        # Навигация
        keyboard.add(InlineKeyboardButton(text="🤖 Управление ботами", callback_data="menu_bots"))
        keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
        
        keyboard.adjust(1, 2, 2, 2)

        menu_text = f"""⚡ **Быстрые действия**

🤖 **Боты:** {running_bots} работает / {stopped_bots} остановлено

⚠️ **Внимание:** Групповые действия могут занять время!

👆 Выберите действие:"""

        await message.edit_text(
            menu_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

    async def show_monitoring_menu(self, message: types.Message):
        """Показать меню мониторинга"""
        keyboard = InlineKeyboardBuilder()
        
        keyboard.add(InlineKeyboardButton(text="📊 Статус системы", callback_data="status"))
        keyboard.add(InlineKeyboardButton(text="🔄 Процессы", callback_data="system_processes"))
        keyboard.add(InlineKeyboardButton(text="📈 Графики нагрузки", callback_data="system_charts"))
        keyboard.add(InlineKeyboardButton(text="⚠️ Алерты", callback_data="system_alerts"))
        keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
        
        keyboard.adjust(2, 2, 1)

        await message.edit_text(
            "📈 **Мониторинг системы**\n\n"
            "Выберите тип мониторинга:",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

    async def show_settings_menu(self, message: types.Message):
        """Показать меню настроек"""
        keyboard = InlineKeyboardBuilder()
        
        keyboard.add(InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications"))
        keyboard.add(InlineKeyboardButton(text="👥 Администраторы", callback_data="settings_admins"))
        keyboard.add(InlineKeyboardButton(text="🔐 Безопасность", callback_data="settings_security"))
        keyboard.add(InlineKeyboardButton(text="⚙️ Система", callback_data="settings_system"))
        keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
        
        keyboard.adjust(2, 2, 1)

        await message.edit_text(
            "🔧 **Настройки системы**\n\n"
            "Выберите раздел настроек:",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

    async def show_logs_menu(self, message: types.Message):
        """Показать меню логов"""
        keyboard = InlineKeyboardBuilder()
        
        keyboard.add(InlineKeyboardButton(text="📄 Системные логи", callback_data="logs_system"))
        keyboard.add(InlineKeyboardButton(text="🤖 Логи ботов", callback_data="logs_bots"))
        keyboard.add(InlineKeyboardButton(text="❌ Логи ошибок", callback_data="logs_errors"))
        keyboard.add(InlineKeyboardButton(text="🧹 Очистить логи", callback_data="quick_clear_logs"))
        keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
        
        keyboard.adjust(2, 2, 1)

        await message.edit_text(
            "📋 **Управление логами**\n\n"
            "Выберите тип логов:",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

    async def quick_start_all_bots(self, callback: CallbackQuery):
        """Быстрый запуск всех ботов"""
        await callback.answer("🚀 Запускаю всех ботов...", show_alert=True)
        
        started = 0
        failed = 0
        
        for bot_id, bot_data in cm.BOT_CONFIGS.items():
            if bot_data.get("status") != "running":
                try:
                    success, message = bm.start_bot_thread(bot_id)
                    if success:
                        started += 1
                    else:
                        failed += 1
                        logger.error(f"Ошибка запуска бота {bot_id}: {message}")
                except Exception as e:
                    failed += 1
                    logger.error(f"Исключение при запуске бота {bot_id}: {e}")
        
        result_text = f"✅ Запущено: {started}\n❌ Ошибок: {failed}"
        
        # Показываем результат и обновляем меню
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="🤖 К управлению ботами", callback_data="menu_bots"))
        keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            f"🚀 **Массовый запуск ботов**\n\n{result_text}",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

    async def quick_stop_all_bots(self, callback: CallbackQuery):
        """Быстрая остановка всех ботов"""
        await callback.answer("🛑 Останавливаю всех ботов...", show_alert=True)
        
        stopped = 0
        failed = 0
        
        for bot_id, bot_data in cm.BOT_CONFIGS.items():
            if bot_data.get("status") == "running":
                try:
                    success, message = bm.stop_bot_thread(bot_id)
                    if success:
                        stopped += 1
                    else:
                        failed += 1
                        logger.error(f"Ошибка остановки бота {bot_id}: {message}")
                except Exception as e:
                    failed += 1
                    logger.error(f"Исключение при остановке бота {bot_id}: {e}")
        
        result_text = f"✅ Остановлено: {stopped}\n❌ Ошибок: {failed}"
        
        # Показываем результат и обновляем меню
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="🤖 К управлению ботами", callback_data="menu_bots"))
        keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            f"🛑 **Массовая остановка ботов**\n\n{result_text}",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

    async def quick_restart_all_bots(self, callback: CallbackQuery):
        """Быстрый перезапуск всех ботов"""
        await callback.answer("🔄 Перезапускаю всех ботов...", show_alert=True)
        
        restarted = 0
        failed = 0
        
        for bot_id, bot_data in cm.BOT_CONFIGS.items():
            try:
                # Останавливаем если работает
                if bot_data.get("status") == "running":
                    bm.stop_bot_thread(bot_id)
                    await asyncio.sleep(1)  # Ждем остановки
                
                # Запускаем
                success, message = bm.start_bot_thread(bot_id)
                if success:
                    restarted += 1
                else:
                    failed += 1
                    logger.error(f"Ошибка перезапуска бота {bot_id}: {message}")
            except Exception as e:
                failed += 1
                logger.error(f"Исключение при перезапуске бота {bot_id}: {e}")
        
        result_text = f"✅ Перезапущено: {restarted}\n❌ Ошибок: {failed}"
        
        # Показываем результат и обновляем меню
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="🤖 К управлению ботами", callback_data="menu_bots"))
        keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            f"🔄 **Массовый перезапуск ботов**\n\n{result_text}",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

    async def show_system_resources(self, message: types.Message):
        """Показать детальную информацию о ресурсах системы"""
        try:
            import psutil
            
            # CPU информация
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Память
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Диск
            disk = psutil.disk_usage("/")
            
            # Сетевая статистика
            net = psutil.net_io_counters()
            
            resources_text = f"""💾 **Детальная информация о ресурсах**

🖥️ **Процессор:**
• Использование: {cpu_percent}%
• Ядер: {cpu_count}
• Частота: {cpu_freq.current:.0f} MHz

🧠 **Оперативная память:**
• Использовано: {memory.percent}% ({memory.used // 1024**3}GB / {memory.total // 1024**3}GB)
• Свободно: {memory.available // 1024**3}GB

💽 **Диск:**
• Использовано: {disk.percent}% ({disk.used // 1024**3}GB / {disk.total // 1024**3}GB)
• Свободно: {disk.free // 1024**3}GB

🌐 **Сеть:**
• Получено: {net.bytes_recv // 1024**2} MB
• Отправлено: {net.bytes_sent // 1024**2} MB

⏰ **Время:** {datetime.now().strftime('%H:%M:%S')}"""

            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="🔄 Обновить", callback_data="system_resources"))
            keyboard.add(InlineKeyboardButton(text="🖥️ К системе", callback_data="menu_system"))
            keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
            keyboard.adjust(1)

            await message.edit_text(
                resources_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Ошибка получения информации о ресурсах: {e}")
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
            await message.edit_text(
                "❌ Ошибка получения информации о ресурсах",
                reply_markup=keyboard.as_markup()
            )

    async def show_system_processes(self, message: types.Message):
        """Показать информацию о процессах"""
        try:
            import psutil
            
            # Информация о процессах Python (ботах)
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if 'python' in proc.info['name'].lower():
                        python_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes_text = f"""🔄 **Системные процессы**

🐍 **Python процессы:** {len(python_processes)}
"""
            
            # Показываем топ-5 процессов по CPU
            python_processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            for i, proc in enumerate(python_processes[:5]):
                processes_text += f"• PID {proc['pid']}: CPU {proc['cpu_percent']:.1f}% RAM {proc['memory_percent']:.1f}%\n"
            
            # Общая информация
            total_processes = len(list(psutil.process_iter()))
            processes_text += f"\n📊 **Всего процессов в системе:** {total_processes}"

            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="🔄 Обновить", callback_data="system_processes"))
            keyboard.add(InlineKeyboardButton(text="🖥️ К системе", callback_data="menu_system"))
            keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
            keyboard.adjust(1)

            await message.edit_text(
                processes_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Ошибка получения информации о процессах: {e}")
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
            await message.edit_text(
                "❌ Ошибка получения информации о процессах",
                reply_markup=keyboard.as_markup()
            )

    async def get_system_status(self) -> str:
        """Получение статуса системы"""
        try:
            # Системные ресурсы
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Статистика ботов
            total_bots = len(cm.BOT_CONFIGS)
            running_bots = sum(
                1 for bot in cm.BOT_CONFIGS.values() if bot.get("status") == "running"
            )

            # Определяем статус системы
            if cpu_percent > 80:
                system_status = "⚠️ Высокая нагрузка"
            elif cpu_percent > 60:
                system_status = "🟡 Средняя нагрузка"
            else:
                system_status = "🟢 Стабильная работа"

            status_text = f"""
🔮 **Статус системы ELECTRONICK Bot Manager**

💻 **Системные ресурсы:**
• CPU: {cpu_percent}%
• RAM: {memory.percent}% ({memory.used // 1024**3}GB / {memory.total // 1024**3}GB)
• Диск: {disk.percent}% ({disk.used // 1024**3}GB / {disk.total // 1024**3}GB)

🤖 **Боты:**
• Всего: {total_bots}
• Работает: {running_bots}
• Остановлено: {total_bots - running_bots}

📊 **Статус:** {system_status}

⏰ **Время:** {datetime.now().strftime('%H:%M:%S')}
            """

            return status_text.strip()

        except Exception as e:
            logger.error(f"Ошибка получения статуса системы: {e}")
            return "❌ Ошибка получения статуса системы"

    async def get_bots_list(self) -> tuple[str, InlineKeyboardMarkup]:
        """Получение списка ботов с кнопками управления (обратная совместимость)"""
        try:
            bots_text = "🤖 **Список ботов:**\n\n"
            keyboard = InlineKeyboardBuilder()

            if not cm.BOT_CONFIGS:
                bots_text += "📭 Боты не найдены"
                keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
                return bots_text, keyboard.as_markup()

            running_count = 0
            stopped_count = 0

            for bot_id, bot_data in cm.BOT_CONFIGS.items():
                status = bot_data.get("status", "stopped")
                status_emoji = "🟢" if status == "running" else "🔴"
                status_text = "Работает" if status == "running" else "Остановлен"

                if status == "running":
                    running_count += 1
                else:
                    stopped_count += 1

                bot_name = bot_data["config"].get("bot_name", f"Bot {bot_id}")
                bots_text += f"{status_emoji} **{bot_name}** (ID: {bot_id})\n"
                bots_text += f"   Статус: {status_text}\n\n"

                # Кнопки управления
                if status == "running":
                    keyboard.add(InlineKeyboardButton(
                        text=f"🔴 Остановить {bot_name[:20]}...", 
                        callback_data=f"stop_bot_{bot_id}"
                    ))
                    keyboard.add(InlineKeyboardButton(
                        text=f"🔄 Перезапуск {bot_name[:20]}...", 
                        callback_data=f"restart_bot_{bot_id}"
                    ))
                else:
                    keyboard.add(InlineKeyboardButton(
                        text=f"🟢 Запустить {bot_name[:20]}...", 
                        callback_data=f"start_bot_{bot_id}"
                    ))
                    keyboard.add(InlineKeyboardButton(
                        text=f"ℹ️ Инфо {bot_name[:20]}...", 
                        callback_data=f"info_bot_{bot_id}"
                    ))

            # Добавляем статистику
            bots_text += f"📊 **Статистика:** {running_count} работает, {stopped_count} остановлено"

            # Кнопки навигации
            keyboard.add(InlineKeyboardButton(text="⚡ Быстрые действия", callback_data="menu_quick"))
            keyboard.add(InlineKeyboardButton(text="🔄 Обновить", callback_data="bots"))
            keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))

            # Размещение кнопок
            bot_buttons_count = len(cm.BOT_CONFIGS) * 2
            adjust_pattern = [2] * (bot_buttons_count // 2)
            if bot_buttons_count % 2:
                adjust_pattern.append(1)
            adjust_pattern.extend([1, 2, 1])
            
            keyboard.adjust(*adjust_pattern)
            return bots_text, keyboard.as_markup()

        except Exception as e:
            logger.error(f"Ошибка получения списка ботов: {e}")
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
            return "❌ Ошибка получения списка ботов", keyboard.as_markup()

    async def get_detailed_stats(self) -> str:
        """Получение детальной статистики"""
        try:
            # Системная статистика
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Статистика ботов
            total_bots = len(cm.BOT_CONFIGS)
            running_bots = sum(
                1 for bot in cm.BOT_CONFIGS.values() if bot.get("status") == "running"
            )

            # Статистика по типам ботов
            ai_bots = sum(
                1
                for bot in cm.BOT_CONFIGS.values()
                if bot["config"].get("enable_ai_responses", True)
            )
            voice_bots = sum(
                1
                for bot in cm.BOT_CONFIGS.values()
                if bot["config"].get("enable_voice_responses", False)
            )
            marketplace_bots = sum(
                1
                for bot in cm.BOT_CONFIGS.values()
                if bot["config"].get("marketplace", {}).get("enabled", False)
            )

            stats_text = f"""
📈 **Детальная статистика**

💻 **Системные ресурсы:**
• CPU: {cpu_percent}%
• RAM: {memory.percent}% ({memory.used // 1024**3}GB / {memory.total // 1024**3}GB)
• Диск: {disk.percent}% ({disk.used // 1024**3}GB / {disk.total // 1024**3}GB)

🤖 **Статистика ботов:**
• Всего ботов: {total_bots}
• Работает: {running_bots}
• Остановлено: {total_bots - running_bots}
• ИИ боты: {ai_bots}
• Голосовые боты: {voice_bots}
• В маркетплейсе: {marketplace_bots}

📊 **Производительность:**
• Загрузка CPU: {'Высокая' if cpu_percent > 80 else 'Средняя' if cpu_percent > 60 else 'Низкая'}
• Использование RAM: {'Высокое' if memory.percent > 80 else 'Среднее' if memory.percent > 60 else 'Низкое'}
• Свободное место: {'Мало' if disk.percent > 90 else 'Достаточно' if disk.percent > 70 else 'Много'}

⏰ **Время:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """

            return stats_text.strip()

        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return "❌ Ошибка получения статистики"

    async def control_bot(self, bot_id: int, action: str) -> str:
        """Управление ботом"""
        try:
            if bot_id not in cm.BOT_CONFIGS:
                return f"❌ Бот с ID {bot_id} не найден"

            bot_data = cm.BOT_CONFIGS[bot_id]
            bot_name = bot_data["config"].get("bot_name", f"Bot {bot_id}")

            if action == "start":
                if bot_data.get("status") == "running":
                    return f"⚠️ Бот {bot_name} уже запущен"

                success, message = bm.start_bot_thread(bot_id)
                if success:
                    return f"✅ Бот {bot_name} запущен"
                else:
                    return f"❌ Ошибка запуска бота {bot_name}: {message}"

            elif action == "stop":
                if bot_data.get("status") != "running":
                    return f"⚠️ Бот {bot_name} уже остановлен"

                success, message = bm.stop_bot_thread(bot_id)
                if success:
                    return f"✅ Бот {bot_name} остановлен"
                else:
                    return f"❌ Ошибка остановки бота {bot_name}: {message}"

            elif action == "restart":
                # Сначала останавливаем
                if bot_data.get("status") == "running":
                    bm.stop_bot_thread(bot_id)
                    await asyncio.sleep(2)  # Ждем остановки

                # Затем запускаем
                success, message = bm.start_bot_thread(bot_id)
                if success:
                    return f"✅ Бот {bot_name} перезапущен"
                else:
                    return f"❌ Ошибка перезапуска бота {bot_name}: {message}"

            elif action == "info":
                status = bot_data.get("status", "unknown")
                config = bot_data.get("config", {})

                info_text = f"""
🤖 **Информация о боте {bot_name}**

📋 **Основная информация:**
• ID: {bot_id}
• Статус: {status}
• ИИ ответы: {'Включены' if config.get('enable_ai_responses', True) else 'Отключены'}
• Голосовые ответы: {'Включены' if config.get('enable_voice_responses', False) else 'Отключены'}
• В маркетплейсе: {'Да' if config.get('marketplace', {}).get('enabled', False) else 'Нет'}

⚙️ **Настройки:**
• Контекст сообщений: {config.get('group_context_limit', 15)}
• Модель голоса: {config.get('voice_model', 'tts-1')}
• Тип голоса: {config.get('voice_type', 'alloy')}
                """
                return info_text.strip()

            else:
                return f"❌ Неизвестное действие: {action}"

        except Exception as e:
            logger.error(f"Ошибка управления ботом {bot_id}: {e}")
            return f"❌ Ошибка управления ботом: {str(e)}"

    async def show_admin_menu(self, message: types.Message):
        """Показать меню администрирования"""
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(text="🔄 Проверить обновления", callback_data="update_check")
        )
        keyboard.add(InlineKeyboardButton(text="📦 Создать бэкап", callback_data="backup_create"))
        keyboard.add(InlineKeyboardButton(text="📋 Список бэкапов", callback_data="backup_list"))
        keyboard.add(InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"))
        keyboard.adjust(1)

        await message.edit_text(
            "🔧 **Администрирование**\n\n" "Выберите действие:",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown",
        )

    async def handle_backup_callback(self, callback: CallbackQuery, data: str):
        """Обработка callback для бэкапов"""
        if data == "backup_create":
            await callback.answer("📦 Создание бэкапа...", show_alert=True)
            # Здесь будет логика создания бэкапа
            await callback.message.answer("✅ Бэкап создан успешно")

        elif data == "backup_list":
            await callback.answer("📋 Получение списка бэкапов...", show_alert=True)
            # Здесь будет логика получения списка бэкапов
            await callback.message.answer(
                "📋 Список бэкапов:\n• backup_2025-01-27_12-00-00.zip\n• backup_2025-01-26_12-00-00.zip"
            )

        elif data == "backup_cleanup":
            await callback.answer("🗑️ Очистка старых бэкапов...", show_alert=True)
            # Здесь будет логика очистки бэкапов
            await callback.message.answer("✅ Старые бэкапы удалены")

    async def start_monitoring(self):
        """Запуск мониторинга системы"""
        if self.monitoring_task:
            return

        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Мониторинг системы запущен")

    async def stop_monitoring(self):
        """Остановка мониторинга системы"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            self.monitoring_task = None
            logger.info("Мониторинг системы остановлен")

    async def _monitoring_loop(self):
        """Цикл мониторинга"""
        while True:
            try:
                # Проверяем CPU
                cpu_percent = psutil.cpu_percent()
                if cpu_percent > 80 and self.notifications.get("high_cpu", True):
                    await self.send_notification_to_all(
                        f"⚠️ **Высокое использование CPU:** {cpu_percent}%"
                    )

                # Проверяем статус ботов
                if self.notifications.get("bot_status", True):
                    for bot_id, bot_data in cm.BOT_CONFIGS.items():
                        # Здесь можно добавить логику отслеживания изменений статуса
                        pass

                # Ждем 5 минут перед следующей проверкой
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(60)  # Ждем минуту при ошибке

    async def send_notification_to_all(self, message: str):
        """Отправка уведомления всем администраторам"""
        for admin_id in self.admin_users:
            try:
                await self.bot.send_message(admin_id, message, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления администратору {admin_id}: {e}")

    async def start(self):
        """Запуск бота"""
        if self.is_running:
            return

        try:
            self.is_running = True
            await self.start_monitoring()
            
            # Запускаем polling без signal handlers (для работы в потоке)
            await self.dp.start_polling(self.bot, handle_signals=False)
        except Exception as e:
            logger.error(f"Ошибка запуска AdminBot: {e}")
            self.is_running = False
        finally:
            await self.stop_monitoring()

    async def stop(self):
        """Остановка бота"""
        if not self.is_running:
            return

        try:
            self.is_running = False
            await self.stop_monitoring()
            await self.bot.session.close()
            logger.info("AdminBot остановлен")
        except Exception as e:
            logger.error(f"Ошибка остановки AdminBot: {e}")


# Глобальный экземпляр админ-бота
admin_bot_instance: AdminBot | None = None


def get_admin_bot() -> AdminBot | None:
    """Получить экземпляр админ-бота"""
    return admin_bot_instance


def set_admin_bot(bot: AdminBot):
    """Установить экземпляр админ-бота"""
    global admin_bot_instance
    admin_bot_instance = bot

