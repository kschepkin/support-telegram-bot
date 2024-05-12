from os import environ

MESSAGES_TO_DELETE_HOURS = int(environ.get('MESSAGES_TO_DELETE_HOURS', 72))
DB_USER = environ.get('DB_USER')
DB_PASSWORD = environ.get('DB_PASSWORD')
DB_NAME = environ.get('DB_NAME')
DB_HOST = environ.get('DB_HOST')