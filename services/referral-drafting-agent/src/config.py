import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service_name: str = "referral-drafting-agent"
    service_port: int = 8014
    log_level: str = "INFO"

    # LLM Configuration — API key via env var, never hardcoded
    llm_api_key: str = os.getenv("OPENAI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL",
        "gemini-2.5-flash" if os.getenv("GOOGLE_API_KEY") and not os.getenv("OPENAI_API_KEY") else "gpt-4o"
    )
    llm_base_url: str = os.getenv("LLM_BASE_URL",
        "https://generativelanguage.googleapis.com/v1beta/openai/" if os.getenv("GOOGLE_API_KEY") and not os.getenv("OPENAI_API_KEY") else ""
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

