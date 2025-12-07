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
        {'tag': 'div', 'class': re.compile(r'iva-item-root.*js-catalog-item')},  # Новый селектор
        {'tag': 'div', 'class': re.compile(r'iva-item-root|items-item|js-catalog-item')},
        {'tag': 'div', 'attrs': {'data-marker': 'item'}},
        {'tag': 'div', 'attrs': {'data-marker': re.compile(r'item')}},
        {'tag': 'div', 'class': re.compile(r'iva-item|item-')},
        {'tag': 'article', 'attrs': {'data-marker': 'item'}},
    ],
    
    # Селекторы для ID объявления
    'item_id': [
        {'attr': 'data-item-id'},
        {'from_url': True},
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
        {'tag': 'div', 'class': re.compile(r'iva-item-titleWrapper|iva-item-title')},
        {'tag': 'h3', 'attrs': {'data-marker': 'item-title'}},
        {'tag': 'a', 'attrs': {'data-marker': 'item-title'}},
        {'tag': 'h3', 'class': re.compile(r'title|item-title|iva-item-title')},
        {'tag': 'a', 'class': re.compile(r'title|item-title')},
    ],
    
    # Селекторы для цены
    'item_price': [
        {'tag': 'span', 'class': re.compile(r'styles-module-size_l.*styles-module-size_l_dense')},
        {'tag': 'span', 'class': re.compile(r'styles-module-size_l|price-text')},
        {'tag': 'span', 'attrs': {'data-marker': 'item-price'}},
        {'tag': 'meta', 'attrs': {'itemprop': 'price'}},
        {'tag': 'span', 'class': re.compile(r'price|iva-item-price')},
        {'tag': 'div', 'class': re.compile(r'price|iva-item-price')},
        {'tag': 'p', 'class': re.compile(r'price')},
        {'tag': 'span', 'attrs': {'itemprop': 'price'}},
    ],
    
    # Селекторы для пагинации
    'pagination': [
        {'tag': 'a', 'class': re.compile(r'styles-module-item.*styles-module-item_arrow.*styles-module-item_link')},
        {'tag': 'a', 'class': re.compile(r'styles-module-listItem.*styles-module-listItem_arrow_next')},
        {'tag': 'a', 'class': re.compile(r'styles-module-item.*styles-module-item_arrow')},
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
        {'tag': 'section'},
        {'tag': 'article'},
        {'tag': 'div', 'class': re.compile(r'item|ad|listing')},
    ],
    
    # Селекторы для ID объявления
    'item_id': [
        {'from_url': True},
    ],
    
    # Селекторы для ссылки на объявление
    'item_link': [
        {'tag': 'a', 'class': 'styles_wrapper__5FoK7'},
        {'tag': 'a', 'class': re.compile(r'styles_wrapper__')},
        {'tag': 'a', 'href': re.compile(r'/item/\d+')},
        {'tag': 'a', 'href': re.compile(r'/\d+$')},
        {'tag': 'a', 'href': True},
    ],
    
    # Селекторы для заголовка
    'item_title': [
        {'tag': 'h3'},
        {'tag': 'a', 'find_inside': 'h3'},
        {'tag': 'h2'},
        {'tag': 'div', 'class': re.compile(r'title|name')},
    ],
    
    # Селекторы для цены
    'item_price': [
        {'tag': 'p', 'class': 'styles_price__aVxZc'},
        {'tag': 'p', 'class': re.compile(r'styles_price__')},
        {'tag': 'span', 'class': re.compile(r'price|cost')},
        {'tag': 'div', 'class': re.compile(r'price|cost')},
        {'tag': 'p', 'class': re.compile(r'price')},
    ],
    
    # Селекторы для региона/города
    'item_region': [
        {'tag': 'p', 'class': 'styles_region__qCRbf'},
        {'tag': 'p', 'class': re.compile(r'styles_region__')},
        {'tag': 'span', 'class': re.compile(r'region|location|city')},
    ],
    
    # Селекторы для пагинации (кнопка "следующая страница")
    'pagination': [
        {'tag': 'a', 'class': re.compile(r'styles_link__8m3I9.*styles_arrow__LNoLG')},  # Основной селектор
        {'tag': 'a', 'class': re.compile(r'styles_link__8m3I9')},
        {'tag': 'a', 'class': re.compile(r'styles_arrow__LNoLG')},
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

