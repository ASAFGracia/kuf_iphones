"""
Главный файл запуска приложения
"""
import asyncio
import logging
import sys
from database import Database
from bot_avito import AvitoTelegramBot
from bot_kufar import KufarTelegramBot
from services.parser_service import ParserService
from services.scheduler import SchedulerService
from utils.median_calculator import MedianPriceCalculator
from utils.logger import get_logger
from config import (
    TELEGRAM_AVITO_BOT_TOKEN, TELEGRAM_KUFAR_BOT_TOKEN,
    DB_CONFIG, PARSING_INTERVAL_MINUTES
)

# Настройка логирования
main_logger = get_logger('main')
logger = main_logger


async def main():
    """Главная функция"""
    db = None
    avito_bot = None
    kufar_bot = None
    parser_service = None
    scheduler_service = None
    
    try:
        # Инициализируем базу данных
        logger.info("=" * 60)
        logger.info("Инициализация базы данных...")
        db = Database(DB_CONFIG)
        logger.info("База данных инициализирована успешно")
        
        # Инициализируем калькулятор медианных цен
        logger.info("Инициализация калькулятора медианных цен...")
        median_calculator = MedianPriceCalculator(db)
        logger.info("Калькулятор медианных цен инициализирован")
        
        # Инициализируем ботов
        logger.info("Инициализация Telegram ботов...")
        avito_bot = AvitoTelegramBot(TELEGRAM_AVITO_BOT_TOKEN, db)
        kufar_bot = KufarTelegramBot(TELEGRAM_KUFAR_BOT_TOKEN, db)
        logger.info("Боты инициализированы")
        
        # Инициализируем сервис парсинга
        logger.info("Инициализация сервиса парсинга...")
        parser_service = ParserService(db, avito_bot, kufar_bot, median_calculator)
        logger.info("Сервис парсинга инициализирован")
        
        # Инициализируем планировщик
        logger.info("Инициализация планировщика задач...")
        scheduler_service = SchedulerService(median_calculator)
        logger.info("Планировщик задач инициализирован")
        
        # Инициализируем ботов (создаем application)
        logger.info("Создание приложений ботов...")
        avito_bot.application = avito_bot._create_application()
        kufar_bot.application = kufar_bot._create_application()
        logger.info("Приложения ботов созданы")
        
        # Запускаем ботов в фоне
        logger.info("Запуск ботов...")
        await avito_bot.application.initialize()
        await avito_bot.application.start()
        await avito_bot.application.updater.start_polling()
        logger.info("Бот Avito запущен")
        
        await kufar_bot.application.initialize()
        await kufar_bot.application.start()
        await kufar_bot.application.updater.start_polling()
        logger.info("Бот Kufar запущен")
        
        logger.info("=" * 60)
        logger.info("Все сервисы запущены успешно!")
        logger.info("=" * 60)
        
        # Запускаем сервис парсинга в фоне
        parsing_task = asyncio.create_task(parser_service.start())
        
        # Запускаем планировщик в фоне
        scheduler_task = asyncio.create_task(scheduler_service.start())
        
        # Ждем завершения (или прерывания)
        try:
            await asyncio.gather(parsing_task, scheduler_task)
        except asyncio.CancelledError:
            logger.info("Задачи остановлены")
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки (Ctrl+C)")
            parser_service.running = False
            scheduler_service.stop()
            parsing_task.cancel()
            scheduler_task.cancel()
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
        if parser_service:
            parser_service.running = False
        if scheduler_service:
            scheduler_service.stop()
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Завершение работы приложения...")
        
        if parser_service:
            parser_service.running = False
            logger.info("Сервис парсинга остановлен")
        
        if scheduler_service:
            scheduler_service.stop()
            logger.info("Планировщик остановлен")
        
        if avito_bot and avito_bot.application:
            try:
                await avito_bot.application.updater.stop()
                await avito_bot.application.stop()
                await avito_bot.application.shutdown()
                logger.info("Бот Avito остановлен")
            except Exception as e:
                logger.error(f"Ошибка при остановке бота Avito: {e}")
        
        if kufar_bot and kufar_bot.application:
            try:
                await kufar_bot.application.updater.stop()
                await kufar_bot.application.stop()
                await kufar_bot.application.shutdown()
                logger.info("Бот Kufar остановлен")
            except Exception as e:
                logger.error(f"Ошибка при остановке бота Kufar: {e}")
        
        if db:
            db.close()
            logger.info("Соединение с базой данных закрыто")
        
        logger.info("Программа завершена")
        logger.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске: {e}", exc_info=True)
        sys.exit(1)
