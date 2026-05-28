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
        "name": "🇩🇪 Германия (Демо)",
        "host": "demo.vpn.example.com",
        "port": 443,
        "country": "de",
        "is_demo": True
    },
    {
        "id": 2,
        "name": "🇳🇱 Нидерланды (Демо)",
        "host": "demo2.vpn.example.com",
        "port": 443,
        "country": "nl",
        "is_demo": True
    },
    {
        "id": 3,
        "name": "🇫🇷 Франция (Демо)",
        "host": "demo3.vpn.example.com",
        "port": 443,
        "country": "fr",
        "is_demo": True
    }
]

# Тарифы подписок
TARIFFS = [
    {"id": "monthly", "name": "📅 1 Месяц", "price": 299, "days": 30, "traffic_gb": 100},
    {"id": "quarterly", "name": "📅 3 Месяца", "price": 799, "days": 90, "traffic_gb": 300, "discount": 10},
    {"id": "yearly", "name": "📅 1 Год", "price": 2499, "days": 365, "traffic_gb": 1000, "discount": 30}
]

# Демо-режим: бесплатный трафик
DEMO_TRAFFIC_MB = 500  # 500 МБ для теста
DEMO_DURATION_DAYS = 3  # 3 дня демо

# Лимиты
MAX_TRIALS_PER_USER = 1  # Один пробный период на пользователя
