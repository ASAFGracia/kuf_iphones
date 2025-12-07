"""
Модуль для расчета медианной цены с оптимизацией производительности
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from utils.logger import get_logger

logger = get_logger('median_calculator')


class MedianPriceCalculator:
    """Калькулятор медианной цены с оптимизацией"""
    
    # Количество записей для расчета медианной цены (баланс между точностью и скоростью)
    MAX_RECORDS_FOR_MEDIAN = 1000
    
    # Период для расчета медианной цены (дни)
    MEDIAN_CALCULATION_PERIOD_DAYS = 30
    
    def __init__(self, db: Database):
        self.db = db
    
    def calculate_median_price(
        self, 
        city: str, 
        model: str, 
        source: str = None,
        use_recent_only: bool = True
    ) -> Optional[float]:
        """
        Рассчитать медианную цену для модели в городе
        
        Args:
            city: Город
            model: Модель iPhone
            source: Источник (avito/kufar) или None для всех
            use_recent_only: Использовать только недавние записи для производительности
        
        Returns:
            Медианная цена или None
        """
        try:
            from psycopg2.extras import RealDictCursor
            with self.db.conn.cursor() as cur:
                if use_recent_only:
                    # Используем только записи за последний период
                    date_threshold = datetime.now() - timedelta(days=self.MEDIAN_CALCULATION_PERIOD_DAYS)
                    
                    if source:
                        query = """
                            SELECT price 
                            FROM advertisements
                            WHERE city = %s 
                            AND model = %s 
                            AND source = %s
                            AND created_at >= %s
                            ORDER BY created_at DESC
                            LIMIT %s
                        """
                        cur.execute(query, (city, model, source, date_threshold, self.MAX_RECORDS_FOR_MEDIAN))
                    else:
                        query = """
                            SELECT price 
                            FROM advertisements
                            WHERE city = %s 
                            AND model = %s
                            AND created_at >= %s
                            ORDER BY created_at DESC
                            LIMIT %s
                        """
                        cur.execute(query, (city, model, date_threshold, self.MAX_RECORDS_FOR_MEDIAN))
                else:
                    # Используем все записи (может быть медленно для больших объемов)
                    if source:
                        query = """
                            SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median
                            FROM advertisements
                            WHERE city = %s AND model = %s AND source = %s
                        """
                        cur.execute(query, (city, model, source))
                        result = cur.fetchone()
                        return float(result[0]) if result and result[0] else None
                    else:
                        query = """
                            SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median
                            FROM advertisements
                            WHERE city = %s AND model = %s
                        """
                        cur.execute(query, (city, model))
                        result = cur.fetchone()
                        return float(result[0]) if result and result[0] else None
                
                # Получаем все цены и вычисляем медиану в Python
                prices = [row[0] for row in cur.fetchall()]
                
                if not prices:
                    logger.debug(f"Нет данных для расчета медианной цены: {city}, {model}, {source}")
                    return None
                
                # Сортируем и находим медиану
                prices_sorted = sorted(prices)
                n = len(prices_sorted)
                
                if n % 2 == 0:
                    median = (prices_sorted[n // 2 - 1] + prices_sorted[n // 2]) / 2
                else:
                    median = prices_sorted[n // 2]
                
                logger.info(
                    f"Медианная цена рассчитана: {city}, {model}, {source or 'all'}, "
                    f"медиана={median:.2f}, записей={n}"
                )
                
                return float(median)
                
        except Exception as e:
            logger.error(f"Ошибка расчета медианной цены для {city}, {model}, {source}: {e}")
            return None
    
    def recalculate_all_medians(self, source: str = None):
        """
        Пересчитать медианные цены для всех комбинаций город-модель
        
        Args:
            source: Источник (avito/kufar) или None для всех
        """
        try:
            logger.info(f"Начало пересчета медианных цен для источника: {source or 'all'}")
            
            with self.db.conn.cursor() as cur:
                # Получаем все уникальные комбинации город-модель
                if source:
                    query = """
                        SELECT DISTINCT city, model 
                        FROM advertisements 
                        WHERE source = %s
                    """
                    cur.execute(query, (source,))
                else:
                    query = """
                        SELECT DISTINCT city, model 
                        FROM advertisements
                    """
                    cur.execute(query)
                
                combinations = cur.fetchall()
                logger.info(f"Найдено {len(combinations)} комбинаций город-модель для пересчета")
                
                updated_count = 0
                for city, model in combinations:
                    median_price = self.calculate_median_price(city, model, source)
                    
                    if median_price:
                        # Обновляем медианные цены для всех объявлений этой комбинации
                        if source:
                            update_query = """
                                UPDATE advertisements
                                SET median_price = %s,
                                    price_difference = price - %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE city = %s AND model = %s AND source = %s
                            """
                            cur.execute(update_query, (median_price, median_price, city, model, source))
                        else:
                            update_query = """
                                UPDATE advertisements
                                SET median_price = %s,
                                    price_difference = price - %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE city = %s AND model = %s
                            """
                            cur.execute(update_query, (median_price, median_price, city, model))
                        
                        updated_count += 1
                
                self.db.conn.commit()
                logger.info(f"Пересчет завершен. Обновлено {updated_count} комбинаций")
                
        except Exception as e:
            self.db.conn.rollback()
            logger.error(f"Ошибка пересчета медианных цен: {e}")
            raise

