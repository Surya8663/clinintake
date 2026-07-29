# ClinIntake Repository Inventory

> Auto-generated during Phase 0 remediation from commit `1946bf13e3099d587de9b8f21d0bf638aba2f745`

---

## 1. Application Services (25)

| # | Service | Port | Config Class | Has Tests |
|---|---------|------|--------------|-----------|
| 1 | audit-service | 8012 | `Settings` | ✅ `test_audit_service.py` |
| 2 | base-template | — | `Settings` | ❌ |
| 3 | care-gap-explanation-agent | 8013 | `Settings` | ✅ `test_care_gap_explanation.py`, `test_llm_explanation.py` |
| 4 | clinical-rules-engine | 8008 | `Settings` | ✅ `test_clinical_rules.py` |
| 5 | clinical-workspace | 8015 | `Settings` | ✅ `test_clinical_workspace.py`, `test_rbac_enforcement.py`, `test_rejection_routing.py` |
| 6 | compliance-dashboard | 8019 | `Settings` | ✅ `test_compliance_dashboard.py` |
| 7 | document-gateway | 8001 | `GatewaySettings` | ✅ `test_gateway_security.py` |
| 8 | document-security-filter | 8002 | `SecurityFilterSettings` | ✅ `test_security_filter.py` |
| 9 | drug-interaction-service | 8010 | `Settings` | ✅ `test_drug_interactions.py` |
| 10 | extraction-agent | 8002 | `Settings` | ✅ `test_extraction_agent.py`, `test_llm_extraction.py`, `test_emergency_interrupt_lane.py` |
| 11 | failure-queue-service | 8016 | `Settings` | ✅ `test_failure_queue.py` |
| 12 | fhir-integration-service | 8006 | `Settings` | ✅ `test_fhir_integration.py` |
| 13 | guardrail-service | 8021 | `Settings` | ✅ `test_guardrails.py` |
| 14 | guideline-retrieval-service | 8011 | `Settings` | ✅ `test_guideline_retrieval.py` |
| 15 | iam-service | 8018 | `Settings` | ✅ `test_iam.py` |
| 16 | metrics-dashboard | 8020 | `Settings` | ✅ `test_metrics_dashboard.py` |
| 17 | notification-system | 8017 | `Settings` | ✅ `test_notifications.py` |
| 18 | ocr-service | 8004 | `Settings` | ✅ `test_ocr_service.py` |
| 19 | orchestrator | 8000 | `OrchestratorSettings` | ✅ `test_orchestrator.py`, `test_governance_approval_rule.py` |
| 20 | patient-identity-service | — | `PatientIdentitySettings` | ✅ `test_patient_matcher.py` |
| 21 | referral-drafting-agent | 8014 | `Settings` | ✅ `test_referral_drafting.py`, `test_llm_referral_drafting.py` |
| 22 | safety-sub-agent | 8005 | `Settings` | ✅ `test_safety_sub_agent.py` |
| 23 | schema-validator | 8003 | `Settings` | ✅ `test_schema_validator.py` |
| 24 | temporal-reasoning-engine | 8009 | `Settings` | ✅ `test_temporal_reasoning.py` |
| 25 | terminology-service | 8007 | `Settings` | ✅ `test_terminology_service.py` |

---

## 2. FastAPI Routes (All Services)

### audit-service (port 8012)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/audit/events` | `AuditRecordResponse` |
| GET | `/audit/events` | `AuditQueryResponse` |
| GET | `/audit/verify` | `IntegrityVerifyResponse` |

### care-gap-explanation-agent (port 8013)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/care-gap/explain` | `CareGapExplanationResponse` |

### clinical-rules-engine (port 8008)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/cql/evaluate` | `CQLEvaluateResponse` |

### clinical-workspace (port 8015)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| GET | `/workspace/reviews` | `List[ReviewItem]` |
| GET | `/workspace/findings/{document_id}` | `DocumentFindingsResponse` |
| PUT | `/workspace/referral/{document_id}` | — |
| POST | `/workspace/decision/{document_id}` | `DecisionSubmitResponse` |

### compliance-dashboard (port 8019)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| GET | `/compliance/audit-trail` | — |
| GET | `/compliance/verify-vault` | — |

### document-gateway (port 8001)
| Method | Path | Response Model |
|--------|------|----------------|
| POST | `/gateway/upload` | — |
| GET | `/health` | — |

### document-security-filter (port 8002)
| Method | Path | Response Model |
|--------|------|----------------|
| POST | `/filter/scan` | — |
| GET | `/health` | — |

### drug-interaction-service (port 8010)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/interactions/check` | `InteractionCheckResponse` |

### extraction-agent (port 8002)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/extract` | `ExtractResponse` |

### failure-queue-service (port 8016)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/failure/enqueue` | `FailureItemResponse` |
| POST | `/failure/retry/{document_id}` | `FailureItemResponse` |
| GET | `/failure/dlq` | `DLQSummaryResponse` |

### fhir-integration-service (port 8006)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/fhir/write-transaction` | `FHIRTransactionResponse` |

### guardrail-service (port 8021)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/guardrail/verify-grounding` | `GroundingVerificationResponse` |
| POST | `/guardrail/scrub-phi` | `PHIScrubResponse` |

### guideline-retrieval-service (port 8011)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/guidelines/retrieve` | `GuidelineQueryResponse` |

### iam-service (port 8018)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/iam/auth/login` | `TokenResponse` |
| POST | `/iam/auth/verify` | `VerifyTokenResponse` |

### metrics-dashboard (port 8020)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| GET | `/metrics/kpis` | `KPISummaryResponse` |

### notification-system (port 8017)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/notify/alert` | `AlertDispatchResponse` |

### ocr-service (port 8004)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/ocr/process` | `OCRResponse` |

### orchestrator (port 8000)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/orchestrator/documents` | — |
| GET | `/orchestrator/documents/{document_id}` | — |
| POST | `/orchestrator/documents/{document_id}/transition` | — |
| POST | `/orchestrator/documents/{document_id}/execute-step` | — |

### patient-identity-service
| Method | Path | Response Model |
|--------|------|----------------|
| POST | `/identity/resolve` | — |
| GET | `/identity/quarantine` | — |
| POST | `/identity/quarantine/{document_id}/resolve` | — |
| GET | `/health` | — |

### referral-drafting-agent (port 8014)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/referral/draft` | `ReferralDraftResponse` |

### safety-sub-agent (port 8005)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/safety/evaluate` | `SafetyEvaluateResponse` |

### schema-validator (port 8003)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/validate/schema` | `ValidateSchemaResponse` |

### temporal-reasoning-engine (port 8009)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/temporal/evaluate` | `TemporalEvaluateResponse` |

### terminology-service (port 8007)
| Method | Path | Response Model |
|--------|------|----------------|
| GET | `/health` | — |
| POST | `/terminology/map` | `TerminologyMapResponse` |

---

## 3. Frontend Applications (3)

| App | Location | Framework | Build Tool |
|-----|----------|-----------|------------|
| Clinical Workspace | `services/clinical-workspace/frontend/` | React + TypeScript | Vite |
| Compliance Dashboard | `services/compliance-dashboard/frontend/` | React + TypeScript | Vite |
| Metrics Dashboard | `services/metrics-dashboard/frontend/` | React + TypeScript | Vite |

### Frontend Component Structure

**clinical-workspace** (`src/`):
- `App.tsx`, `main.tsx`, `index.css`
- `components/`: DocumentViewer, EvidenceList, Header, ReferralEditor, ReviewQueueList, StatusNotification
- `services/`: api.ts
- `types/`: clinical.ts

**compliance-dashboard** (`src/`):
- `App.tsx`, `main.tsx`, `index.css`
- `components/`: AuditLogTable, ErrorBanner, Header, VaultIntegrityPanel
- `services/`: api.ts
- `types/`: compliance.ts

**metrics-dashboard** (`src/`):
- `App.tsx`, `main.tsx`, `index.css`
- `components/`: BenchmarkDetailPanel, ErrorBanner, Header, KpiCardGrid, TrendCharts
- `services/`: api.ts
- `types/`: metrics.ts

---

## 4. Infrastructure Services (Docker Compose)

| Service | Image | Ports | Volumes |
|---------|-------|-------|---------|
| postgres | `postgres:15-alpine` | 5432 | `postgres_data` |
| redis | `redis:7-alpine` | 6379 | `redis_data` |
| qdrant | `qdrant/qdrant:latest` | 6333, 6334 | `qdrant_data` |
| redpanda | `redpandadata/redpanda:latest` | 8081, 8082, 9092, 29092 | `redpanda_data` |
| hapi-fhir | `hapiproject/hapi:latest` | 8080 | `hapi_data` |
| clamav | `clamav/clamav:latest` | 3310 | `clamav_data` |

---

## 5. Docker Compose Application Services (20)

| Service | Build Context | Port | Dockerfile Exists |
|---------|--------------|------|--------------------|
| ocr-service | `./services/ocr-service` | 8004 | ❌ |
| extraction-agent | `./services/extraction-agent` | 8002 | ❌ |
| terminology-service | `./services/terminology-service` | 8007 | ❌ |
| schema-validator | `./services/schema-validator` | 8003 | ❌ |
| fhir-integration-service | `./services/fhir-integration-service` | 8006 | ❌ |
| clinical-rules-engine | `./services/clinical-rules-engine` | 8008 | ❌ |
| temporal-reasoning-engine | `./services/temporal-reasoning-engine` | 8009 | ❌ |
| drug-interaction-service | `./services/drug-interaction-service` | 8010 | ❌ |
| guideline-retrieval-service | `./services/guideline-retrieval-service` | 8011 | ❌ |
| safety-sub-agent | `./services/safety-sub-agent` | 8005 | ❌ |
| audit-service | `./services/audit-service` | 8012 | ❌ |
| care-gap-explanation-agent | `./services/care-gap-explanation-agent` | 8013 | ❌ |
| referral-drafting-agent | `./services/referral-drafting-agent` | 8014 | ❌ |
| clinical-workspace | `./services/clinical-workspace` | 8015 | ❌ |
| failure-queue-service | `./services/failure-queue-service` | 8016 | ❌ |
| notification-system | `./services/notification-system` | 8017 | ❌ |
| iam-service | `./services/iam-service` | 8018 | ❌ |
| compliance-dashboard | `./services/compliance-dashboard` | 8019 | ❌ |
| metrics-dashboard | `./services/metrics-dashboard` | 8020 | ❌ |
| guardrail-service | `./services/guardrail-service` | 8021 | ❌ |

---

## 6. Required Environment Variables

### Secrets (MUST be provided, no safe default)

| Variable | Service(s) | Description |
|----------|-----------|-------------|
| `HMAC_SECRET_KEY` | audit-service | HMAC-SHA256 key for audit record integrity |
| `JWT_SECRET_KEY` | iam-service, document-gateway | HS256 signing key for JWT tokens |
| `ENCRYPTION_KEY` | document-gateway | 32-byte Fernet key for document-at-rest encryption |
| `EHR_CLIENT_SECRET` | fhir-integration-service | OAuth2 client secret for EHR write access |
| `EHR_API_KEY` | fhir-integration-service | API key for FHIR server write access |
| `DATABASE_URL` | patient-identity-service | PostgreSQL connection string (contains credentials) |
| `POSTGRES_PASSWORD` | postgres (docker-compose) | PostgreSQL superuser password |
| `OPENAI_API_KEY` or `GOOGLE_API_KEY` | extraction-agent, care-gap-explanation-agent, referral-drafting-agent | LLM provider API key |

### Infrastructure URLs (have localhost defaults for dev)

| Variable | Service(s) | Default |
|----------|-----------|---------|
| `VAULT_DATABASE_URL` | audit-service | `sqlite+aiosqlite:///./audit_vault.db` |
| `KAFKA_BOOTSTRAP_SERVERS` | audit-service, orchestrator | `localhost:9092` |
| `REDIS_HOST` | fhir-integration-service, orchestrator | `localhost` |
| `REDIS_PORT` | fhir-integration-service, orchestrator | `6379` |
| `HAPI_FHIR_BASE_URL` | fhir-integration-service | `http://localhost:8080/fhir` |
| `HAPI_FHIR_URL` | schema-validator | `http://localhost:8080/fhir` |
| `QDRANT_URL` | guideline-retrieval-service | `http://localhost:6333` |
| `CLAMAV_HOST` | document-security-filter | `localhost` |
| `CLAMAV_PORT` | document-security-filter | `3310` |
| `SECURITY_FILTER_URL` | document-gateway | `http://localhost:8002/filter/scan` |
| `ORCHESTRATOR_URL` | clinical-workspace | `http://localhost:8000` |
| `AUDIT_SERVICE_URL` | compliance-dashboard, orchestrator | `http://localhost:8012` |
| `SAFETY_SUB_AGENT_URL` | extraction-agent | `http://localhost:8005` |
| `RXNAV_INTERACTION_API_URL` | drug-interaction-service | `https://rxnav.nlm.nih.gov/REST/interaction` |
| `RXNAV_API_BASE_URL` | terminology-service | `https://rxnav.nlm.nih.gov/REST` |

### Non-Secret Configuration (safe defaults)

| Variable | Service(s) | Default |
|----------|-----------|---------|
| `SERVICE_PORT` | all services | varies per service |
| `LOG_LEVEL` | all services | `INFO` |
| `CONFIDENCE_THRESHOLD` | extraction-agent, terminology-service | `0.70` / `0.65` |
| `RELEVANCE_THRESHOLD` | guideline-retrieval-service | `0.60` |
| `MAX_RETRIES` | failure-queue-service | `3` |
| `SLA_LATENCY_THRESHOLD_MS` | notification-system | `2000.0` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | iam-service | `15` |
| `AUDIT_TOPIC` | audit-service, orchestrator | `audit-events` |
| `PATIENT_MATCH_THRESHOLD` | patient-identity-service | `0.85` |
| `TESSERACT_CMD` | ocr-service | `tesseract` |
| `LLM_MODEL` | extraction-agent, care-gap-explanation-agent, referral-drafting-agent | auto-detect |
| `LLM_BASE_URL` | extraction-agent, care-gap-explanation-agent, referral-drafting-agent | auto-detect |
| `EHR_CLIENT_ID` | fhir-integration-service | `clinintake_fhir_writer_client` |

---

## 7. Databases / Message Queues / Vector Stores

| System | Technology | Used By |
|--------|-----------|---------|
| Primary DB | PostgreSQL 15 | patient-identity-service |
| Audit Vault | SQLite (aiosqlite) | audit-service |
| Cache / State | Redis 7 | orchestrator, fhir-integration-service |
| Message Bus | Redpanda (Kafka-compatible) | audit-service, orchestrator |
| Vector Store | Qdrant | guideline-retrieval-service |
| FHIR Server | HAPI FHIR (H2 embedded) | fhir-integration-service, schema-validator |
| AV Scanner | ClamAV | document-security-filter |

---

## 8. Test Suites

### Unit Test Suites (per service)

| Service | Test File(s) | Command |
|---------|-------------|---------|
| audit-service | `tests/test_audit_service.py` | `pytest services/audit-service/tests/` |
| care-gap-explanation-agent | `tests/test_care_gap_explanation.py`, `tests/test_llm_explanation.py` | `pytest services/care-gap-explanation-agent/tests/` |
| clinical-rules-engine | `tests/test_clinical_rules.py` | `pytest services/clinical-rules-engine/tests/` |
| clinical-workspace | `tests/test_clinical_workspace.py`, `tests/test_rbac_enforcement.py`, `tests/test_rejection_routing.py` | `pytest services/clinical-workspace/tests/` |
| compliance-dashboard | `tests/test_compliance_dashboard.py` | `pytest services/compliance-dashboard/tests/` |
| document-gateway | `tests/test_gateway_security.py` | `pytest services/document-gateway/tests/` |
| document-security-filter | `tests/test_security_filter.py` | `pytest services/document-security-filter/tests/` |
| drug-interaction-service | `tests/test_drug_interactions.py` | `pytest services/drug-interaction-service/tests/` |
| extraction-agent | `tests/test_extraction_agent.py`, `tests/test_llm_extraction.py`, `tests/test_emergency_interrupt_lane.py` | `pytest services/extraction-agent/tests/` |
| failure-queue-service | `tests/test_failure_queue.py` | `pytest services/failure-queue-service/tests/` |
| fhir-integration-service | `tests/test_fhir_integration.py` | `pytest services/fhir-integration-service/tests/` |
| guardrail-service | `tests/test_guardrails.py` | `pytest services/guardrail-service/tests/` |
| guideline-retrieval-service | `tests/test_guideline_retrieval.py` | `pytest services/guideline-retrieval-service/tests/` |
| iam-service | `tests/test_iam.py` | `pytest services/iam-service/tests/` |
| metrics-dashboard | `tests/test_metrics_dashboard.py` | `pytest services/metrics-dashboard/tests/` |
| notification-system | `tests/test_notifications.py` | `pytest services/notification-system/tests/` |
| ocr-service | `tests/test_ocr_service.py` | `pytest services/ocr-service/tests/` |
| orchestrator | `tests/test_orchestrator.py`, `tests/test_governance_approval_rule.py` | `pytest services/orchestrator/tests/` |
| patient-identity-service | `tests/test_patient_matcher.py` | `pytest services/patient-identity-service/tests/` |
| referral-drafting-agent | `tests/test_referral_drafting.py`, `tests/test_llm_referral_drafting.py` | `pytest services/referral-drafting-agent/tests/` |
| safety-sub-agent | `tests/test_safety_sub_agent.py` | `pytest services/safety-sub-agent/tests/` |
| schema-validator | `tests/test_schema_validator.py` | `pytest services/schema-validator/tests/` |
| temporal-reasoning-engine | `tests/test_temporal_reasoning.py` | `pytest services/temporal-reasoning-engine/tests/` |
| terminology-service | `tests/test_terminology_service.py` | `pytest services/terminology-service/tests/` |

### E2E Test Suites

| Test File | Command |
|-----------|---------|
| `tests/e2e/test_full_pipeline_e2e.py` | `pytest tests/e2e/test_full_pipeline_e2e.py` |
| `tests/e2e/test_phase18_self_critique_audit.py` | `pytest tests/e2e/test_phase18_self_critique_audit.py` |

### Frontend Build Commands

| App | Command |
|-----|---------|
| clinical-workspace | `cd services/clinical-workspace/frontend && npm install && npm run build` |
| compliance-dashboard | `cd services/compliance-dashboard/frontend && npm install && npm run build` |
| metrics-dashboard | `cd services/metrics-dashboard/frontend && npm install && npm run build` |
