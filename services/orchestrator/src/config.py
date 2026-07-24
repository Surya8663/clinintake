from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class OrchestratorSettings(BaseSettings):
    service_name: str = Field(default="workflow-orchestrator")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    
    # Redis configuration
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    
    # Kafka/Redpanda configuration
    kafka_bootstrap_servers: str = Field(default="localhost:9092")
    audit_topic: str = Field(default="audit-events")
    
    # Downstream service URLs (placeholders/contracts)
    document_gateway_url: str = Field(default="http://localhost:8001")
    extraction_agent_url: str = Field(default="http://localhost:8002")
    validation_agent_url: str = Field(default="http://localhost:8003")
    reasoning_agent_url: str = Field(default="http://localhost:8004")
    safety_sub_agent_url: str = Field(default="http://localhost:8005")
    ehr_writer_url: str = Field(default="http://localhost:8006")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = OrchestratorSettings()
