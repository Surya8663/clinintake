import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service_name: str = "extraction-agent"
    service_port: int = 8002
    ocr_service_url: str = os.getenv("OCR_SERVICE_URL", "http://localhost:8004")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.70"))
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
