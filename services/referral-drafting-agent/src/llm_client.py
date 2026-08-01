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
    """Raised when the Lyzr / LLM referral drafting API service is unavailable or fails."""


class LLMInvalidResponseError(Exception):
    """Raised when the referral drafting response is invalid JSON or empty."""


REFERRAL_DRAFT_SYSTEM_PROMPT = """You are an expert clinical referral documentation agent.
Your task is to draft a formal, professional, natural-language clinical referral letter from a primary care clinician to a medical specialist.

RULES:
1. Grounding: You must ONLY refer to the patient ID, target specialty, urgency level, clinical reasons, and guideline evidence explicitly provided in the user prompt. Do NOT invent unsubstantiated patient symptoms, diagnoses, or guideline citations.
2. Tone & Structure: Write a standard, formal medical referral letter appropriate for clinical practice:
   - Header (Date, To: Department of [Specialty], Re: Patient ID, Urgency Level)
   - Formal opening salutation (e.g. "Dear Specialist,")
   - Clear statement of referral purpose and clinical rationale based on the provided reasons
   - Citation of clinical guideline evidence supporting the referral (referencing provided section, clause ID, and quote)
   - Professional closing and sign-off
3. Formatting: Return a JSON object with this exact schema:
{
  "referral_letter_text": "The full text of the clinical referral letter..."
}

Return ONLY the JSON object. No markdown wrapping outside JSON, no extra commentary."""


def call_llm_referral_draft(patient_id: str, target_specialty: str, urgency_level: str, clinical_reasons: list[str], evidence_items: list[dict[str, Any]], document_id: str) -> str:
    """
    Calls the configured Lyzr Referral Agent with Responsible AI governance and exponential retries.
    """
    api_key = settings.lyzr_api_key
    if not api_key or api_key in ("MISSING", "INVALID_CREDENTIALS"):
        raise LLMUnavailableError("LYZR_API_KEY mandatory configuration missing or invalid. Direct LLM fallback forbidden.")

    agent_id = settings.lyzr_referral_agent_id
    if not agent_id or agent_id in ("MISSING", "INVALID_AGENT_ID"):
        raise LLMUnavailableError("LYZR_REFERRAL_AGENT_ID mandatory configuration missing or invalid.")

    context = {
        "document_id": document_id,
        "patient_id": patient_id,
        "target_specialty": target_specialty,
        "urgency_level": urgency_level,
        "clinical_reasons": clinical_reasons,
        "grounded_evidence": evidence_items,
    }

    user_prompt = f"Draft a formal clinical referral letter for the following patient referral details:\n\n{json.dumps(context, indent=2)}"

    logger.info(f"Calling Lyzr Referral Drafting Agent (doc_id={document_id})...")

    base_url = settings.lyzr_base_url.rstrip("/") if settings.lyzr_base_url else "https://api.lyzr.ai"
    url = f"{base_url}/v3/agents/{agent_id}/execute"

    max_retries = settings.lyzr_max_retries
    timeout_sec = settings.lyzr_request_timeout
    last_exception = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            backoff_sec = min(2.0, 0.05 * (2 ** attempt))
            logger.info(f"Retrying Lyzr referral agent call (attempt {attempt}/{max_retries}) after {backoff_sec}s...")
            time.sleep(backoff_sec)

        try:
            with httpx.Client(timeout=timeout_sec) as client:
                res = client.post(url, json={"prompt": user_prompt, "system_prompt": REFERRAL_DRAFT_SYSTEM_PROMPT}, headers={"x-api-key": api_key, "Content-Type": "application/json"})
                if res.status_code == 200:
                    raw_data = res.json()
                    text = ""
                    if "response" in raw_data and isinstance(raw_data["response"], dict):
                        text = raw_data["response"].get("referral_letter_text", "")
                    elif "response" in raw_data and isinstance(raw_data["response"], str):
                        parsed = json.loads(raw_data["response"])
                        text = parsed.get("referral_letter_text", "")
                    elif isinstance(raw_data, dict):
                        text = raw_data.get("referral_letter_text", "")

                    if not text:
                        raise LLMInvalidResponseError("Lyzr Referral Agent response missing 'referral_letter_text'")

                    return text

                elif res.status_code == 429:
                    last_exception = LLMRateLimitError("Lyzr Referral Agent rate limit exceeded (HTTP 429)")
                    continue
                elif 400 <= res.status_code < 500:
                    raise LLMRequestError(f"Lyzr Referral Agent client request error HTTP {res.status_code}: {res.text}")
                else:
                    last_exception = LLMServiceError(f"Lyzr Referral Agent server error HTTP {res.status_code}: {res.text}")
                    continue

        except (httpx.TimeoutException, LLMTimeoutError) as e:
            logger.warning(f"Lyzr Referral Agent request timed out: {e}")
            last_exception = LLMTimeoutError(f"Lyzr Referral Agent timed out: {e}")
            continue
        except (httpx.ConnectError, httpx.NetworkError, httpx.RequestError) as e:
            logger.warning(f"Lyzr Referral Agent connection error: {e}")
            last_exception = LLMUnavailableError(f"Lyzr Referral Agent service unavailable: {e}")
            continue
        except json.JSONDecodeError as e:
            raise LLMInvalidResponseError(f"Lyzr Referral Agent returned invalid JSON: {e}") from e

    raise last_exception or LLMUnavailableError("Lyzr Referral Agent service call failed after retries")
