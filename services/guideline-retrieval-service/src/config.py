import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "guideline-retrieval-service"
    service_port: int = 8011
    qdrant_url: str = os.getenv("QDRANT_URL")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_collection_name: str = os.getenv("QDRANT_COLLECTION_NAME", "clinical_guidelines")
    dense_vector_name: str = "dense"
    sparse_vector_name: str = "sparse"
    relevance_threshold: float = float(os.getenv("RELEVANCE_THRESHOLD", "0.60"))
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
