#!/bin/bash

echo "⏹️  Остановка проекта Parser Avito & Kufar"
echo ""

docker-compose stop

echo "✅ Проект остановлен"
echo ""
echo "Для полного удаления контейнеров:"
echo "   docker-compose down"
echo ""
echo "Для удаления с данными:"
echo "   docker-compose down -v"
