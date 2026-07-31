# PRD Requirement-to-Code-to-Test Traceability Matrix

## Legend
- ✅ Implemented & tested
- ⚠️ Implemented, integration test requires live dependencies
- ❌ Not implemented (blocked by licensing/external credential)

---

## PRD Section 1: Document Ingestion & Security

| Requirement | File | Endpoint | Test |
|------------|------|---------|------|
| JWT authentication on document upload | `services/document-gateway/src/auth.py` | `POST /ingest` | `tests/e2e/test_full_pipeline_e2e.py::test_document_ingestion_requires_auth` ✅ |
| ClamAV malware scan before storage | `services/document-gateway/src/scanner.py` | `POST /ingest` | `services/document-gateway/tests/test_scanner.py` ✅ |
| MinIO object storage with SHA-256 hash | `services/document-gateway/src/storage.py` | `POST /ingest` | `tests/e2e/test_full_pipeline_e2e.py` ⚠️ |
| PHI out of all logs | `services/common/phi_safe_logger.py` | All services | `services/common/tests/test_phi_safe_logger.py` ✅ |

---

## PRD Section 2: OCR & Extraction

| Requirement | File | Endpoint | Test |
|------------|------|---------|------|
| PDF text extraction with bounding boxes | `services/ocr-service/src/main.py` | `POST /ocr/extract` | `services/ocr-service/tests/test_extractor.py` ✅ |
| Grounded field extraction with source quotes | `services/extraction-agent/src/main.py` | `POST /extract` | `services/extraction-agent/tests/test_extractor.py` ✅ |
| Low-confidence fields marked incomplete | `services/extraction-agent/src/extractor.py` | `POST /extract` | `services/extraction-agent/tests/test_extractor.py::test_low_confidence_incomplete` ✅ |

---

## PRD Section 3: Guideline Retrieval (Qdrant)

| Requirement | File | Endpoint | Test |
|------------|------|---------|------|
| Hybrid dense+sparse RRF retrieval | `services/guideline-retrieval-service/src/qdrant_repository.py` | `POST /retrieve` | `services/guideline-retrieval-service/tests/test_retrieval.py` ✅ |
| Jurisdiction and version filtering | `services/guideline-retrieval-service/src/qdrant_repository.py` | `POST /retrieve` | `services/guideline-retrieval-service/tests/test_retrieval.py::test_jurisdiction_filter` ✅ |
| INSUFFICIENT_GUIDELINE_EVIDENCE when below threshold | `services/guideline-retrieval-service/src/main.py` | `POST /retrieve` | `test_evaluation_benchmark_15_cases.py::test_case_08` ✅ |

---

## PRD Section 4: Deterministic Clinical Decisions

| Requirement | File | Endpoint | Test |
|------------|------|---------|------|
| CQL care-gap evaluation (deterministic, no LLM) | `services/clinical-rules-engine/src/main.py` | `POST /evaluate` | `services/clinical-rules-engine/tests/test_engine.py` ✅ |
| Temporal date arithmetic for overdue status | `services/temporal-reasoning-engine/src/main.py` | `POST /analyze` | `services/temporal-reasoning-engine/tests/test_temporal.py` ✅ |
| Drug interaction pharmacological check | `services/drug-interaction-service/src/main.py` | `POST /check` | `services/drug-interaction-service/tests/test_interactions.py` ✅ |

---

## PRD Section 5: Safety & Guardrails

| Requirement | File | Endpoint | Test |
|------------|------|---------|------|
| Emergency red-flag interrupt lane | `services/safety-sub-agent/src/main.py` | `POST /assess` | `test_evaluation_benchmark_15_cases.py::test_case_12` ✅ |
| Lyzr prompt injection guardrail | `services/guardrail-service/src/main.py` | `POST /screen` | `test_evaluation_benchmark_15_cases.py::test_case_13` ✅ |
| Hallucinated citation verifier | `services/care-gap-explanation-agent/src/citation_verifier.py` | Internal | `test_evaluation_benchmark_15_cases.py::test_case_14` ✅ |

---

## PRD Section 6: Clinician Review & EHR Write Authorization

| Requirement | File | Endpoint | Test |
|------------|------|---------|------|
| Step-up authentication challenge | `services/clinical-workspace/src/main.py` | `POST /review/step-up` | `tests/e2e/test_full_pipeline_e2e.py` ✅ |
| Orchestrator write auth token (short-lived, hash-bound) | `services/orchestrator/src/main.py` | `POST /authorize-ehr-write` | `tests/e2e/test_full_pipeline_e2e.py` ✅ |
| FHIR R4 bundle persistence with idempotency | `services/fhir-integration-service/src/main.py` | `POST /fhir/write` | `services/fhir-integration-service/tests/test_fhir_bundle_writer.py` ✅ |

---

## PRD Section 7: Audit & Immutability

| Requirement | File | Endpoint | Test |
|------------|------|---------|------|
| SHA-256 HMAC hash chain | `services/audit-service/src/audit_signer.py` | `POST /audit/event` | `services/audit-service/tests/test_audit_signer.py` ✅ |
| Append-only vault (DELETE/UPDATE blocked) | `services/audit-service/src/vault_db.py` | N/A (ORM-level) | `tests/e2e/test_full_pipeline_e2e.py::test_audit_immutability` ✅ |
| Hash chain integrity verification API | `services/audit-service/src/main.py` | `GET /audit/verify-integrity` | `services/audit-service/tests/test_audit_signer.py` ✅ |

---

## PRD Section 8: Persistence & Recovery

| Requirement | File | Endpoint | Test |
|------------|------|---------|------|
| Persistent workflow state (PostgreSQL) | `services/orchestrator/src/persistence.py` | Internal | `tests/e2e/test_full_pipeline_e2e.py::test_workflow_restart_recovery` ✅ |
| Dead-letter queue with manual re-drive | `services/failure-queue-service/src/dlq_engine.py` | `POST /dlq/{id}/redrive` | `test_evaluation_benchmark_15_cases.py::test_case_15` ✅ |
| /health/ready returns 503 on dependency failure | `services/common/health.py` | `GET /health/ready` | `tests/integration/test_health_checks.py` ✅ |
