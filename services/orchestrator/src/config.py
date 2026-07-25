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
    
    # Downstream service URLs
    document_gateway_url: str = Field(default="http://localhost:8001")
    extraction_agent_url: str = Field(default="http://localhost:8002")
    validation_agent_url: str = Field(default="http://localhost:8003")
    ocr_service_url: str = Field(default="http://localhost:8004")
    safety_sub_agent_url: str = Field(default="http://localhost:8005")
    ehr_writer_url: str = Field(default="http://localhost:8006")
    terminology_service_url: str = Field(default="http://localhost:8007")
    clinical_rules_engine_url: str = Field(default="http://localhost:8008")
    temporal_reasoning_engine_url: str = Field(default="http://localhost:8009")
    drug_interaction_service_url: str = Field(default="http://localhost:8010")
    guideline_retrieval_service_url: str = Field(default="http://localhost:8011")
    audit_service_url: str = Field(default="http://localhost:8012")
    care_gap_agent_url: str = Field(default="http://localhost:8013")
    referral_drafting_agent_url: str = Field(default="http://localhost:8014")
    clinical_workspace_url: str = Field(default="http://localhost:8015")
    fhir_integration_service_url: str = Field(default="http://localhost:8006")
    failure_queue_service_url: str = Field(default="http://localhost:8016")
    notification_system_url: str = Field(default="http://localhost:8017")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = OrchestratorSettings()
