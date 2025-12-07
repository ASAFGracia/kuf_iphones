#!/bin/bash

echo "🔄 Перезапуск проекта Parser Avito & Kufar"
echo ""

# Проверка Docker
if ! docker ps >/dev/null 2>&1; then
    echo "❌ Docker не запущен!"
    exit 1
fi

# Остановка
echo "⏹️  Остановка контейнеров..."
docker-compose stop

# Запуск
echo "▶️  Запуск контейнеров..."
docker-compose up -d

# Проверка
sleep 3
echo ""
if docker-compose ps | grep -q "Up"; then
    echo "✅ Проект перезапущен!"
    echo ""
    echo "📊 Статус:"
    docker-compose ps
    echo ""
    echo "📝 Логи:"
    echo "   docker-compose logs -f app"
else
    echo "❌ Ошибка перезапуска!"
    echo "Проверьте логи: docker-compose logs app"
    exit 1
fi
