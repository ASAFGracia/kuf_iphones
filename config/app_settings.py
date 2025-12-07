"""
Основные настройки приложения
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Интервал парсинга (минуты)
PARSING_INTERVAL_MINUTES = int(os.getenv('PARSING_INTERVAL_MINUTES', 3))  # Изменено на 3 минуты

# Интервал пересчета медианных цен (часы)
MEDIAN_RECALCULATION_INTERVAL_HOURS = int(os.getenv('MEDIAN_RECALCULATION_INTERVAL_HOURS', 10))

# Admin Settings
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 8507895419))

