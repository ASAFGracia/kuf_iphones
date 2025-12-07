# Быстрый старт

## 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

## 2. Настройка PostgreSQL
```sql
CREATE DATABASE avito_parser;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE avito_parser TO your_user;
```

## 3. Создание файла .env
Создайте файл `.env` в корне проекта:
```
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
DB_HOST=localhost
DB_PORT=5432
DB_NAME=avito_parser
DB_USER=your_user
DB_PASSWORD=your_password
PARSING_INTERVAL_MINUTES=3
```

## 4. Получение токена Telegram бота
1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен в файл `.env`

## 5. Запуск
```bash
python main.py
```

## 6. Использование бота
1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Выберите город командой `/city`
4. Выберите модель iPhone командой `/model`
5. Установите максимальную цену командой `/price`
6. Бот начнет автоматически искать выгодные предложения!

## Важно
- Бот отправляет только объявления, цена которых ниже медианной более чем на 15%
- При первом запуске медианная цена может быть неточной (нужно накопить данные)
- Парсинг происходит каждые 3 минуты (настраивается в .env)


