from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = Field(default="care-gap-explanation-agent")
    service_port: int = Field(default=8013)
    log_level: str = Field(default="INFO")

    # Lyzr Agent Configuration (Required BaseSettings fields - min_length=1 prevents empty strings)
    lyzr_api_key: str = Field(..., min_length=1)
    lyzr_base_url: str = Field(..., min_length=1)
    lyzr_explanation_agent_id: str = Field(..., min_length=1)

    # Execution controls
    lyzr_request_timeout: float = Field(default=10.0)
    lyzr_max_retries: int = Field(default=3)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
