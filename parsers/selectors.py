"""
Конфигурация селекторов для парсинга Avito и Kufar
Здесь можно настроить селекторы элементов, если структура сайтов изменится

ВАЖНО: Если парсер не находит объявления, проверьте и обновите селекторы здесь!
"""
import re

# ==================== AVITO SELECTORS ====================

AVITO_SELECTORS = {
    # Селекторы для поиска объявлений (порядок важен - пробуем по очереди)
    'item_container': [
        {'tag': 'div', 'class': re.compile(r'iva-item-root|items-item|js-catalog-item')},  # Новый селектор
        {'tag': 'div', 'attrs': {'data-marker': 'item'}},  # Основной селектор Avito
        {'tag': 'div', 'attrs': {'data-marker': re.compile(r'item')}},
        {'tag': 'div', 'class': re.compile(r'iva-item|item-')},
        {'tag': 'article', 'attrs': {'data-marker': 'item'}},
    ],
    
    # Селекторы для ID объявления
    'item_id': [
        {'attr': 'data-item-id'},  # Атрибут data-item-id
        {'from_url': True},  # Извлечь из URL
    ],
    
    # Селекторы для ссылки на объявление
    'item_link': [
        {'tag': 'a', 'attrs': {'data-marker': 'item-title'}},
        {'tag': 'a', 'href': re.compile(r'/.*/\d+$')},
        {'tag': 'a', 'href': re.compile(r'/\d+$')},
        {'tag': 'a', 'href': True},
    ],
    
    # Селекторы для заголовка
    'item_title': [
        {'tag': 'div', 'class': re.compile(r'iva-item-titleWrapper|iva-item-title')},  # Новые селекторы
        {'tag': 'h3', 'attrs': {'data-marker': 'item-title'}},
        {'tag': 'a', 'attrs': {'data-marker': 'item-title'}},
        {'tag': 'h3', 'class': re.compile(r'title|item-title|iva-item-title')},
        {'tag': 'a', 'class': re.compile(r'title|item-title')},
    ],
    
    # Селекторы для цены
    'item_price': [
        {'tag': 'span', 'class': re.compile(r'styles-module-size_l|price-text')},  # Новый селектор
        {'tag': 'span', 'attrs': {'data-marker': 'item-price'}},
        {'tag': 'meta', 'attrs': {'itemprop': 'price'}},
        {'tag': 'span', 'class': re.compile(r'price|iva-item-price')},
        {'tag': 'div', 'class': re.compile(r'price|iva-item-price')},
        {'tag': 'p', 'class': re.compile(r'price')},
        {'tag': 'span', 'attrs': {'itemprop': 'price'}},
    ],
    
    # Селекторы для пагинации (для определения следующей страницы)
    'pagination': [
        {'tag': 'a', 'class': re.compile(r'styles_link__8m3I9.*styles_arrow__LNoLG')},  # Kufar пагинация
        {'tag': 'a', 'class': re.compile(r'styles-module-item.*styles-module-item_arrow')},  # Avito пагинация
        {'tag': 'a', 'class': re.compile(r'styles-module-listItem.*styles-module-listItem_arrow')},
    ],
    
    # Селекторы для описания
    'item_description': [
        {'tag': 'div', 'attrs': {'data-marker': 'item-description'}},
        {'tag': 'div', 'class': re.compile(r'description|item-text')},
    ],
}

# ==================== KUFAR SELECTORS ====================

KUFAR_SELECTORS = {
    # Селекторы для поиска объявлений (порядок важен)
    'item_container': [
        {'tag': 'section'},  # Основной селектор - section элементы
        {'tag': 'article'},
        {'tag': 'div', 'class': re.compile(r'item|ad|listing')},
    ],
    
    # Селекторы для ID объявления
    'item_id': [
        {'from_url': True},  # Извлечь из URL (формат: /item/123456 или /123456)
    ],
    
    # Селекторы для ссылки на объявление
    'item_link': [
        {'tag': 'a', 'class': 'styles_wrapper__5FoK7'},  # Конкретный класс из старого парсера
        {'tag': 'a', 'class': re.compile(r'styles_wrapper__')},  # Общий паттерн
        {'tag': 'a', 'href': re.compile(r'/item/\d+')},
        {'tag': 'a', 'href': re.compile(r'/\d+$')},
        {'tag': 'a', 'href': True},
    ],
    
    # Селекторы для заголовка
    'item_title': [
        {'tag': 'h3'},  # Основной селектор - h3 внутри section
        {'tag': 'a', 'find_inside': 'h3'},  # Найти h3 внутри ссылки
        {'tag': 'h2'},
        {'tag': 'div', 'class': re.compile(r'title|name')},
    ],
    
    # Селекторы для цены
    'item_price': [
        {'tag': 'p', 'class': 'styles_price__aVxZc'},  # Конкретный класс из старого парсера
        {'tag': 'p', 'class': re.compile(r'styles_price__')},  # Общий паттерн
        {'tag': 'span', 'class': re.compile(r'price|cost')},
        {'tag': 'div', 'class': re.compile(r'price|cost')},
        {'tag': 'p', 'class': re.compile(r'price')},
    ],
    
    # Селекторы для региона/города
    'item_region': [
        {'tag': 'p', 'class': 'styles_region__qCRbf'},  # Конкретный класс
        {'tag': 'p', 'class': re.compile(r'styles_region__')},  # Общий паттерн
        {'tag': 'span', 'class': re.compile(r'region|location|city')},
    ],
}

# ==================== URL PATTERNS ====================

AVITO_URL_PATTERNS = {
    'base': 'https://www.avito.ru',
    'search': '/{city}/telefony/mobilnye_telefony/apple-ASgBAgICAkS0wA3OqzmwwQ2I_Dc',
    'params': {
        's': '104',  # Сортировка по дате
    }
}

KUFAR_URL_PATTERNS = {
    'base': 'https://www.kufar.by',
    'search': '/l/r~{city}/mobilnye-telefony/mt~apple',
    'params': {
        'sort': 'lst.d',  # Сортировка по дате
    }
}

