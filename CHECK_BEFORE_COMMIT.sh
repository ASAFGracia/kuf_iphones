#!/bin/bash
echo "🔍 Проверка перед коммитом..."
echo ""

# Проверка .env
if git status --porcelain 2>/dev/null | grep -q "\.env"; then
    echo "❌ ОШИБКА: .env попадет в коммит!"
    echo "   Убедитесь что .env в .gitignore"
    exit 1
else
    echo "✅ .env не попадет в коммит"
fi

# Проверка токенов
TOKENS=$(grep -r "8499560253\|8327994324" . --exclude-dir=.git --exclude-dir=logs --exclude-dir=kuf_iphones --exclude=".env" --exclude=".env.example" --exclude="GIT_SETUP.md" --exclude="PRE_COMMIT_CHECK.md" --exclude="GITHUB_READY.md" --exclude="CHECK_BEFORE_COMMIT.sh" 2>/dev/null | wc -l | tr -d ' ')
if [ "$TOKENS" -gt 0 ]; then
    echo "❌ ОШИБКА: Найдены реальные токены в коде!"
    echo "   Найдено совпадений: $TOKENS"
    exit 1
else
    echo "✅ Реальных токенов в коде нет"
fi

# Проверка паролей
PASSWORDS=$(grep -r "parser_password_2024" . --exclude-dir=.git --exclude-dir=logs --exclude-dir=kuf_iphones --exclude=".env" --exclude=".env.example" --exclude="GIT_SETUP.md" --exclude="PRE_COMMIT_CHECK.md" --exclude="GITHUB_READY.md" --exclude="CHECK_BEFORE_COMMIT.sh" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PASSWORDS" -gt 0 ]; then
    echo "❌ ОШИБКА: Найден реальный пароль в коде!"
    echo "   Найдено совпадений: $PASSWORDS"
    exit 1
else
    echo "✅ Реальных паролей в коде нет"
fi

echo ""
echo "✅ Все проверки пройдены! Можно коммитить."
