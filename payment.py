import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from config import settings

class PaymentSystem:
    def __init__(self):
        self.token = settings.PAYMENT_TOKEN
        self.webhook_url = settings.PAYMENT_WEBHOOK_URL
        self.base_url = "https://api.qiwi.com/partner/bill/v1"

    async def create_payment(self, amount: float, currency: str, payment_id: str) -> Dict[str, Any]:
        """Создание платежа"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "amount": {
                "currency": currency,
                "value": str(amount)
            },
            "expirationDateTime": (datetime.now() + timedelta(hours=1)).isoformat(),
            "customer": {
                "phone": None,
                "email": None,
                "account": payment_id
            },
            "comment": f"Оплата VPN-подписки {payment_id}",
            "successUrl": f"{self.webhook_url}/success",
            "failUrl": f"{self.webhook_url}/fail"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/bills",
                headers=headers,
                json=data
            ) as response:
                return await response.json()

    async def check_payment(self, payment_id: str) -> Dict[str, Any]:
        """Проверка статуса платежа"""
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/bills/{payment_id}",
                headers=headers
            ) as response:
                return await response.json()

    async def cancel_payment(self, payment_id: str) -> Dict[str, Any]:
        """Отмена платежа"""
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/bills/{payment_id}/reject",
                headers=headers
            ) as response:
                return await response.json() 