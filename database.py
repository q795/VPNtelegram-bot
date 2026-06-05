"""
Файловая база данных для VPN-бота (JSON)
"""
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from config import DB_PATH, DEMO_SERVERS, DEMO_TRAFFIC_MB, DEMO_DURATION_DAYS, MAX_TRIALS_PER_USER

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_db()

    def _ensure_db(self):
        """Создаёт файл БД если не существует"""
        if not os.path.exists(self.db_path):
            self._save({
                "users": {},
                "subscriptions": {},
                "payments": {},
                "stats": {
                    "total_users": 0,
                    "total_trials": 0,
                    "total_subscriptions": 0
                }
            })

    def _load(self) -> dict:
        """Загружает данные из файла"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"users": {}, "subscriptions": {}, "payments": {}, "stats": {}}

    def _save(self, data: dict):
        """Сохраняет данные в файл"""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # === Пользователи ===

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя по ID"""
        db = self._load()
        return db["users"].get(str(user_id))

    def get_all_users(self) -> List[Dict]:
        """Получить всех пользователей"""
        db = self._load()
        return list(db["users"].values())

    def create_user(self, user_id: int, username: str = "", first_name: str = "") -> Dict:
        """Создать или обновить пользователя"""
        db = self._load()

        if str(user_id) not in db["users"]:
            db["users"][str(user_id)] = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "created_at": datetime.now().isoformat(),
                "trials_used": 0,
                "is_subscribed": False,
                "last_expired_notify": False
            }
            db["stats"]["total_users"] += 1
            self._save(db)

        return db["users"][str(user_id)]

    def increment_trial(self, user_id: int) -> bool:
        """Увеличить счётчик пробных периодов"""
        db = self._load()
        user_id_str = str(user_id)

        if user_id_str not in db["users"]:
            return False

        if db["users"][user_id_str]["trials_used"] < MAX_TRIALS_PER_USER:
            db["users"][user_id_str]["trials_used"] += 1
            db["stats"]["total_trials"] += 1
            self._save(db)
            return True

        return False

    def mark_expired_notification_sent(self, user_id: int):
        """Отметить что уведомление об истечении отправлено"""
        db = self._load()
        if str(user_id) in db["users"]:
            db["users"][str(user_id)]["last_expired_notify"] = True
            self._save(db)

    # === Подписки ===

    def create_subscription(self, user_id: int, tariff_id: str, is_trial: bool = False) -> Dict:
        """Создать подписку для пользователя"""
        db = self._load()
        sub_id = f"sub_{user_id}_{datetime.now().timestamp()}"

        # Вычисляем срок действия
        days = DEMO_DURATION_DAYS if is_trial else self._get_tariff_days(tariff_id)
        traffic_mb = DEMO_TRAFFIC_MB if is_trial else self._get_tariff_traffic(tariff_id)

        subscription = {
            "id": sub_id,
            "user_id": user_id,
            "tariff_id": tariff_id,
            "is_trial": is_trial,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=days)).isoformat(),
            "traffic_mb": traffic_mb,
            "traffic_used_mb": 0,
            "is_active": True,
            "server_id": DEMO_SERVERS[0]["id"]
        }

        db["subscriptions"][sub_id] = subscription
        db["users"][str(user_id)]["is_subscribed"] = True

        if not is_trial:
            db["stats"]["total_subscriptions"] += 1

        self._save(db)
        return subscription

    def get_subscription(self, user_id: int) -> Optional[Dict]:
        """Получить активную подписку пользователя"""
        db = self._load()

        for sub in db["subscriptions"].values():
            if sub["user_id"] == user_id and sub["is_active"]:
                expires = datetime.fromisoformat(sub["expires_at"])
                if expires > datetime.now():
                    return sub
                else:
                    sub["is_active"] = False
                    db["users"][str(user_id)]["is_subscribed"] = False
                    self._save(db)

        return None

    def get_active_subscriptions_count(self) -> int:
        """Получить количество активных подписок"""
        db = self._load()
        count = 0
        for sub in db["subscriptions"].values():
            if sub["is_active"]:
                expires = datetime.fromisoformat(sub["expires_at"])
                if expires > datetime.now():
                    count += 1
        return count

    def use_traffic(self, user_id: int, mb: float) -> bool:
        """Использовать трафик"""
        db = self._load()
        sub = self.get_subscription(user_id)

        if not sub:
            return False

        new_used = sub["traffic_used_mb"] + mb

        if new_used <= sub["traffic_mb"]:
            db["subscriptions"][sub["id"]]["traffic_used_mb"] = new_used
            self._save(db)
            return True

        return False

    def get_traffic_info(self, user_id: int) -> Dict:
        """Получить информацию о трафике"""
        sub = self.get_subscription(user_id)

        if not sub:
            return {"has_subscription": False}

        remaining = max(0, sub["traffic_mb"] - sub["traffic_used_mb"])
        used_percent = (sub["traffic_used_mb"] / sub["traffic_mb"] * 100) if sub["traffic_mb"] > 0 else 0

        return {
            "has_subscription": True,
            "total_mb": sub["traffic_mb"],
            "used_mb": sub["traffic_used_mb"],
            "remaining_mb": remaining,
            "used_percent": round(used_percent, 1),
            "expires_at": sub["expires_at"],
            "is_trial": sub["is_trial"]
        }

    # === Платежи ===

    def create_payment(self, user_id: int, tariff_id: str, amount: int) -> Dict:
        """Создать платёж (демо)"""
        db = self._load()
        payment_id = f"pay_{user_id}_{datetime.now().timestamp()}"

        payment = {
            "id": payment_id,
            "user_id": user_id,
            "tariff_id": tariff_id,
            "amount": amount,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        db["payments"][payment_id] = payment
        self._save(db)
        return payment

    def complete_payment(self, payment_id: str) -> Optional[Dict]:
        """Подтвердить платёж (демо)"""
        db = self._load()

        if payment_id in db["payments"]:
            db["payments"][payment_id]["status"] = "completed"
            self._save(db)
            return db["payments"][payment_id]

        return None

    # === Статистика ===

    def get_stats(self) -> Dict:
        """Получить базовую статистику бота"""
        db = self._load()
        return db["stats"]

    def get_full_stats(self) -> Dict:
        """Получить расширенную статистику бота"""
        db = self._load()
        now = datetime.now()

        # Базовые stats
        stats = db["stats"].copy()

        # Активные подписки
        active_count = 0
        for sub in db["subscriptions"].values():
            if sub["is_active"]:
                expires = datetime.fromisoformat(sub["expires_at"])
                if expires > now:
                    active_count += 1
        stats['active_subscriptions'] = active_count

        # Новые пользователи за периоды
        daily_new = 0
        weekly_new = 0
        monthly_new = 0

        for user in db["users"].values():
            created = datetime.fromisoformat(user["created_at"])
            days_ago = (now - created).days

            if days_ago == 0:
                daily_new += 1
            if days_ago < 7:
                weekly_new += 1
            if days_ago < 30:
                monthly_new += 1

        stats['daily_new'] = daily_new
        stats['weekly_new'] = weekly_new
        stats['monthly_new'] = monthly_new

        return stats

    # === Вспомогательные ===

    def _get_tariff_days(self, tariff_id: str) -> int:
        """Получить количество дней по тарифу"""
        from config import TARIFFS
        for t in TARIFFS:
            if t["id"] == tariff_id:
                return t["days"]
        return 30

    def _get_tariff_traffic(self, tariff_id: str) -> int:
        """Получить трафик по тарифу в МБ"""
        from config import TARIFFS
        for t in TARIFFS:
            if t["id"] == tariff_id:
                return t.get("traffic_gb", 100) * 1024
        return 100 * 1024

    def update_subscription_notification(self, user_id: int):
        """Обновить время последнего уведомления о подписке"""
        db = self._load()
        for sub in db["subscriptions"].values():
            if sub["user_id"] == user_id and sub["is_active"]:
                sub["last_notification"] = datetime.now().isoformat()
                self._save(db)
                return

# Глобальный экземпляр
db = Database()
