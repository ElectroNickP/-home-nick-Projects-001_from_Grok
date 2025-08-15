import os
import time
import asyncio
import logging
import openai
from pydub import AudioSegment
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.bot import DefaultBotProperties

from config_manager import CONVERSATIONS, CONVERSATIONS_LOCK, OPENAI_LOCK

logger = logging.getLogger(__name__)

# Configuration for group context analysis
GROUP_CONTEXT_MESSAGES_LIMIT = 15  # Number of recent messages to analyze in groups

# Store recent group messages for context analysis
GROUP_MESSAGES_CACHE = {}  # {chat_id: [message_data, ...]}

async def transcribe_audio(file_path):
    """Транскрибирует аудиофайл с помощью OpenAI Whisper."""
    try:
        with open(file_path, "rb") as audio_file:
            transcript = await asyncio.to_thread(openai.audio.transcriptions.create,
                model="whisper-1",
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        logger.error(f"Ошибка транскрибации аудио: {e}")
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

async def ask_openai(prompt, config, conversation_key):
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
                    CONVERSATIONS[conversation_key] = {"thread_id": thread_id, "messages": []}

            client.beta.threads.messages.create(thread_id=thread_id, role="user", content=prompt)
            run_resp = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=config["assistant_id"])

        start_time = time.time()
        timeout = 45
        while True:
            with OPENAI_LOCK:
                status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_resp.id).status
            if status == "completed":
                break
            if time.time() - start_time > timeout:
                return "❌ Ошибка: Превышено время ожидания ответа от OpenAI."
            await asyncio.sleep(2)

        with OPENAI_LOCK:
            messages = client.beta.threads.messages.list(thread_id=thread_id).data

        with CONVERSATIONS_LOCK:
            CONVERSATIONS[conversation_key]["messages"] = [
                {"role": msg.role, "content": msg.content[0].text.value, "timestamp": msg.created_at}
                for msg in messages
            ]
        return messages[0].content[0].text.value
    except Exception as e:
        logger.exception("Ошибка в ask_openai:")
        return f"❌ Ошибка: {e}"

async def aiogram_bot(config, stop_event):
    """Основная функция запуска бота aiogram с поддержкой групп."""
    bot = Bot(token=config["telegram_token"], default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    bot_user = await bot.get_me()
    bot_username = bot_user.username
    logger.info(f"Бот {bot_username} запущен.")

    @dp.message(Command(commands=["start"]))
    async def cmd_start(message: types.Message):
        text = (f"👋 Привет! Я бот {config.get('bot_name', '')}. "
                f"В личных сообщениях я отвечаю на всё. "
                f"В группах — когда вы упоминаете меня (@{bot_username}) или отвечаете на мои сообщения.")
        await message.answer(text)

    @dp.message()
    async def handle_group_message(message: types.Message):
        """Обрабатывает текстовые и голосовые сообщения в ЛС и группах."""
        
        # Обрабатываем только текстовые и голосовые сообщения
        if not (message.text or message.voice):
            return

        text_content = message.text or message.caption or ""
        
        # Добавляем все сообщения из групп в кэш для контекста
        if message.chat.type != 'private' and (message.text or message.caption):
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
                    "time": message.date.strftime("%H:%M")
                }
                context_limit = config.get("group_context_limit", GROUP_CONTEXT_MESSAGES_LIMIT)
                add_message_to_cache(message.chat.id, message_data, context_limit)

        # 1. Определяем, должен ли бот реагировать
        should_process = False

        if message.chat.type == 'private':
            should_process = True
        elif message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
            should_process = True
        elif f"@{bot_username}" in text_content:
            should_process = True

        if not should_process:
            return  # Игнорируем сообщение

        # 2. Определяем ключ диалога (личный или групповой)
        if message.chat.type == 'private':
            conversation_key = f"{config['telegram_token']}_{message.from_user.id}"
        else:
            conversation_key = f"{config['telegram_token']}_{message.chat.id}"

        # 3. Получаем текст от пользователя (из текста или голоса)
        user_prompt = ""
        if message.voice:
            voice_file_id = message.voice.file_id
            file_info = await bot.get_file(voice_file_id)
            ogg_filename = f"{voice_file_id}.ogg"
            mp3_filename = f"{voice_file_id}.mp3"
            await bot.download_file(file_info.file_path, ogg_filename)
            try:
                audio = AudioSegment.from_ogg(ogg_filename)
                audio.export(mp3_filename, format="mp3")
                with OPENAI_LOCK:
                    openai.api_key = config["openai_api_key"]
                    transcribed_text = await transcribe_audio(mp3_filename)
                if transcribed_text:
                    await message.reply(f"<i>Транскрибация: \"{transcribed_text}\"</i>")
                    user_prompt = transcribed_text
            finally:
                if os.path.exists(ogg_filename): os.remove(ogg_filename)
                if os.path.exists(mp3_filename): os.remove(mp3_filename)
        else: # message.text
            user_prompt = message.text

        # Убираем упоминание бота из запроса
        cleaned_prompt = user_prompt.replace(f"@{bot_username}", "").strip()

        if not cleaned_prompt:
            await message.reply("Я вас слушаю. Задайте свой вопрос или дайте команду.")
            return

        # 4. Формируем финальный запрос с контекстом для групп
        final_prompt = cleaned_prompt
        
        # В групповых чатах добавляем контекст последних сообщений
        if message.chat.type != 'private':
            chat_context = get_group_chat_context(message.chat.id)
            
            # Формируем запрос с контекстом
            final_prompt = f"""Контекст группового чата:
{chat_context}

Пользователь обращается к тебе с вопросом: {cleaned_prompt}

Ответь учитывая контекст беседы. Если контекст помогает понять вопрос лучше, используй его. Отвечай естественно и по делу."""

        # 5. Отправляем в OpenAI и отвечаем пользователю
        response = await ask_openai(final_prompt, config, conversation_key)
        await message.reply(response)

    logger.info(f"Запуск Telegram-бота {config.get('bot_name', '')}...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        stop_wait_task = asyncio.create_task(stop_event.wait())
        polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
        await asyncio.wait([polling_task, stop_wait_task], return_when=asyncio.FIRST_COMPLETED)
        if stop_wait_task.done():
            polling_task.cancel()
            logger.info(f"Остановка бота {config.get('bot_name', '')} по запросу.")
    except Exception as e:
        logger.exception(f"Ошибка в боте {config.get('bot_name', '')}:")
    finally:
        await bot.session.close()
