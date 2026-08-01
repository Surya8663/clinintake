from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "iam-service"
    service_port: int = 8018
    keycloak_url: str = Field(...)
    keycloak_realm: str = Field(...)
    keycloak_client_id: str = Field(...)
    keycloak_client_secret: str = Field(..., description="Keycloak client secret for OIDC token verification")
    jwt_secret_key: str = Field(
        ...,
        description="HS256/RS256 signing key for JWT tokens",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # type: ignore[call-arg]
