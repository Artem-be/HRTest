# Telegram Bot для HR-услуг

Бот для демонстрации услуг и сбора заявок от клиентов с интеграцией Django API и ежедневной отчётностью.

## Структура проекта
- `TgBot/` - Telegram бот (aiogram) - обработчики команд и логика бота
- `HRTest/` - Django API для хранения данных - логика БД и API endpoints
- `api/` - Django REST API endpoints
- `models.py` - Модели данных (UserControl, UserActivity)
- `serializers.py` - Сериализаторы
- `management/commands/` - Django management commands для отчётности

## Запуск

### Локальный запуск
```bash
# Запуск Django API
cd HRTest
python manage.py migrate
python manage.py createsuperuser  # Создание админа для Django admin
python manage.py runserver

# Запуск бота (в другом терминале)
cd TgBot
python main.py
```

### Docker запуск
```bash
# Создайте .env файл с переменными
BOT_TOKEN=ваш_токен_бота
ADMIN_ID=ваш_telegram_id
DJANGO_API_URL=http://localhost:8000/api/usercontrol/

# Запуск через Docker (попробуйте по порядку):
docker compose up --build
# или
docker-compose up --build
# или
docker compose -f docker-compose.yml up --build
```

## API Endpoints
- `POST /api/usercontrol/create_or_update/` - Создание заявки
- `POST /api/usercontrol/log_activity/` - Логирование активности пользователя
- `GET /api/usercontrol/daily_stats/` - Статистика за 24 часа
- `GET /api/usercontrol/` - Список всех заявок

## Django Admin
После создания суперпользователя доступен админ-интерфейс:
- `http://localhost:8000/admin/` - Админ-панель Django
- **UserControl** - Просмотр всех заявок от пользователей
- **UserActivity** - Просмотр активности пользователей

## Ежедневная отчётность
```bash
# Ручной запуск отчёта
cd HRTest
python manage.py send_daily_report

# Настройка cron для автоматической отправки (каждый день в 9:00)
0 9 * * * cd /path/to/HRTest && python manage.py send_daily_report
```

## Тесты
```bash
cd HRTest
python manage.py test
```

## Логирование
Логи сохраняются в файл `bot.log` в папке TgBot. 