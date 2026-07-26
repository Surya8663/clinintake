import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from src.config import settings
from src.logger import logger

EXTRACTION_SYSTEM_PROMPT = """You are a clinical document extraction engine. You receive raw OCR text from a scanned clinical document and must extract structured clinical entities.

For EACH entity you extract, you MUST provide:
1. "value": The normalized extracted value (e.g., "PAT-88491", "Essential Hypertension", "Lisinopril 10mg oral daily")
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


def _build_user_prompt(ocr_text: str, ocr_words: Optional[List[Dict[str, Any]]] = None) -> str:
    """Constructs the user prompt with OCR text and optional word-level bounding box context."""
    prompt = f"Extract all clinical entities from this OCR text:\n\n---\n{ocr_text}\n---"
    if ocr_words:
        # Provide spatial context for grounding
        word_summary = [
            {"text": w.get("text", ""), "bbox": w.get("bbox", {})}
            for w in ocr_words[:200]  # cap to avoid token overflow
        ]
        prompt += f"\n\nWord-level bounding box data (for spatial grounding):\n{json.dumps(word_summary, indent=None)}"
    return prompt


def call_llm_extraction(
    ocr_text: str,
    ocr_words: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Calls the configured LLM to extract structured clinical entities from OCR text.
    Returns parsed JSON matching the extraction schema.
    Uses the OpenAI-compatible chat completions interface — works with OpenAI, Azure, or any
    compatible endpoint by changing base_url/api_key in config.
    """
    client = OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url if settings.llm_base_url else None,
    )

    user_prompt = _build_user_prompt(ocr_text, ocr_words)

    logger.info(f"Calling LLM ({settings.llm_model}) for clinical extraction...")

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
        logger.info(f"LLM response received ({len(raw_content)} chars)")
        parsed = json.loads(raw_content)
        return parsed

    except Exception as e:
        logger.error(f"LLM extraction call failed: {e}")
        raise RuntimeError(f"LLM extraction failed: {e}") from e
