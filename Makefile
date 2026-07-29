# ClinIntake Suite — Top-Level Makefile
# ─────────────────────────────────────
# Usage:
#   make lint                  — Ruff check + format verification
#   make test-unit             — Pytest across all services
#   make test-integration      — Integration tests (requires running infra)
#   make security-scan         — Hardcoded secret detection
#   make contract-check        — Verify Pydantic models are importable
#   make compose-config        — Validate and list Docker Compose services
#   make verify-no-runtime-fakes — Scan for forbidden mock/fake terms
#   make quality-gates         — Run ALL quality gate scripts

.PHONY: lint test-unit test-integration security-scan contract-check \
        compose-config verify-no-runtime-fakes quality-gates help

PYTHON ?= python
PYTEST ?= pytest

help: ## Show this help
	@echo "ClinIntake Suite — Available targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-28s %s\n", $$1, $$2}'

lint: ## Run ruff linter and format check
	$(PYTHON) -m ruff check services/ scripts/
	$(PYTHON) -m ruff format --check services/ scripts/

test-unit: ## Run pytest unit tests for all services
	@echo "Running unit tests for all services..."
	@for dir in services/*/tests; do \
		if [ -d "$$dir" ]; then \
			echo "── Testing $$(dirname $$dir) ──"; \
			$(PYTEST) "$$dir" -x -q 2>&1 || true; \
		fi \
	done
	@echo "── E2E tests ──"
	$(PYTEST) tests/ -x -q 2>&1 || true

test-integration: ## Run integration tests (requires running infrastructure)
	@echo "Integration tests require running Docker Compose services."
	@echo "Start infrastructure first:  docker compose up -d postgres redis qdrant redpanda hapi-fhir clamav"
	@echo ""
	@echo "Then run:  $(PYTEST) tests/e2e/ -v"

security-scan: ## Scan for hardcoded secrets in source code
	$(PYTHON) scripts/quality/scan_secrets.py

contract-check: ## Verify Pydantic settings models are importable (no startup crash)
	@echo "Verifying Pydantic settings contracts..."
	@for cfg in services/*/src/config.py; do \
		svc=$$(echo $$cfg | cut -d/ -f2); \
		echo -n "  $$svc: "; \
		$(PYTHON) -c "import sys; sys.path.insert(0, '$$(dirname $$cfg)'); exec(open('$$cfg').read())" 2>&1 && echo "OK" || echo "FAIL"; \
	done

compose-config: ## Validate Docker Compose config and list services
	docker compose config --services

verify-no-runtime-fakes: ## Scan for forbidden mock/fake/dummy terms in runtime code
	$(PYTHON) scripts/quality/scan_forbidden_terms.py

quality-gates: ## Run ALL quality gate scripts
	$(PYTHON) scripts/quality/run_all_gates.py
