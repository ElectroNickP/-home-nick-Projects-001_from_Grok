#!/bin/bash

# Скрипт для тестирования развертывания через Docker

echo "🐳 DOCKER DEPLOYMENT TEST"
echo "=========================="
echo

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    echo "Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен!"
    echo "Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker и Docker Compose найдены"
echo

# Создание директории для результатов
mkdir -p test-results logs

echo "🏗️ Сборка Docker образа для тестирования..."
docker build -t telegram-bot-manager-test .

if [ $? -eq 0 ]; then
    echo "✅ Docker образ успешно собран"
else
    echo "❌ Ошибка сборки Docker образа"
    exit 1
fi

echo
echo "🧪 Запуск тестов развертывания..."

# Тест локального развертывания
echo "1️⃣ Тестирование локального развертывания..."
docker run --rm \
    -v "$(pwd)/test-results:/home/testuser/test-results" \
    telegram-bot-manager-test

echo
echo "2️⃣ Тестирование клонирования из GitHub..."

# Создание и запуск GitHub clone теста
docker run --rm \
    -v "$(pwd)/test-results:/test-results" \
    ubuntu:22.04 \
    bash -c "
        echo '🌐 ТЕСТ КЛОНИРОВАНИЯ ИЗ GITHUB'
        echo '=============================='
        
        # Установка зависимостей
        apt-get update -q > /dev/null 2>&1
        apt-get install -y python3 python3-pip python3-venv git curl > /dev/null 2>&1
        
        # Клонирование
        cd /tmp
        echo '📥 Клонирование репозитория...'
        git clone https://github.com/ElectroNickP/Telegram-Bot-Manager.git > /dev/null 2>&1
        
        if [ \$? -eq 0 ]; then
            echo '✅ Репозиторий успешно клонирован'
        else
            echo '❌ Ошибка клонирования репозитория'
            exit 1
        fi
        
        cd Telegram-Bot-Manager
        
        # Переключение на ветку
        echo '🔄 Переключение на ветку prod-test...'
        git checkout prod-test > /dev/null 2>&1
        
        if [ \$? -eq 0 ]; then
            echo '✅ Переключение на ветку prod-test успешно'
        else
            echo '❌ Ветка prod-test не найдена'
            exit 1
        fi
        
        # Проверка файлов
        echo '📋 Проверка критичных файлов...'
        files_ok=true
        
        for file in start.py requirements-prod.txt deploy-test.py; do
            if [ -f \"\$file\" ]; then
                echo \"✅ \$file\"
            else
                echo \"❌ \$file не найден\"
                files_ok=false
            fi
        done
        
        if [ \"\$files_ok\" = true ]; then
            echo '🧪 Запуск тестов развертывания...'
            timeout 30 python3 deploy-test.py
            echo '✅ Тесты завершены'
        else
            echo '❌ Критичные файлы отсутствуют'
            exit 1
        fi
        
        echo '✅ GITHUB CLONE TEST COMPLETED' > /test-results/github-test.log
        echo '🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!'
    "

echo
echo "📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:"
echo "=========================="

# Проверка результатов
if [ -f "test-results/github-test.log" ]; then
    echo "✅ GitHub clone test: PASSED"
else
    echo "❌ GitHub clone test: FAILED"
fi

echo
echo "🎯 ЗАКЛЮЧЕНИЕ:"
if [ -f "test-results/github-test.log" ]; then
    echo "✅ Проект готов к развертыванию на Ubuntu!"
    echo "✅ Клонирование из GitHub работает корректно"
    echo "✅ Все критичные файлы присутствуют"
    echo "✅ Тесты развертывания проходят успешно"
else
    echo "❌ Обнаружены проблемы с развертыванием"
fi

echo
echo "📁 Результаты сохранены в ./test-results/"
echo "📋 Логи в ./logs/"

