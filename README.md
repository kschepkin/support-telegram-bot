# Support Telegram Bot Infrastructure

Полная инфраструктура для Telegram-бота поддержки с автоматической очисткой сообщений.

## Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram      │    │   Support Bot   │    │     MySQL       │
│   Users         │◄──►│   Application   │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        ▲
                              ▼                        │
                       ┌─────────────────┐             │
                       │ Message Cleaner │◄────────────┘
                       │   (Scheduled)   │
                       └─────────────────┘
```

## Сервисы

### 1. Support Bot (`support_bot/`)
- **Функция**: Основной Telegram-бот для обработки обращений пользователей
- **Особенности**: 
  - Автоматическая инициализация базы данных
  - Пересылка сообщений между пользователями и админами
  - Система банов и ограничений
  - Поддержка всех типов сообщений

### 2. Message Cleaner (`message_cleaner/`)
- **Функция**: Автоматическая очистка устаревших сообщений из БД
- **Особенности**:
  - Ждет создания таблиц основным ботом
  - Удаляет сообщения старше заданного времени
  - Работает по расписанию (каждые 24 часа)

### 3. MySQL Database
- **Функция**: Хранение сообщений и списка заблокированных пользователей
- **Особенности**:
  - Автоматическое создание схемы
  - Индексы для оптимизации запросов
  - UTF8MB4 кодировка для поддержки эмодзи

## Быстрый старт

### 1. Подготовка
```bash
# Клонируйте репозиторий
git clone <repository-url>
cd support-tg-bot

# Отредактируйте переменные окружения в docker-compose.yaml
nano docker-compose.yaml
```

### 2. Настройка переменных
Обновите следующие переменные в `docker-compose.yaml`:
- `BOT_TOKEN` - токен вашего Telegram-бота
- `ADMIN_CHAT_ID` - ваш Telegram ID
- `MYSQL_ROOT_PASSWORD` - пароль root для MySQL

### 3. Запуск
```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## Переменные окружения

### Support Bot
| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram-бота | Обязательно |
| `ADMIN_CHAT_ID` | ID администратора | Обязательно |
| `DB_*` | Настройки БД | Заданы в compose |
| `BAN_MESSAGE` | Сообщение для бана | "Бан+1" |
| `MESSAGE_COUNT_PERIOD` | Период лимита (сек) | 60 |
| `COUNT_OF_MESSAGES_IN_PERIOD` | Лимит сообщений | 3 |

### Message Cleaner
| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `MESSAGES_TO_DELETE_HOURS` | Время хранения (часы) | 72 |
| `DB_*` | Настройки БД | Заданы в compose |

## Порядок запуска

1. **MySQL Database** - Запускается первым, создает базу данных
2. **Support Bot** - Ждет готовности БД, создает таблицы и индексы
3. **Message Cleaner** - Ждет готовности бота, начинает работу

## Логи и мониторинг

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f support_bot
docker-compose logs -f message_cleaner
docker-compose logs -f database

# Статус сервисов
docker-compose ps

# Healthcheck статус
docker inspect support_bot_app | grep -A 10 "Health"
```

## Разработка

### Структура проекта
```
support-tg-bot/
├── support_bot/          # Основной бот
│   ├── run.py           # Главный файл
│   ├── db_init.py       # Инициализация БД
│   ├── db_connector.py  # Работа с БД
│   └── ...
├── message_cleaner/      # Сервис очистки
│   ├── message_cleaner.py
│   └── settings.py
├── docker-compose.yaml   # Оркестрация
└── data/                # Данные MySQL
```

### Локальная разработка
```bash
# Запуск только БД для разработки
docker-compose up database

# Запуск бота локально
cd support_bot
python run.py
```
