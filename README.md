# VPN Telegram Bot

Telegram-бот для управления VPN-подписками с интеграцией платежной системы и панели управления 3x-ui.

## Возможности

- Регистрация пользователей
- Выбор тарифных планов
- Оплата через QIWI
- Автоматическая выдача VPN-ключей
- Управление подписками
- Административная панель
- Статистика использования

## Требования

- Python 3.8+
- PostgreSQL или SQLite
- Панель управления 3x-ui
- Аккаунт QIWI для приема платежей

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/vpn-telegram-bot.git
cd vpn-telegram-bot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` в корневой директории проекта:
```env
# Telegram Bot
BOT_TOKEN=your_bot_token

# 3x-ui Panel
PANEL_URL=http://your-panel-url
PANEL_USERNAME=your_username
PANEL_PASSWORD=your_password

# Database
DATABASE_URL=sqlite+aiosqlite:///bot.db

# Payment System
PAYMENT_TOKEN=your_qiwi_token
PAYMENT_WEBHOOK_URL=https://your-domain.com/webhook

# Admin Settings
ADMIN_IDS=[123456789,987654321]

# Subscription Settings
DEFAULT_SUBSCRIPTION_DAYS=30
```

5. Инициализируйте базу данных:
```bash
python init_db.py
```

## Запуск

1. Запустите бота:
```bash
python bot.py
```

2. Запустите вебхук-сервер для обработки платежей:
```bash
uvicorn webhooks:app --host 0.0.0.0 --port 8000
```

## Административные команды

- `/admin_stats` - Статистика бота
- `/admin_users` - Список пользователей
- `/admin_tariffs` - Управление тарифами
- `/admin_payments` - Список платежей

## Команды для пользователей

- `/start` - Начать работу с ботом
- `/buy` - Купить подписку
- `/status` - Проверить статус подписки
- `/help` - Показать справку

## Безопасность

- Все платежи проверяются через вебхуки
- Используется шифрование для VPN-соединений
- Реализована система ролей (админ/пользователь)
- Защита от подделки платежей

## Лицензия

MIT 