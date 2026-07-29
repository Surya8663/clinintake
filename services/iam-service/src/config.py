from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    service_name: str = "iam-service"
    service_port: int = 8018
    jwt_secret_key: str = Field(
        ...,  # Required — no default; service fails to start without it
        description="HS256 signing key for JWT tokens",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15 # Short-lived JWT requirement (15 min)
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
