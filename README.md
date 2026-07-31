# ClinIntake – Clinical Document AI Platform
## Production-Oriented Reference Architecture

> **⚠️ Reference Implementation Notice**
> ClinIntake is an **enterprise-grade AI engineering reference architecture** for clinical document intake, care-gap detection, and evidence-grounded clinician review. It is **not a certified production medical device** and must be deployed alongside institutional EHR governance, security, and compliance protocols.

---

## Architecture Overview

ClinIntake implements a **hub-and-spoke microservice topology** orchestrated by **Lyzr SuperFlow**, backed by:

| Layer | Technology |
|-------|-----------|
| Workflow Orchestration | Lyzr SuperFlow + Lyzr Responsible AI Guardrails |
| Vector Knowledge Store | Qdrant (hybrid dense + sparse RRF retrieval) |
| Identity & Authorization | Keycloak OIDC + RBAC + Step-Up Auth |
| Audit Vault | PostgreSQL + SHA-256 HMAC hash chain (append-only) |
| Message Bus | Redpanda (Kafka-compatible) |
| EHR Integration | HAPI FHIR R4 |
| Object Storage | MinIO (S3-compatible) |
| Malware Scanning | ClamAV |
| Database | PostgreSQL 15 with Alembic migrations |
| Caching | Redis (ephemeral only; no durable clinical state) |

---

## Full Pipeline Flow

```
Document Upload
  → Document Gateway (JWT auth + RBAC)
  → ClamAV Malware Scan
  → MinIO Object Storage
  → Lyzr SuperFlow Orchestration
    → OCR Service (PyPDF + Tesseract)
    → Extraction Agent (LLM-grounded, source-quoted)
    → Patient Identity Service
    → Terminology Service (SNOMED/LOINC mapping)
    → Schema Validator (Pydantic contracts)
    → Clinical Rules Engine (deterministic CQL)
    → Temporal Reasoning Engine (date arithmetic)
    → Drug Interaction Service (RxNorm pharmacological check)
    → Guideline Retrieval Service (Qdrant hybrid RAG)
    → Safety Sub-Agent (Emergency interrupt lane)
    → Care-Gap Explanation Agent (Lyzr LLM, constrained to decision package)
    → Guardrail Service (Lyzr Prompt Injection Protection)
    → Referral Drafting Agent (LLM-grounded draft)
  → Clinical Workspace (Step-Up Auth → Clinician Review)
  → FHIR Integration Service (authorized FHIR R4 transaction)
  → Audit Service (immutable event vault)
  → Notification System
  → Metrics / Compliance Dashboard
```

---

## Non-Negotiable Governance Rules

1. **No hardcoded secrets** – all credentials via validated env vars or runtime mounts
2. **No synthetic fallbacks** – fail honestly with typed errors; preserve state for retry
3. **No unauthenticated EHR writes** – every write requires clinician step-up + orchestrator authorization token
4. **No raw PHI in logs** – logs contain IDs, hashes, states, durations, and error codes only
5. **No direct service-to-service calls** – all communication through Lyzr hub-and-spoke topology
6. **No LLM clinical decisions** – LLMs extract, explain, and draft; deterministic services decide

---

## Mandatory Prerequisites for Deployment

| Credential | Source |
|-----------|--------|
| `KEYCLOAK_ADMIN_PASSWORD` | Institutional IdP secret vault |
| `JWT_SECRET_KEY` | Runtime secret mount |
| `HMAC_SECRET_KEY` | Runtime secret mount (Audit Vault HMAC) |
| `EHR_CLIENT_SECRET` | EHR vendor OAuth2 credentials |
| `LYZR_API_KEY` | Lyzr platform API key |
| `QDRANT_API_KEY` | Qdrant Cloud API key |

---

## Quick Start (Local Development)

```bash
# 1. Copy environment template
cp .env.example .env
# 2. Fill in required secrets in .env (never commit .env)

# 3. Start full platform stack
docker compose --profile dev up -d

# 4. Run database migrations
docker compose exec audit-service alembic upgrade head

# 5. Provision Keycloak realm + Qdrant collection
python scripts/provision_platform.py

# 6. Run end-to-end test suite
pytest tests/e2e/ -v
```

---

## Deployment

See [`docs/deployment.md`](docs/deployment.md) for Kubernetes manifests, Helm values, and managed secret injection documentation.

---

## Known Limitations

1. **Reference Architecture**: Not a certified production medical device. Institutional governance required.
2. **Terminology API Licensing**: Requires valid NLM API keys for live RxNav, SNOMED CT, and LOINC endpoints.
3. **EHR Connectivity**: HAPI FHIR R4 endpoint required; offline outages trigger honest failure queue escalation.
4. **Guideline Ingestion**: Approved clinical guideline documents must be ingested separately by authorized administrators before guideline retrieval is functional.

---

## License

Apache 2.0 – See [LICENSE](LICENSE)
