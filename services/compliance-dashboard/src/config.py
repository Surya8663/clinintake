import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "compliance-dashboard"
    service_port: int = 8019
    audit_service_url: str = os.getenv("AUDIT_SERVICE_URL")
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
