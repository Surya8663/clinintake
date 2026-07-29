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
| audit-service | `src/config.py:8` | `hmac_secret_key` | `clinintake_kms_master_audit_secret_key_2026` |
| document-gateway | `src/config.py:10` | `jwt_secret_key` | `test-secret-key-do-not-use-in-prod-1234567890` |
| document-gateway | `src/config.py:13` | `encryption_key` | `L_U1X0b44v87gD2WvLgA_90f23JmH_fGfHjKsJ0G2k4=` |
| fhir-integration-service | `src/config.py:9` | `ehr_client_secret` | `sec_kms_ehr_write_token_2026_x99` |
| fhir-integration-service | `src/config.py:10` | `ehr_api_key` | `key_live_fhir_write_access` |
| iam-service | `src/config.py:7` | `jwt_secret_key` | `clinintake_kms_master_jwt_secret_2026_x99` |

### Hardcoded Credentials in Defaults

| Service | File | Field | Issue |
|---------|------|-------|-------|
| patient-identity-service | `src/config.py:10` | `database_url` | Contains `dev_user:dev_password` in default |
| docker-compose.yml | lines 6-8 | postgres env | `POSTGRES_USER=dev_user`, `POSTGRES_PASSWORD=dev_password` |
| docker-compose.yml | line 128 | fhir env | `EHR_CLIENT_SECRET=sec_kms_ehr_write_token_2026_x99` |
| docker-compose.yml | line 188 | audit env | `HMAC_SECRET_KEY=clinintake_kms_master_audit_secret_key_2026` |

### Missing Dockerfiles

All 20 application services in `docker-compose.yml` have `build: context:` directives
but **no Dockerfile exists** in any of the build contexts.

### Hardcoded localhost URLs

The orchestrator config has 20+ `localhost` URL defaults for inter-service communication.
These are acceptable for local dev but must be overridden in deployment.
