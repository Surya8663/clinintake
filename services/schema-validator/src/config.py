import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "schema-validator"
    service_port: int = 8003
    hapi_fhir_url: str = os.getenv("HAPI_FHIR_URL")
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
