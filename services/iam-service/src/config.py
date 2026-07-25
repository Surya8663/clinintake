import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service_name: str = "iam-service"
    service_port: int = 8018
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "clinintake_kms_master_jwt_secret_2026_x99")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15 # Short-lived JWT requirement (15 min)
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
