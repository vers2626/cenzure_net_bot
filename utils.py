import uuid
import base64
from typing import Optional
from datetime import datetime, timedelta

def generate_vpn_config(
    server: str,
    port: int,
    email: str,
    protocol: str = "vless",
    network: str = "tcp",
    security: str = "none"
) -> str:
    """Генерация конфигурации VPN"""
    if protocol == "vless":
        config = f"vless://{email}@{server}:{port}?encryption=none&security={security}&type={network}"
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")
    
    return config

def generate_qr_code(config: str) -> str:
    """Генерация QR-кода для конфигурации"""
    # TODO: Реализовать генерацию QR-кода
    return config

def format_traffic(bytes_value: int) -> str:
    """Форматирование трафика в читаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f}{unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f}PB"

def calculate_expiry_date(days: int) -> datetime:
    """Расчет даты окончания подписки"""
    return datetime.utcnow() + timedelta(days=days)

def is_subscription_active(end_date: datetime) -> bool:
    """Проверка активности подписки"""
    return datetime.utcnow() < end_date

def generate_payment_id() -> str:
    """Генерация уникального ID платежа"""
    return f"vpn_{uuid.uuid4().hex[:8]}"

def format_subscription_info(
    start_date: datetime,
    end_date: datetime,
    up_traffic: int,
    down_traffic: int
) -> str:
    """Форматирование информации о подписке"""
    return (
        f"📅 Начало: {start_date.strftime('%d.%m.%Y')}\n"
        f"⏰ Окончание: {end_date.strftime('%d.%m.%Y')}\n"
        f"⬆️ Отправлено: {format_traffic(up_traffic)}\n"
        f"⬇️ Получено: {format_traffic(down_traffic)}"
    ) 