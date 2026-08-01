import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorSettings(BaseSettings):
    service_name: str = Field(default="workflow-orchestrator")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    
    # Redis configuration
    redis_host: str = Field(...)
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    
    # Kafka/Redpanda configuration
    kafka_bootstrap_servers: str = Field(...)
    audit_topic: str = Field(default="audit-events")

    # Lyzr SuperFlow & Agent Governance Configuration
    lyzr_api_key: str = Field(default_factory=lambda: os.getenv("LYZR_API_KEY", "lyzr_dev_master_key_2026"))
    lyzr_base_url: str = Field(...)
    lyzr_superflow_id: str = Field(...)
    lyzr_extraction_agent_id: str = Field(...)
    lyzr_explanation_agent_id: str = Field(...)
    lyzr_referral_agent_id: str = Field(...)
    lyzr_policy_prompt_injection_id: str = Field(...)
    lyzr_policy_grounding_id: str = Field(...)
    lyzr_webhook_secret: str = Field(...)
    
    # Real Downstream Microservice URLs
    document_gateway_url: str = Field(...)
    document_security_filter_url: str = Field(...)
    ocr_service_url: str = Field(...)
    extraction_agent_url: str = Field(...)
    patient_identity_service_url: str = Field(...)
    schema_validator_url: str = Field(...)
    terminology_service_url: str = Field(...)
    clinical_rules_engine_url: str = Field(...)
    temporal_reasoning_engine_url: str = Field(...)
    drug_interaction_service_url: str = Field(...)
    guideline_retrieval_service_url: str = Field(...)
    safety_sub_agent_url: str = Field(...)
    care_gap_explanation_agent_url: str = Field(...)
    referral_drafting_agent_url: str = Field(...)
    clinical_workspace_url: str = Field(...)
    fhir_integration_service_url: str = Field(...)
    failure_queue_service_url: str = Field(...)
    notification_system_url: str = Field(...)
    iam_service_url: str = Field(...)
    compliance_dashboard_url: str = Field(...)
    metrics_dashboard_url: str = Field(...)
    guardrail_service_url: str = Field(...)
    audit_service_url: str = Field(...)
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = OrchestratorSettings()
