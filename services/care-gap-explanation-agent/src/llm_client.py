import json
from typing import List, Dict, Any
from openai import OpenAI
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
    care_gaps_found: List[str],
    guideline_passages: List[Dict[str, Any]],
    safety_assessment: Dict[str, Any],
    drug_interactions: List[Dict[str, Any]],
    document_id: str,
    patient_id: str = None,
    correction_instruction: str = None,
) -> Dict[str, Any]:
    """
    Calls the LLM to generate a grounded clinical care-gap explanation.
    Uses the OpenAI-compatible chat completions interface.
    """
    client = OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url if settings.llm_base_url else None,
    )

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

    logger.info(f"Calling LLM ({settings.llm_model}) for care-gap explanation (doc_id={document_id})...")

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
        logger.info(f"LLM explanation response received ({len(raw_content)} chars)")
        parsed = json.loads(raw_content)
        return parsed

    except Exception as e:
        logger.error(f"LLM explanation call failed: {e}")
        raise RuntimeError(f"LLM explanation call failed: {e}") from e
