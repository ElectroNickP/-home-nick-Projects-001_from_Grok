# Dockerfile для тестирования развертывания на чистой Ubuntu
FROM ubuntu:22.04

# Избегаем интерактивных вопросов при установке
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для безопасности
RUN useradd -m -s /bin/bash testuser
WORKDIR /home/testuser

# Копирование проекта (для локального тестирования)
COPY . ./telegram-bot-manager/
RUN chown -R testuser:testuser ./telegram-bot-manager/

# Переключение на пользователя
USER testuser

# Рабочая директория
WORKDIR /home/testuser/telegram-bot-manager

# Скрипт для тестирования развертывания
RUN echo '#!/bin/bash\n\
echo "🚀 ТЕСТИРОВАНИЕ РАЗВЕРТЫВАНИЯ ПРОЕКТА НА ЧИСТОЙ UBUNTU"\n\
echo "=" | tr "=" "=" | head -c 60 && echo\n\
echo\n\
\n\
echo "📋 Информация о системе:"\n\
echo "OS: $(lsb_release -d | cut -f2)"\n\
echo "Python: $(python3 --version)"\n\
echo "Git: $(git --version)"\n\
echo\n\
\n\
echo "🔍 Проверка файлов проекта..."\n\
ls -la\n\
echo\n\
\n\
echo "📦 Проверка зависимостей..."\n\
if [ -f "requirements-prod.txt" ]; then\n\
    echo "✅ requirements-prod.txt найден"\n\
else\n\
    echo "❌ requirements-prod.txt не найден"\n\
fi\n\
\n\
if [ -f "start.py" ]; then\n\
    echo "✅ start.py найден"\n\
    chmod +x start.py\n\
else\n\
    echo "❌ start.py не найден"\n\
fi\n\
echo\n\
\n\
echo "🧪 Запуск тестирования развертывания..."\n\
python3 deploy-test.py\n\
echo\n\
\n\
echo "📝 Тестирование start.py --help..."\n\
python3 start.py --help\n\
echo\n\
\n\
echo "🎯 РЕЗУЛЬТАТ: Проект готов к развертыванию на Ubuntu!"\n\
' > test-deployment.sh && chmod +x test-deployment.sh

# Запуск тестов при старте контейнера
CMD ["./test-deployment.sh"]
