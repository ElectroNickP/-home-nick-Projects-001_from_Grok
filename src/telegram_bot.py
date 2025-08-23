import asyncio
import logging
import os
import re
import time

import openai
from aiogram import Bot, Dispatcher, types
from aiogram.client.bot import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.utils.token import validate_token

from config_manager import CONVERSATIONS, CONVERSATIONS_LOCK, OPENAI_LOCK

logger = logging.getLogger(__name__)


def validate_telegram_token(token):
    """Валидация Telegram токена"""
    try:
        # Проверяем формат токена (должен быть в формате 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)
        if not re.match(r"^\d+:[A-Za-z0-9_-]{35}$", token):
            logger.error(f"❌ Неверный формат токена: {token}")
            return False, "Неверный формат токена"

        # Используем встроенную валидацию aiogram
        validate_token(token)
        logger.info(f"✅ Токен валиден: {token[:10]}...")
        return True, "Токен валиден"

    except Exception as e:
        logger.error(f"❌ Ошибка валидации токена: {e}")
        return False, str(e)


# Configuration for group context analysis
GROUP_CONTEXT_MESSAGES_LIMIT = 15  # Number of recent messages to analyze in groups

# Store recent group messages for context analysis
GROUP_MESSAGES_CACHE = {}  # {chat_id: [message_data, ...]}


def get_user_info(message):
    """Извлекает информацию о пользователе/группе из сообщения Telegram."""
    user_info = {}
    
    if message.chat.type == "private":
        # Личный чат - информация о пользователе
        user = message.from_user
        if user:
            user_info = {
                "type": "user",
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "display_name": None
            }
            
            # Формируем отображаемое имя
            if user.username:
                user_info["display_name"] = f"@{user.username}"
            elif user.first_name:
                full_name = user.first_name
                if user.last_name:
                    full_name += f" {user.last_name}"
                user_info["display_name"] = full_name
            else:
                user_info["display_name"] = f"Пользователь {user.id}"
    else:
        # Групповой чат - информация о группе
        chat = message.chat
        user_info = {
            "type": "group",
            "id": chat.id,
            "title": chat.title,
            "username": chat.username,
            "display_name": chat.title or f"Группа {chat.id}"
        }
    
    return user_info


def save_transcription_dialog(conversation_key, user_message, bot_response, user_info=None):
    """Сохраняет диалог в режиме транскрибатора для отображения в веб-интерфейсе."""
    import time
    
    current_time = int(time.time())
    
    with CONVERSATIONS_LOCK:
        if conversation_key not in CONVERSATIONS:
            CONVERSATIONS[conversation_key] = {
                "thread_id": None, 
                "messages": [],
                "user_info": user_info or {}
            }
        
        # Обновляем информацию о пользователе, если она предоставлена
        if user_info and "user_info" in CONVERSATIONS[conversation_key]:
            CONVERSATIONS[conversation_key]["user_info"].update(user_info)
        
        # Добавляем сообщение пользователя
        CONVERSATIONS[conversation_key]["messages"].append({
            "role": "user",
            "content": user_message,
            "timestamp": current_time
        })
        
        # Добавляем ответ бота (транскрибацию или информационное сообщение)
        CONVERSATIONS[conversation_key]["messages"].append({
            "role": "assistant", 
            "content": bot_response,
            "timestamp": current_time + 1
        })
        
        logger.info(f"💾 Диалог сохранен в режиме транскрибатора: {conversation_key}")


async def transcribe_audio(file_path):
    """Транскрибирует аудиофайл с помощью OpenAI Whisper."""
    try:
        logger.info(f"🎧 Начинаю транскрибацию файла: {file_path}")

        # Проверяем существование файла
        if not os.path.exists(file_path):
            logger.error(f"❌ Файл для транскрибации не найден: {file_path}")
            return None

        file_size = os.path.getsize(file_path)
        logger.info(f"📊 Размер файла для транскрибации: {file_size} байт")

        if file_size == 0:
            logger.error(f"❌ Файл для транскрибации пустой: {file_path}")
            return None

        logger.info("📡 Отправляю файл в OpenAI Whisper API...")
        with open(file_path, "rb") as audio_file:
            # Добавляем timeout для Whisper API (30 секунд)
            transcript = await asyncio.wait_for(
                asyncio.to_thread(
                    openai.audio.transcriptions.create, model="whisper-1", file=audio_file
                ),
                timeout=30.0
            )

        result_text = transcript.text
        logger.info(f"🎯 Whisper API ответил: '{result_text}'")
        return result_text

    except asyncio.TimeoutError:
        logger.error("⏰ Whisper API не ответил за 30 секунд - превышен timeout")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка транскрибации аудио: {e}")
        return None


async def text_to_speech(text, config, voice_model="tts-1", voice="alloy"):
    """Преобразует текст в речь с помощью OpenAI TTS API."""
    try:
        logger.info(f"🎤 Начинаю генерацию голоса для текста: '{text[:50]}...'")

        # Ограничиваем длину текста (OpenAI TTS имеет лимит в 4096 символов)
        if len(text) > 4000:
            text = text[:4000] + "..."
            logger.warning("⚠️ Текст обрезан до 4000 символов для TTS")

        # Генерируем уникальное имя файла
        import uuid

        audio_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"

        logger.info("📡 Отправляю текст в OpenAI TTS API...")
        with OPENAI_LOCK:
            client = openai.OpenAI(api_key=config["openai_api_key"])
            # Добавляем timeout для TTS API (30 секунд)
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.audio.speech.create,
                    model=voice_model,
                    voice=voice,
                    input=text,
                    response_format="mp3",
                ),
                timeout=30.0
            )

        # Сохраняем аудиофайл
        logger.info(f"💾 Сохраняю голосовой файл: {audio_filename}")
        logger.info(f"📊 Размер response.content: {len(response.content)} байт")
        try:
            with open(audio_filename, "wb") as f:
                f.write(response.content)
            logger.info(f"✅ Файл успешно сохранен: {audio_filename}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения файла: {e}")
            logger.error(f"❌ Тип response.content: {type(response.content)}")
            return None

        # Проверяем размер созданного файла
        file_size = os.path.getsize(audio_filename)
        logger.info(f"✅ Голосовой файл создан: {audio_filename} (размер: {file_size} байт)")

        if file_size == 0:
            logger.error(f"❌ Созданный голосовой файл пустой: {audio_filename}")
            if os.path.exists(audio_filename):
                os.remove(audio_filename)
            return None

        logger.info(f"🎯 text_to_speech завершен успешно, возвращаю: {audio_filename}")
        return audio_filename

    except asyncio.TimeoutError:
        logger.error("⏰ TTS API не ответил за 30 секунд - превышен timeout")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка генерации голоса: {e}")
        return None


def add_message_to_cache(chat_id, message_data, limit=GROUP_CONTEXT_MESSAGES_LIMIT):
    """Добавляет сообщение в кэш для анализа контекста."""
    if chat_id not in GROUP_MESSAGES_CACHE:
        GROUP_MESSAGES_CACHE[chat_id] = []

    GROUP_MESSAGES_CACHE[chat_id].append(message_data)

    # Keep only recent messages
    if len(GROUP_MESSAGES_CACHE[chat_id]) > limit:
        GROUP_MESSAGES_CACHE[chat_id] = GROUP_MESSAGES_CACHE[chat_id][-limit:]


def get_group_chat_context(chat_id):
    """Получает контекст группового чата из кэша сообщений."""
    try:
        if chat_id not in GROUP_MESSAGES_CACHE or not GROUP_MESSAGES_CACHE[chat_id]:
            return "No recent messages found in chat."

        messages = GROUP_MESSAGES_CACHE[chat_id]

        # Format context as text
        context_lines = [f"[{msg['time']}] {msg['user']}: {msg['text']}" for msg in messages]
        context = "Recent chat context:\n" + "\n".join(context_lines)
        return context

    except Exception as e:
        logger.error(f"Error getting group chat context: {e}")
        return "Unable to retrieve chat context."


async def ask_openai(prompt, config, conversation_key, user_info=None):
    """Отправляет запрос в OpenAI и возвращает ответ."""
    try:
        with OPENAI_LOCK:
            client = openai.OpenAI(api_key=config["openai_api_key"])

            with CONVERSATIONS_LOCK:
                if conversation_key in CONVERSATIONS:
                    thread_id = CONVERSATIONS[conversation_key]["thread_id"]
                else:
                    thread_resp = client.beta.threads.create()
                    thread_id = thread_resp.id
                    CONVERSATIONS[conversation_key] = {
                        "thread_id": thread_id, 
                        "messages": [],
                        "user_info": user_info or {}
                    }
                
                # Обновляем информацию о пользователе, если она предоставлена
                if user_info and "user_info" in CONVERSATIONS[conversation_key]:
                    CONVERSATIONS[conversation_key]["user_info"].update(user_info)

            try:
                client.beta.threads.messages.create(
                    thread_id=thread_id, role="user", content=prompt
                )
                run_resp = client.beta.threads.runs.create(
                    thread_id=thread_id, assistant_id=config["assistant_id"]
                )
            except Exception as e:
                logger.error(f"❌ Ошибка создания сообщения или run: {e}")
                # Создаем новый thread для следующего запроса
                with CONVERSATIONS_LOCK:
                    if conversation_key in CONVERSATIONS:
                        del CONVERSATIONS[conversation_key]
                return "❌ Ошибка: Не удалось отправить запрос в OpenAI"

        start_time = time.time()
        timeout = 45
        while True:
            with OPENAI_LOCK:
                status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id, run_id=run_resp.id
                ).status
            if status == "completed":
                break
            elif status == "failed":
                return "❌ Ошибка: OpenAI Assistant не смог обработать запрос."
            elif status == "cancelled":
                return "❌ Ошибка: Запрос к OpenAI Assistant был отменен."
            if time.time() - start_time > timeout:
                return "❌ Ошибка: Превышено время ожидания ответа от OpenAI."
            await asyncio.sleep(2)

        with OPENAI_LOCK:
            messages = client.beta.threads.messages.list(thread_id=thread_id).data

        with CONVERSATIONS_LOCK:
            CONVERSATIONS[conversation_key]["messages"] = []
            for msg in messages:
                if msg.content and len(msg.content) > 0:
                    content_text = ""
                    for content_item in msg.content:
                        if hasattr(content_item, "text") and hasattr(content_item.text, "value"):
                            content_text += content_item.text.value
                        elif hasattr(content_item, "text"):
                            content_text += str(content_item.text)
                    if content_text:
                        CONVERSATIONS[conversation_key]["messages"].append(
                            {"role": msg.role, "content": content_text, "timestamp": msg.created_at}
                        )

        # Возвращаем ответ
        if messages and messages[0].content and len(messages[0].content) > 0:
            first_content = messages[0].content[0]
            if hasattr(first_content, "text") and hasattr(first_content.text, "value"):
                return first_content.text.value
            elif hasattr(first_content, "text"):
                return str(first_content.text)

        return "❌ Ошибка: Не удалось получить ответ от OpenAI"
    except Exception as e:
        logger.exception("Ошибка в ask_openai:")
        return f"❌ Ошибка: {e}"


async def aiogram_bot(config, stop_event):
    """Основная функция запуска бота aiogram с поддержкой групп."""

    # Валидация токена перед запуском
    token = config.get("telegram_token")
    if not token:
        logger.error("❌ Токен Telegram не найден в конфигурации")
        return

    is_valid, message = validate_telegram_token(token)
    if not is_valid:
        logger.error(f"❌ Невалидный токен Telegram: {message}")
        return

    try:
        bot = Bot(token=token, default=DefaultBotProperties(parse_mode="HTML"))
        dp = Dispatcher()
        bot_user = await bot.get_me()
        bot_username = bot_user.username
        logger.info(f"Бот {bot_username} запущен.")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Telegram API: {e}")
        return

    @dp.message(Command(commands=["start"]))
    async def cmd_start(message: types.Message):
        enable_ai_responses = config.get("enable_ai_responses", True)

        if enable_ai_responses:
            # Обычный режим с ИИ ответами
            text = (
                f"👋 Привет! Я бот {config.get('bot_name', '')}. "
                f"В личных сообщениях я отвечаю на всё. "
                f"В группах — когда вы упоминаете меня (@{bot_username}) или отвечаете на мои сообщения."
            )
        else:
            # Режим только транскрибатора
            text = (
                f"🎙️ Привет! Я бот-транскрибатор {config.get('bot_name', '')}.\n\n"
                f"📝 **Режим работы:** Только транскрибация голосовых сообщений\n"
                f"🎤 Отправьте голосовое сообщение — я распознаю речь и отправлю вам текст\n"
                f"🚫 ИИ ответы отключены — я не генерирую текстовые ответы"
            )

        await message.answer(text)

    @dp.message()
    async def handle_group_message(message: types.Message):
        """Обрабатывает текстовые и голосовые сообщения в ЛС и группах."""

        # Обрабатываем только текстовые и голосовые сообщения
        if not (message.text or message.voice):
            return

        text_content = message.text or message.caption or ""

        # Добавляем все сообщения из групп в кэш для контекста
        if message.chat.type != "private" and (message.text or message.caption):
            user_name = "Unknown"
            if message.from_user:
                user_name = message.from_user.first_name or "User"
                if message.from_user.username:
                    user_name += f" (@{message.from_user.username})"

            # Skip very short messages or system messages
            if len(text_content.strip()) >= 2:
                message_data = {
                    "user": user_name,
                    "text": text_content,
                    "time": message.date.strftime("%H:%M"),
                }
                context_limit = config.get("group_context_limit", GROUP_CONTEXT_MESSAGES_LIMIT)
                add_message_to_cache(message.chat.id, message_data, context_limit)

        # 1. Определяем, должен ли бот реагировать
        should_process = False

        if message.chat.type == "private" or message.reply_to_message and message.reply_to_message.from_user.id == bot.id or message.voice or f"@{bot_username}" in text_content:
            should_process = True

        if not should_process:
            return  # Игнорируем сообщение

        # 2. Определяем ключ диалога (личный или групповой)
        if message.chat.type == "private":
            conversation_key = f"{config['telegram_token']}_{message.from_user.id}"
        else:
            conversation_key = f"{config['telegram_token']}_{message.chat.id}"
        
        # 2.1. Получаем информацию о пользователе/группе для сохранения
        user_info = get_user_info(message)

        # 3. Получаем текст от пользователя (из текста или голоса)
        user_prompt = ""
        if message.voice:
            logger.info(
                f"🎤 Получено голосовое сообщение от пользователя {message.from_user.first_name if message.from_user else 'Unknown'}"
            )
            try:
                voice_file_id = message.voice.file_id
                logger.info(f"📥 Начинаю скачивание голосового файла {voice_file_id}")

                file_info = await bot.get_file(voice_file_id)
                ogg_filename = f"{voice_file_id}.ogg"

                logger.info(f"⬇️ Скачиваю файл: {file_info.file_path} → {ogg_filename}")
                await bot.download_file(file_info.file_path, ogg_filename)

                # Проверяем размер скачанного файла
                file_size = os.path.getsize(ogg_filename) if os.path.exists(ogg_filename) else 0
                logger.info(f"📁 Файл скачан: {ogg_filename} (размер: {file_size} байт)")

                if file_size == 0:
                    logger.error(f"❌ Скачанный файл пустой: {ogg_filename}")
                    await message.reply("❌ Ошибка: голосовое сообщение пустое")
                    return

                # OpenAI Whisper поддерживает OGG напрямую - НЕ НУЖНА КОНВЕРТАЦИЯ!
                logger.info("✅ Пропускаю конвертацию - Whisper поддерживает OGG напрямую")

                logger.info("🤖 Отправляю OGG напрямую в OpenAI Whisper...")
                with OPENAI_LOCK:
                    openai.api_key = config["openai_api_key"]
                    transcribed_text = await transcribe_audio(ogg_filename)

                if transcribed_text:
                    logger.info(f"✅ Транскрибация успешна: '{transcribed_text}'")
                    await message.reply(f'<i>Транскрибация: "{transcribed_text}"</i>')
                    user_prompt = transcribed_text
                else:
                    logger.error("❌ Транскрибация не удалась")
                    await message.reply("❌ Не удалось распознать речь в голосовом сообщении")
                    return

            except Exception as e:
                logger.error(f"❌ Ошибка обработки голосового сообщения: {e}")
                await message.reply(f"❌ Ошибка обработки голосового сообщения: {e}")
                return
            finally:
                # Удаляем временный OGG файл
                if os.path.exists(ogg_filename):
                    os.remove(ogg_filename)
                    logger.info(f"🗑️ Удален временный файл: {ogg_filename}")
        else:  # message.text
            user_prompt = message.text
            logger.info(
                f"💬 Получено текстовое сообщение: '{user_prompt[:50]}...' от {message.from_user.first_name if message.from_user else 'Unknown'}"
            )

        # 4. Проверяем режим работы бота (ИИ ответы включены или только транскрибация)
        enable_ai_responses = config.get(
            "enable_ai_responses", True
        )  # По умолчанию включены для обратной совместимости

        if not enable_ai_responses:
            # Режим только транскрибации - ИИ ответы отключены
            if message.voice:
                # Сохраняем диалог в режиме транскрибатора для отображения в веб-интерфейсе
                save_transcription_dialog(conversation_key, "🎤 Голосовое сообщение", f'Транскрибация: "{user_prompt}"', user_info)
                logger.info("🎯 Бот в режиме транскрибатора - голос обработан, диалог сохранен, ИИ ответ пропущен")
                return
            else:
                # For text messages, send info about transcription-only mode
                if message.chat.type == "private":
                    transcriber_reply = "🎙️ Бот работает в режиме транскрибатора. Отправьте голосовое сообщение для распознавания речи."
                    await message.reply(transcriber_reply)
                    # Сохраняем диалог для текстовых сообщений в ЛС
                    save_transcription_dialog(conversation_key, user_prompt, transcriber_reply, user_info)
                # В группах не отвечаем на текстовые сообщения в режиме транскрибатора
                logger.info("🎯 Бот в режиме транскрибатора - текстовое сообщение пропущено")
                return

        # 5. Обычный режим с ИИ ответами
        # Убираем упоминание бота из запроса
        cleaned_prompt = user_prompt.replace(f"@{bot_username}", "").strip()

        if not cleaned_prompt:
            await message.reply("Я вас слушаю. Задайте свой вопрос или дайте команду.")
            return

        # 6. Формируем финальный запрос с контекстом для групп
        final_prompt = cleaned_prompt

        # В групповых чатах добавляем контекст последних сообщений
        if message.chat.type != "private":
            chat_context = get_group_chat_context(message.chat.id)

            # Формируем запрос с контекстом
            final_prompt = f"""Контекст группового чата:
{chat_context}

Пользователь обращается к тебе с вопросом: {cleaned_prompt}

Ответь учитывая контекст беседы. Если контекст помогает понять вопрос лучше, используй его. Отвечай естественно и по делу."""

        # 7. Отправляем в OpenAI и отвечаем пользователю
        logger.info(f"🧠 Отправляю запрос в OpenAI: '{final_prompt[:100]}...'")
        response = await ask_openai(final_prompt, config, conversation_key, user_info)
        logger.info(f"✅ Получен ответ от OpenAI: '{response[:100]}...'")

        # 8. Проверяем, нужно ли отправить голосовой ответ
        enable_voice_responses = config.get("enable_voice_responses", False)
        voice_model = config.get("voice_model", "tts-1")
        voice_type = config.get("voice_type", "alloy")

        if enable_voice_responses:
            logger.info("🎤 Генерирую голосовой ответ...")
            try:
                # Генерируем голосовое сообщение
                logger.info("🔧 Вызываю text_to_speech...")
                audio_file_path = await text_to_speech(response, config, voice_model, voice_type)
                logger.info(f"🔧 text_to_speech завершен, результат: {audio_file_path}")

                if audio_file_path and os.path.exists(audio_file_path):
                    logger.info(f"📤 Отправляю текстовый ответ: {response[:50]}...")
                    # Отправляем и текстовый и голосовой ответ
                    await message.reply(response)

                    logger.info(f"📤 Отправляю голосовой ответ: {audio_file_path}")
                    # Отправляем голосовое сообщение используя FSInputFile
                    voice_file = FSInputFile(audio_file_path)
                    await message.reply_voice(voice_file)

                    logger.info("🎵 Голосовой ответ отправлен пользователю")

                    # Удаляем временный файл
                    os.remove(audio_file_path)
                    logger.info(f"🗑️ Удален временный голосовой файл: {audio_file_path}")
                else:
                    logger.warning("⚠️ Не удалось создать голосовой файл, отправляю только текст")
                    await message.reply(response)

            except Exception as e:
                logger.error(f"❌ Ошибка при создании голосового ответа: {e}")
                # В случае ошибки отправляем текстовый ответ
                await message.reply(response)
        else:
            # Обычный текстовый ответ
            logger.info(f"📤 Отправляю текстовый ответ: {response[:50]}...")
            await message.reply(response)

        logger.info("📤 Ответ отправлен пользователю")

    logger.info(f"Запуск Telegram-бота {config.get('bot_name', '')}...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        stop_wait_task = asyncio.create_task(stop_event.wait())
        polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
        await asyncio.wait([polling_task, stop_wait_task], return_when=asyncio.FIRST_COMPLETED)
        if stop_wait_task.done():
            polling_task.cancel()
            logger.info(f"Остановка бота {config.get('bot_name', '')} по запросу.")
    except Exception:
        logger.exception(f"Ошибка в боте {config.get('bot_name', '')}:")
    finally:
        await bot.session.close()
