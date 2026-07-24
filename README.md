# clinintake — Human-Governed Autonomous Clinical Intake & Care-Gap Agent

A production-oriented reference implementation for a healthcare hackathon, built phase by phase.

## Architecture

```
services/
  base-template/          # Reusable FastAPI service template
  document-gateway/       # Clinical DMZ — multipart upload + JWT auth + AES-256 storage
  document-security-filter/ # MIME validation, ClamAV malware scan, prompt-injection detection
  orchestrator/           # Central workflow hub — state machine, Redis persistence, Kafka audit bus
  patient-identity-service/ # Probabilistic patient matching + quarantine management
  extraction-agent/       # (Phase 4) OCR + clinical entity extraction
  safety-sub-agent/       # (Phase 4) Emergency safety interrupt
infrastructure/           # IaC configs
gitops/                   # GitOps manifests
```

## Local Development

### Prerequisites
- Docker & Docker Compose
- Python 3.12+

### Start Infrastructure
```bash
docker-compose up -d
```
This spins up: Postgres, Redis, Qdrant (vector DB), Redpanda (Kafka), HAPI FHIR Server, ClamAV.

### Run Tests
```bash
# Per service
python -m pytest services/orchestrator/tests
python -m pytest services/document-gateway/tests
python -m pytest services/document-security-filter/tests
python -m pytest services/patient-identity-service/tests
```

## Non-Negotiable Constraints

1. No hardcoded values — all config via environment variables
2. No mocked final components — real adapters against open-source substitutes
3. Every service has structured audit logging
4. All PRD requirements map to real working code
5. Single-hub-and-spoke architecture enforced in code structure
