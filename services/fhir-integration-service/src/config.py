from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "fhir-integration-service"
    service_port: int = 8006
    # Exclusive EHR credentials (sole component with write credentials)
    ehr_client_id: str = Field(default="clinintake_fhir_writer_client")
    ehr_client_secret: str = Field(
        ...,  # Required — no default; service fails to start without it
        description="OAuth2 client secret for EHR write access",
    )
    ehr_api_key: str = Field(
        ...,  # Required — no default; service fails to start without it
        description="API key for FHIR server write access",
    )

    hapi_fhir_base_url: str = Field(default="http://localhost:8080/fhir")
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()  # type: ignore[call-arg]
