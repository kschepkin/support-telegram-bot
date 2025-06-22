FROM python:3.11

WORKDIR /usr/src/app

# Копируем файл зависимостей
COPY requirements.txt ./

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем все файлы приложения
COPY . .

# Делаем скрипт healthcheck исполняемым
RUN chmod +x db_healthcheck.py

# Добавляем healthcheck для контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python db_healthcheck.py --check-only || exit 1

# Команда запуска
CMD ["python", "run.py"]
