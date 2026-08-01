import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "extraction-agent"
    service_port: int = 8002
    safety_sub_agent_url: str = os.getenv("SAFETY_SUB_AGENT_URL", "http://localhost:8011")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.70"))
    log_level: str = "INFO"

    # LLM / Lyzr Configuration — API key via env var, never hardcoded
    lyzr_api_key: str = os.getenv("LYZR_API_KEY", "")
    llm_api_key: str = os.getenv("LYZR_API_KEY", "") or os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o")
    llm_base_url: str = os.getenv("LLM_BASE_URL", os.getenv("LYZR_BASE_URL", "https://api.lyzr.ai"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
