# ClinIntake – Threat Model

## System Classification
Production-oriented AI engineering reference architecture. Not a certified medical device.

---

## Trust Boundaries

| Boundary | Direction | Controls |
|---------|-----------|----------|
| External → Document Gateway | Inbound | TLS, JWT verification, RBAC, rate limiting |
| Gateway → Services | Internal | Service mesh mTLS, Lyzr hub-and-spoke topology |
| Services → EHR (HAPI FHIR) | Outbound | Orchestrator-issued write auth token, idempotency key |
| Services → Audit Vault | Outbound | HMAC-signed, append-only, AuditVaultImmutableError on mutation |
| Clinician → Clinical Workspace | Inbound | OIDC session, step-up auth challenge nonce |

---

## Threat Catalog

### T-01: Unauthenticated Document Ingestion
- **Threat**: Attacker submits document without valid JWT
- **Mitigation**: Document Gateway validates JWT on every request; missing/invalid token → HTTP 401
- **Evidence**: `services/document-gateway/src/auth.py` – `verify_jwt()`

### T-02: Role Escalation
- **Threat**: Authenticated user with `viewer` role attempts clinician approval action
- **Mitigation**: RBAC engine enforces `clinician` role for all approval/review endpoints
- **Evidence**: `services/iam-service/src/rbac_engine.py`

### T-03: JWT Tampering / Replay
- **Threat**: Attacker modifies JWT payload or replays captured token
- **Mitigation**: HS256 signature verification; `exp` claim enforced; step-up nonce is single-use
- **Evidence**: `services/common/jwt_verifier.py`

### T-04: Spoofed Clinician Identity
- **Threat**: Request claims a clinician `sub` it doesn't possess
- **Mitigation**: Keycloak-issued JWT `sub` verified against RBAC; step-up nonce bound to specific `sub`
- **Evidence**: `services/clinical-workspace/src/main.py` – `verify_step_up_attestation()`

### T-05: Direct FHIR Write (No Approval)
- **Threat**: Service or attacker writes to HAPI FHIR without clinician approval
- **Mitigation**: FHIR Integration Service requires orchestrator-issued write auth token (short-lived, document/patient/hash-bound)
- **Evidence**: `services/fhir-integration-service/src/main.py`

### T-06: Stale Package Approval
- **Threat**: Clinician approves an outdated decision package hash
- **Mitigation**: Decision package hash is verified at write time; mismatch → HTTP 409 Conflict
- **Evidence**: FHIR Integration Service hash verification

### T-07: Prompt Injection via PDF
- **Threat**: Adversarial PDF content instructs LLM to override safety policies
- **Mitigation**: Lyzr Responsible AI Guardrails scan extracted text; detected injection → quarantine + audit event
- **Evidence**: `services/guardrail-service/` + Lyzr Guardrail Policy V3

### T-08: Hallucinated Clinical Citation
- **Threat**: LLM fabricates a guideline citation not present in the decision package
- **Mitigation**: Citation verifier checks every cited clause ID against the input decision package; mismatches trigger bounded retry and safe error
- **Evidence**: `services/care-gap-explanation-agent/src/citation_verifier.py`

### T-09: PHI in Logs
- **Threat**: Patient data (name, DOB, diagnosis text) exposed in log aggregation systems
- **Mitigation**: PHI-safe structured JSON formatter redacts known PHI field names
- **Evidence**: `services/common/phi_safe_logger.py`

### T-10: Audit Vault Tampering
- **Threat**: Insider modifies audit records to conceal activity
- **Mitigation**: Append-only table with ORM-level `AuditVaultImmutableError`; SHA-256 HMAC hash chain; integrity verification API
- **Evidence**: `services/audit-service/src/vault_db.py`

### T-11: Object Storage URL Leakage
- **Threat**: Presigned MinIO URLs exposed in logs or API responses beyond their validity window
- **Mitigation**: Presigned URLs have short TTL; log contains only document ID and SHA-256 hash, not raw URL
- **Evidence**: `services/document-gateway/src/storage.py`

### T-12: Secret Leakage via Environment
- **Threat**: Secrets accidentally committed to repository or exposed in container env
- **Mitigation**: Gitleaks CI scan; all secrets via env vars or mounted secret files; no defaults in code
- **Evidence**: `.github/workflows/ci.yml` – `security-secret-scan` job
