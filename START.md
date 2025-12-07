# Инструкция по запуску проекта

## Вариант 1: Запуск через Docker (рекомендуется)

### Требования:
- Docker Desktop установлен и запущен
- Docker Compose установлен

### Шаги:

1. **Убедитесь, что Docker запущен:**
   - На Mac: откройте Docker Desktop
   - Проверьте: `docker ps`

2. **Запустите проект:**
   ```bash
   docker-compose up -d
   ```

3. **Проверьте логи:**
   ```bash
   docker-compose logs -f app
   ```

4. **Остановка:**
   ```bash
   docker-compose down
   ```

## Вариант 2: Локальный запуск (без Docker)

### Требования:
- Python 3.11+
- PostgreSQL установлен и запущен

### Шаги:

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Создайте базу данных:**
   ```sql
   CREATE DATABASE parser_db;
   CREATE USER parser_user WITH PASSWORD 'your_secure_password_here';
   GRANT ALL PRIVILEGES ON DATABASE parser_db TO parser_user;
   ```

3. **Обновите .env для локального запуска:**
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=parser_db
   DB_USER=parser_user
   DB_PASSWORD=your_secure_password_here
   ```

4. **Запустите проект:**
   ```bash
   python main.py
   ```

## Данные для подключения к базе данных

**При использовании Docker:**
- Хост: `localhost` (извне) или `postgres` (изнутри контейнера)
- Порт: `5432`
- База данных: `parser_db`
- Пользователь: `parser_user`
- **Пароль: `your_secure_password_here`**

**При локальном запуске:**
- Хост: `localhost`
- Порт: `5432`
- База данных: `parser_db`
- Пользователь: `parser_user`
- **Пароль: `your_secure_password_here`**

## Боты

- **Avito бот:** @iphones_avito_bot
- **Kufar бот:** @iphones_kufar_bot

## Проверка работы

1. Найдите ботов в Telegram
2. Отправьте `/start` любому боту
3. Выберите город командой `/city`
4. Выберите модель командой `/model`
5. Установите максимальную цену командой `/price`
6. Бот начнет автоматически искать выгодные предложения!

## Логи

Логи сохраняются в:
- Docker: `docker-compose logs -f app`
- Локально: файл `logs/parser.log`

## Устранение проблем

### Docker не запускается:
- Убедитесь, что Docker Desktop запущен
- Проверьте: `docker ps`

### Ошибки подключения к БД:
- Проверьте, что PostgreSQL запущен
- Проверьте настройки в `.env`
- Для Docker: убедитесь, что контейнер `postgres` запущен

### Боты не отвечают:
- Проверьте токены в `.env`
- Проверьте логи: `docker-compose logs -f app`

