"""
Сервис парсинга объявлений
"""
import asyncio
import logging
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from parsers.avito_parser import AvitoParser
from parsers.kufar_parser import KufarParser
from bot_avito import AvitoTelegramBot
from bot_kufar import KufarTelegramBot
from utils.median_calculator import MedianPriceCalculator
from utils.logger import get_logger
from config.app_settings import PARSING_INTERVAL_MINUTES
from config.parsers.settings import PARSING_PAGES_COUNT
from config.cities import AVITO_CITIES, KUFAR_CITIES
import time

logger = get_logger('parser_service')


class ParserService:
    """Сервис для парсинга объявлений с Avito и Kufar"""
    
    def __init__(
        self, 
        db: Database, 
        avito_bot: AvitoTelegramBot, 
        kufar_bot: KufarTelegramBot,
        median_calculator: MedianPriceCalculator
    ):
        self.db = db
        self.avito_bot = avito_bot
        self.kufar_bot = kufar_bot
        self.avito_parser = AvitoParser()
        self.kufar_parser = KufarParser()
        self.median_calculator = median_calculator
        self.running = False

    async def process_advertisement(self, ad: dict, user_settings: dict, source: str):
        """Обработать объявление для пользователя"""
        try:
            city = user_settings.get('city')
            model = ad['model']
            
            # Определяем ID объявления в зависимости от источника
            ad_id = ad.get('avito_id') if source == 'avito' else ad.get('kufar_id')
            if not ad_id:
                logger.warning(f"Не найден ID объявления для источника {source}")
                return False
            
            # Проверяем существует ли объявление и было ли оно уже отправлено
            if self.db.advertisement_exists(ad_id, source):
                # Проверяем, было ли оно уже отправлено
                if self.db.is_advertisement_notified(ad_id, source):
                    logger.debug(f"Объявление уже было отправлено: {ad_id}, {source}")
                    return False
                logger.debug(f"Объявление уже существует, но не было отправлено: {ad_id}, {source}")
                # Продолжаем обработку, чтобы обновить данные и проверить снова
            
            # Сначала добавляем объявление в БД без медианной цены
            # Память может быть None, проверяем и нормализуем
            memory = ad.get('memory')
            if memory and memory.startswith('\\'):  # Исправляем ошибку парсинга "\1 ГБ"
                memory = None
            
            self.db.add_advertisement(
                ad_id=ad_id,
                price=ad['price'],
                model=model,
                city=city,
                memory=memory,
                url=ad['url'],
                source=source
            )
            
            # Рассчитываем медианную цену используя оптимизированный калькулятор
            median_price = self.median_calculator.calculate_median_price(city, model, source)
            
            # Если медианной цены еще нет (первое объявление), используем текущую цену как базовую
            if not median_price:
                median_price = float(ad['price'])
                logger.info(f"Первое объявление для {city}, {model}, {source}. Используем цену как медиану: {median_price}")
            
            # Обновляем медианную цену для всех объявлений этой модели в городе
            self.median_calculator.recalculate_all_medians(source)
            
            # Получаем актуальную медианную цену после пересчета
            median_price = self.median_calculator.calculate_median_price(city, model, source)
            if not median_price:
                median_price = float(ad['price'])
            
            # Рассчитываем разницу (экономия - положительное значение)
            # price_difference = median_price - price (экономия в рублях)
            price_difference = median_price - ad['price']
            
            # Определяем пороги для разных источников
            if source == 'kufar':
                min_discount_rubles = 200  # BYN
            else:  # avito
                min_discount_rubles = 6000  # RUB
            
            # Проверяем условие: цена должна быть ниже медианной на 15% ИЛИ на фиксированную сумму
            discount_percent = (price_difference / median_price * 100) if median_price > 0 else 0
            is_good_deal = price_difference > 0 and (discount_percent >= 15 or price_difference >= min_discount_rubles)
            
            if is_good_deal:
                # Обновляем объявление с медианной ценой
                # Память может быть None, проверяем и нормализуем
                memory = ad.get('memory')
                if memory and memory.startswith('\\'):  # Исправляем ошибку парсинга "\1 ГБ"
                    memory = None
                
                self.db.add_advertisement(
                    ad_id=ad_id,
                    price=ad['price'],
                    model=model,
                    city=city,
                    memory=memory,
                    url=ad['url'],
                    source=source,
                    median_price=median_price,
                    price_difference=price_difference
                )
                
                # Получаем дату создания объявления из БД
                ad_created_at = self.db.get_advertisement_created_at(ad_id, source)
                
                # Отправляем пользователю через соответствующий бот
                ad_data = {
                    'price': ad['price'],
                    'model': model,
                    'city': city,
                    'memory': ad.get('memory'),
                    'url': ad['url'],
                    'median_price': median_price,
                    'price_difference': price_difference,
                    'created_at': ad_created_at  # Дата создания объявления
                }
                
                if source == 'avito':
                    await self.avito_bot.send_advertisement(user_settings['user_id'], ad_data)
                else:
                    await self.kufar_bot.send_advertisement(user_settings['user_id'], ad_data)
                
                # Помечаем объявление как отправленное
                self.db.mark_advertisement_notified(ad_id, source)
                
                logger.info(
                    f"Выгодное предложение отправлено: {model} за {ad['price']} "
                    f"(медиана: {median_price:.2f}, экономия: {price_difference:.2f}, {discount_percent:.1f}%)"
                )
                return True
            else:
                logger.debug(
                    f"Объявление не прошло фильтр: {model}, цена={ad['price']}, "
                    f"медиана={median_price:.2f}, скидка={discount_percent:.1f}%"
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обработки объявления: {e}", exc_info=True)
            return False

    async def parse_for_user_avito(self, user_settings: dict):
        """Парсить объявления Avito для конкретного пользователя"""
        start_time = time.time()
        pages_parsed = 0
        ads_found = 0
        ads_processed = 0
        ads_sent = 0
        errors_count = 0
        status = 'completed'
        error_message = None
        
        try:
            city = user_settings.get('city')
            model = user_settings.get('model')
            max_price = user_settings.get('max_price')
            
            if not city:
                logger.warning(f"Пользователь {user_settings['user_id']} не выбрал город")
                return
            
            city_code = AVITO_CITIES.get(city)
            if not city_code:
                logger.warning(f"Город {city} не найден в списке Avito")
                return
            
            logger.info(f"Парсинг Avito для пользователя {user_settings['user_id']}: {city}, {model or 'все модели'}, max_price={max_price or 'не ограничена'}")
            
            # Парсим объявления
            ads = self.avito_parser.parse_avito(city_code, model, max_price, pages=PARSING_PAGES_COUNT)
            ads_found = len(ads)
            pages_parsed = PARSING_PAGES_COUNT
            
            logger.info(f"Найдено {len(ads)} объявлений Avito для пользователя {user_settings['user_id']}")
            
            # Обрабатываем каждое объявление
            for ad in ads:
                try:
                    if await self.process_advertisement(ad, user_settings, 'avito'):
                        ads_sent += 1
                    ads_processed += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    errors_count += 1
                    logger.error(f"Ошибка обработки объявления: {e}")
            
            logger.info(f"Обработано {ads_processed} объявлений, отправлено {ads_sent} выгодных Avito для пользователя {user_settings['user_id']}")
                
        except Exception as e:
            errors_count += 1
            status = 'error'
            error_message = str(e)
            logger.error(f"Ошибка парсинга Avito для пользователя {user_settings['user_id']}: {e}", exc_info=True)
        finally:
            # Логируем результат парсинга
            duration = time.time() - start_time
            self.db.add_parsing_log(
                source='avito',
                city=user_settings.get('city'),
                model=user_settings.get('model'),
                pages_parsed=pages_parsed,
                ads_found=ads_found,
                ads_processed=ads_processed,
                ads_sent=ads_sent,
                errors_count=errors_count,
                duration_seconds=round(duration, 2),
                status=status,
                error_message=error_message
            )

    async def parse_for_user_kufar(self, user_settings: dict):
        """Парсить объявления Kufar для конкретного пользователя"""
        start_time = time.time()
        pages_parsed = 0
        ads_found = 0
        ads_processed = 0
        ads_sent = 0
        errors_count = 0
        status = 'completed'
        error_message = None
        
        try:
            city = user_settings.get('city')
            model = user_settings.get('model')
            max_price = user_settings.get('max_price')
            
            if not city:
                logger.warning(f"Пользователь {user_settings['user_id']} не выбрал город")
                return
            
            if city not in KUFAR_CITIES:
                logger.warning(f"Город {city} не найден в списке Kufar")
                return
            
            logger.info(f"Парсинг Kufar для пользователя {user_settings['user_id']}: {city}, {model or 'все модели'}")
            
            # Парсим объявления (последние N страниц)
            ads = self.kufar_parser.parse_kufar(city, model, max_price, pages=PARSING_PAGES_COUNT)
            ads_found = len(ads)
            pages_parsed = PARSING_PAGES_COUNT
            
            logger.info(f"Найдено {len(ads)} объявлений Kufar для пользователя {user_settings['user_id']}")
            
            # Обрабатываем каждое объявление
            for ad in ads:
                try:
                    if await self.process_advertisement(ad, user_settings, 'kufar'):
                        ads_sent += 1
                    ads_processed += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    errors_count += 1
                    logger.error(f"Ошибка обработки объявления: {e}")
            
            logger.info(f"Обработано {ads_processed} объявлений, отправлено {ads_sent} выгодных Kufar для пользователя {user_settings['user_id']}")
                
        except Exception as e:
            errors_count += 1
            status = 'error'
            error_message = str(e)
            logger.error(f"Ошибка парсинга Kufar для пользователя {user_settings['user_id']}: {e}", exc_info=True)
        finally:
            # Логируем результат парсинга
            duration = time.time() - start_time
            self.db.add_parsing_log(
                source='kufar',
                city=user_settings.get('city'),
                model=user_settings.get('model'),
                pages_parsed=pages_parsed,
                ads_found=ads_found,
                ads_processed=ads_processed,
                ads_sent=ads_sent,
                errors_count=errors_count,
                duration_seconds=round(duration, 2),
                status=status,
                error_message=error_message
            )

    async def run_parsing_cycle(self):
        """Запустить цикл парсинга"""
        while self.running:
            try:
                # Получаем активных пользователей для каждого источника
                avito_users = self.db.get_active_users('avito')
                kufar_users = self.db.get_active_users('kufar')
                
                total_users = len(avito_users) + len(kufar_users)
                
                if total_users == 0:
                    logger.info("Нет активных пользователей")
                else:
                    logger.info(
                        f"Начало цикла парсинга: {len(avito_users)} пользователей Avito, "
                        f"{len(kufar_users)} пользователей Kufar"
                    )
                    
                    # Парсим для пользователей Avito
                    for user_settings in avito_users:
                        if user_settings.get('is_active'):
                            await self.parse_for_user_avito(user_settings)
                            await asyncio.sleep(1)
                    
                    # Парсим для пользователей Kufar
                    for user_settings in kufar_users:
                        if user_settings.get('is_active'):
                            await self.parse_for_user_kufar(user_settings)
                            await asyncio.sleep(1)
                    
                    logger.info(f"Цикл парсинга завершен. Следующий цикл через {PARSING_INTERVAL_MINUTES} минут")
                
            except Exception as e:
                logger.error(f"Ошибка в цикле парсинга: {e}", exc_info=True)
            
            # Ждем указанное время (в секундах)
            await asyncio.sleep(PARSING_INTERVAL_MINUTES * 60)

    async def start(self):
        """Запустить сервис парсинга"""
        self.running = True
        logger.info("Сервис парсинга запущен")
        await self.run_parsing_cycle()

