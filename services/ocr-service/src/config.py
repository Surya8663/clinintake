import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "ocr-service"
    service_port: int = 8004
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "tesseract")
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
