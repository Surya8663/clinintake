import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service_name: str = "audit-service"
    service_port: int = 8012
    vault_database_url: str = os.getenv("VAULT_DATABASE_URL", "sqlite+aiosqlite:///./audit_vault.db")
    hmac_secret_key: str = os.getenv("HMAC_SECRET_KEY", "clinintake_kms_master_audit_secret_key_2026")
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    audit_topic: str = os.getenv("AUDIT_TOPIC", "audit-events")
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
