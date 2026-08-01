import os

backend_services = [
    "ocr-service",
    "extraction-agent",
    "terminology-service",
    "schema-validator",
    "fhir-integration-service",
    "clinical-rules-engine",
    "temporal-reasoning-engine",
    "drug-interaction-service",
    "guideline-retrieval-service",
    "safety-sub-agent",
    "audit-service",
    "care-gap-explanation-agent",
    "referral-drafting-agent",
    "failure-queue-service",
    "notification-system",
    "iam-service",
    "guardrail-service",
]

frontend_services = ["clinical-workspace", "compliance-dashboard", "metrics-dashboard"]

backend_dockerfile = """FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
ENV PYTHONPATH=/app

# Default port is 8000 but compose overrides it to $SERVICE_PORT using command
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}"]
"""

frontend_dockerfile = """# Build frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Build backend
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
ENV PYTHONPATH=/app
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}"]
"""

for service in backend_services:
    with open(os.path.join("services", service, "Dockerfile"), "w") as f:
        f.write(backend_dockerfile)

for service in frontend_services:
    with open(os.path.join("services", service, "Dockerfile"), "w") as f:
        f.write(frontend_dockerfile)

print("Dockerfiles created.")
