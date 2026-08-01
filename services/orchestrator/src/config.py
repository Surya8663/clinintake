from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Lyzr SuperFlow & Agent Governance Configuration (Required BaseSettings fields - min_length=1 prevents empty strings)
    lyzr_api_key: str = Field(..., min_length=1)
    lyzr_base_url: str = Field(..., min_length=1)
    lyzr_superflow_id: str = Field(..., min_length=1)
    lyzr_extraction_agent_id: str = Field(..., min_length=1)
    lyzr_explanation_agent_id: str = Field(..., min_length=1)
    lyzr_referral_agent_id: str = Field(..., min_length=1)
    lyzr_webhook_secret: str = Field(..., min_length=1)

    # Lyzr HTTP Client execution controls
    lyzr_request_timeout: float = Field(default=10.0)
    lyzr_max_retries: int = Field(default=3)

    # Real Downstream Microservice URLs (Internal local-development defaults, environment-overridable)
    document_gateway_url: str = Field(default="http://localhost:8000")
    document_security_filter_url: str = Field(default="http://localhost:8001")
    ocr_service_url: str = Field(default="http://localhost:8006")
    extraction_agent_url: str = Field(default="http://localhost:8002")
    patient_identity_service_url: str = Field(default="http://localhost:8003")
    schema_validator_url: str = Field(default="http://localhost:8004")
    terminology_service_url: str = Field(default="http://localhost:8005")
    clinical_rules_engine_url: str = Field(default="http://localhost:8007")
    temporal_reasoning_engine_url: str = Field(default="http://localhost:8008")
    drug_interaction_service_url: str = Field(default="http://localhost:8009")
    guideline_retrieval_service_url: str = Field(default="http://localhost:8010")
    safety_sub_agent_url: str = Field(default="http://localhost:8011")
    care_gap_explanation_agent_url: str = Field(default="http://localhost:8013")
    referral_drafting_agent_url: str = Field(default="http://localhost:8014")
    clinical_workspace_url: str = Field(default="http://localhost:8015")
    fhir_integration_service_url: str = Field(default="http://localhost:8016")
    failure_queue_service_url: str = Field(default="http://localhost:8017")
    notification_system_url: str = Field(default="http://localhost:8018")
    iam_service_url: str = Field(default="http://localhost:8019")
    compliance_dashboard_url: str = Field(default="http://localhost:8020")
    metrics_dashboard_url: str = Field(default="http://localhost:8021")
    guardrail_service_url: str = Field(default="http://localhost:8022")
    audit_service_url: str = Field(default="http://localhost:8023")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = OrchestratorSettings()
