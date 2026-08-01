from src.config import settings
from src.llm_client import call_llm_referral_draft
from src.logger import logger
from src.models import GroundedEvidenceItem, ReferralDraftRequest, ReferralDraftResponse


class ReferralValidationError(Exception):
    """Raised when referral drafting inputs (target_specialty or clinical reasons) are missing or invalid."""


class ReferralDraftingError(Exception):
    """Raised when referral letter drafting fails."""


def generate_referral_draft_letter(request: ReferralDraftRequest) -> ReferralDraftResponse:
    """
    Generates a structured draft referral letter grounded in ClinicalDecisionPackage evidence.

    Determining urgency, reasons, and evidence items remains strictly deterministic.
    Target specialty and clinical reasons are strictly validated without runtime placeholder defaults.
    """
    logger.info(f"Generating draft referral letter for document_id={request.document_id}")

    pkg = request.clinical_decision_package or {}
    patient_id = request.patient_id or pkg.get("patient_id")

    # 1. Target specialty validation (Must be explicitly supplied in request or package)
    specialty = request.target_specialty or pkg.get("target_specialty")
    if not specialty or not str(specialty).strip():
        raise ReferralValidationError("Missing required target_specialty: target_specialty must be explicitly supplied or deterministically derived.")

    specialty = str(specialty).strip()
    urgency = "ROUTINE"
    reasons = []
    evidence_items: list[GroundedEvidenceItem] = []

    # 2. Deterministic urgency & reason classification (safety red flags)
    safety = pkg.get("safety_assessment", {})
    if safety.get("is_emergency"):
        urgency = "EMERGENCY"
        for rf in safety.get("red_flags", []):
            desc = rf.get("description", "").strip()
            if desc:
                reasons.append(f"Safety Red Flag: {desc}")

    # 3. Deterministic care gap reasons
    gaps = pkg.get("temporal_care_gaps", [])
    for gap in gaps:
        if gap.get("status") in ["due", "overdue"]:
            measure = gap.get("measure_name", "Screening").strip()
            reasons.append(f"Care Gap Identified: {measure} is {gap.get('status').upper()}")

    # 4. Require at least one supported clinical reason (No manufactured default reasons)
    if not reasons:
        raise ReferralValidationError(f"Missing required clinical_reasons: no supported care gaps or safety items exist for specialty '{specialty}'.")

    # 5. Deterministic evidence collection
    passages = pkg.get("guideline_passages", [])
    for p in passages:
        evidence_items.append(GroundedEvidenceItem(source_quote=p.get("passage_text", ""), section=p.get("section", ""), clause_id=p.get("clause_id", "")))

    # 6. Real LLM Call — No canned fallback letter
    api_key = settings.lyzr_api_key
    if not api_key or api_key in ("MISSING", "INVALID_CREDENTIALS"):
        from src.llm_client import LLMUnavailableError
        raise LLMUnavailableError("LYZR_API_KEY mandatory configuration missing or invalid. Direct LLM fallback forbidden.")

    evidence_dicts = [ev.model_dump() for ev in evidence_items]
    letter_text = call_llm_referral_draft(
        patient_id=patient_id or "Unknown", target_specialty=specialty, urgency_level=urgency, clinical_reasons=reasons, evidence_items=evidence_dicts, document_id=request.document_id
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
