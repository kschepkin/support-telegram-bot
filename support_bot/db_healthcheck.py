#!/usr/bin/env python3
"""
Скрипт для проверки состояния и восстановления базы данных.
Может использоваться как healthcheck или для ручного восстановления.
"""
import sys
import logging
from db_init import initialize_database, check_database_connection

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():
    """Основная функция для проверки и восстановления БД"""
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check-only':
        # Только проверка без восстановления
        logger.info("Режим проверки базы данных...")
        if check_database_connection():
            logger.info("✅ База данных в порядке")
            sys.exit(0)
        else:
            logger.error("❌ Проблемы с базой данных")
            sys.exit(1)
    
    # Полная инициализация
    logger.info("Запуск инициализации базы данных...")
    
    if initialize_database():
        logger.info("✅ База данных успешно инициализирована")
        
        if check_database_connection():
            logger.info("✅ Проверка подключения прошла успешно")
            sys.exit(0)
        else:
            logger.error("❌ Ошибка при проверке подключения")
            sys.exit(1)
    else:
        logger.error("❌ Ошибка инициализации базы данных")
        sys.exit(1)


if __name__ == '__main__':
    main()
