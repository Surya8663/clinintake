from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class PatientIdentitySettings(BaseSettings):
    service_name: str = Field(default="patient-identity-service")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    
    # Postgres database URL (can be overridden to sqlite+aiosqlite:///:memory: for unit tests)
    database_url: str = Field(default="postgresql+asyncpg://dev_user:dev_password@localhost:5432/healthcare_db")
    
    # Probabilistic matching confidence threshold (0.0 to 1.0)
    patient_match_threshold: float = Field(default=0.85)
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = PatientIdentitySettings()
