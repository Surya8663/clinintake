import json
import time
from typing import Any

import httpx

from src.config import settings
from src.logger import logger


class LLMRequestError(Exception):
    """Raised when the Lyzr API returns a non-retryable 4xx client request error."""


class LLMRateLimitError(Exception):
    """Raised when the Lyzr API returns a 429 rate limit error."""


class LLMServiceError(Exception):
    """Raised when the Lyzr API returns a 5xx server error."""


class LLMTimeoutError(Exception):
    """Raised when the Lyzr API call times out."""


class LLMUnavailableError(Exception):
    """Raised when the explanation LLM or Lyzr API service is unavailable or fails."""


class LLMInvalidResponseError(Exception):
    """Raised when the LLM returns invalid JSON or unparsable structure."""


EXPLANATION_SYSTEM_PROMPT = """You are a clinical care-gap explanation engine. You receive a structured Clinical Decision Package containing:
- Temporal care gaps (screening statuses, due dates)
- Guideline passages (with source_title, version, section, clause_id, passage_text)
- Safety assessments (emergency flags, red flags)
- Drug interactions (severity, descriptions)
- Parsed care gap findings (deterministic analysis results)

Your job is to generate a clear, natural-language clinical explanation of the care gaps and clinical findings.

CRITICAL GROUNDING RULES:
1. You may ONLY cite guideline passages that are explicitly provided in the input. Do NOT invent, hallucinate, or reference any guideline, study, or recommendation not present in the input.
2. When citing a guideline, you MUST use the EXACT source_title and clause_id from the provided passages.
3. Your explanation should reference the specific care gaps found, link them to the provided guideline passages, and note any safety or drug interaction concerns.
4. Do NOT add clinical recommendations beyond what the provided data supports.

Return a JSON object with this exact schema:
{
  "explanation_summary": "Your natural language explanation here...",
  "citations_used": [
    {
      "source_title": "exact source_title from input",
      "clause_id": "exact clause_id from input"
    }
  ]
}

Return ONLY the JSON object. No markdown, no commentary."""


def call_llm_explanation(
    care_gaps_found: list[str],
    guideline_passages: list[dict[str, Any]],
    safety_assessment: dict[str, Any],
    drug_interactions: list[dict[str, Any]],
    document_id: str,
    patient_id: str = None,
    correction_instruction: str = None,
) -> dict[str, Any]:
    """
    Calls the configured Lyzr Explanation Agent with Responsible AI governance and exponential retries.
    """
    api_key = settings.lyzr_api_key
    if not api_key or api_key in ("MISSING", "INVALID_CREDENTIALS"):
        raise LLMUnavailableError("LYZR_API_KEY mandatory configuration missing or invalid. Direct LLM fallback forbidden.")

    agent_id = settings.lyzr_explanation_agent_id
    if not agent_id or agent_id in ("MISSING", "INVALID_AGENT_ID"):
        raise LLMUnavailableError("LYZR_EXPLANATION_AGENT_ID mandatory configuration missing or invalid.")

    context = {
        "document_id": document_id,
        "patient_id": patient_id or "Unknown",
        "care_gaps_found": care_gaps_found,
        "guideline_passages": guideline_passages,
        "safety_assessment": safety_assessment,
        "drug_interactions": drug_interactions,
    }

    user_prompt = f"Generate a grounded clinical care-gap explanation for this Clinical Decision Package:\n\n{json.dumps(context, indent=2)}"
    if correction_instruction:
        user_prompt += f"\n\nIMPORTANT CORRECTION: {correction_instruction}"

    logger.info(f"Calling Lyzr Explanation Agent (doc_id={document_id})...")

    base_url = settings.lyzr_base_url.rstrip("/") if settings.lyzr_base_url else "https://api.lyzr.ai"
    url = f"{base_url}/v3/agents/{agent_id}/execute"

    max_retries = settings.lyzr_max_retries
    timeout_sec = settings.lyzr_request_timeout
    last_exception = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            backoff_sec = min(2.0, 0.05 * (2 ** attempt))
            logger.info(f"Retrying Lyzr explanation agent call (attempt {attempt}/{max_retries}) after {backoff_sec}s...")
            time.sleep(backoff_sec)

        try:
            with httpx.Client(timeout=timeout_sec) as client:
                res = client.post(url, json={"prompt": user_prompt, "system_prompt": EXPLANATION_SYSTEM_PROMPT}, headers={"x-api-key": api_key, "Content-Type": "application/json"})
                if res.status_code == 200:
                    raw_data = res.json()
                    if "response" in raw_data and isinstance(raw_data["response"], dict):
                        return raw_data["response"]
                    elif "response" in raw_data and isinstance(raw_data["response"], str):
                        return json.loads(raw_data["response"])
                    elif isinstance(raw_data, dict):
                        return raw_data
                    else:
                        raise LLMInvalidResponseError("Lyzr Explanation Agent returned unexpected payload format.")

                elif res.status_code == 429:
                    last_exception = LLMRateLimitError("Lyzr Explanation Agent rate limit exceeded (HTTP 429)")
                    continue
                elif 400 <= res.status_code < 500:
                    raise LLMRequestError(f"Lyzr Explanation Agent client request error HTTP {res.status_code}: {res.text}")
                else:
                    last_exception = LLMServiceError(f"Lyzr Explanation Agent server error HTTP {res.status_code}: {res.text}")
                    continue

        except (httpx.TimeoutException, LLMTimeoutError) as e:
            logger.warning(f"Lyzr Explanation Agent request timed out: {e}")
            last_exception = LLMTimeoutError(f"Lyzr Explanation Agent timed out: {e}")
            continue
        except (httpx.ConnectError, httpx.NetworkError, httpx.RequestError) as e:
            logger.warning(f"Lyzr Explanation Agent connection error: {e}")
            last_exception = LLMUnavailableError(f"Lyzr Explanation Agent service unavailable: {e}")
            continue
        except json.JSONDecodeError as e:
            raise LLMInvalidResponseError(f"Lyzr Explanation Agent returned invalid JSON: {e}") from e

    raise last_exception or LLMUnavailableError("Lyzr Explanation Agent service call failed after retries")
