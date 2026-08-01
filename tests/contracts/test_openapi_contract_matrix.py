import os
import sys
import pytest
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient

os.environ["EHR_CLIENT_SECRET"] = "test_ehr_secret_2026"
os.environ["EHR_API_KEY"] = "test_ehr_api_key_2026"
os.environ["HMAC_SECRET_KEY"] = "test_hmac_secret_2026"
os.environ["JWT_SECRET_KEY"] = "test_contract_jwt_secret_2026"
os.environ["KEYCLOAK_CLIENT_SECRET"] = "test_keycloak_client_secret_2026"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def load_app(service_name: str):
    for k in list(sys.modules.keys()):
        if k == 'src' or k.startswith('src.'):
            del sys.modules[k]

    service_dir = REPO_ROOT / "services" / service_name
    service_path = service_dir / "src" / "main.py"

    sys.path.insert(0, str(service_dir))
    spec = importlib.util.spec_from_file_location(f"{service_name.replace('-', '_')}.main", service_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.path.pop(0)
    return module.app

SERVICES_TO_TEST = [
    ("document-security-filter", "/filter/scan", "post"),
    ("ocr-service", "/ocr/process", "post"),
    ("extraction-agent", "/extract", "post"),
    ("patient-identity-service", "/identity/resolve", "post"),
    ("schema-validator", "/validate/schema", "post"),
    ("terminology-service", "/terminology/map", "post"),
    ("clinical-rules-engine", "/cql/evaluate", "post"),
    ("temporal-reasoning-engine", "/temporal/evaluate", "post"),
    ("drug-interaction-service", "/interactions/check", "post"),
    ("guideline-retrieval-service", "/guidelines/retrieve", "post"),
    ("safety-sub-agent", "/safety/evaluate", "post"),
    ("care-gap-explanation-agent", "/care-gap/explain", "post"),
    ("referral-drafting-agent", "/referral/draft", "post"),
    ("guardrail-service", "/guardrail/verify-grounding", "post"),
    ("fhir-integration-service", "/fhir/write-transaction", "post"),
    ("audit-service", "/audit/events", "post"),
    ("iam-service", "/iam/auth/login", "post"),
    ("clinical-workspace", "/workspace/reviews", "get"),
    ("compliance-dashboard", "/compliance/audit-trail", "get"),
    ("metrics-dashboard", "/metrics/kpis", "get"),
    ("orchestrator", "/orchestrator/documents", "post")
]

@pytest.mark.parametrize("service_name,route,method", SERVICES_TO_TEST)
def test_service_openapi_schema_contains_route(service_name, route, method):
    app = load_app(service_name)
    client = TestClient(app)
    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()

    paths = schema.get("paths", {})
    assert route in paths, f"Route {route} not found in OpenAPI schema for {service_name}"
    assert method in paths[route], f"Method {method.upper()} not found for route {route} in {service_name}"

    endpoint_def = paths[route][method]
    assert "responses" in endpoint_def
    assert "200" in endpoint_def["responses"] or "201" in endpoint_def["responses"] or "202" in endpoint_def["responses"]
