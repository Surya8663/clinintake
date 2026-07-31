# Remediation Baseline

## Baseline Commit

- **Hash**: `1946bf13e3099d587de9b8f21d0bf638aba2f745`
- **Message**: `feat(suite): add top-level ClinIntake Suite navigation bar to Metrics Dashboard Header`
- **Date**: 2026-07-28
- **Branch**: `master` (tracking `origin/main`)

## Phase 0 Objective

Establish automated quality gates and a trustworthy baseline to prevent the repository
from drifting back to:

1. Hardcoded secrets, credentials, or insecure defaults in runtime code
2. Mock, dummy, fake, or fabricated runtime data
3. Silent exception swallowing that reports success on failure
4. Missing Dockerfiles, placeholder endpoints, or dead UI buttons
5. Unvalidated dictionaries passed between services (no typed contracts)
6. PHI leakage into ordinary logs
7. Unverifiable "done" claims without raw command output

## Remediation Branch

- **Branch name**: `remediation/phase-0-baseline`
- **Created from**: `1946bf13e3099d587de9b8f21d0bf638aba2f745`

## Identified Issues at Baseline

### Hardcoded Secrets (6 instances in 5 config files)

| Service | File | Field | Hardcoded Value |
|---------|------|-------|-----------------|
| audit-service | `src/config.py:8` | `hmac_secret_key` | `<REDACTED — rotated>` |
| document-gateway | `src/config.py:10` | `jwt_secret_key` | `<REDACTED — rotated>` |
| document-gateway | `src/config.py:13` | `encryption_key` | `<REDACTED — rotated>` |
| fhir-integration-service | `src/config.py:9` | `ehr_client_secret` | `<REDACTED — rotated>` |
| fhir-integration-service | `src/config.py:10` | `ehr_api_key` | `<REDACTED — rotated>` |
| iam-service | `src/config.py:7` | `jwt_secret_key` | `<REDACTED — rotated>` |

### Hardcoded Credentials in Defaults

| Service | File | Field | Issue |
|---------|------|-------|-------|
| patient-identity-service | `src/config.py:10` | `database_url` | Contains `dev_user:<REDACTED>` in default |
| docker-compose.yml | lines 6-8 | postgres env | `POSTGRES_USER=dev_user`, `POSTGRES_PASSWORD=<REDACTED>` |
| docker-compose.yml | line 128 | fhir env | `EHR_CLIENT_SECRET=<REDACTED — rotated>` |
| docker-compose.yml | line 188 | audit env | `HMAC_SECRET_KEY=<REDACTED — rotated>` |

### Missing Dockerfiles

All 20 application services in `docker-compose.yml` have `build: context:` directives
but **no Dockerfile exists** in any of the build contexts.

### Hardcoded localhost URLs

The orchestrator config has 20+ `localhost` URL defaults for inter-service communication.
These are acceptable for local dev but must be overridden in deployment.
