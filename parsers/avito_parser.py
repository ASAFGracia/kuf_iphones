"""
Парсер объявлений с Avito
Использует настраиваемые селекторы из parsers/selectors.py
"""
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import logging
from typing import List, Dict, Optional
from urllib.parse import urlencode
import time
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from parsers.selectors import AVITO_SELECTORS, AVITO_URL_PATTERNS
from parsers.model_extractor import extract_iphone_model, extract_memory

logger = get_logger('avito_parser')


class AvitoParser:
    """Парсер объявлений с Avito"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
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

    def _extract_iphone_model(self, title: str, description: str = "") -> Optional[str]:
        """Извлечь модель iPhone из заголовка и описания"""
        text = f"{title} {description}".strip()
        return extract_iphone_model(text)

    def _extract_memory(self, title: str, description: str = "") -> Optional[str]:
        """Извлечь объем памяти из текста"""
        text = f"{title} {description}".strip()
        return extract_memory(text)

    def _extract_price(self, text: str) -> Optional[int]:
        """Извлечь цену из текста"""
        if not text:
            return None
        
        text = text.replace(' ', '').replace('\xa0', '').replace(',', '')
        
        patterns = [
            r'(\d{4,7})\s*[руб₽]',
            r'(\d{1,3}(?:\s*\d{3})*)\s*[руб₽]',
            r'(\d{4,7})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(' ', '')
                try:
                    price = int(price_str)
                    if 1000 <= price <= 10000000:  # Разумные пределы для iPhone
                        return price
                except ValueError:
                    continue
        
        return None

    def parse_avito(self, city: str, model: str = None, max_price: int = None, pages: int = 10) -> List[Dict]:
        """Парсить объявления с Avito (с пагинацией)"""
        ads = []
        all_ads = []
        
        try:
            # Формируем базовый URL для поиска
            base_url = AVITO_URL_PATTERNS['base']
            search_path = AVITO_URL_PATTERNS['search'].format(city=city)
            
            # Парсим несколько последних страниц
            for page in range(1, pages + 1):
                try:
                    params = {
                        's': AVITO_URL_PATTERNS['params']['s'],
                        'p': page,  # Номер страницы
                    }
                    
                    url = f"{base_url}{search_path}?{urlencode(params)}"
                    logger.info(f"Парсинг Avito URL (страница {page}): {url}")
                    
                    response = self._get_page(url)
                    if not response:
                        logger.warning(f"Не удалось получить страницу {page} Avito")
                        continue
                    
                    page_ads = self._parse_avito_page(response, base_url, model, max_price)
                    if page_ads:
                        all_ads.extend(page_ads)
                        logger.info(f"Найдено {len(page_ads)} объявлений на странице {page}")
                    else:
                        logger.info(f"На странице {page} объявлений не найдено, прекращаем парсинг")
                        break  # Если на странице нет объявлений, прекращаем
                    
                    # Небольшая задержка между запросами
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Ошибка при парсинге страницы {page}: {e}")
                    continue
            
            logger.info(f"Всего найдено {len(all_ads)} объявлений на {pages} страницах Avito")
            return all_ads
            
        except Exception as e:
            logger.error(f"Ошибка парсинга Avito: {e}", exc_info=True)
            return all_ads
    
    def _parse_avito_page(self, response, base_url: str, model: str = None, max_price: int = None) -> List[Dict]:
        """Парсить одну страницу Avito"""
        ads = []
        
        try:
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Сохраняем HTML для отладки (первые 5000 символов)
            logger.debug(f"Размер HTML: {len(response.text)} символов")
            
            # Ищем объявления используя селекторы
            items = []
            for selector in AVITO_SELECTORS['item_container']:
                try:
                    tag = selector.get('tag')
                    attrs = selector.get('attrs', {})
                    class_name = selector.get('class')
                    
                    if attrs:
                        # Обрабатываем регулярные выражения в attrs
                        processed_attrs = {}
                        for key, value in attrs.items():
                            if hasattr(value, 'pattern'):  # Это регулярное выражение
                                # Используем find_all с функцией фильтрации
                                found = soup.find_all(tag, attrs={key: value})
                            else:
                                processed_attrs[key] = value
                                found = soup.find_all(tag, attrs=processed_attrs) if processed_attrs else soup.find_all(tag)
                    elif class_name:
                        if hasattr(class_name, 'pattern'):  # Регулярное выражение
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
            
            # Дополнительная попытка: ищем через data-marker напрямую
            if not items:
                items = soup.find_all(attrs={'data-marker': re.compile(r'item')})
                if items:
                    logger.info(f"Найдено {len(items)} объявлений через data-marker")
            
            # Еще одна попытка: ищем по новым классам Avito
            if not items:
                items = soup.find_all('div', class_=re.compile(r'iva-item-root|items-item|js-catalog-item'))
                if items:
                    logger.info(f"Найдено {len(items)} элементов по новым классам Avito")
            
            # Еще одна попытка: ищем все элементы с классом содержащим "item"
            if not items:
                items = soup.find_all(class_=re.compile(r'item', re.I))
                if items:
                    logger.info(f"Найдено {len(items)} элементов с классом 'item'")
            
            if not items:
                logger.debug("Не найдено объявлений на странице")
                return ads
            
            for item in items:
                try:
                    # Извлекаем ID объявления
                    item_id = None
                    if 'data-item-id' in item.attrs:
                        item_id = item.get('data-item-id')
                    
                    # Извлекаем ссылку
                    link_elem = self._find_element(soup, AVITO_SELECTORS['item_link'], parent=item)
                    if not link_elem:
                        logger.debug("Не найдена ссылка на объявление")
                        continue
                    
                    href = link_elem.get('href', '')
                    if not href.startswith('http'):
                        href = f"{base_url}{href}"
                    
                    # Извлекаем ID из URL если не нашли
                    if not item_id:
                        match = re.search(r'/(\d+)$', href)
                        if match:
                            item_id = match.group(1)
                    
                    if not item_id:
                        logger.debug("Не удалось извлечь ID объявления")
                        continue
                    
                    # Извлекаем заголовок (пробуем новые селекторы)
                    title_elem = None
                    # Сначала пробуем найти div с классом iva-item-titleWrapper или iva-item-title
                    title_wrapper = item.find('div', class_=re.compile(r'iva-item-titleWrapper|iva-item-title'))
                    if title_wrapper:
                        # Ищем внутри h3 или a
                        title_elem = title_wrapper.find('h3') or title_wrapper.find('a') or title_wrapper
                    else:
                        title_elem = self._find_element(soup, AVITO_SELECTORS['item_title'], parent=item)
                    
                    if not title_elem:
                        title_elem = link_elem
                    
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    if not title:
                        logger.debug("Не найден заголовок объявления")
                        continue
                    
                    # Извлекаем описание
                    desc_elem = self._find_element(soup, AVITO_SELECTORS['item_description'], parent=item)
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    # Извлекаем цену (пробуем новые селекторы)
                    price_elem = None
                    # Сначала пробуем найти span с классом styles-module-size_l
                    price_span = item.find('span', class_=re.compile(r'styles-module-size_l|price-text'))
                    if price_span:
                        price_elem = price_span
                    else:
                        price_elem = self._find_element(soup, AVITO_SELECTORS['item_price'], parent=item)
                    
                    price_text = ""
                    if price_elem:
                        price_text = price_elem.get('content', '') or price_elem.get_text(strip=True)
                    else:
                        # Пробуем найти цену в тексте элемента
                        price_text = item.get_text()
                    
                    price = self._extract_price(price_text)
                    if not price:
                        logger.debug(f"Не удалось извлечь цену из: {price_text[:50]}")
                        continue
                    
                    # Фильтруем по максимальной цене
                    if max_price and price > max_price:
                        logger.debug(f"Цена {price} превышает максимум {max_price}")
                        continue
                    
                    # Определяем модель
                    detected_model = self._extract_iphone_model(title, description)
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
                    memory = self._extract_memory(title, description)
                    
                    ad = {
                        'avito_id': str(item_id),
                        'title': title,
                        'price': price,
                        'model': detected_model,
                        'memory': memory,
                        'url': href,
                        'source': 'avito'
                    }
                    
                    ads.append(ad)
                    logger.info(f"✓ Найдено объявление Avito: {detected_model} за {price} руб. - {title[:50]}")
                    
                except Exception as e:
                    logger.error(f"Ошибка при парсинге объявления Avito: {e}", exc_info=True)
                    continue
            
            logger.info(f"Всего найдено {len(ads)} подходящих объявлений Avito")
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге Avito: {e}", exc_info=True)
        
        return ads

