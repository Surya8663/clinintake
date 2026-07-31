from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PatientIdentitySettings(BaseSettings):
    service_name: str = Field(default="patient-identity-service")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # Postgres database URL — must be provided via env var (contains credentials)
    database_url: str = Field(
        default="sqlite+aiosqlite:///:memory:",
        description="PostgreSQL connection string (postgresql+asyncpg://user:pass@host:port/db)",
    )

    # Probabilistic matching confidence threshold (0.0 to 1.0)
    patient_match_threshold: float = Field(default=0.85)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = PatientIdentitySettings()  # type: ignore[call-arg]
