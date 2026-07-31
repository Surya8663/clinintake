# ClinIntake Deployment Guide

## Supported Deployment Targets

| Target | Status |
|--------|--------|
| Docker Compose (local/staging) | ✅ Supported |
| Kubernetes (AWS EKS / GKE) | ✅ Supported |
| Bare metal | ⚠️ Manual config required |

---

## 1. Environment Variables

Copy `.env.example` to `.env`. **Never commit `.env` to version control.**

### Required secrets (from runtime secret vault):

| Variable | Purpose |
|---------|---------|
| `JWT_SECRET_KEY` | HS256 JWT signing key |
| `HMAC_SECRET_KEY` | Audit Vault HMAC signing key |
| `EHR_CLIENT_SECRET` | FHIR server OAuth2 client secret |
| `LYZR_API_KEY` | Lyzr platform API key |
| `POSTGRES_PASSWORD` | PostgreSQL admin password |
| `KEYCLOAK_ADMIN_PASSWORD` | Keycloak admin password |
| `QDRANT_API_KEY` | Qdrant Cloud API key (if using cloud) |
| `MINIO_SECRET_KEY` | MinIO secret access key |

### Non-secret configuration (safe to version-control):

| Variable | Default | Purpose |
|---------|---------|---------|
| `POSTGRES_USER` | `clinintake` | Postgres user |
| `POSTGRES_DB` | `clinintake_db` | Postgres database name |
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant service URL |
| `KAFKA_BOOTSTRAP_SERVERS` | `redpanda:9092` | Kafka/Redpanda broker |
| `HAPI_FHIR_BASE_URL` | `http://hapi-fhir:8080/fhir` | HAPI FHIR R4 base URL |
| `CONFIDENCE_THRESHOLD` | `0.70` | Extraction confidence minimum |
| `RELEVANCE_THRESHOLD` | `0.60` | Guideline retrieval minimum score |
| `MAX_RETRIES` | `3` | DLQ maximum retry attempts |
| `LOG_LEVEL` | `INFO` | Structured JSON log level |

---

## 2. Docker Compose (Local / Staging)

```bash
# Start full platform (all 27 services)
docker compose up -d

# Run database migrations
docker compose exec audit-service alembic upgrade head

# Provision Qdrant collection and Keycloak realm
docker compose exec audit-service python /app/scripts/provision_platform.py

# Check all service readiness
curl http://localhost:8001/health/ready  # document-gateway
curl http://localhost:8012/health/ready  # audit-service
```

---

## 3. Kubernetes Deployment (AWS EKS)

```bash
# Apply namespace and secrets (secrets injected from AWS Secrets Manager)
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets-provider.yaml

# Deploy infrastructure (postgres, redis, qdrant, redpanda)
kubectl apply -f k8s/infrastructure/

# Deploy migration job
kubectl apply -f k8s/jobs/migration-job.yaml
kubectl wait --for=condition=complete job/alembic-migration --timeout=120s

# Deploy all microservices
kubectl apply -f k8s/services/

# Check deployment health
kubectl get pods -n clinintake
kubectl rollout status deployment/orchestrator -n clinintake
```

---

## 4. Database Migration

Migrations run automatically in the `migration` init container on service start.
To run manually:

```bash
alembic upgrade head
```

---

## 5. Rollback Procedure

```bash
# Rollback to previous Alembic revision
alembic downgrade -1

# Rollback Kubernetes deployment
kubectl rollout undo deployment/orchestrator -n clinintake

# Verify health after rollback
kubectl get pods -n clinintake
```

---

## 6. Release Checklist

- [ ] All environment variables populated in secret vault
- [ ] `docker compose build --no-cache` succeeds with 0 errors
- [ ] `alembic upgrade head` runs successfully on clean database
- [ ] `python scripts/provision_platform.py` completes without errors
- [ ] All `/health/ready` endpoints return HTTP 200
- [ ] Full E2E test suite passes: `pytest tests/e2e/ -v`
- [ ] Gitleaks secret scan: 0 violations
- [ ] Trivy container scan: 0 CRITICAL/HIGH vulnerabilities
- [ ] Guideline documents ingested into Qdrant collection
- [ ] Keycloak realm configured with clinician and auditor roles
