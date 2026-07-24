from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class GatewaySettings(BaseSettings):
    service_name: str = Field(default="document-gateway")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    
    # HS256 HMAC-SHA256 signature key for JWT checking
    jwt_secret_key: str = Field(default="test-secret-key-do-not-use-in-prod-1234567890")
    
    # 32 url-safe base64-encoded bytes for AES-256 (Fernet)
    encryption_key: str = Field(default="L_U1X0b44v87gD2WvLgA_90f23JmH_fGfHjKsJ0G2k4=")
    
    # Encrypted Clinical Doc Store target directory
    storage_dir: str = Field(default="./clinical-doc-store")
    
    # Downstream Filter service configuration
    security_filter_url: str = Field(default="http://localhost:8002/filter/scan")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = GatewaySettings()
