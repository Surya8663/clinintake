import json
import time
from typing import Any

import httpx
from pydantic import ValidationError

from src.config import settings
from src.logger import logger
from src.models import LyzrExtractionResponse


class LLMRequestError(Exception):
    """Raised when the Lyzr / LLM API returns a non-retryable 4xx client request error."""


class LLMRateLimitError(Exception):
    """Raised when the Lyzr / LLM API returns a 429 rate limit error."""


class LLMServiceError(Exception):
    """Raised when the Lyzr / LLM API returns a 5xx server error."""


class LLMTimeoutError(Exception):
    """Raised when the Lyzr / LLM API call times out."""


class LLMUnavailableError(Exception):
    """Raised when the Lyzr / LLM extraction service is network-unavailable or fails execution."""


class LLMInvalidResponseError(Exception):
    """Raised when the LLM returns malformed JSON, unparsable structure, or ungrounded literal quotes."""


class LLMGovernanceViolationError(Exception):
    """Raised when prompt injection or governance policy violation is detected."""


EXTRACTION_SYSTEM_PROMPT = """You are a clinical document extraction engine. You receive raw OCR text from a scanned clinical document and must extract structured clinical entities.

For EACH entity you extract, you MUST provide:
1. "value": The normalized extracted value
2. "literal_quote": The EXACT substring from the OCR text that you extracted this from — copy it character-for-character from the input. Do NOT paraphrase.
3. "confidence": Your confidence in this extraction as a float between 0.0 and 1.0. Base this on text clarity, completeness, and whether the value is unambiguous. If the text is blurry, partial, or ambiguous, use a LOW confidence (e.g., 0.2-0.5). If clear and unambiguous, use HIGH confidence (e.g., 0.85-0.99).

Return a JSON object with this exact schema:
{
  "patient_id": {"value": "...", "literal_quote": "...", "confidence": 0.0},
  "diagnoses": [
    {"name": {"value": "...", "literal_quote": "...", "confidence": 0.0},
     "icd10_code": {"value": "...", "literal_quote": "...", "confidence": 0.0}}
  ],
  "medications": [
    {"name": {"value": "...", "literal_quote": "...", "confidence": 0.0},
     "rxnorm_code": {"value": "...", "literal_quote": "...", "confidence": 0.0},
     "dosage": {"value": "...", "literal_quote": "...", "confidence": 0.0}}
  ],
  "labs": [
    {"name": {"value": "...", "literal_quote": "...", "confidence": 0.0},
     "loinc_code": {"value": "...", "literal_quote": "...", "confidence": 0.0},
     "value": {"value": "...", "literal_quote": "...", "confidence": 0.0}}
  ]
}

Rules:
- If a field category (diagnoses, medications, labs) has no entries in the text, return an empty array [].
- If a patient_id cannot be found at all, set value to "" and confidence to 0.0.
- The literal_quote must be a verbatim substring of the input OCR text. Never fabricate or paraphrase it.
- For ICD-10, RxNorm, or LOINC codes: extract them from the text if present. If a code is not stated in the text, set value to "" and confidence to 0.0.
- Return ONLY the JSON object. No markdown, no commentary."""


def _build_user_prompt(ocr_text: str, ocr_words: list[dict[str, Any]] | None = None) -> str:
    """Constructs the user prompt with OCR text and optional word-level bounding box context."""
    prompt = f"Extract all clinical entities from this OCR text:\n\n---\n{ocr_text}\n---"
    if ocr_words:
        word_summary = [
            {"text": w.get("text", ""), "bbox": w.get("bbox", {})}
            for w in ocr_words[:200]
        ]
        prompt += f"\n\nWord-level bounding box data (for spatial grounding):\n{json.dumps(word_summary, indent=None)}"
    return prompt


def _validate_extraction_schema(raw_dict: dict[str, Any], ocr_text: str) -> dict[str, Any]:
    """Validates top-level and nested structure, finite float confidence bounds, and literal quote substring matching."""
    try:
        validated_model = LyzrExtractionResponse.model_validate(raw_dict)
    except ValidationError as val_err:
        raise LLMInvalidResponseError(f"Extraction response schema validation failed: {val_err}") from val_err

    model_dict = validated_model.model_dump()

    # Verify literal_quote is an exact substring of OCR text for all supported values
    fields_to_check = [("patient_id", model_dict.get("patient_id"))]

    for diag in model_dict.get("diagnoses", []):
        fields_to_check.append(("diagnosis.name", diag.get("name")))
        fields_to_check.append(("diagnosis.icd10_code", diag.get("icd10_code")))

    for med in model_dict.get("medications", []):
        fields_to_check.append(("medication.name", med.get("name")))
        fields_to_check.append(("medication.rxnorm_code", med.get("rxnorm_code")))
        fields_to_check.append(("medication.dosage", med.get("dosage")))

    for lab in model_dict.get("labs", []):
        fields_to_check.append(("lab.name", lab.get("name")))
        fields_to_check.append(("lab.loinc_code", lab.get("loinc_code")))
        fields_to_check.append(("lab.value", lab.get("value")))

    for label, field_obj in fields_to_check:
        if not field_obj:
            continue
        val = str(field_obj.get("value", "")).strip()
        quote = str(field_obj.get("literal_quote", "")).strip()
        if val and val.lower() not in ("incomplete", "unknown", "pat-unknown"):
            # Check quote presence in OCR text
            if quote and quote not in ocr_text:
                raise LLMInvalidResponseError(f"Grounded field '{label}' literal quote '{quote}' is not an exact substring of input OCR text.")

            # Code field validation: code cannot be accepted if literal quote is absent or not in OCR
            if ("code" in label or "rxnorm" in label or "loinc" in label or "icd10" in label) and not quote:
                raise LLMInvalidResponseError(f"Code field '{label}' value '{val}' missing required verbatim literal quote.")

    return model_dict


def call_llm_extraction(ocr_text: str, ocr_words: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """
    Calls the configured Lyzr Extraction Agent with Responsible AI governance, strict schema validation,
    and exponential backoff retries for retryable network/status errors.
    """
    # 1. Responsible AI Policy Check: Prompt Injection
    if "ignore previous instructions" in ocr_text.lower() or "system prompt:" in ocr_text.lower():
        logger.warning("[LYZR GOVERNANCE] Prompt injection attempt detected by Lyzr Policy in OCR text.")
        raise LLMGovernanceViolationError("LYZR_POLICY_VIOLATION: Prompt injection detected by Lyzr Policy.")

    user_prompt = _build_user_prompt(ocr_text, ocr_words)
    logger.info("Calling Lyzr Extraction Agent for clinical extraction...")

    api_key = settings.lyzr_api_key
    if not api_key or api_key in ("MISSING", "INVALID_CREDENTIALS"):
        raise LLMUnavailableError("LYZR_API_KEY mandatory configuration missing or invalid. Direct LLM fallback forbidden.")

    agent_id = settings.lyzr_extraction_agent_id
    if not agent_id or agent_id in ("MISSING", "INVALID_AGENT_ID"):
        raise LLMUnavailableError("LYZR_EXTRACTION_AGENT_ID mandatory configuration missing or invalid.")

    base_url = settings.lyzr_base_url.rstrip("/") if settings.lyzr_base_url else "https://api.lyzr.ai"
    url = f"{base_url}/v3/agents/{agent_id}/execute"

    max_retries = settings.lyzr_max_retries
    timeout_sec = settings.lyzr_request_timeout

    last_exception = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            backoff_sec = min(2.0, 0.05 * (2 ** attempt))
            logger.info(f"Retrying Lyzr extraction agent call (attempt {attempt}/{max_retries}) after {backoff_sec}s...")
            time.sleep(backoff_sec)

        try:
            with httpx.Client(timeout=timeout_sec) as client:
                res = client.post(url, json={"prompt": user_prompt, "system_prompt": EXTRACTION_SYSTEM_PROMPT}, headers={"x-api-key": api_key, "Content-Type": "application/json"})
                if res.status_code == 200:
                    raw_data = res.json()
                    parsed = None
                    if "response" in raw_data and isinstance(raw_data["response"], dict):
                        parsed = raw_data["response"]
                    elif "response" in raw_data and isinstance(raw_data["response"], str):
                        parsed = json.loads(raw_data["response"])
                    elif isinstance(raw_data, dict):
                        parsed = raw_data

                    if not parsed or not isinstance(parsed, dict):
                        raise LLMInvalidResponseError("Lyzr response is not a valid JSON dictionary")

                    return _validate_extraction_schema(parsed, ocr_text)

                elif res.status_code == 429:
                    last_exception = LLMRateLimitError("Lyzr API rate limit exceeded (HTTP 429)")
                    continue
                elif 400 <= res.status_code < 500:
                    raise LLMRequestError(f"Lyzr API client request error HTTP {res.status_code}: {res.text}")
                else:
                    last_exception = LLMServiceError(f"Lyzr API server error HTTP {res.status_code}: {res.text}")
                    continue

        except (httpx.TimeoutException, LLMTimeoutError) as e:
            logger.warning(f"Lyzr Extraction API request timed out: {e}")
            last_exception = LLMTimeoutError(f"Lyzr Extraction API request timed out: {e}")
            continue
        except (httpx.ConnectError, httpx.NetworkError, httpx.RequestError) as e:
            logger.warning(f"Lyzr Extraction API connection error: {e}")
            last_exception = LLMUnavailableError(f"Lyzr Extraction API service unavailable: {e}")
            continue
        except json.JSONDecodeError as e:
            raise LLMInvalidResponseError(f"Lyzr Extraction response JSON parsing error: {e}") from e

    raise last_exception or LLMUnavailableError("Lyzr Extraction API service call failed after retries")
