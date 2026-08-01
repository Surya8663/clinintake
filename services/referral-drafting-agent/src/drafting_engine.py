from src.config import settings
from src.llm_client import LLMInvalidResponseError, call_llm_referral_draft
from src.logger import logger
from src.models import GroundedEvidenceItem, LyzrReferralResponse, ReferralDraftRequest, ReferralDraftResponse


class ReferralValidationError(Exception):
    """Raised when referral drafting inputs (target_specialty, patient_id, or clinical reasons) are missing or invalid."""


class ReferralDraftingError(Exception):
    """Raised when referral letter drafting fails or evidence references are ungrounded."""


def generate_referral_draft_letter(request: ReferralDraftRequest) -> ReferralDraftResponse:
    """
    Generates a structured draft referral letter grounded in ClinicalDecisionPackage evidence.

    Target specialty, patient identity, care gap measure names, and clinical reasons are strictly validated.
    Evidence references in LLM response are strictly verified against supplied evidence items.
    """
    logger.info(f"Generating draft referral letter for document_id={request.document_id}")

    pkg = request.clinical_decision_package or {}

    # 1. Patient identity validation (No fallback to "Unknown")
    patient_id = request.patient_id or pkg.get("patient_id")
    if not patient_id or not str(patient_id).strip():
        raise ReferralValidationError("Missing required patient_id: referral may proceed only with a valid patient identifier.")
    patient_id = str(patient_id).strip()

    # 2. Target specialty validation (Must be explicitly supplied in request or package)
    specialty = request.target_specialty or pkg.get("target_specialty")
    if not specialty or not str(specialty).strip():
        raise ReferralValidationError("Missing required target_specialty: target_specialty must be explicitly supplied or deterministically derived.")

    specialty = str(specialty).strip()
    urgency = "ROUTINE"
    reasons = []
    evidence_items: list[GroundedEvidenceItem] = []

    # 3. Deterministic urgency & reason classification (safety red flags)
    safety = pkg.get("safety_assessment", {})
    if safety.get("is_emergency"):
        urgency = "EMERGENCY"
        for rf in safety.get("red_flags", []):
            desc = rf.get("description", "").strip()
            if desc:
                reasons.append(f"Safety Red Flag: {desc}")

    # 4. Deterministic care gap reasons (Reject gaps missing measure_name — no default "Screening")
    gaps = pkg.get("temporal_care_gaps", [])
    for gap in gaps:
        if gap.get("status") in ["due", "overdue"]:
            measure = gap.get("measure_name")
            if not measure or not str(measure).strip():
                raise ReferralValidationError(f"Due or overdue care gap missing measure_name in package for document_id={request.document_id}.")
            reasons.append(f"Care Gap Identified: {str(measure).strip()} is {gap.get('status').upper()}")

    # 5. Require at least one supported clinical reason
    if not reasons:
        raise ReferralValidationError(f"Missing required clinical_reasons: no supported care gaps or safety items exist for specialty '{specialty}'.")

    # 6. Deterministic evidence collection (validate GroundedEvidenceItem models)
    passages = pkg.get("guideline_passages", [])
    for p in passages:
        quote = (p.get("passage_text") or "").strip()
        sec = (p.get("section") or "").strip() or None
        clause = (p.get("clause_id") or "").strip() or None
        if quote and (sec or clause):
            evidence_items.append(GroundedEvidenceItem(source_quote=quote, section=sec, clause_id=clause))

    # 7. Real LLM Call — No canned fallback letter
    api_key = settings.lyzr_api_key
    if not api_key or api_key in ("MISSING", "INVALID_CREDENTIALS"):
        from src.llm_client import LLMUnavailableError
        raise LLMUnavailableError("LYZR_API_KEY mandatory configuration missing or invalid. Direct LLM fallback forbidden.")

    evidence_dicts = [ev.model_dump() for ev in evidence_items]
    typed_llm_res: LyzrReferralResponse = call_llm_referral_draft(
        patient_id=patient_id,
        target_specialty=specialty,
        urgency_level=urgency,
        clinical_reasons=reasons,
        evidence_items=evidence_dicts,
        document_id=request.document_id,
    )

    letter_text = typed_llm_res.referral_letter_text.strip()
    if not letter_text:
        raise ReferralDraftingError("LLM referral drafting returned empty letter text.")

    # 8. Evidence Reference Verification
    if evidence_items and len(typed_llm_res.evidence_refs_used) == 0:
        raise LLMInvalidResponseError("Referral drafting response contained zero evidence references despite supplied guideline evidence.")

    supplied_quotes = {ev.source_quote.strip().lower() for ev in evidence_items}
    supplied_clauses = {ev.clause_id.strip().lower() for ev in evidence_items if ev.clause_id}

    for ref in typed_llm_res.evidence_refs_used:
        ref_quote = ref.source_quote.strip().lower()
        ref_clause = (ref.clause_id or "").strip().lower()

        is_quote_valid = ref_quote in supplied_quotes or any(ref_quote in sq for sq in supplied_quotes)
        is_clause_valid = ref_clause in supplied_clauses if ref_clause else True

        if not (is_quote_valid or (ref_clause and is_clause_valid)):
            raise LLMInvalidResponseError(
                f"Referral evidence reference (clause_id='{ref.clause_id}', source_quote='{ref.source_quote}') is not present in supplied guideline evidence."
            )

    return ReferralDraftResponse(
        document_id=request.document_id,
        patient_id=patient_id,
        target_specialty=specialty,
        urgency_level=urgency,
        referral_letter_text=letter_text,
        clinical_reasons=reasons,
        grounded_evidence=evidence_items,
    )
