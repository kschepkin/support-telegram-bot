from os import environ

BOT_TOKEN = environ.get('BOT_TOKEN')
ADMIN_CHAT_ID = int(environ.get('ADMIN_CHAT_ID'))
BAN_MESSAGE = environ.get('BAN_MESSAGE', 'Бан+1')
MESSAGE_COUNT_PERIOD = int(environ.get('MESSAGE_COUNT_PERIOD', 60))
MESSAGE_IS_RECEIVED_BY_ADMIN = environ.get('MESSAGE_IS_RECEIVED_BY_ADMIN',
                                           'Ваше обращение успешно отправлено. Вам ответят в ближайшее время')
COUNT_OF_MESSAGES_IN_PERIOD = int(environ.get('COUNT_OF_MESSAGES_IN_PERIOD', 3))
START_MESSAGE = environ.get('START_MESSAGE', 'Добрый день! Напишите сообщение — и мы обязательно ответим!')
DB_USER = environ.get('DB_USER')
DB_PASSWORD = environ.get('DB_PASSWORD')
DB_NAME = environ.get('DB_NAME')
DB_HOST = environ.get('DB_HOST')
