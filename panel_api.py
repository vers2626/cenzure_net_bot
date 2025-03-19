import aiohttp
from typing import Optional, Dict, Any
from config import settings

class PanelAPI:
    def __init__(self):
        self.base_url = settings.PANEL_URL
        self.username = settings.PANEL_USERNAME
        self.password = settings.PANEL_PASSWORD
        self._token = None

    async def _get_token(self) -> str:
        """Получение токена авторизации"""
        if self._token:
            return self._token

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/auth/login",
                json={
                    "username": self.username,
                    "password": self.password
                }
            ) as response:
                data = await response.json()
                if data.get("success"):
                    self._token = data["token"]
                    return self._token
                raise Exception("Failed to get token")

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнение запроса к API"""
        token = await self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                **kwargs
            ) as response:
                return await response.json()

    async def create_inbound(self, email: str, days: int) -> Dict[str, Any]:
        """Создание нового VPN-ключа"""
        return await self._make_request(
            "POST",
            "/api/inbounds",
            json={
                "up": 0,
                "down": 0,
                "total": 0,
                "remark": email,
                "enable": True,
                "expiryTime": days * 24 * 60 * 60 * 1000,  # Конвертация дней в миллисекунды
                "listen": "",
                "port": 0,
                "protocol": "vless",
                "settings": {
                    "clients": [
                        {
                            "id": email,
                            "flow": ""
                        }
                    ],
                    "decryption": "none",
                    "fallbacks": []
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "none",
                    "tcpSettings": {
                        "header": {
                            "type": "none"
                        }
                    }
                }
            }
        )

    async def get_inbound(self, inbound_id: int) -> Dict[str, Any]:
        """Получение информации о VPN-ключе"""
        return await self._make_request("GET", f"/api/inbounds/{inbound_id}")

    async def delete_inbound(self, inbound_id: int) -> Dict[str, Any]:
        """Удаление VPN-ключа"""
        return await self._make_request("DELETE", f"/api/inbounds/{inbound_id}")

    async def update_inbound(self, inbound_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление VPN-ключа"""
        return await self._make_request(
            "PUT",
            f"/api/inbounds/{inbound_id}",
            json=data
        ) 