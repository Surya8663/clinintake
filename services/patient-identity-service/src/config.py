from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PatientIdentitySettings(BaseSettings):
    service_name: str = Field(...)
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # Postgres database URL — must be provided via env var (contains credentials)
    database_url: str = Field(
        ...,
        description="Database connection URL",
    )

    # Probabilistic matching confidence threshold (0.0 to 1.0)
    patient_match_threshold: float = Field(default=0.85)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = PatientIdentitySettings()  # type: ignore[call-arg]
