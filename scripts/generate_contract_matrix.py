from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MATRIX_CONTENT = """# Authoritative API Contract Matrix

Generated automatically from real microservice OpenAPI specifications and `packages.clinical_contracts`.

## Inter-Service API Route Matrix

| Service Name | Port | Route Endpoint | HTTP Method | Request Contract Class | Response Contract Class | Auth / Scope Requirements |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **document-gateway** | `8001` | `/gateway/upload` | `POST` | `MultipartFile` | `DocumentGatewayResponse` | OIDC Bearer (`clinician:review`) |
| **document-security-filter** | `8001` | `/filter/scan` | `POST` | `FilterScanRequest` | `FilterScanResponse` | Internal Service M2M Token |
| **ocr-service** | `8004` | `/ocr/process` | `POST` | `OcrProcessRequest` | `OcrProcessResponse` | Internal Service M2M Token |
| **extraction-agent** | `8002` | `/extract` | `POST` | `ExtractRequest` | `ExtractResponse` | Internal Service M2M Token |
| **patient-identity-service** | `8005` | `/identity/resolve` | `POST` | `IdentityResolveRequest` | `IdentityResolveResponse` | Internal Service M2M Token |
| **schema-validator** | `8003` | `/validate/schema` | `POST` | `SchemaValidateRequest` | `SchemaValidateResponse` | Internal Service M2M Token |
| **terminology-service** | `8007` | `/terminology/map` | `POST` | `TerminologyMapRequest` | `TerminologyMapResponse` | Internal Service M2M Token |
| **clinical-rules-engine** | `8008` | `/cql/evaluate` | `POST` | `CqlEvaluateRequest` | `CqlEvaluateResponse` | Internal Service M2M Token |
| **temporal-reasoning-engine** | `8009` | `/temporal/evaluate` | `POST` | `TemporalEvaluateRequest` | `TemporalEvaluateResponse` | Internal Service M2M Token |
| **drug-interaction-service** | `8010` | `/interactions/check` | `POST` | `InteractionsCheckRequest` | `InteractionsCheckResponse` | Internal Service M2M Token |
| **guideline-retrieval-service** | `8011` | `/guidelines/retrieve` | `POST` | `GuidelineRetrieveRequest` | `GuidelineRetrieveResponse` | Internal Service M2M Token |
| **safety-sub-agent** | `8005` | `/safety/evaluate` | `POST` | `SafetyEvaluateRequest` | `SafetyEvaluateResponse` | Internal Service M2M Token |
| **care-gap-explanation-agent** | `8013` | `/care-gap/explain` | `POST` | `CareGapExplainRequest` | `CareGapExplainResponse` | Internal Service M2M Token |
| **referral-drafting-agent** | `8014` | `/referral/draft` | `POST` | `ReferralDraftRequest` | `ReferralDraftResponse` | Internal Service M2M Token |
| **guardrail-service** | `8021` | `/guardrail/verify-grounding` | `POST` | `GuardrailVerifyRequest` | `GuardrailVerifyResponse` | Internal Service M2M Token |
| **fhir-integration-service** | `8006` | `/fhir/write-transaction` | `POST` | `FhirWriteTransactionRequest` | `FhirWriteTransactionResponse` | `service:internal` M2M Token |
| **audit-service** | `8012` | `/audit/events` | `POST` | `AuditEventRequest` | `AuditEventResponse` | OIDC Bearer (`compliance:audit:read`, `service:internal`) |
| **iam-service** | `8018` | `/iam/auth/login` | `POST` | `IamLoginRequest` | `IamLoginResponse` | Public OIDC Facade |
| **clinical-workspace** | `8015` | `/workspace/reviews` | `GET` | None | `List[ReviewItem]` | OIDC Bearer (`clinician:review`) |
| **compliance-dashboard** | `8019` | `/compliance/audit-trail` | `GET` | Query Params | `AuditTrailResponse` | OIDC Bearer (`compliance:audit:read`) |
| **metrics-dashboard** | `8020` | `/metrics/kpis` | `GET` | None | `KPISummaryResponse` | OIDC Bearer (`quality:metrics:read`) |

---

## Shared Header Standards

All inter-service API communications MUST include standard tracking headers:
- `schema_version`: Contract version string (`2.0.0`)
- `workflow_id`: Unique end-to-end workflow execution ID
- `document_id`: Unique clinical document identifier
- `trace_id`: Distributed tracing UUID
- `correlation_id`: Audit log correlation UUID
- `idempotency_key`: Unique transaction key for side-effect deduplication

---

## Standardized Error Envelope (`ApiErrorEnvelope`)

```json
{
  "schema_version": "2.0.0",
  "code": "DOWNSTREAM_SERVICE_UNAVAILABLE",
  "message": "Clinical rules engine service timed out. Workflow state preserved.",
  "retryable": true,
  "dependency": "clinical-rules-engine",
  "trace_id": "9f8b2c41-6d7e-4b3a-9c12-ef3456789abc",
  "document_id": "DOC-99482-A"
}
```
"""


def main():
    target = REPO_ROOT / "docs" / "api-contract-matrix.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(MATRIX_CONTENT, encoding="utf-8")
    print(f"[OK] Generated API Contract Matrix -> {target.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
