"""
Парсер объявлений с Kufar
Использует настраиваемые селекторы из parsers/selectors.py
"""
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import logging
from typing import List, Dict, Optional
import time
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from config.parsers.selectors import KUFAR_SELECTORS, KUFAR_URL_PATTERNS
from config.parsers.settings import PARSING_PAGES_COUNT, REQUEST_DELAY
from parsers.model_extractor import extract_iphone_model, extract_memory

logger = get_logger('kufar_parser')


class KufarParser:
    """Парсер объявлений с Kufar"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

    def _get_page(self, url: str, retries: int = 3) -> Optional[requests.Response]:
        """Получить страницу с повторными попытками"""
        for attempt in range(retries):
            try:
                self.session.headers['User-Agent'] = self.ua.random
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    logger.debug(f"Успешно получена страница: {url}")
                    return response
                elif response.status_code == 403:
                    logger.warning(f"Доступ запрещен (403), попытка {attempt + 1}/{retries}")
                    time.sleep(2 ** attempt)
                else:
                    logger.warning(f"Статус код {response.status_code}, попытка {attempt + 1}/{retries}")
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Ошибка при запросе: {e}, попытка {attempt + 1}/{retries}")
                time.sleep(2 ** attempt)
        return None

    def _find_element(self, soup, selectors: List[Dict], parent=None):
        """Найти элемент используя список селекторов"""
        search_in = parent if parent else soup
        
        for selector in selectors:
            try:
                tag = selector.get('tag')
                attrs = selector.get('attrs', {})
                class_name = selector.get('class')
                href = selector.get('href')
                find_inside = selector.get('find_inside')
                
                if find_inside and parent:
                    # Найти элемент внутри родителя
                    found = parent.find(tag)
                    if found:
                        inner = found.find(find_inside)
                        if inner:
                            return inner
                
                if tag:
                    if attrs:
                        result = search_in.find(tag, attrs=attrs)
                    elif class_name:
                        if isinstance(class_name, str):
                            result = search_in.find(tag, class_=class_name)
                        else:
                            result = search_in.find(tag, class_=class_name)
                    elif href:
                        result = search_in.find(tag, href=href)
                    else:
                        result = search_in.find(tag)
                    
                    if result:
                        return result
            except Exception as e:
                logger.debug(f"Ошибка при поиске элемента: {e}")
                continue
        
        return None

    def _extract_iphone_model(self, title: str) -> Optional[str]:
        """Извлечь модель iPhone из заголовка"""
        return extract_iphone_model(title)

    def _extract_memory(self, title: str) -> Optional[str]:
        """Извлечь объем памяти из текста"""
        return extract_memory(title)

    def _extract_price(self, text: str) -> Optional[int]:
        """Извлечь цену из текста (в BYN)"""
        if not text:
            return None
        
        # Очищаем текст
        text = text.replace(' ', '').replace('\xa0', '').replace(',', '')
        
        # Ищем цену в формате "50000руб" или "50 000 BYN"
        patterns = [
            r'(\d{3,7})\s*(?:руб|byn|₽|р\.)',
            r'(\d{1,3}(?:\s*\d{3})*)\s*(?:руб|byn|₽|р\.)',
            r'(\d{3,7})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(' ', '')
                try:
                    price = int(price_str)
                    if 100 <= price <= 10000000:  # Разумные пределы для iPhone в BYN
                        return price
                except ValueError:
                    continue
        
        return None

    def parse_kufar(self, city: str, model: str = None, max_price: int = None, pages: int = None) -> List[Dict]:
        """Парсить объявления с Kufar (с пагинацией через кнопку следующей страницы)"""
        if pages is None:
            pages = PARSING_PAGES_COUNT
        
        all_ads = []
        
        try:
            # Формируем URL для поиска
            from config.cities import KUFAR_CITIES
            city_code = KUFAR_CITIES.get(city)
            if not city_code:
                logger.error(f"Город {city} не поддерживается")
                return all_ads
            
            base_url = KUFAR_URL_PATTERNS['base']
            search_path = KUFAR_URL_PATTERNS['search'].format(city=city_code)
            params = KUFAR_URL_PATTERNS['params']
            
            # Начинаем с первой страницы
            current_url = f"{base_url}{search_path}?sort={params['sort']}"
            page_num = 1
            
            # Парсим страницы пока не достигнем лимита или не закончатся страницы
            while page_num <= pages:
                try:
                    logger.info(f"Парсинг Kufar URL (страница {page_num}): {current_url}")
                    
                    response = self._get_page(current_url)
                    if not response:
                        logger.warning(f"Не удалось получить страницу {page_num} Kufar")
                        break
                    
                    page_ads = self._parse_kufar_page(response, base_url, city, model, max_price)
                    if page_ads:
                        all_ads.extend(page_ads)
                        logger.info(f"Найдено {len(page_ads)} объявлений на странице {page_num} (всего: {len(all_ads)})")
                    else:
                        logger.info(f"На странице {page_num} объявлений не найдено")
                    
                    # Ищем кнопку "следующая страница"
                    next_url = self._find_next_page_url(response)
                    if not next_url:
                        logger.info(f"Кнопка следующей страницы не найдена, парсинг завершен")
                        break
                    
                    # Формируем полный URL следующей страницы
                    if not next_url.startswith('http'):
                        next_url = f"{base_url}{next_url}"
                    
                    current_url = next_url
                    page_num += 1
                    
                    # Задержка между запросами
                    time.sleep(REQUEST_DELAY)
                    
                except Exception as e:
                    logger.error(f"Ошибка при парсинге страницы {page_num}: {e}")
                    break
            
            logger.info(f"Всего найдено {len(all_ads)} объявлений на {page_num} страницах Kufar")
            return all_ads
            
        except Exception as e:
            logger.error(f"Ошибка парсинга Kufar: {e}", exc_info=True)
            return all_ads
    
    def _find_next_page_url(self, response) -> Optional[str]:
        """Найти URL следующей страницы через кнопку пагинации"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем кнопку пагинации с классами styles_link__8m3I9 styles_arrow__LNoLG
            pagination_buttons = soup.find_all('a', class_=re.compile(r'styles_link__8m3I9.*styles_arrow__LNoLG'))
            
            if not pagination_buttons:
                # Пробуем найти любую кнопку с этими классами отдельно
                for btn in soup.find_all('a'):
                    classes = btn.get('class', [])
                    if 'styles_link__8m3I9' in classes and 'styles_arrow__LNoLG' in classes:
                        href = btn.get('href')
                        if href:
                            return href
            
            # Если нашли кнопки, берем первую (обычно это "следующая")
            if pagination_buttons:
                href = pagination_buttons[0].get('href')
                if href:
                    return href
            
            return None
        except Exception as e:
            logger.debug(f"Ошибка поиска следующей страницы: {e}")
            return None
    
    def _parse_kufar_page(self, response, base_url: str, city: str, model: str = None, max_price: int = None) -> List[Dict]:
        """Парсить одну страницу Kufar"""
        ads = []
        
        try:
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Сохраняем HTML для отладки
            logger.debug(f"Размер HTML: {len(response.text)} символов")
            
            # Ищем объявления используя селекторы
            items = []
            for selector in KUFAR_SELECTORS['item_container']:
                try:
                    tag = selector.get('tag')
                    attrs = selector.get('attrs', {})
                    class_name = selector.get('class')
                    
                    if attrs:
                        found = soup.find_all(tag, attrs=attrs)
                    elif class_name:
                        if isinstance(class_name, str):
                            found = soup.find_all(tag, class_=class_name)
                        else:
                            found = soup.find_all(tag, class_=class_name)
                    else:
                        found = soup.find_all(tag)
                    
                    if found:
                        items = found
                        logger.info(f"Найдено {len(items)} объявлений используя селектор: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Ошибка при поиске контейнеров: {e}")
                    continue
            
            if not items:
                logger.warning("Не найдено объявлений на странице Kufar. Возможно, изменилась структура сайта.")
                logger.warning("Проверьте селекторы в parsers/selectors.py")
                # Сохраняем часть HTML для анализа
                logger.debug(f"Первые 2000 символов HTML:\n{response.text[:2000]}")
                return ads
            
            logger.info(f"Найдено {len(items)} объявлений на странице Kufar")
            
            for section in items:
                try:
                    # Ищем ссылку на объявление
                    a_tag = self._find_element(soup, KUFAR_SELECTORS['item_link'], parent=section)
                    if not a_tag:
                        logger.debug("Не найдена ссылка на объявление Kufar")
                        continue
                    
                    href = a_tag.get('href', '')
                    if not href.startswith('http'):
                        href = f"{base_url}{href}"
                    
                    # Извлекаем ID из URL
                    match = re.search(r'/(\d+)$', href) or re.search(r'/item/(\d+)', href)
                    if not match:
                        logger.debug(f"Не удалось извлечь ID из URL: {href}")
                        continue
                    item_id = match.group(1)
                    
                    # Извлекаем заголовок
                    title_tag = self._find_element(soup, KUFAR_SELECTORS['item_title'], parent=section)
                    if not title_tag and a_tag:
                        # Пробуем найти h3 внутри ссылки
                        title_tag = a_tag.find('h3')
                    if not title_tag:
                        title_tag = a_tag
                    
                    title = title_tag.get_text(strip=True) if title_tag else ""
                    if not title:
                        logger.debug("Не найден заголовок объявления Kufar")
                        continue
                    
                    # Очищаем заголовок от лишних символов
                    title = re.sub(r'\s*(Обмен|Продажа|Торг|€|\$|₽|,|\.)\b', '', title).strip()
                    
                    # Извлекаем цену
                    price_tag = self._find_element(soup, KUFAR_SELECTORS['item_price'], parent=section)
                    price_text = ""
                    if price_tag:
                        # Пробуем найти span внутри price_tag (как в старом парсере)
                        price_span = price_tag.find('span')
                        if price_span:
                            price_text = price_span.get_text(strip=True)
                        else:
                            price_text = price_tag.get_text(strip=True)
                    else:
                        price_text = section.get_text()
                    
                    price = self._extract_price(price_text)
                    if not price:
                        logger.debug(f"Не удалось извлечь цену из: {price_text[:50]}")
                        continue
                    
                    # Фильтруем по максимальной цене
                    if max_price and price > max_price:
                        logger.debug(f"Цена {price} превышает максимум {max_price}")
                        continue
                    
                    # Определяем модель
                    detected_model = self._extract_iphone_model(title)
                    if not detected_model:
                        logger.debug(f"Не удалось определить модель из: {title[:50]}")
                        continue
                    
                    # Фильтруем по модели если указана (гибкое сравнение)
                    if model:
                        # Нормализуем названия для сравнения
                        detected_normalized = detected_model.lower().replace(' ', '').replace('-', '')
                        model_normalized = model.lower().replace(' ', '').replace('-', '')
                        
                        # Проверяем точное совпадение или частичное (например, "iPhone SE" и "iPhone SE (2-го поколения)")
                        if detected_normalized != model_normalized and not detected_normalized.startswith(model_normalized) and not model_normalized.startswith(detected_normalized):
                            logger.debug(f"Модель {detected_model} не соответствует фильтру {model}")
                            continue
                    
                    # Извлекаем память
                    memory = self._extract_memory(title)
                    
                    # Извлекаем город из региона
                    region_tag = self._find_element(soup, KUFAR_SELECTORS['item_region'], parent=section)
                    detected_city = city
                    if region_tag:
                        region_text = region_tag.get_text(strip=True)
                        if region_text:
                            detected_city = region_text.split(',')[0].strip()
                    
                    ad = {
                        'kufar_id': str(item_id),
                        'title': title,
                        'price': price,
                        'model': detected_model,
                        'memory': memory,
                        'url': href,
                        'city': detected_city,
                        'source': 'kufar'
                    }
                    
                    ads.append(ad)
                    logger.info(f"✓ Найдено объявление Kufar: {detected_model} за {price} BYN - {title[:50]}")
                    
                except Exception as e:
                    logger.error(f"Ошибка при парсинге объявления Kufar: {e}", exc_info=True)
                    continue
            
            logger.info(f"Всего найдено {len(ads)} подходящих объявлений Kufar")
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге Kufar: {e}", exc_info=True)
        
        return ads

