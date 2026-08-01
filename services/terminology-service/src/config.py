import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "terminology-service"
    service_port: int = 8007
    rxnav_api_base_url: str = os.getenv("RXNAV_API_BASE_URL", "https://rxnav.nlm.nih.gov/REST")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
