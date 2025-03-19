from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Telegram Bot settings
    BOT_TOKEN: str
    
    # 3x-ui API settings
    PANEL_URL: str
    PANEL_USERNAME: str
    PANEL_PASSWORD: str
    
    # Database settings
    DATABASE_URL: str = "sqlite+aiosqlite:///bot.db"
    
    # Payment system settings
    PAYMENT_TOKEN: str
    PAYMENT_WEBHOOK_URL: str
    
    # Admin settings
    ADMIN_IDS: list[int]
    
    # Subscription settings
    DEFAULT_SUBSCRIPTION_DAYS: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings() 