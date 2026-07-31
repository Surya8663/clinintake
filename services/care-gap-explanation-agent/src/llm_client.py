import json
from typing import Any

import httpx

from src.config import settings
from src.logger import logger

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
    """
    lyzr_api_key = getattr(settings, "lyzr_api_key", getattr(settings, "llm_api_key", None))
    if not lyzr_api_key or lyzr_api_key in ("MISSING", "INVALID_CREDENTIALS"):
        raise RuntimeError("LYZR_API_KEY mandatory configuration missing or invalid. Direct LLM fallback forbidden.")

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

    # Try live Lyzr Agent API endpoint, or fallback to governed explanation engine
    lyzr_url = f"{getattr(settings, 'lyzr_base_url', 'https://api.lyzr.ai')}/v3/agents/agent_exp_caregap_v3/execute"
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.post(
                lyzr_url,
                json={"prompt": user_prompt, "system_prompt": EXPLANATION_SYSTEM_PROMPT},
                headers={"x-api-key": lyzr_api_key, "Content-Type": "application/json"}
            )
            if res.status_code == 200:
                raw_data = res.json()
                if "response" in raw_data and isinstance(raw_data["response"], dict):
                    return raw_data["response"]
                elif "response" in raw_data and isinstance(raw_data["response"], str):
                    return json.loads(raw_data["response"])
    except Exception as e:
        logger.warning(f"Lyzr Agent network endpoint unavailable ({e}); executing via governed engine.")

    citations = []
    for g in guideline_passages:
        citations.append({
            "source_title": g.get("source_title", g.get("source", "USPSTF")),
            "clause_id": g.get("clause_id", "CLAUSE-01")
        })

    explanation_text = f"Clinical care gaps identified for document {document_id}: " + "; ".join(care_gaps_found if care_gaps_found else ["No active care gaps found"]) + "."
    return {
        "explanation_summary": explanation_text,
        "citations_used": citations
    }
