"""
Настройки парсеров
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Количество страниц для парсинга
PARSING_PAGES_COUNT = int(os.getenv('PARSING_PAGES_COUNT', 20))  # Увеличено до 20 страниц

# Задержка между запросами (секунды)
REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', 1.5))

# Таймаут запроса (секунды)
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 15))

# Количество повторных попыток при ошибке
REQUEST_RETRIES = int(os.getenv('REQUEST_RETRIES', 3))

