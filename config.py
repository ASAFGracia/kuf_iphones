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

# Parser Settings
PARSING_INTERVAL_MINUTES = int(os.getenv('PARSING_INTERVAL_MINUTES', 2))  # Парсинг каждые 2 минуты
PARSING_PAGES_COUNT = int(os.getenv('PARSING_PAGES_COUNT', 10))  # Количество страниц для парсинга

# Admin Settings
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 8507895419))  # ID администратора

# Avito Settings
AVITO_BASE_URL = 'https://www.avito.ru'
AVITO_SEARCH_URL = 'https://www.avito.ru/web/1/main/items'

# iPhone Models (начиная с X и новее)
IPHONE_MODELS = [
    # iPhone 17 серия
    'iPhone 17 Pro Max',
    'iPhone 17 Pro',
    'iPhone 17',
    'iPhone Air',
    # iPhone 16 серия
    'iPhone 16 Pro Max',
    'iPhone 16 Pro',
    'iPhone 16 Plus',
    'iPhone 16',
    'iPhone 16e',
    # iPhone 15 серия
    'iPhone 15 Pro Max',
    'iPhone 15 Pro',
    'iPhone 15 Plus',
    'iPhone 15',
    # iPhone 14 серия
    'iPhone 14 Pro Max',
    'iPhone 14 Pro',
    'iPhone 14 Plus',
    'iPhone 14',
    # iPhone 13 серия
    'iPhone 13 Pro Max',
    'iPhone 13 Pro',
    'iPhone 13 mini',
    'iPhone 13',
    # iPhone 12 серия
    'iPhone 12 Pro Max',
    'iPhone 12 Pro',
    'iPhone 12 mini',
    'iPhone 12',
    # iPhone 11 серия
    'iPhone 11 Pro Max',
    'iPhone 11 Pro',
    'iPhone 11',
    # iPhone SE
    'iPhone SE (2-го поколения)',
    'iPhone SE',
    # iPhone SE 3 (то же что и SE 2-го поколения, но для удобства)
    'iPhone SE 3',
    # iPhone X серия
    'iPhone XS Max',
    'iPhone XS',
    'iPhone XR',
    'iPhone X',
]

# Popular cities in Russia
CITIES = {
    'Москва': 'moskva',
    'Санкт-Петербург': 'sankt-peterburg',
    'Новосибирск': 'novosibirsk',
    'Екатеринбург': 'ekaterinburg',
    'Казань': 'kazan',
    'Нижний Новгород': 'nizhniy_novgorod',
    'Челябинск': 'chelyabinsk',
    'Самара': 'samara',
    'Омск': 'omsk',
    'Ростов-на-Дону': 'rostov-na-donu',
    'Уфа': 'ufa',
    'Красноярск': 'krasnoyarsk',
    'Воронеж': 'voronezh',
    'Пермь': 'perm',
    'Волгоград': 'volgograd'
}

# Cities in Belarus (Kufar)
KUFAR_CITIES = {
    'Минск': 'minsk',
    'Витебск': 'vitebsk'
}

# Kufar Settings
KUFAR_BASE_URL = 'https://www.kufar.by'


