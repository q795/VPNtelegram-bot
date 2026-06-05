"""
Конфигурация VPN-бота
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8871473965:AAEZ7SXoLQkpn7fa4valSccwgeGISOZ4TGs")

# Путь к базе данных
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "database.json")

# Создаём директорию для данных
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# VLESS Серверы (демо-режим)
DEMO_SERVERS = [
    {
        "id": 1,
        "name": "🇩🇪 Германия",
        "host": "de1.vpn.example.com",
        "port": 443,
        "country": "de"
    },
    {
        "id": 2,
        "name": "🇳🇱 Нидерланды",
        "host": "nl1.vpn.example.com",
        "port": 443,
        "country": "nl"
    },
    {
        "id": 3,
        "name": "🇺🇸 США",
        "host": "us1.vpn.example.com",
        "port": 443,
        "country": "us"
    }
]

# Тарифы подписок (1/6/12 месяцев) - по фото пользователя
TARIFFS = [
    {
        "id": "month_1",
        "name": "📅 1 МЕСЯЦ",
        "price": 299,
        "days": 30,
        "traffic_gb": 100,
        "description": "299₽"
    },
    {
        "id": "month_6",
        "name": "📅 6 МЕСЯЦЕВ",
        "price": 1490,
        "days": 180,
        "traffic_gb": 600,
        "description": "249₽/мес",
        "monthly_price": 249
    },
    {
        "id": "month_12",
        "name": "📅 12 МЕСЯЦЕВ",
        "price": 2490,
        "days": 365,
        "traffic_gb": 1000,
        "description": "208₽/мес",
        "monthly_price": 208
    }
]

# Демо-режим: бесплатный пробный период
DEMO_TRAFFIC_MB = 500  # 500 МБ для теста
DEMO_DURATION_DAYS = 3  # 3 дня демо

# Лимиты
MAX_TRIALS_PER_USER = 1  # Один пробный период на пользователя

# ID администратора (для доступа к /admin)
ADMIN_IDS = [123456789]  # Замени на свой Telegram ID

# Ссылки для документов
USER_AGREEMENT_URL = "https://example.com/agreement"
PRIVACY_POLICY_URL = "https://example.com/privacy"

# Поддержка
SUPPORT_USERNAME = "vera_support_bot"