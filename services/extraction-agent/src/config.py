import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service_name: str = "extraction-agent"
    service_port: int = 8002
    safety_sub_agent_url: str = os.getenv("SAFETY_SUB_AGENT_URL", "http://localhost:8005")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.70"))
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
