#!/bin/bash
set -e

echo "🧹 Очистка старых контейнеров..."
docker stop test-telegram-bot-manager 2>/dev/null || true  
docker rm test-telegram-bot-manager 2>/dev/null || true
docker rmi telegram-bot-manager-test 2>/dev/null || true

echo "🐳 Создаем чистый Ubuntu контейнер..."
cat > Dockerfile.test << 'INNER_EOF'
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    git \
    curl \
    wget \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.11
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Set working directory
WORKDIR /app

# Clone the repository (simulating user action)
RUN git clone https://github.com/ElectroNickP/Telegram-Bot-Manager.git . && \
    git checkout prod-test

# Expose port
EXPOSE 5000

# Default command - what user would run
CMD ["python3", "start.py", "--help"]
INNER_EOF

echo "🔨 Собираем Docker образ..."
docker build -f Dockerfile.test -t telegram-bot-manager-test .

echo "🚀 Тестируем help команду..."
docker run --rm telegram-bot-manager-test

echo "🎯 Запускаем полный тест развертывания..."
docker run -d --name test-telegram-bot-manager -p 5001:5000 telegram-bot-manager-test python3 start.py --port 5000

echo "⏳ Ждем запуска сервера..."
sleep 15

echo "🔍 Проверяем логи контейнера..."
docker logs test-telegram-bot-manager

echo "🌐 Проверяем доступность веб-интерфейса..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/ || echo "FAILED"

echo "🧹 Очистка после теста..."
docker stop test-telegram-bot-manager
docker rm test-telegram-bot-manager

echo "✅ Тест завершен!"
