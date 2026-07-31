from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    service_name: str = Field(default="base-service")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    
    # Example external service settings, to be configured via ENV
    # e.g., KAFKA_BOOTSTRAP_SERVERS, DATABASE_URL
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = AppSettings()
