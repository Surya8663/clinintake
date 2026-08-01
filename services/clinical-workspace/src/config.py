import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "clinical-workspace"
    service_port: int = 8015
    orchestrator_url: str = os.getenv("ORCHESTRATOR_URL")
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
