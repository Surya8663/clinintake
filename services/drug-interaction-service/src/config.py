import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "drug-interaction-service"
    service_port: int = 8010
    rxnav_interaction_api_url: str = os.getenv("RXNAV_INTERACTION_API_URL", "https://rxnav.nlm.nih.gov/REST/interaction")
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
