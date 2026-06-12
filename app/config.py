from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "cloud"
    state_backend: str = "firestore"

    # CleanBnB Credentials
    cleanbnb_username: str
    cleanbnb_password: str
    cleanbnb_property_id: Optional[str] = ""

    # Logic Configuration
    reservation_lookback_days: int = 30
    reservation_lookahead_days: int = 365

    # SMTP Notifications
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_to: Optional[str] = None

    # Telegram Notifications
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # GCP Project ID (for Firestore and Secret Manager)
    gcp_project: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

def get_settings() -> Settings:
    return Settings()
