import json
from typing import List, Dict, Any
from openai import OpenAI
from src.config import settings
from src.logger import logger

REFERRAL_DRAFT_SYSTEM_PROMPT = """You are an expert clinical referral documentation agent.
Your task is to draft a formal, professional, natural-language clinical referral letter from a primary care clinician to a medical specialist.

RULES:
1. Grounding: You must ONLY refer to the patient ID, target specialty, urgency level, clinical reasons, and guideline evidence explicitly provided in the user prompt. Do NOT invent fake patient symptoms, diagnoses, or guideline citations.
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

def call_llm_referral_draft(
    patient_id: str,
    target_specialty: str,
    urgency_level: str,
    clinical_reasons: List[str],
    evidence_items: List[Dict[str, Any]],
    document_id: str
) -> str:
    """
    Calls the configured LLM to draft a natural-language clinical referral letter.
    Uses the OpenAI-compatible chat completions interface.
    """
    client = OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url if settings.llm_base_url else None,
    )

    context = {
        "document_id": document_id,
        "patient_id": patient_id,
        "target_specialty": target_specialty,
        "urgency_level": urgency_level,
        "clinical_reasons": clinical_reasons,
        "grounded_evidence": evidence_items,
    }

    user_prompt = (
        f"Draft a formal clinical referral letter for the following patient referral details:\n\n"
        f"{json.dumps(context, indent=2)}"
    )

    logger.info(f"Calling LLM ({settings.llm_model}) for referral letter drafting (doc_id={document_id})...")

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": REFERRAL_DRAFT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
        logger.info(f"LLM referral draft response received ({len(raw_content)} chars)")
        parsed = json.loads(raw_content)
        letter = parsed.get("referral_letter_text", "").strip()
        if not letter:
            raise ValueError("LLM returned empty referral_letter_text")
        return letter

    except Exception as e:
        logger.error(f"LLM referral draft call failed: {e}")
        raise RuntimeError(f"LLM referral draft call failed: {e}") from e
