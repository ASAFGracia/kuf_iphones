#!/bin/bash
set -e

echo "🚀 Подготовка к push в GitHub..."
echo ""

# Проверка что мы в правильной директории
if [ ! -f "main.py" ]; then
    echo "❌ Ошибка: Не найдено main.py. Убедитесь что вы в корне проекта."
    exit 1
fi

# Проверка безопасности
echo "🔒 Проверка безопасности..."
./CHECK_BEFORE_COMMIT.sh || exit 1

echo ""
echo "📦 Инициализация Git (если нужно)..."

# Инициализация Git если нужно
if [ ! -d .git ]; then
    git init
    echo "✅ Git инициализирован"
fi

# Добавление remote репозитория
echo ""
echo "🔗 Настройка remote репозитория..."
if git remote get-url origin >/dev/null 2>&1; then
    echo "⚠️  Remote 'origin' уже настроен:"
    git remote get-url origin
    read -p "Перезаписать? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote set-url origin https://github.com/ASAFGracia/kuf_iphones.git
        echo "✅ Remote обновлен"
    fi
else
    git remote add origin https://github.com/ASAFGracia/kuf_iphones.git
    echo "✅ Remote добавлен"
fi

# Проверка что .env не попадет в коммит
echo ""
echo "🔍 Проверка файлов..."
if git status --porcelain 2>/dev/null | grep -q "\.env$"; then
    echo "❌ ОШИБКА: .env попадет в коммит!"
    echo "   Убедитесь что .env в .gitignore"
    exit 1
fi

# Добавление всех файлов
echo ""
echo "📝 Добавление файлов..."
git add .

# Показываем что будет закоммичено
echo ""
echo "📋 Файлы для коммита:"
git status --short | head -20

# Создание коммита
echo ""
read -p "Создать коммит? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "Initial commit: Parser for Avito and Kufar with Telegram bots
    
- Парсеры для Avito (Россия) и Kufar (Беларусь)
- Telegram боты для уведомлений
- PostgreSQL база данных
- Docker поддержка
- Аналитика и админ панель"
    echo "✅ Коммит создан"
    
    # Push
    echo ""
    read -p "Отправить в GitHub? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📤 Отправка в GitHub..."
        git push -u origin main 2>&1 || git push -u origin master 2>&1
        echo "✅ Проект успешно отправлен в GitHub!"
    fi
else
    echo "ℹ️  Коммит отменен. Вы можете сделать это вручную:"
    echo "   git commit -m 'Your message'"
    echo "   git push -u origin main"
fi
