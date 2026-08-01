from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "audit-service"
    service_port: int = 8012
    vault_database_url: str = Field(...)
    hmac_secret_key: str = Field(
        ...,
        description="HMAC-SHA256 key for audit record integrity signing",
    )
    kafka_bootstrap_servers: str = Field(...)
    audit_topic: str = Field(default="audit-events")
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # type: ignore[call-arg]
