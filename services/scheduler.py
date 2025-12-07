"""
Сервис для планирования задач (ежедневный пересчет медианной цены)
"""
import asyncio
import logging
import sys
import os
from datetime import datetime, time

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.median_calculator import MedianPriceCalculator
from utils.logger import get_logger

logger = get_logger('scheduler')


class SchedulerService:
    """Сервис для планирования периодических задач"""
    
    def __init__(self, median_calculator: MedianPriceCalculator):
        self.median_calculator = median_calculator
        self.running = False
        self.last_recalculation_date = None
    
    async def daily_median_recalculation(self):
        """Ежедневный пересчет медианных цен"""
        while self.running:
            try:
                now = datetime.now()
                current_date = now.date()
                
                # Проверяем, нужно ли пересчитывать (если еще не пересчитывали сегодня)
                if self.last_recalculation_date != current_date:
                    # Пересчитываем в 3:00 ночи
                    if now.hour >= 3:
                        logger.info("Начало ежедневного пересчета медианных цен")
                        
                        # Пересчитываем для обоих источников
                        self.median_calculator.recalculate_all_medians('avito')
                        self.median_calculator.recalculate_all_medians('kufar')
                        
                        self.last_recalculation_date = current_date
                        logger.info("Ежедневный пересчет медианных цен завершен")
                
                # Проверяем каждые 6 часов
                await asyncio.sleep(6 * 60 * 60)
                
            except Exception as e:
                logger.error(f"Ошибка в ежедневном пересчете медианных цен: {e}")
                await asyncio.sleep(60 * 60)  # Ждем час перед повтором
    
    async def start(self):
        """Запустить планировщик"""
        self.running = True
        logger.info("Планировщик задач запущен")
        await self.daily_median_recalculation()
    
    def stop(self):
        """Остановить планировщик"""
        self.running = False
        logger.info("Планировщик задач остановлен")

