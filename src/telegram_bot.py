import os
import time
import asyncio
import logging
import openai
from pydub import AudioSegment
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.bot import DefaultBotProperties

from src.config_manager import CONVERSATIONS, CONVERSATIONS_LOCK, OPENAI_LOCK

logger = logging.getLogger(__name__)

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
    """Основная функция запуска бота aiogram."""
    bot = Bot(token=config["telegram_token"], default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    @dp.message(Command(commands=["start"]))
    async def cmd_start(message: types.Message):
        text = f"👋 Привет! Я бот {config.get('bot_name', '')}. Напиши или отправь голосовое сообщение."
        await message.answer(text)

    @dp.message(types.ContentType.VOICE)
    async def handle_voice_message(message: types.Message):
        """Обрабатывает голосовые сообщения."""
        voice_file_id = message.voice.file_id
        file_info = await bot.get_file(voice_file_id)
        file_path = file_info.file_path

        ogg_filename = f"{voice_file_id}.ogg"
        mp3_filename = f"{voice_file_id}.mp3"

        await bot.download_file(file_path, ogg_filename)

        try:
            audio = AudioSegment.from_ogg(ogg_filename)
            audio.export(mp3_filename, format="mp3")

            with OPENAI_LOCK:
                openai.api_key = config["openai_api_key"]
                transcribed_text = await transcribe_audio(mp3_filename)

            if transcribed_text:
                await message.reply(f"<i>Транскрибация: \"{transcribed_text}\"</i>")
                conversation_key = f"{config['telegram_token']}_{message.from_user.id}"
                response = await ask_openai(transcribed_text, config, conversation_key)
                await message.answer(response)
            else:
                await message.answer("Не удалось распознать речь в голосовом сообщении.")
        except Exception as e:
            logger.error(f"Ошибка обработки голосового сообщения: {e}")
            await message.answer("Произошла ошибка при обработке вашего голосового сообщения.")
        finally:
            if os.path.exists(ogg_filename):
                os.remove(ogg_filename)
            if os.path.exists(mp3_filename):
                os.remove(mp3_filename)

    @dp.message()
    async def handle_text_message(message: types.Message):
        """Обрабатывает текстовые сообщения."""
        conversation_key = f"{config['telegram_token']}_{message.from_user.id}"
        response = await ask_openai(message.text, config, conversation_key)
        await message.answer(response)

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
