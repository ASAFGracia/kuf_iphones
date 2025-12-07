#!/bin/bash

echo "🚀 Запуск проекта Parser Avito & Kufar"
echo ""

# Проверка Docker
if ! docker ps >/dev/null 2>&1; then
    echo "❌ Docker не запущен!"
    echo "   Запустите Docker Desktop и попробуйте снова"
    exit 1
fi

# Проверка .env
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден"
    echo "   Создаю из шаблона..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ .env создан из .env.example"
        echo "   ⚠️  ВАЖНО: Заполните .env своими данными перед запуском!"
        read -p "Заполнили .env? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Откройте .env и заполните все поля, затем запустите скрипт снова"
            exit 1
        fi
    else
        echo "❌ .env.example не найден!"
        exit 1
    fi
fi

# Запуск проекта
echo ""
echo "📦 Запуск Docker контейнеров..."
docker-compose up -d

# Проверка статуса
echo ""
echo "⏳ Ожидание запуска контейнеров..."
sleep 5

# Проверка
if docker-compose ps | grep -q "Up"; then
    echo "✅ Проект запущен!"
    echo ""
    echo "📊 Статус контейнеров:"
    docker-compose ps
    echo ""
    echo "📝 Просмотр логов:"
    echo "   docker-compose logs -f app"
    echo ""
    echo "🛑 Остановка проекта:"
    echo "   docker-compose stop"
    echo ""
    echo "🔄 Перезапуск:"
    echo "   docker-compose restart app"
else
    echo "❌ Ошибка запуска!"
    echo "Проверьте логи:"
    echo "   docker-compose logs app"
    exit 1
fi
