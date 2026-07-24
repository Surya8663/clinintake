from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class FilterSettings(BaseSettings):
    service_name: str = Field(default="document-security-filter")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    
    # ClamAV settings
    clamav_host: str = Field(default="localhost")
    clamav_port: int = Field(default=3310)
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = FilterSettings()
