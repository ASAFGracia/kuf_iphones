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
from config.app_settings import MEDIAN_RECALCULATION_INTERVAL_HOURS

logger = get_logger('scheduler')


class SchedulerService:
    """Сервис для планирования периодических задач"""
    
    def __init__(self, median_calculator: MedianPriceCalculator):
        self.median_calculator = median_calculator
        self.running = False
        self.last_recalculation_time = None
    
    async def periodic_median_recalculation(self):
        """Периодический пересчет медианных цен (каждые N часов)"""
        while self.running:
            try:
                now = datetime.now()
                
                # Проверяем, нужно ли пересчитывать
                should_recalculate = False
                if self.last_recalculation_time is None:
                    # Первый запуск - пересчитываем сразу
                    should_recalculate = True
                else:
                    # Проверяем прошло ли достаточно времени
                    time_diff = (now - self.last_recalculation_time).total_seconds() / 3600
                    if time_diff >= MEDIAN_RECALCULATION_INTERVAL_HOURS:
                        should_recalculate = True
                
                if should_recalculate:
                    logger.info(f"Начало пересчета медианных цен (интервал: {MEDIAN_RECALCULATION_INTERVAL_HOURS} часов)")
                    
                    # Пересчитываем для обоих источников
                    self.median_calculator.recalculate_all_medians('avito')
                    self.median_calculator.recalculate_all_medians('kufar')
                    
                    self.last_recalculation_time = now
                    logger.info("Пересчет медианных цен завершен")
                
                # Проверяем каждые час
                await asyncio.sleep(60 * 60)
                
            except Exception as e:
                logger.error(f"Ошибка в пересчете медианных цен: {e}")
                await asyncio.sleep(60 * 60)  # Ждем час перед повтором
    
    async def start(self):
        """Запустить планировщик"""
        self.running = True
        logger.info(f"Планировщик задач запущен (пересчет каждые {MEDIAN_RECALCULATION_INTERVAL_HOURS} часов)")
        await self.periodic_median_recalculation()
    
    def stop(self):
        """Остановить планировщик"""
        self.running = False
        logger.info("Планировщик задач остановлен")

