import time
import datetime
import logging
import sys
from peewee import *
from settings import DB_USER, DB_HOST, DB_NAME, DB_PASSWORD, MESSAGES_TO_DELETE_HOURS

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

dbhandle = MySQLDatabase(
    DB_NAME, 
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    charset='utf8mb4'
)


class Messages(Model):
    class Meta:
        database = dbhandle
        order_by = ('id',)
        table_name = 'messages'

    user_id = BigIntegerField()
    user_full_name = CharField()
    message_date = BigIntegerField()
    message_id = BigIntegerField()
    last_reply_time = BigIntegerField(null=True)


def wait_for_tables(max_retries=30, delay=10):
    """Ждет, пока основной бот создаст таблицы"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Проверка наличия таблиц (попытка {attempt + 1}/{max_retries})")
            
            dbhandle.connect(reuse_if_open=True)
            
            # Проверяем, существует ли таблица messages
            cursor = dbhandle.execute_sql("SHOW TABLES LIKE 'messages'")
            result = cursor.fetchone()
            
            if result:
                # Дополнительно проверим, что можем выполнить простой запрос
                Messages.select().count()
                logger.info("✅ Таблица messages найдена и доступна")
                dbhandle.close()
                return True
            else:
                logger.info("❌ Таблица messages еще не создана")
                
        except Exception as e:
            logger.warning(f"Ошибка при проверке таблиц: {e}")
        
        finally:
            if not dbhandle.is_closed():
                dbhandle.close()
        
        if attempt < max_retries - 1:
            logger.info(f"Ожидание {delay} секунд перед следующей попыткой...")
            time.sleep(delay)
    
    logger.error("Не удалось дождаться создания таблиц")
    return False


def remove_obsolete_messages():
    """Удаляет устаревшие сообщения"""
    try:
        edge = datetime.datetime.now().timestamp() - MESSAGES_TO_DELETE_HOURS * 3600
        
        dbhandle.connect(reuse_if_open=True)
        
        # Подсчитываем количество записей для удаления
        messages_to_delete = Messages.select().where(
            (Messages.last_reply_time.is_null(False)) & 
            (Messages.last_reply_time < edge)
        ).count()
        
        if messages_to_delete > 0:
            # Удаляем устаревшие сообщения
            query = Messages.delete().where(
                (Messages.last_reply_time.is_null(False)) & 
                (Messages.last_reply_time < edge)
            )
            deleted_count = query.execute()
            
            logger.info(f"Удалено {deleted_count} устаревших сообщений (старше {MESSAGES_TO_DELETE_HOURS} часов)")
        else:
            logger.info("Нет устаревших сообщений для удаления")
            
    except Exception as e:
        logger.error(f"Ошибка при удалении устаревших сообщений: {e}")
    finally:
        if not dbhandle.is_closed():
            dbhandle.close()


def main():
    """Основная функция"""
    logger.info("Запуск сервиса очистки сообщений...")
    
    # Ждем, пока основной бот создаст таблицы
    if not wait_for_tables():
        logger.critical("Не удалось дождаться создания таблиц. Завершение работы.")
        sys.exit(1)
    
    logger.info(f"Сервис очистки запущен. Проверка каждые 24 часа, удаление сообщений старше {MESSAGES_TO_DELETE_HOURS} часов.")
    
    # Основной цикл
    while True:
        try:
            remove_obsolete_messages()
            logger.info("Следующая проверка через 24 часа")
            time.sleep(86400)  # 24 часа
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания. Завершение работы...")
            break
        except Exception as e:
            logger.error(f"Неожиданная ошибка в основном цикле: {e}")
            logger.info("Ожидание 10 минут перед повторной попыткой...")
            time.sleep(600)  # 10 минут


if __name__ == "__main__":
    main()
