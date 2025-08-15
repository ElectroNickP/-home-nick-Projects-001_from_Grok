# 🤖 Telegram Bot Manager with OpenAI Assistant v2.4.0

Мощная система управления Telegram ботами с поддержкой OpenAI Assistant API, голосовых сообщений, группового контекста и профессиональным REST API с enterprise-level автообновлением.

🆕 **Новое в версии 2.4.0:** 
- 🛡️ **Профессиональное автообновление** с системой бэкапов и rollback
- 📦 **Автоматические бэкапы** перед каждым обновлением
- 🔄 **Система rollback** при ошибках обновления
- 📊 **Прогресс-бар в реальном времени** для процесса обновления
- 🗂️ **Управление бэкапами** через веб-интерфейс
- ⚡ **Надежный restart** механизм через bash скрипты
- 📋 **Детальное логирование** всех операций обновления

## ✨ Основные возможности

### 🌐 Пользовательский интерфейс
- **Веб-интерфейс** для визуального управления ботами
- **Просмотр диалогов** и истории сообщений в реальном времени
- **Профессиональное автообновление** с прогресс-баром и системой бэкапов
- **Управление бэкапами** с возможностью rollback

### 🤖 Telegram бот функции
- **Интеграция с OpenAI Assistant API** для умных ответов
- **Поддержка голосовых сообщений** (транскрибация через Whisper)
- **Голосовые ответы** (преобразование текста в речь через TTS)
- **Анализ группового контекста** (умные ответы с учетом истории)
- **Работа в группах и личных сообщениях**

### ⚡ Professional API v2.0
- **CRUD операции** для полного управления ботами
- **REST API endpoints** с стандартизированными ответами
- **Real-time мониторинг** системы и статистика
- **Встроенная документация** с примерами использования
- **HTTP Basic Authentication** для безопасности

## 🚀 Быстрый старт

### 1. Установка

```bash
# Клонируем репозиторий
git clone https://github.com/ElectroNickP/-home-nick-Projects-001_from_Grok.git
cd -home-nick-Projects-001_from_Grok

# Создаем виртуальное окружение
python3 -m venv venv

# Активируем виртуальное окружение
# На Linux/Mac:
source venv/bin/activate
# На Windows:
# venv\Scripts\activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 2. Запуск

```bash
# Переходим в директорию src
cd src

# Запускаем приложение
python app.py
```

🌐 **Веб-интерфейс будет доступен по адресу:** http://localhost:60183

**Данные для входа:**
- **Логин:** `admin`
- **Пароль:** `securepassword123`

⚠️ **ВАЖНО:** Измените логин и пароль в файле `src/app.py` (строка 22) перед использованием в продакшене!

✅ **Статус:** Система полностью протестирована и готова к продакшену. Все функции включая голосовые ответы, CRUD API v2, system monitoring и enterprise-level автообновление с бэкапами работают корректно.

## 📋 Пошаговая инструкция

### Шаг 1: Подготовка Telegram бота

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите **Telegram Token** (выглядит как `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
3. Сохраните токен - он понадобится при настройке

### Шаг 2: Настройка OpenAI Assistant

1. Зайдите в [OpenAI Platform](https://platform.openai.com/)
2. Создайте **API Key** в разделе API Keys
3. Создайте **Assistant** в разделе Assistants
4. Скопируйте **Assistant ID** (выглядит как `asst_abc123...`)

### Шаг 3: Добавление бота в систему

1. Откройте веб-интерфейс: http://localhost:60183
2. Войдите с данными: `admin` / `securepassword123`
3. Заполните форму "Добавить нового бота":
   - **Название бота:** Любое удобное имя
   - **Telegram Token:** Токен от BotFather
   - **OpenAI API Key:** Ваш ключ OpenAI
   - **Assistant ID:** ID вашего ассистента
   - **Количество сообщений для контекста:** 15 (по умолчанию)
   - **🎤 Голосовые ответы:** Включить для TTS ответов
   - **Модель голоса:** TTS-1 (быстрая) или TTS-1-HD (качественная)
   - **Тип голоса:** Выберите подходящий голос (Alloy, Echo, Fable, Onyx, Nova, Shimmer)
4. Нажмите **"Создать"**
5. Нажмите **"Старт"** чтобы запустить бота

### Шаг 4: Тестирование

1. Найдите своего бота в Telegram
2. Отправьте команду `/start`
3. Попробуйте отправить текстовое или голосовое сообщение
4. В группах упоминайте бота через `@username` или отвечайте на его сообщения

## ⚙️ Настройки системы

### Изменение логина и пароля

Отредактируйте файл `src/app.py`, строку 22:

```python
USERS = {"ваш_логин": "ваш_пароль"}
```

### Настройка групповых ботов

- **Количество сообщений для контекста:** определяет сколько последних сообщений анализирует бот
- **Рекомендуется:** 10-20 сообщений для оптимальной производительности
- **Максимум:** 50 сообщений

## 🔧 Системные требования

- **Python:** 3.8 или выше
- **ОС:** Linux, macOS, Windows
- **RAM:** минимум 512 MB
- **Дисковое пространство:** 500 MB

### Дополнительные зависимости

Для работы с голосовыми сообщениями необходим `ffmpeg`:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**CentOS/RHEL:**
```bash
sudo yum install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Скачайте с [официального сайта](https://ffmpeg.org/download.html)

## 🐳 Docker (альтернативный запуск)

```dockerfile
# Создайте Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
EXPOSE 60183

CMD ["python", "src/app.py"]
```

```bash
# Сборка и запуск
docker build -t telegram-bot-manager .
docker run -p 60183:60183 telegram-bot-manager
```

## 📁 Структура проекта

```
├── README.md                 # Этот файл
├── requirements.txt          # Python зависимости
├── .gitignore               # Git игнорируемые файлы
└── src/
    ├── app.py               # Основное Flask приложение
    ├── bot_manager.py       # Управление ботами
    ├── config_manager.py    # Управление конфигурацией
    ├── telegram_bot.py      # Telegram бот логика
    └── templates/
        ├── index.html       # Главная страница
        └── dialogs.html     # Страница диалогов
```

## 🎯 Использование

### В личных сообщениях
Бот отвечает на все сообщения автоматически.

### В группах
Бот реагирует на:
- Упоминания: `@bot_username ваш вопрос`
- Ответы на сообщения бота
- Анализирует контекст последних сообщений для более умных ответов

### Голосовые сообщения
Отправьте голосовое сообщение - бот автоматически:
1. Транскрибирует речь в текст
2. Покажет результат транскрибации
3. Ответит на основе распознанного текста

### Голосовые ответы (TTS)
При включенной настройке **"Голосовые ответы"** бот будет:
1. Отправлять обычный текстовый ответ
2. Генерировать голосовую версию ответа через OpenAI TTS
3. Отправлять голосовое сообщение с ответом

**Доступные голоса:**
- **Alloy** - универсальный голос
- **Echo** - мужской голос  
- **Fable** - британский акцент
- **Onyx** - мужской, глубокий
- **Nova** - женский, молодой
- **Shimmer** - женский, мягкий

**Модели TTS:**
- **TTS-1** - быстрая генерация, стандартное качество
- **TTS-1-HD** - медленнее, но качество выше

## 📡 Professional API v2.0

Система предоставляет полный REST API для программного управления ботами.

### 🔗 Документация API
**Полная документация:** http://localhost:60183/api/v2/docs

### 🔐 Аутентификация
Все API endpoints требуют HTTP Basic Authentication:
```bash
curl -u username:password http://localhost:60183/api/v2/...
```

### 🤖 CRUD операции с ботами

#### Создание бота
```bash
curl -u username:password -X POST http://localhost:60183/api/v2/bots \
  -H "Content-Type: application/json" \
  -d '{
    "bot_name": "MyBot",
    "telegram_token": "YOUR_TELEGRAM_TOKEN", 
    "openai_api_key": "YOUR_OPENAI_KEY",
    "assistant_id": "YOUR_ASSISTANT_ID",
    "enable_voice_responses": true,
    "voice_model": "tts-1-hd",
    "voice_type": "nova"
  }'
```

#### Обновление конфигурации
```bash
curl -u username:password -X PUT http://localhost:60183/api/v2/bots/4 \
  -H "Content-Type: application/json" \
  -d '{"bot_name": "UpdatedName", "group_context_limit": 30}'
```

#### Управление состоянием
```bash
# Запуск бота
curl -u username:password -X POST http://localhost:60183/api/v2/bots/4/start

# Остановка бота
curl -u username:password -X POST http://localhost:60183/api/v2/bots/4/stop

# Перезапуск бота  
curl -u username:password -X POST http://localhost:60183/api/v2/bots/4/restart
```

#### Получение информации
```bash
# Список ботов
curl -u username:password http://localhost:60183/api/v2/bots

# Статус бота
curl -u username:password http://localhost:60183/api/v2/bots/4/status

# Системная информация
curl -u username:password http://localhost:60183/api/v2/system/health
```

#### Удаление бота
```bash
curl -u username:password -X DELETE http://localhost:60183/api/v2/bots/4
```

### 📊 System Monitoring API

#### Проверка здоровья системы
```bash
curl -u username:password http://localhost:60183/api/v2/system/health
```

#### Детальная информация о системе  
```bash
curl -u username:password http://localhost:60183/api/v2/system/info
```

#### Real-time статистика
```bash
curl -u username:password http://localhost:60183/api/v2/system/stats
```

### 📋 Формат ответов API v2
Все endpoints возвращают стандартизированные JSON ответы:
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully",
  "timestamp": "2025-08-15T20:00:00Z"
}
```

### ⚠️ HTTP коды ошибок
- **200** - Успешный запрос
- **201** - Ресурс создан
- **400** - Неверный запрос
- **401** - Не авторизован  
- **404** - Ресурс не найден
- **500** - Внутренняя ошибка сервера

## 🔍 Просмотр диалогов

1. В веб-интерфейсе нажмите **"Диалоги"** рядом с ботом
2. Выберите беседу из списка
3. Просматривайте историю сообщений в реальном времени

## ⚠️ Устранение неполадок

### Бот не отвечает
- Проверьте правильность Telegram Token
- Убедитесь, что бот запущен (зеленый статус)
- Проверьте логи в файле `bot.log`

### Ошибки OpenAI
- Проверьте правильность API Key
- Убедитесь, что Assistant ID существует
- Проверьте баланс на OpenAI аккаунте

### Проблемы с голосом
- Установите ffmpeg
- Проверьте права доступа к файлам
- Убедитесь в наличии свободного места

### Ошибка импорта модулей
```bash
# Если получаете ошибки импорта, запускайте из корневой директории:
cd /path/to/project
PYTHONPATH=/path/to/project python src/app.py
```

## 🔐 Безопасность

- **Измените стандартный пароль** в `src/app.py`
- **Не публикуйте** токены и ключи API в публичных репозиториях
- **Используйте HTTPS** в продакшене
- **Ограничьте доступ** к веб-интерфейсу

## 🤝 Поддержка

Если у вас возникли проблемы:

1. Проверьте логи в файле `bot.log`
2. Убедитесь в правильности всех токенов
3. Проверьте системные требования
4. Создайте Issue в GitHub репозитории

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл LICENSE для подробностей.

---

**Разработано с ❤️ для управления Telegram ботами**
# Test update for demo
# Test restart mechanism
# Test improved restart mechanism v2.0
# Test fixed restart mechanism v2.1 with proper venv activation
