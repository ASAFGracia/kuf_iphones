"""
Основная конфигурация (для обратной совместимости)
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bots
TELEGRAM_AVITO_BOT_TOKEN = os.getenv('TELEGRAM_AVITO_BOT_TOKEN')
TELEGRAM_KUFAR_BOT_TOKEN = os.getenv('TELEGRAM_KUFAR_BOT_TOKEN')

# PostgreSQL Database
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'parser_db'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Avito Settings
AVITO_BASE_URL = 'https://www.avito.ru'
AVITO_SEARCH_URL = 'https://www.avito.ru/web/1/main/items'

# Kufar Settings
KUFAR_BASE_URL = 'https://www.kufar.by'

# Импорты из новых модулей
from config.app_settings import PARSING_INTERVAL_MINUTES, MEDIAN_RECALCULATION_INTERVAL_HOURS, ADMIN_USER_ID
from config.parsers.settings import PARSING_PAGES_COUNT
from config.cities import AVITO_CITIES, KUFAR_CITIES
from config.models import IPHONE_MODELS

# Для обратной совместимости
CITIES = AVITO_CITIES

