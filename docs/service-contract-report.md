# Service Contract Report

This document outlines the verified service-to-service contracts within the ClinIntake platform.

| Caller | Target Service | HTTP Method | Configured URL | Actual Target Route | Request Schema | Response Schema | Auth | Timeout | Retry | Failure |
|--------|----------------|-------------|----------------|---------------------|----------------|-----------------|------|---------|-------|---------|
| Orchestrator | Document Gateway | POST | `DOCUMENT_GATEWAY_URL` | `/gateway/process` | `DocumentRequest` | `DocumentResponse` | Internal | 30s | 3x | Queue |
| Orchestrator | OCR Service | POST | `OCR_SERVICE_URL` | `/ocr/extract` | `OCRRequest` | `OCRResponse` | Internal | 60s | 3x | Fail |
| Orchestrator | Extraction Agent | POST | `EXTRACTION_AGENT_URL` | `/extraction/extract` | `ExtractReq` | `ExtractRes` | Internal | 60s | 3x | Fallback |
| Orchestrator | Terminology | POST | `TERMINOLOGY_SERVICE_URL` | `/terminology/normalize` | `TermReq` | `TermRes` | Internal | 10s | 3x | Fail |
| Orchestrator | FHIR Integration | POST | `FHIR_INTEGRATION_SERVICE_URL`| `/fhir/write` | `FHIRWriteReq` | `FHIRWriteRes` | Signed JWT | 30s | 3x | Alert |
| Workspace UI | Clinical Workspace| GET | `/workspace/reviews` | `/workspace/reviews`| `None` | `List[ReviewItem]` | OIDC JWT | 10s | None | 401 |
| Workspace UI | Clinical Workspace| POST | `/workspace/decision/{id}` | `/workspace/decision/{id}` | `DecisionSubmit`| `DecisionResponse` | OIDC JWT | 10s | None | 401/403 |

## Mismatches Corrected
No missing or mismatched routes were found during the final verification pass. All configurations route to valid endpoints.
