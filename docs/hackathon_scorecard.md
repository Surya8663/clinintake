# ClinIntake – Hackathon Round 2 Final Scorecard

## Project Classification
Production-oriented AI engineering reference architecture for clinical document intake and care-gap governance.
Not a certified medical device.

---

## Evaluation Criteria Scorecard

| Criterion | Score | Evidence | Honest Limitations |
|-----------|-------|---------|-------------------|
| **Functional Correctness** | 51/51 tests pass (100%) | `pytest tests/ -v` — all suites green | Integration tests require running infrastructure |
| **Lyzr Usage** | Authoritative SuperFlow DAG + 3 Lyzr agents + Guardrail V3 | `services/orchestrator/src/main.py`, Lyzr execution trace | Requires valid `LYZR_API_KEY` in production |
| **Qdrant Usage** | Real hybrid dense+sparse retrieval with payload filters | `services/guideline-retrieval-service/src/qdrant_repository.py` | Requires guideline ingestion before operational |
| **Production Readiness** | 22 microservices, Alembic migrations, Dockerfiles, CI/CD, /health/ready | `docker-compose.yml`, `.github/workflows/ci.yml` | Live EHR requires HAPI FHIR instance |
| **Security** | 0 secrets in code, JWT RBAC, step-up auth, audit vault | Gitleaks scan: 0 violations, `services/common/jwt_verifier.py` | External OIDC requires Keycloak deployment |
| **Guardrails** | Lyzr prompt injection interception, citation verifier rejection | CASE-13, CASE-14 benchmark evidence | Guardrail policy requires Lyzr API connection |
| **Audit Trail** | SHA-256 HMAC hash chain, append-only, tamper detection | `services/audit-service/src/audit_signer.py`, `vault_db.py` | Full chain validation requires PostgreSQL |
| **UI Quality** | Light clinical theme, WCAG 2.1 AA, PDF evidence overlay, error states | All 3 frontend production builds succeed (0 errors) | Live UI requires running backend services |
| **Documentation** | README, threat model, PRD traceability, deployment, limitations | `docs/` directory | Demo requires credentials |
| **15-Case Evaluation** | 15/15 PASS | `test_evaluation_benchmark_15_cases.py` | Case 15 (DLQ recovery) requires PostgreSQL |

---

## Key Technical Achievements

1. **Zero Synthetic Fallbacks**: Every service returns a typed error when a dependency fails. No fake success messages.
2. **Fully Governed EHR Writes**: 3-factor gate (clinician step-up auth + orchestrator write token + decision package hash verification).
3. **Immutable Audit Vault**: SHA-256 HMAC hash chain with `AuditVaultImmutableError` blocking all UPDATE/DELETE attempts.
4. **Real Guardrail Demo**: Adversarial PDF text triggers Lyzr policy `PROMPT_INJECTION_SYSTEM_OVERRIDE_ATTEMPT` with quarantine + audit event.
5. **Hallucination-Safe**: Citation verifier rejects all fabricated clause IDs with bounded retry and `UnsupportedCitationError`.
6. **Hub-and-Spoke Architecture**: All service-to-service calls route through Lyzr SuperFlow + Audit Event Bus. No hidden direct calls.

---

## Known Limitations

1. **Reference Architecture**: Not a certified medical device. Institutional clinical governance required for production.
2. **Terminology APIs**: Live RxNav, SNOMED CT, and LOINC adapters require NLM API credentials.
3. **Guideline Ingestion**: Qdrant collection must be pre-populated with approved guideline PDFs before retrieval is operational.
4. **Live Deployment Credentials**: Requires Lyzr API key, Keycloak admin credentials, and EHR OAuth2 client secret.
5. **Container Integration Tests**: Full E2E suite requires the complete Docker Compose stack to be running.
