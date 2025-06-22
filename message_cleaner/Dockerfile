FROM python:3.11

WORKDIR /usr/src/app

# Копируем файл зависимостей
COPY requirements.txt ./

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем все файлы приложения
COPY . .

# Команда запуска
CMD ["python", "message_cleaner.py"]
