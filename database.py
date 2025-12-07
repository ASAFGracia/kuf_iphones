import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, List, Dict
import logging
from utils.logger import get_logger

logger = get_logger('database')


class Database:
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Установить соединение с базой данных"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("Подключение к базе данных установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise

    def _create_tables(self):
        """Создать таблицы если их нет"""
        try:
            with self.conn.cursor() as cur:
                # Таблица пользователей
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        nickname VARCHAR(255),
                        first_name VARCHAR(255),
                        last_name VARCHAR(255),
                        city VARCHAR(100),
                        model VARCHAR(100),
                        max_price INTEGER,
                        source VARCHAR(20) DEFAULT 'avito' CHECK (source IN ('avito', 'kufar')),
                        is_active BOOLEAN DEFAULT TRUE,
                        is_admin BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Миграция: добавляем колонки nickname и is_admin если их нет
                try:
                    cur.execute("""
                        DO $$ 
                        BEGIN 
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name='users' AND column_name='nickname'
                            ) THEN
                                ALTER TABLE users ADD COLUMN nickname VARCHAR(255);
                            END IF;
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name='users' AND column_name='is_admin'
                            ) THEN
                                ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
                            END IF;
                        END $$;
                    """)
                except Exception as e:
                    logger.warning(f"Не удалось добавить колонки в users: {e}")

                # Таблица логов взаимодействия с ботом
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_logs (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                        action VARCHAR(255),
                        message_text TEXT,
                        command VARCHAR(100),
                        source VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Миграция: добавляем колонки command и source если их нет
                try:
                    cur.execute("""
                        DO $$ 
                        BEGIN 
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name='user_logs' AND column_name='command'
                            ) THEN
                                ALTER TABLE user_logs ADD COLUMN command VARCHAR(100);
                            END IF;
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name='user_logs' AND column_name='source'
                            ) THEN
                                ALTER TABLE user_logs ADD COLUMN source VARCHAR(20);
                            END IF;
                        END $$;
                    """)
                except Exception as e:
                    logger.warning(f"Не удалось добавить колонки в user_logs: {e}")

                # Таблица объявлений
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS advertisements (
                        id SERIAL PRIMARY KEY,
                        avito_id VARCHAR(100),
                        kufar_id VARCHAR(100),
                        source VARCHAR(20) NOT NULL CHECK (source IN ('avito', 'kufar')),
                        price INTEGER NOT NULL,
                        model VARCHAR(100) NOT NULL,
                        city VARCHAR(100) NOT NULL,
                        memory VARCHAR(50),
                        url TEXT NOT NULL,
                        median_price DECIMAL(10, 2),
                        price_difference DECIMAL(10, 2),
                        notified BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(avito_id, source),
                        UNIQUE(kufar_id, source)
                    )
                """)

                # Индексы для быстрого поиска
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ads_city_model 
                    ON advertisements(city, model)
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ads_avito_id 
                    ON advertisements(avito_id)
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ads_kufar_id 
                    ON advertisements(kufar_id)
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ads_source 
                    ON advertisements(source)
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_active 
                    ON users(is_active)
                """)
                
                # Миграция: добавляем колонку notified если её нет
                try:
                    cur.execute("""
                        DO $$ 
                        BEGIN 
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name='advertisements' AND column_name='notified'
                            ) THEN
                                ALTER TABLE advertisements ADD COLUMN notified BOOLEAN DEFAULT FALSE;
                            END IF;
                        END $$;
                    """)
                except Exception as e:
                    logger.warning(f"Не удалось добавить колонку notified (возможно уже существует): {e}")
                
                # Устанавливаем админа (пользователь 8507895419)
                try:
                    from config import ADMIN_USER_ID
                    cur.execute("""
                        UPDATE users SET is_admin = TRUE 
                        WHERE user_id = %s
                    """, (ADMIN_USER_ID,))
                except Exception as e:
                    logger.warning(f"Не удалось установить админа: {e}")
                
                self.conn.commit()
                logger.info("Таблицы созданы успешно")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка создания таблиц: {e}")
            raise

    def add_user(self, user_id: int, username: str = None, 
                 first_name: str = None, last_name: str = None,
                 source: str = None, nickname: str = None, is_admin: bool = False):
        """Добавить нового пользователя"""
        try:
            with self.conn.cursor() as cur:
                # Проверяем существующего пользователя для сохранения статуса админа
                cur.execute("SELECT is_admin FROM users WHERE user_id = %s", (user_id,))
                existing = cur.fetchone()
                if existing:
                    is_admin = existing[0] or is_admin
                
                cur.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, source, nickname, is_admin)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        nickname = COALESCE(EXCLUDED.nickname, users.nickname),
                        is_admin = COALESCE(EXCLUDED.is_admin, users.is_admin),
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, username, first_name, last_name, source, nickname, is_admin))
                self.conn.commit()
                logger.info(f"Пользователь {user_id} добавлен/обновлен")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка добавления пользователя: {e}")
            raise
    
    def update_user_nickname(self, user_id: int, nickname: str):
        """Обновить никнейм пользователя"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET nickname = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (nickname, user_id))
                self.conn.commit()
                return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка обновления никнейма: {e}")
            return False
    
    def is_admin(self, user_id: int) -> bool:
        """Проверить является ли пользователь админом"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT is_admin FROM users WHERE user_id = %s", (user_id,))
                result = cur.fetchone()
                return result[0] if result else False
        except Exception as e:
            logger.error(f"Ошибка проверки статуса админа: {e}")
            return False

    def add_log(self, user_id: int, action: str, message_text: str = None,
                command: str = None, source: str = None):
        """Добавить лог взаимодействия с ботом"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_logs (user_id, action, message_text, command, source)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, action, message_text, command, source))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка добавления лога: {e}")
    
    def execute_sql(self, query: str, limit: int = 100) -> tuple:
        """
        Выполнить SQL запрос (только SELECT)
        Возвращает (результаты, ошибка)
        """
        try:
            # Проверяем что это SELECT запрос
            query_upper = query.strip().upper()
            if not query_upper.startswith('SELECT'):
                return None, "Разрешены только SELECT запросы"
            
            # Добавляем LIMIT если его нет (только для запросов без GROUP BY, ORDER BY с LIMIT)
            if 'LIMIT' not in query_upper and 'GROUP BY' not in query_upper:
                query = f"{query.rstrip(';')} LIMIT {limit}"
            
            with self.conn.cursor() as cur:
                cur.execute(query)
                
                # Получаем результаты
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
                    return (columns, rows), None
                else:
                    return None, "Запрос не вернул результаты"
        except Exception as e:
            return None, str(e)
    
    def get_analytics(self) -> dict:
        """Получить аналитику проекта"""
        try:
            with self.conn.cursor() as cur:
                # Всего пользователей
                cur.execute("SELECT COUNT(*) FROM users")
                total_users = cur.fetchone()[0]
                
                # Активных пользователей
                cur.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
                active_users = cur.fetchone()[0]
                
                # Пользователей по источникам
                cur.execute("SELECT COUNT(*) FROM users WHERE source = 'avito' AND is_active = TRUE")
                avito_users = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM users WHERE source = 'kufar' AND is_active = TRUE")
                kufar_users = cur.fetchone()[0]
                
                # Всего объявлений
                cur.execute("SELECT COUNT(*) FROM advertisements")
                total_ads = cur.fetchone()[0]
                
                # Объявления по источникам
                cur.execute("SELECT COUNT(*) FROM advertisements WHERE source = 'avito'")
                avito_ads = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM advertisements WHERE source = 'kufar'")
                kufar_ads = cur.fetchone()[0]
                
                # Отправленных объявлений
                cur.execute("SELECT COUNT(*) FROM advertisements WHERE notified = TRUE")
                sent_ads = cur.fetchone()[0]
                
                # Топ пользователей по действиям
                cur.execute("""
                    SELECT u.user_id, u.nickname, u.username, COUNT(l.id) as actions_count
                    FROM users u
                    LEFT JOIN user_logs l ON u.user_id = l.user_id
                    GROUP BY u.user_id, u.nickname, u.username
                    ORDER BY actions_count DESC
                    LIMIT 10
                """)
                top_users_rows = cur.fetchall()
                top_users = "\n".join([
                    f"• {row[1] or row[2] or f'ID:{row[0]}'}: {row[3]} действий"
                    for row in top_users_rows
                ]) if top_users_rows else "Нет данных"
                
                # Топ моделей
                cur.execute("""
                    SELECT model, COUNT(*) as count
                    FROM advertisements
                    GROUP BY model
                    ORDER BY count DESC
                    LIMIT 10
                """)
                top_models_rows = cur.fetchall()
                top_models = "\n".join([
                    f"• {row[0]}: {row[1]} объявлений"
                    for row in top_models_rows
                ]) if top_models_rows else "Нет данных"
                
                return {
                    'total_users': total_users,
                    'active_users': active_users,
                    'avito_users': avito_users,
                    'kufar_users': kufar_users,
                    'total_ads': total_ads,
                    'avito_ads': avito_ads,
                    'kufar_ads': kufar_ads,
                    'sent_ads': sent_ads,
                    'top_users': top_users,
                    'top_models': top_models,
                }
        except Exception as e:
            logger.error(f"Ошибка получения аналитики: {e}")
            return {}
    
    def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Получить профиль пользователя со статистикой"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Основная информация о пользователе
                cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cur.fetchone()
                
                if not user:
                    return None
                
                user_dict = dict(user)
                
                # Статистика: высланных объявлений
                cur.execute("""
                    SELECT COUNT(*) FROM advertisements 
                    WHERE notified = TRUE 
                    AND EXISTS (
                        SELECT 1 FROM users u 
                        WHERE u.user_id = %s 
                        AND u.city = advertisements.city 
                        AND (u.model = advertisements.model OR u.model IS NULL)
                    )
                """, (user_id,))
                sent_ads_count = cur.fetchone()[0]
                
                # Статистика: действий в боте
                cur.execute("SELECT COUNT(*) FROM user_logs WHERE user_id = %s", (user_id,))
                actions_count = cur.fetchone()[0]
                
                # Статистика: нажатий кнопок
                cur.execute("""
                    SELECT COUNT(*) FROM user_logs 
                    WHERE user_id = %s AND command = 'button'
                """, (user_id,))
                button_clicks = cur.fetchone()[0]
                
                user_dict['sent_ads_count'] = sent_ads_count
                user_dict['actions_count'] = actions_count
                user_dict['button_clicks'] = button_clicks
                
                return user_dict
        except Exception as e:
            logger.error(f"Ошибка получения профиля: {e}")
            return None

    def update_user_settings(self, user_id: int, city: str = None, 
                            model: str = None, max_price: int = None, 
                            is_active: bool = None, source: str = None):
        """Обновить настройки пользователя"""
        try:
            updates = []
            params = []
            
            if city is not None:
                updates.append("city = %s")
                params.append(city)
            if model is not None:
                updates.append("model = %s")
                params.append(model)
            if max_price is not None:
                updates.append("max_price = %s")
                params.append(max_price)
            if is_active is not None:
                updates.append("is_active = %s")
                params.append(is_active)
            if source is not None:
                updates.append("source = %s")
                params.append(source)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(user_id)
                
                with self.conn.cursor() as cur:
                    cur.execute(f"""
                        UPDATE users 
                        SET {', '.join(updates)}
                        WHERE user_id = %s
                    """, params)
                    self.conn.commit()
                    logger.info(f"Настройки пользователя {user_id} обновлены")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка обновления настроек: {e}")
            raise

    def get_user_settings(self, user_id: int) -> Optional[Dict]:
        """Получить настройки пользователя"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM users WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Ошибка получения настроек пользователя: {e}")
            return None

    def get_active_users(self, source: str = None) -> List[Dict]:
        """Получить список активных пользователей"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if source:
                    cur.execute("""
                        SELECT * FROM users WHERE is_active = TRUE AND source = %s
                    """, (source,))
                else:
                    cur.execute("""
                        SELECT * FROM users WHERE is_active = TRUE
                    """)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения активных пользователей: {e}")
            return []

    def add_advertisement(self, ad_id: str, price: int, model: str, 
                         city: str, memory: str, url: str, source: str,
                         median_price: float = None, price_difference: float = None,
                         notified: bool = False):
        """Добавить объявление в базу данных"""
        try:
            with self.conn.cursor() as cur:
                if source == 'avito':
                    cur.execute("""
                        INSERT INTO advertisements 
                        (avito_id, source, price, model, city, memory, url, median_price, price_difference, notified)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (avito_id, source) DO UPDATE SET
                            price = EXCLUDED.price,
                            memory = EXCLUDED.memory,
                            median_price = EXCLUDED.median_price,
                            price_difference = EXCLUDED.price_difference,
                            updated_at = CURRENT_TIMESTAMP
                    """, (ad_id, source, price, model, city, memory, url, median_price, price_difference, notified))
                elif source == 'kufar':
                    cur.execute("""
                        INSERT INTO advertisements 
                        (kufar_id, source, price, model, city, memory, url, median_price, price_difference, notified)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (kufar_id, source) DO UPDATE SET
                            price = EXCLUDED.price,
                            memory = EXCLUDED.memory,
                            median_price = EXCLUDED.median_price,
                            price_difference = EXCLUDED.price_difference,
                            updated_at = CURRENT_TIMESTAMP
                    """, (ad_id, source, price, model, city, memory, url, median_price, price_difference, notified))
                self.conn.commit()
                return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка добавления объявления: {e}")
            return False
    
    def mark_advertisement_notified(self, ad_id: str, source: str):
        """Пометить объявление как отправленное"""
        try:
            with self.conn.cursor() as cur:
                if source == 'avito':
                    cur.execute("""
                        UPDATE advertisements
                        SET notified = TRUE, updated_at = CURRENT_TIMESTAMP
                        WHERE avito_id = %s AND source = %s
                    """, (ad_id, source))
                elif source == 'kufar':
                    cur.execute("""
                        UPDATE advertisements
                        SET notified = TRUE, updated_at = CURRENT_TIMESTAMP
                        WHERE kufar_id = %s AND source = %s
                    """, (ad_id, source))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка пометки объявления как отправленного: {e}")
    
    def is_advertisement_notified(self, ad_id: str, source: str) -> bool:
        """Проверить было ли объявление отправлено"""
        try:
            with self.conn.cursor() as cur:
                if source == 'avito':
                    cur.execute("""
                        SELECT notified FROM advertisements
                        WHERE avito_id = %s AND source = %s
                    """, (ad_id, source))
                elif source == 'kufar':
                    cur.execute("""
                        SELECT notified FROM advertisements
                        WHERE kufar_id = %s AND source = %s
                    """, (ad_id, source))
                else:
                    return False
                
                result = cur.fetchone()
                return result[0] if result else False
        except Exception as e:
            logger.error(f"Ошибка проверки статуса объявления: {e}")
            return False
    
    def get_advertisement_created_at(self, ad_id: str, source: str):
        """Получить дату создания объявления"""
        try:
            with self.conn.cursor() as cur:
                if source == 'avito':
                    cur.execute("""
                        SELECT created_at FROM advertisements
                        WHERE avito_id = %s AND source = %s
                    """, (ad_id, source))
                elif source == 'kufar':
                    cur.execute("""
                        SELECT created_at FROM advertisements
                        WHERE kufar_id = %s AND source = %s
                    """, (ad_id, source))
                else:
                    return None
                
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Ошибка получения даты объявления: {e}")
            return None

    def advertisement_exists(self, ad_id: str, source: str) -> bool:
        """Проверить существует ли объявление"""
        try:
            with self.conn.cursor() as cur:
                if source == 'avito':
                    cur.execute("""
                        SELECT 1 FROM advertisements WHERE avito_id = %s AND source = %s
                    """, (ad_id, source))
                elif source == 'kufar':
                    cur.execute("""
                        SELECT 1 FROM advertisements WHERE kufar_id = %s AND source = %s
                    """, (ad_id, source))
                else:
                    return False
                return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка проверки объявления: {e}")
            return False

    def calculate_median_price(self, city: str, model: str, source: str = None) -> Optional[float]:
        """
        Рассчитать медианную цену для модели в городе
        ВНИМАНИЕ: Используйте MedianPriceCalculator для оптимизированного расчета
        """
        try:
            with self.conn.cursor() as cur:
                if source:
                    cur.execute("""
                        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median
                        FROM advertisements
                        WHERE city = %s AND model = %s AND source = %s
                    """, (city, model, source))
                else:
                    cur.execute("""
                        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median
                        FROM advertisements
                        WHERE city = %s AND model = %s
                    """, (city, model))
                result = cur.fetchone()
                return float(result[0]) if result and result[0] else None
        except Exception as e:
            logger.error(f"Ошибка расчета медианной цены: {e}")
            return None

    def update_median_prices(self, city: str, model: str, source: str = None):
        """Обновить медианные цены для всех объявлений модели в городе"""
        try:
            median_price = self.calculate_median_price(city, model, source)
            if median_price:
                with self.conn.cursor() as cur:
                    if source:
                        cur.execute("""
                            UPDATE advertisements
                            SET median_price = %s,
                                price_difference = %s - price,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE city = %s AND model = %s AND source = %s
                        """, (median_price, median_price, city, model, source))
                    else:
                        cur.execute("""
                            UPDATE advertisements
                            SET median_price = %s,
                                price_difference = %s - price,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE city = %s AND model = %s
                        """, (median_price, median_price, city, model))
                    self.conn.commit()
                    return median_price
            return None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка обновления медианных цен: {e}")
            return None

    def close(self):
        """Закрыть соединение с базой данных"""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с базой данных закрыто")


