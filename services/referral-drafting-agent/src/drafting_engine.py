from src.config import settings
from src.logger import logger
from src.models import GroundedEvidenceItem, ReferralDraftRequest, ReferralDraftResponse


def _build_deterministic_letter(patient_id: str, specialty: str, urgency: str, reasons: list[str], evidence_items: list[GroundedEvidenceItem]) -> str:
    """Fallback deterministic letter layout if LLM call is unavailable or fails."""
    reasons_formatted = "\n- ".join(reasons)
    letter_text = (
        f"CLINICAL REFERRAL LETTER (DRAFT)\n"
        f"=================================\n"
        f"Date: 2026-07-25\n"
        f"To: Department of {specialty}\n"
        f"Re: Patient ID: {patient_id}\n"
        f"Urgency Level: {urgency}\n\n"
        f"Dear Specialist,\n\n"
        f"I am referring the above-named patient for clinical evaluation and management regarding:\n- {reasons_formatted}\n\n"
        f"Clinical Guideline Evidence Grounding:\n"
    )

    for ev in evidence_items:
        letter_text += f'- [{ev.section} / {ev.clause_id}]: "{ev.source_quote}"\n'

    letter_text += "\nThank you for seeing this patient in consultation.\n\n" "Sincerely,\n" "Referring Clinician / ClinIntake System"
    return letter_text


def generate_referral_draft_letter(request: ReferralDraftRequest) -> ReferralDraftResponse:
    """
    Generates a structured draft referral letter grounded in ClinicalDecisionPackage evidence.

    Determining urgency, reasons, and evidence items remains strictly deterministic.
    The final natural-language clinical letter drafting is performed via LLM reasoning.
    """
    logger.info(f"Generating draft referral letter for document_id={request.document_id}")

    pkg = request.clinical_decision_package
    patient_id = request.patient_id or pkg.get("patient_id", "PAT-UNKNOWN")
    specialty = request.target_specialty or "Gastroenterology"

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
        evidence_items.append(GroundedEvidenceItem(source_quote=p.get("passage_text", ""), section=p.get("section", "Recommendation"), clause_id=p.get("clause_id", "CLAUSE-01")))

    if not reasons:
        reasons.append(f"Routine specialist evaluation for {specialty}.")

    # 4. LLM Drafting of final clinical letter text (or fallback)
    letter_text = ""
    if settings.llm_api_key:
        try:
            from src.llm_client import call_llm_referral_draft

            evidence_dicts = [ev.model_dump() for ev in evidence_items]
            letter_text = call_llm_referral_draft(
                patient_id=patient_id, target_specialty=specialty, urgency_level=urgency, clinical_reasons=reasons, evidence_items=evidence_dicts, document_id=request.document_id
            )
        except Exception as e:
            logger.error(f"LLM referral letter drafting failed: {e}. Using deterministic layout fallback.")
            letter_text = _build_deterministic_letter(patient_id, specialty, urgency, reasons, evidence_items)
    else:
        logger.info("No LLM API key set. Using deterministic referral letter layout.")
        letter_text = _build_deterministic_letter(patient_id, specialty, urgency, reasons, evidence_items)

    return ReferralDraftResponse(
        document_id=request.document_id,
        patient_id=patient_id,
        target_specialty=specialty,
        urgency_level=urgency,
        referral_letter_text=letter_text,
        clinical_reasons=reasons,
        grounded_evidence=evidence_items,
    )
