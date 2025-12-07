"""
Конфигурация проекта
Импорты из отдельных модулей для обратной совместимости
"""
from config.app_settings import PARSING_INTERVAL_MINUTES, MEDIAN_RECALCULATION_INTERVAL_HOURS, ADMIN_USER_ID
from config.parsers.settings import PARSING_PAGES_COUNT, REQUEST_DELAY, REQUEST_TIMEOUT, REQUEST_RETRIES
from config.cities import AVITO_CITIES, KUFAR_CITIES
from config.models import IPHONE_MODELS

# Для обратной совместимости
CITIES = AVITO_CITIES

