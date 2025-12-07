import logging
from utils.logger import get_logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from database import Database
from config import KUFAR_CITIES, IPHONE_MODELS, ADMIN_USER_ID
from typing import Dict

logger = get_logger('kufar_bot')


class KufarTelegramBot:
    def __init__(self, token: str, db: Database):
        self.token = token
        self.db = db
        self.application = None
        self.user_states = {}
        self.source = 'kufar'

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        
        # Проверяем является ли пользователь админом (из БД или по ID)
        is_admin = self.db.is_admin(user_id) or (user_id == ADMIN_USER_ID)
        
        self.db.add_user(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            source='kufar',
            is_admin=is_admin
        )
        
        self.db.update_user_settings(user_id, source='kufar')
        self.db.add_log(user_id, 'start', update.message.text, command='/start', source='kufar')
        
        # Проверяем есть ли никнейм
        settings = self.db.get_user_settings(user_id)
        if not settings.get('nickname'):
            # Запрашиваем никнейм
            self.user_states[user_id] = 'waiting_nickname'
            await update.message.reply_text(
                "👋 Привет! Добро пожаловать в бот для поиска выгодных предложений iPhone на Kufar.\n\n"
                "📝 Введите свой ник для аналитики (персональные данные не распространяются):"
            )
            return
        
        welcome_text = f"""
👋 Привет, {user.first_name}!

Я бот для поиска выгодных предложений iPhone на Kufar (Беларусь).

📊 Твои текущие настройки:
• Город: {settings.get('city', 'не выбран')}
• Модель: {settings.get('model', 'не выбрана')}
• Макс. цена: {settings.get('max_price', 'не установлена')} BYN
• Статус: {'🟢 Активен' if settings.get('is_active') else '🔴 На паузе'}

Используй команды:
/start - Начать работу
/city - Выбрать город
/model - Выбрать модель iPhone
/price - Установить максимальную цену
/status - Статус парсинга
/pause - Поставить на паузу
/resume - Возобновить парсинг
/help - Помощь
"""
        
        if is_admin:
            welcome_text += "\n🔧 Админ команды:\n/sql - Выполнить SQL запрос"
        
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📖 Справка по командам:

/start - Начать работу с ботом
/city - Выбрать город для парсинга
/model - Выбрать модель iPhone
/price - Установить максимальную цену
/status - Показать текущие настройки
/pause - Поставить парсинг на паузу
/resume - Возобновить парсинг
/help - Показать эту справку

ℹ️ Бот будет присылать объявления только если:
• Цена ниже медианной более чем на 15%
• Цена не превышает установленный максимум
• Модель соответствует выбранной
"""
        await update.message.reply_text(help_text)
        self.db.add_log(update.effective_user.id, 'help', None, command='/help', source='kufar')

    async def city_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /city"""
        keyboard = []
        cities_list = list(KUFAR_CITIES.items())
        
        for i in range(0, len(cities_list), 2):
            row = []
            row.append(InlineKeyboardButton(
                cities_list[i][0],
                callback_data=f"city_{cities_list[i][1]}"
            ))
            if i + 1 < len(cities_list):
                row.append(InlineKeyboardButton(
                    cities_list[i + 1][0],
                    callback_data=f"city_{cities_list[i + 1][1]}"
                ))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🏙 Выбери город для парсинга:",
            reply_markup=reply_markup
        )
        self.db.add_log(update.effective_user.id, 'city_selection', None, command='/city', source='kufar')

    async def model_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /model"""
        keyboard = []
        models_list = IPHONE_MODELS
        
        for i in range(0, len(models_list), 2):
            row = []
            row.append(InlineKeyboardButton(
                models_list[i],
                callback_data=f"model_{models_list[i]}"
            ))
            if i + 1 < len(models_list):
                row.append(InlineKeyboardButton(
                    models_list[i + 1],
                    callback_data=f"model_{models_list[i + 1]}"
                ))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton(
            "Все модели",
            callback_data="model_all"
        )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📱 Выбери модель iPhone:",
            reply_markup=reply_markup
        )
        self.db.add_log(update.effective_user.id, 'model_selection', None, command='/model', source='kufar')

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /price"""
        await update.message.reply_text(
            "💰 Введи максимальную цену в BYN (например: 1000)\n"
            "Или отправь 0 чтобы убрать ограничение:"
        )
        self.user_states[update.effective_user.id] = 'waiting_price'
        self.db.add_log(update.effective_user.id, 'price_setting', None, command='/price', source='kufar')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        user_id = update.effective_user.id
        settings = self.db.get_user_settings(user_id)
        
        if not settings:
            await update.message.reply_text("❌ Настройки не найдены. Используй /start")
            return
        
        status_text = f"""
📊 Твои настройки:

🏙 Город: {settings.get('city', 'не выбран')}
📱 Модель: {settings.get('model', 'не выбрана')}
💰 Макс. цена: {settings.get('max_price', 'не установлена')} BYN
🔄 Статус: {'🟢 Активен' if settings.get('is_active') else '🔴 На паузе'}
"""
        await update.message.reply_text(status_text)
        self.db.add_log(user_id, 'status_check', None, command='/status', source='kufar')

    async def pause_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /pause"""
        user_id = update.effective_user.id
        self.db.update_user_settings(user_id, is_active=False)
        await update.message.reply_text("⏸ Парсинг поставлен на паузу")
        self.db.add_log(user_id, 'pause', None, command='/pause', source='kufar')

    async def resume_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /resume"""
        user_id = update.effective_user.id
        self.db.update_user_settings(user_id, is_active=True)
        await update.message.reply_text("▶️ Парсинг возобновлен")
        self.db.add_log(user_id, 'resume', None, command='/resume', source='kufar')

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data.startswith('city_'):
            city_code = data.replace('city_', '')
            city_name = [name for name, code in KUFAR_CITIES.items() if code == city_code][0]
            self.db.update_user_settings(user_id, city=city_name)
            await query.edit_message_text(f"✅ Город выбран: {city_name}")
            self.db.add_log(user_id, f'city_selected_{city_name}', None, command='button', source='kufar')
        
        elif data.startswith('model_'):
            model = data.replace('model_', '')
            if model == 'all':
                model = None
                self.db.update_user_settings(user_id, model=None)
                await query.edit_message_text("✅ Выбраны все модели")
            else:
                self.db.update_user_settings(user_id, model=model)
                await query.edit_message_text(f"✅ Модель выбрана: {model}")
            self.db.add_log(user_id, f'model_selected_{model}', None, command='button', source='kufar')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        
        self.db.add_log(user_id, 'message', text, command=None, source='kufar')
        
        # Обработка никнейма
        if user_id in self.user_states and self.user_states[user_id] == 'waiting_nickname':
            if text and len(text.strip()) > 0:
                nickname = text.strip()[:50]  # Ограничиваем длину
                self.db.update_user_nickname(user_id, nickname)
                del self.user_states[user_id]
                await update.message.reply_text(
                    f"✅ Никнейм сохранен: {nickname}\n\n"
                    "Теперь можешь использовать команды бота. /help - для справки"
                )
                # Показываем приветствие с настройками
                settings = self.db.get_user_settings(user_id)
                welcome_text = f"""
👋 Привет, {update.effective_user.first_name}!

Я бот для поиска выгодных предложений iPhone на Kufar (Беларусь).

📊 Твои текущие настройки:
• Город: {settings.get('city', 'не выбран')}
• Модель: {settings.get('model', 'не выбрана')}
• Макс. цена: {settings.get('max_price', 'не установлена')} BYN
• Статус: {'🟢 Активен' if settings.get('is_active') else '🔴 На паузе'}

Используй команды:
/start - Начать работу
/city - Выбрать город
/model - Выбрать модель iPhone
/price - Установить максимальную цену
/status - Статус парсинга
/pause - Поставить на паузу
/resume - Возобновить парсинг
/help - Помощь
"""
                if self.db.is_admin(user_id):
                    welcome_text += "\n🔧 Админ команды:\n/sql - SQL запросы\n/analytics - Аналитика"
                await update.message.reply_text(welcome_text)
            else:
                await update.message.reply_text("❌ Никнейм не может быть пустым. Введите свой ник:")
            return
        
        # Обработка SQL режима
        if user_id in self.user_states and self.user_states[user_id] == 'sql_mode':
            if not self.db.is_admin(user_id):
                await update.message.reply_text("❌ У вас нет доступа к SQL режиму")
                del self.user_states[user_id]
                return
            
            query = text.strip()
            self.db.add_log(user_id, 'sql_execute', query, command='sql_mode', source='kufar')
            
            try:
                result, error = self.db.execute_sql(query)
                
                if error:
                    await update.message.reply_text(f"❌ Ошибка: {error}")
                    return
                
                if not result:
                    await update.message.reply_text("ℹ️ Запрос не вернул результатов")
                    return
                
                columns, rows = result
                
                if not rows:
                    await update.message.reply_text("ℹ️ Результатов не найдено")
                    return
                
                # Ограничиваем количество строк
                max_rows = 50
                rows_to_show = rows[:max_rows]
                
                # Формируем таблицу
                result_text = "📊 Результаты запроса:\n\n"
                result_text += " | ".join(columns) + "\n"
                result_text += "-" * 50 + "\n"
                
                for row in rows_to_show:
                    row_str = " | ".join([str(val) if val is not None else "NULL" for val in row])
                    result_text += row_str + "\n"
                
                if len(rows) > max_rows:
                    result_text += f"\n... и еще {len(rows) - max_rows} строк(и)"
                
                # Разбиваем на части если слишком длинное
                if len(result_text) > 4000:
                    parts = [result_text[i:i+4000] for i in range(0, len(result_text), 4000)]
                    for part in parts:
                        await update.message.reply_text(f"```\n{part}\n```", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"```\n{result_text}\n```", parse_mode='Markdown')
                    
            except Exception as e:
                await update.message.reply_text(f"❌ Ошибка выполнения запроса: {str(e)}")
                logger.error(f"Ошибка выполнения SQL запроса: {e}")
            return
        
        # Обработка цены
        if user_id in self.user_states and self.user_states[user_id] == 'waiting_price':
            try:
                price = int(text)
                if price < 0:
                    await update.message.reply_text("❌ Цена не может быть отрицательной")
                    return
                
                if price == 0:
                    self.db.update_user_settings(user_id, max_price=None)
                    await update.message.reply_text("✅ Ограничение по цене снято")
                else:
                    self.db.update_user_settings(user_id, max_price=price)
                    await update.message.reply_text(f"✅ Максимальная цена установлена: {price} BYN")
                
                del self.user_states[user_id]
            except ValueError:
                await update.message.reply_text("❌ Пожалуйста, введи число")
        else:
            await update.message.reply_text(
                "Используй команды для управления ботом. /help - для справки"
            )
    
    async def sql_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /sql (только для админа)"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_USER_ID:
            await update.message.reply_text("❌ У вас нет доступа к этой команде")
            self.db.add_log(user_id, 'sql_denied', None, command='/sql', source='kufar')
            return
        
        # Проверяем есть ли SQL запрос в сообщении
        if not context.args:
            await update.message.reply_text(
                "🔧 Выполнение SQL запроса (только SELECT)\n\n"
                "Использование: /sql SELECT * FROM users LIMIT 10\n\n"
                "⚠️ Разрешены только SELECT запросы!"
            )
            self.db.add_log(user_id, 'sql_help', None, command='/sql', source='kufar')
            return
        
        query = ' '.join(context.args)
        self.db.add_log(user_id, 'sql_execute', query, command='/sql', source='kufar')
        
        try:
            result, error = self.db.execute_sql(query)
            
            if error:
                await update.message.reply_text(f"❌ Ошибка: {error}")
                return
            
            if not result:
                await update.message.reply_text("ℹ️ Запрос не вернул результатов")
                return
            
            columns, rows = result
            
            # Форматируем результат
            if not rows:
                await update.message.reply_text("ℹ️ Результатов не найдено")
                return
            
            # Ограничиваем количество строк для отправки
            max_rows = 50
            rows_to_show = rows[:max_rows]
            
            # Формируем таблицу
            result_text = "📊 Результаты запроса:\n\n"
            result_text += " | ".join(columns) + "\n"
            result_text += "-" * 50 + "\n"
            
            for row in rows_to_show:
                row_str = " | ".join([str(val) if val is not None else "NULL" for val in row])
                result_text += row_str + "\n"
            
            if len(rows) > max_rows:
                result_text += f"\n... и еще {len(rows) - max_rows} строк(и)"
            
            # Разбиваем на части если слишком длинное
            if len(result_text) > 4000:
                parts = [result_text[i:i+4000] for i in range(0, len(result_text), 4000)]
                for part in parts:
                    await update.message.reply_text(f"```\n{part}\n```", parse_mode='Markdown')
            else:
                await update.message.reply_text(f"```\n{result_text}\n```", parse_mode='Markdown')
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка выполнения запроса: {str(e)}")
            logger.error(f"Ошибка выполнения SQL запроса: {e}")

    async def send_advertisement(self, user_id: int, ad_data: Dict):
        """Отправить объявление пользователю"""
        try:
            price = ad_data['price']
            median_price = ad_data.get('median_price', 0)
            price_difference = ad_data.get('price_difference', 0)  # Уже положительное значение (экономия)
            discount_percent = (price_difference / median_price * 100) if median_price > 0 else 0
            
            # Форматируем дату создания
            created_at = ad_data.get('created_at')
            date_str = ""
            if created_at:
                if isinstance(created_at, str):
                    date_str = f"\n📅 Дата: {created_at}"
                else:
                    from datetime import datetime
                    if isinstance(created_at, datetime):
                        date_str = f"\n📅 Дата: {created_at.strftime('%d.%m.%Y %H:%M')}"
            
            message = f"""
🎯 Найдено выгодное предложение на Kufar!

📱 Модель: {ad_data['model']}
💰 Цена: {price:,} BYN
📊 Медианная цена: {median_price:,.0f} BYN
💵 Экономия: {price_difference:,.0f} BYN ({discount_percent:.1f}%)

🏙 Город: {ad_data['city']}
💾 Память: {ad_data.get('memory', 'не указана')}{date_str}

🔗 {ad_data['url']}
"""
            
            if self.application and self.application.bot:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
            else:
                logger.error(f"Application не инициализирован, не могу отправить сообщение пользователю {user_id}")
            
            self.db.add_log(user_id, 'advertisement_sent', ad_data['url'], command=None, source='kufar')
            logger.info(f"Объявление отправлено пользователю {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки объявления пользователю {user_id}: {e}")

    def _create_application(self):
        """Создать и настроить приложение бота"""
        application = Application.builder().token(self.token).build()
        
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("city", self.city_command))
        application.add_handler(CommandHandler("model", self.model_command))
        application.add_handler(CommandHandler("price", self.price_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("pause", self.pause_command))
        application.add_handler(CommandHandler("resume", self.resume_command))
        application.add_handler(CommandHandler("sql", self.sql_command))
        application.add_handler(CommandHandler("stopsql", self.stopsql_command))
        application.add_handler(CommandHandler("analytics", self.analytics_command))
        application.add_handler(CommandHandler("profile", self.profile_command))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        return application

    def run(self):
        """Запустить бота"""
        if not self.application:
            self.application = self._create_application()
        
        logger.info("Telegram бот Kufar запущен")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

