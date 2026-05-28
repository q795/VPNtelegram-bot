"""
Генератор VLESS-конфигураций (демо-режим)
"""
import uuid
import base64
import json
import hashlib
from datetime import datetime
from config import DEMO_SERVERS

class VLESSGenerator:
    """Генератор VLESS-ссылок для VPN"""

    @staticmethod
    def generate_uuid() -> str:
        """Генерирует UUID для VLESS"""
        return str(uuid.uuid4())

    @staticmethod
    def generate_user_id() -> str:
        """Генерирует короткий ID пользователя"""
        return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]

    @staticmethod
    def create_vless_link(
        user_uuid: str,
        server_host: str,
        server_port: int = 443,
        flow: str = "xtls-rprx-vision",
        transport: str = "reality"
    ) -> str:
        """
        Создаёт VLESS-ссылку

        VLESS format: vless://uuid@host:port?params#remark
        """
        # Параметры
        params = []
        params.append(f"encryption=none")
        params.append(f"flow={flow}")
        params.append(f"type={transport}")
        params.append(f"security={transport}")

        if transport == "reality":
            params.append(f"fp=chrome")
            params.append(f"pbk=s")
            params.append(f"sid=")
            params.append(f"spx=%2F")
            params.append(f"alpn=h2,http/1.1")
            params.append(f"allowInsecure=0")

        query = "&".join(params)

        # Создаём ссылку
        link = f"vless://{user_uuid}@{server_host}:{server_port}?{query}#{server_host}"

        return link

    @staticmethod
    def create_demo_config(user_id: int) -> dict:
        """Создаёт демо-конфиг для пользователя"""
        user_uuid = VLESSGenerator.generate_uuid()
        server = DEMO_SERVERS[0]  # Берём первый сервер

        # Генерируем VLESS-ссылки для всех демо-серверов
        configs = []
        for srv in DEMO_SERVERS:
            link = VLESSGenerator.create_vless_link(
                user_uuid=user_uuid,
                server_host=srv["host"],
                server_port=srv["port"]
            )
            configs.append({
                "server": srv["name"],
                "link": link,
                "host": srv["host"],
                "country": srv["country"]
            })

        return {
            "user_id": user_id,
            "uuid": user_uuid,
            "configs": configs,
            "default_server": server["name"],
            "created_at": datetime.now().isoformat(),
            "is_demo": True
        }

    @staticmethod
    def create_qr_data(vless_link: str) -> str:
        """Создаёт данные для QR-кода"""
        return vless_link

    @staticmethod
    def get_subscription_url(user_id: int) -> str:
        """Создаёт URL подписки (формат Base64)"""
        # В демо-режиме возвращаем просто текстовую ссылку
        sub_data = {
            "user_id": user_id,
            "v": "2",
            "ps": "VPN Demo",
            "add": DEMO_SERVERS[0]["host"],
            "port": "443",
            "id": VLESSGenerator.generate_uuid(),
            "aid": "0",
            "net": "tcp",
            "type": "http",
            "host": "",
            "path": "",
            "tls": "reality"
        }

        # Base64 encoded subscription
        sub_json = json.dumps(sub_data)
        sub_b64 = base64.b64encode(sub_json.encode()).decode()

        return f"https://t.me/{'vless_demo_bot'}?sub={sub_b64}"


# Глобальный экземпляр
vless_gen = VLESSGenerator()
