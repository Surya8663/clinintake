from typing import List, Dict, Any
from src.models import ReferralDraftRequest, ReferralDraftResponse, GroundedEvidenceItem
from src.logger import logger

def generate_referral_draft_letter(request: ReferralDraftRequest) -> ReferralDraftResponse:
    """Generates a structured draft referral letter grounded in ClinicalDecisionPackage evidence."""
    logger.info(f"Generating draft referral letter for document_id={request.document_id}")
    
    pkg = request.clinical_decision_package
    patient_id = request.patient_id or pkg.get("patient_id", "PAT-UNKNOWN")
    specialty = request.target_specialty or "Gastroenterology"

    urgency = "ROUTINE"
    reasons = []
    evidence_items: List[GroundedEvidenceItem] = []

    # Check for safety emergency red flags
    safety = pkg.get("safety_assessment", {})
    if safety.get("is_emergency"):
        urgency = "EMERGENCY"
        for rf in safety.get("red_flags", []):
            reasons.append(f"Safety Red Flag: {rf.get('description', '')}")

    # Check care gaps
    gaps = pkg.get("temporal_care_gaps", [])
    for gap in gaps:
        if gap.get("status") in ["due", "overdue"]:
            measure = gap.get("measure_name", "Screening")
            reasons.append(f"Care Gap Identified: {measure} is {gap.get('status').upper()}")

    # Check guideline passages for grounding evidence
    passages = pkg.get("guideline_passages", [])
    for p in passages:
        evidence_items.append(GroundedEvidenceItem(
            source_quote=p.get("passage_text", ""),
            section=p.get("section", "Recommendation"),
            clause_id=p.get("clause_id", "CLAUSE-01")
        ))

    if not reasons:
        reasons.append(f"Routine specialist evaluation for {specialty}.")

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
        letter_text += f"- [{ev.section} / {ev.clause_id}]: \"{ev.source_quote}\"\n"

    letter_text += (
        f"\nThank you for seeing this patient in consultation.\n\n"
        f"Sincerely,\n"
        f"Referring Clinician / ClinIntake System"
    )

    return ReferralDraftResponse(
        document_id=request.document_id,
        patient_id=patient_id,
        target_specialty=specialty,
        urgency_level=urgency,
        referral_letter_text=letter_text,
        clinical_reasons=reasons,
        grounded_evidence=evidence_items
    )
