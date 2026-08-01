from src.config import settings
from src.llm_client import LLMInvalidResponseError, LLMUnavailableError, call_llm_referral_draft
from src.logger import logger
from src.models import GroundedEvidenceItem, ReferralDraftRequest, ReferralDraftResponse


class ReferralDraftingError(Exception):
    """Raised when referral letter drafting fails."""


def generate_referral_draft_letter(request: ReferralDraftRequest) -> ReferralDraftResponse:
    """
    Generates a structured draft referral letter grounded in ClinicalDecisionPackage evidence.

    Determining urgency, reasons, and evidence items remains strictly deterministic.
    The final natural-language clinical letter drafting is performed via LLM reasoning.
    """
    logger.info(f"Generating draft referral letter for document_id={request.document_id}")

    pkg = request.clinical_decision_package
    patient_id = request.patient_id or pkg.get("patient_id", "")
    specialty = request.target_specialty or "Specialist Evaluation"

    urgency = "ROUTINE"
    reasons = []
    evidence_items: list[GroundedEvidenceItem] = []

    # 1. Deterministic urgency & reason classification (safety red flags)
    safety = pkg.get("safety_assessment", {})
    if safety.get("is_emergency"):
        urgency = "EMERGENCY"
        for rf in safety.get("red_flags", []):
            reasons.append(f"Safety Red Flag: {rf.get('description', '')}")

    # 2. Deterministic care gap reasons
    gaps = pkg.get("temporal_care_gaps", [])
    for gap in gaps:
        if gap.get("status") in ["due", "overdue"]:
            measure = gap.get("measure_name", "Screening")
            reasons.append(f"Care Gap Identified: {measure} is {gap.get('status').upper()}")

    # 3. Deterministic evidence collection
    passages = pkg.get("guideline_passages", [])
    for p in passages:
        evidence_items.append(GroundedEvidenceItem(source_quote=p.get("passage_text", ""), section=p.get("section", ""), clause_id=p.get("clause_id", "")))

    if not reasons:
        reasons.append(f"Routine specialist evaluation for {specialty}.")

    # 4. Real LLM Call — No canned fallback letter
    api_key = settings.llm_api_key or settings.lyzr_api_key
    if not api_key or api_key in ("MISSING", "INVALID_CREDENTIALS"):
        raise LLMUnavailableError("LYZR_API_KEY / LLM_API_KEY mandatory configuration missing or invalid. Direct LLM fallback forbidden.")

    evidence_dicts = [ev.model_dump() for ev in evidence_items]
    letter_text = call_llm_referral_draft(
        patient_id=patient_id, target_specialty=specialty, urgency_level=urgency, clinical_reasons=reasons, evidence_items=evidence_dicts, document_id=request.document_id
    )

    if not letter_text:
        raise ReferralDraftingError("LLM referral drafting returned empty letter text.")

    return ReferralDraftResponse(
        document_id=request.document_id,
        patient_id=patient_id,
        target_specialty=specialty,
        urgency_level=urgency,
        referral_letter_text=letter_text,
        clinical_reasons=reasons,
        grounded_evidence=evidence_items,
    )
