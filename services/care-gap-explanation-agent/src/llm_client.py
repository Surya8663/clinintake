import json
from typing import Any

import httpx

from src.config import settings
from src.logger import logger


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
    Calls the Lyzr Care Gap Explanation Agent (agent_exp_caregap_v3) with Responsible AI governance.
    Raises typed LLMUnavailableError if the external endpoint fails or credentials are missing.
    """
    api_key = settings.llm_api_key or settings.lyzr_api_key
    if not api_key or api_key in ("MISSING", "INVALID_CREDENTIALS"):
        raise LLMUnavailableError("LYZR_API_KEY / LLM_API_KEY mandatory configuration missing or invalid. Direct LLM fallback forbidden.")

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

    base_url = settings.llm_base_url.rstrip("/") if settings.llm_base_url else "https://api.lyzr.ai"
    url = f"{base_url}/v3/agents/agent_exp_caregap_v3/execute"
    try:
        with httpx.Client(timeout=10.0) as client:
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
            else:
                raise LLMUnavailableError(f"Lyzr Explanation Agent returned HTTP {res.status_code}: {res.text}")
    except httpx.HTTPError as e:
        logger.error(f"Lyzr Explanation Agent request failed: {e}")
        raise LLMUnavailableError(f"Lyzr Explanation Agent service unavailable: {e}") from e
    except json.JSONDecodeError as e:
        logger.error(f"Lyzr Explanation Agent returned invalid JSON: {e}")
        raise LLMInvalidResponseError(f"LLM explanation JSON parse failure: {e}") from e
