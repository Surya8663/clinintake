import hashlib
import hmac
from typing import Any

import httpx

from src.config import settings
from src.logger import logger


class LyzrApiError(Exception):
    """Base exception for Lyzr API failures."""


class LyzrGovernanceViolationError(LyzrApiError):
    """Raised when a Lyzr Responsible AI policy (prompt injection, grounding) is violated."""


class LyzrTimeoutError(LyzrApiError):
    """Raised when a Lyzr request times out."""


class LyzrUnavailableError(LyzrApiError):
    """Raised when Lyzr API is network-unavailable or fails connection."""


class LyzrRequestError(LyzrApiError):
    """Raised when Lyzr API returns a 4xx client request error."""


class LyzrServiceError(LyzrApiError):
    """Raised when Lyzr API returns a 5xx server error."""


class LyzrInvalidResponseError(LyzrApiError):
    """Raised when Lyzr API returns a malformed or invalid response payload."""


# Retain alias for backward compatibility if imported elsewhere
LyzrExecutionTimeoutError = LyzrTimeoutError


class LyzrSuperFlowClient:
    def __init__(self):
        self.api_key = settings.lyzr_api_key
        self.base_url = settings.lyzr_base_url.rstrip("/") if settings.lyzr_base_url else ""
        self.superflow_id = settings.lyzr_superflow_id
        self.webhook_secret = settings.lyzr_webhook_secret

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key or self.api_key in ("MISSING", "INVALID_CREDENTIALS"):
            raise LyzrApiError("LYZR_API_KEY mandatory configuration missing or invalid.")
        return {"x-api-key": self.api_key, "Content-Type": "application/json"}

    def start_superflow_execution(self, workflow_id: str, document_id: str, input_payload: dict[str, Any]) -> dict[str, Any]:
        """
        Initiates a Lyzr SuperFlow DAG execution for the clinical workflow.
        Returns execution_id, session_id, trace_id, and node statuses from the real validated response.
        """
        if not self.api_key or self.api_key in ("MISSING", "INVALID_CREDENTIALS"):
            raise LyzrApiError("LYZR_API_KEY mandatory configuration missing or invalid.")

        # Check for prompt injection in untrusted input text
        doc_text = str(input_payload.get("raw_text", "") or input_payload.get("ocr_text", ""))
        if "ignore previous instructions" in doc_text.lower() or "system prompt:" in doc_text.lower():
            logger.warning(f"[LYZR GOVERNANCE] Prompt injection attempt detected in document {document_id}")
            raise LyzrGovernanceViolationError("LYZR_POLICY_VIOLATION: Prompt injection pattern detected by Lyzr Responsible AI Policy.")

        request_body = {
            "workflow_id": workflow_id or self.superflow_id,
            "document_id": document_id,
            "input_payload": input_payload,
        }

        url = f"{self.base_url}/v3/superflow/{self.superflow_id}/execute"
        logger.info(f"Starting Lyzr SuperFlow execution for document={document_id}")

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=request_body, headers=self._get_headers())
                if res.status_code == 200:
                    try:
                        data = res.json()
                    except Exception as json_err:
                        raise LyzrInvalidResponseError("Lyzr returned malformed JSON response") from json_err

                    if not isinstance(data, dict) or "execution_id" not in data:
                        raise LyzrInvalidResponseError("Lyzr response missing required 'execution_id' field")

                    return {
                        "execution_id": data["execution_id"],
                        "session_id": data.get("session_id", ""),
                        "trace_id": data.get("trace_id", ""),
                        "status": data.get("status", "RUNNING"),
                        "nodes": data.get("nodes", {}),
                    }
                elif 400 <= res.status_code < 500:
                    raise LyzrRequestError(f"Lyzr request rejected with HTTP {res.status_code}: {res.text}")
                else:
                    raise LyzrServiceError(f"Lyzr service returned server error HTTP {res.status_code}: {res.text}")

        except httpx.TimeoutException as e:
            logger.error(f"Lyzr API request timed out: {e}")
            raise LyzrTimeoutError(f"Lyzr API execution timed out: {e}") from e
        except (httpx.ConnectError, httpx.NetworkError, httpx.RequestError) as e:
            logger.error(f"Lyzr API connection error: {e}")
            raise LyzrUnavailableError(f"Lyzr API service unavailable: {e}") from e

    def execute_agent(self, agent_id: str, input_payload: dict[str, Any]) -> dict[str, Any]:
        """
        Executes a specialized Lyzr Agent with Responsible AI policy validation.
        """
        if not self.api_key or self.api_key in ("MISSING", "INVALID_CREDENTIALS"):
            raise LyzrApiError("LYZR_API_KEY mandatory configuration missing or invalid.")

        # Check prompt injection policy
        prompt_text = str(input_payload.get("prompt", "") or input_payload.get("ocr_text", "") or "")
        if "ignore previous instructions" in prompt_text.lower() or "system prompt:" in prompt_text.lower():
            raise LyzrGovernanceViolationError("LYZR_POLICY_VIOLATION: Prompt injection detected by Lyzr Policy.")

        url = f"{self.base_url}/v3/agents/{agent_id}/execute"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=input_payload, headers=self._get_headers())
                if res.status_code == 200:
                    try:
                        return res.json()
                    except Exception as json_err:
                        raise LyzrInvalidResponseError(f"Lyzr Agent '{agent_id}' returned malformed JSON response") from json_err
                elif 400 <= res.status_code < 500:
                    raise LyzrRequestError(f"Lyzr Agent '{agent_id}' request rejected with HTTP {res.status_code}: {res.text}")
                else:
                    raise LyzrServiceError(f"Lyzr Agent '{agent_id}' service returned HTTP {res.status_code}: {res.text}")

        except httpx.TimeoutException as e:
            logger.error(f"Lyzr Agent '{agent_id}' request timed out: {e}")
            raise LyzrTimeoutError(f"Lyzr Agent '{agent_id}' timed out: {e}") from e
        except (httpx.ConnectError, httpx.NetworkError, httpx.RequestError) as e:
            logger.error(f"Lyzr Agent '{agent_id}' connection error: {e}")
            raise LyzrUnavailableError(f"Lyzr Agent '{agent_id}' service unavailable: {e}") from e

    def verify_webhook_signature(self, body_bytes: bytes, signature_header: str) -> bool:
        """Verifies HMAC-SHA256 webhook callback signatures from Lyzr SuperFlow."""
        if not signature_header or not self.webhook_secret:
            return False
        expected_sig = hmac.new(self.webhook_secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, signature_header)


lyzr_client = LyzrSuperFlowClient()
