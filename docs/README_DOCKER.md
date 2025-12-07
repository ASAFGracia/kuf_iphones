# Запуск проекта через Docker

## Быстрый старт

1. **Создайте файл `.env`** (уже создан с вашими токенами):
```env
TELEGRAM_AVITO_BOT_TOKEN=your_avito_bot_token_here
TELEGRAM_KUFAR_BOT_TOKEN=your_kufar_bot_token_here
DB_HOST=postgres
DB_PORT=5432
DB_NAME=parser_db
DB_USER=parser_user
DB_PASSWORD=your_secure_password_here
PARSING_INTERVAL_MINUTES=3
```

2. **Запустите проект через Docker Compose:**
```bash
docker-compose up -d
```

3. **Проверьте логи:**
```bash
docker-compose logs -f app
```

## Данные для подключения к базе данных

**Хост:** localhost (извне контейнера) или `postgres` (изнутри контейнера)
**Порт:** 5432
**База данных:** parser_db
**Пользователь:** parser_user
**Пароль:** your_secure_password_here

## Остановка проекта

```bash
docker-compose down
```

## Остановка с удалением данных

```bash
docker-compose down -v
```

## Полезные команды

- Просмотр логов: `docker-compose logs -f app`
- Перезапуск: `docker-compose restart app`
- Подключение к базе данных:
  ```bash
  docker exec -it avito_kufar_postgres psql -U parser_user -d parser_db
  ```

## Структура проекта

- **Avito бот:** @iphones_avito_bot
- **Kufar бот:** @iphones_kufar_bot

Оба бота работают параллельно и парсят объявления каждые 3 минуты.

