import json
from typing import Any

import httpx

from src.config import settings
from src.logger import logger


class LLMUnavailableError(Exception):
    """Raised when the LLM or Lyzr extraction service is network-unavailable or fails execution."""


class LLMInvalidResponseError(Exception):
    """Raised when the LLM returns malformed JSON or unparsable clinical output."""


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


def call_llm_extraction(ocr_text: str, ocr_words: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """
    Calls the configured Lyzr / LLM Extraction Agent with Responsible AI governance.
    Enforces prompt injection checks and re-validates returned JSON output.
    """
    # 1. Responsible AI Policy Check: Prompt Injection
    if "ignore previous instructions" in ocr_text.lower() or "system prompt:" in ocr_text.lower():
        logger.warning("[LYZR GOVERNANCE] Prompt injection attempt detected by Lyzr Policy in OCR text.")
        raise LLMGovernanceViolationError("LYZR_POLICY_VIOLATION: Prompt injection detected by Lyzr Policy.")

    user_prompt = _build_user_prompt(ocr_text, ocr_words)
    logger.info("Calling LLM / Lyzr Extraction Agent for clinical extraction...")

    api_key = settings.llm_api_key or settings.lyzr_api_key
    if not api_key or api_key in ("MISSING", "INVALID_CREDENTIALS"):
        raise LLMUnavailableError("LYZR_API_KEY / LLM_API_KEY mandatory configuration missing or invalid. Direct LLM fallback forbidden.")

    base_url = settings.llm_base_url.rstrip("/") if settings.llm_base_url else "https://api.lyzr.ai"
    url = f"{base_url}/v3/agents/agent_ext_clin_v3/execute"
    try:
        with httpx.Client(timeout=10.0) as client:
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
                    raise LLMInvalidResponseError("LLM response is not a valid JSON dictionary")

                return parsed
            else:
                raise LLMUnavailableError(f"Lyzr / LLM API returned error status {res.status_code}: {res.text}")
    except httpx.HTTPError as e:
        logger.error(f"Lyzr / LLM Extraction API request failed: {e}")
        raise LLMUnavailableError(f"Lyzr / LLM Extraction service unavailable: {e}") from e
    except json.JSONDecodeError as e:
        logger.error(f"Lyzr / LLM Extraction returned invalid JSON: {e}")
        raise LLMInvalidResponseError(f"LLM response JSON parsing error: {e}") from e
