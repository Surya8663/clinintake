import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service_name: str = "fhir-integration-service"
    service_port: int = 8006
    # Exclusive EHR credentials (sole component with write credentials)
    ehr_client_id: str = os.getenv("EHR_CLIENT_ID", "clinintake_fhir_writer_client")
    ehr_client_secret: str = os.getenv("EHR_CLIENT_SECRET", "sec_kms_ehr_write_token_2026_x99")
    ehr_api_key: str = os.getenv("EHR_API_KEY", "key_live_fhir_write_access")
    
    hapi_fhir_base_url: str = os.getenv("HAPI_FHIR_BASE_URL", "http://localhost:8080/fhir")
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
