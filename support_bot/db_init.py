"""
Модуль для инициализации базы данных.
Создает базу данных, таблицы и индексы при первом запуске.
"""
import logging
import pymysql
from peewee import *
from settings import DB_USER, DB_HOST, DB_NAME, DB_PASSWORD

logger = logging.getLogger(__name__)


def create_database_if_not_exists():
    """Создает базу данных, если она не существует"""
    try:
        # Подключаемся к MySQL без указания конкретной базы данных
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # Создаем базу данных, если она не существует
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"База данных {DB_NAME} создана или уже существует")
            
        connection.commit()
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при создании базы данных: {e}")
        return False


def create_tables_with_indexes():
    """Создает таблицы с индексами"""
    try:
        # Подключаемся к созданной базе данных
        dbhandle = MySQLDatabase(
            DB_NAME, 
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            charset='utf8mb4'
        )
        
        dbhandle.connect()
        
        # Создаем таблицы, если они не существуют
        dbhandle.execute_sql("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                user_full_name VARCHAR(255) NOT NULL,
                message_date BIGINT NOT NULL,
                message_id BIGINT NOT NULL,
                last_reply_time BIGINT NULL,
                INDEX idx_user_id (user_id),
                INDEX idx_message_date (message_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        dbhandle.execute_sql("""
            CREATE TABLE IF NOT EXISTS bannedusers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                nickname VARCHAR(255) NULL,
                full_name VARCHAR(255) NOT NULL,
                INDEX idx_user_id_banned (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        logger.info("Таблицы и индексы созданы успешно")
        dbhandle.close()
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")
        return False


def initialize_database():
    """Полная инициализация базы данных"""
    logger.info("Начинаем инициализацию базы данных...")
    
    # Шаг 1: Создаем базу данных
    if not create_database_if_not_exists():
        logger.error("Не удалось создать базу данных")
        return False
    
    # Шаг 2: Создаем таблицы с индексами
    if not create_tables_with_indexes():
        logger.error("Не удалось создать таблицы")
        return False
    
    logger.info("Инициализация базы данных завершена успешно")
    return True


def check_database_connection():
    """Проверяет подключение к базе данных"""
    try:
        # Используем pymysql для более простой проверки
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # Проверяем существование таблиц
            cursor.execute("SHOW TABLES")
            tables_result = cursor.fetchall()
            
            # Извлекаем имена таблиц из результата
            table_names = []
            for table_row in tables_result:
                # В результате SHOW TABLES первое (и единственное) значение - это имя таблицы
                table_name = list(table_row.values())[0]
                table_names.append(table_name)
            
            logger.info(f"Найденные таблицы: {table_names}")
            
            required_tables = ['messages', 'bannedusers']
            missing_tables = [table for table in required_tables if table not in table_names]
            
            if missing_tables:
                logger.warning(f"Отсутствуют таблицы: {missing_tables}")
                connection.close()
                return False
            
            # Дополнительная проверка: попробуем выполнить простой запрос к каждой таблице
            for table in required_tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                logger.info(f"Таблица {table}: {result['count']} записей")
        
        connection.close()
        logger.info("Подключение к базе данных и проверка таблиц прошли успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при проверке подключения к базе данных: {e}")
        return False
