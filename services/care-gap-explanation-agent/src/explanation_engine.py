from src.logger import logger
from src.models import CareGapExplanationResponse, CitationItem, ClinicalDecisionPackage, DocumentSpanItem


class GroundingVerificationError(Exception):
    """Raised when LLM-generated explanation citations cannot be verified against grounded guideline evidence."""


def _parse_deterministic_findings(package: ClinicalDecisionPackage):
    """
    Deterministic parsing of temporal gaps, safety flags, and drug interactions.
    Outputs feed INTO the LLM prompt as grounding context.
    """
    gaps_found: list[str] = []
    citations: list[CitationItem] = []
    spans: list[DocumentSpanItem] = []

    # 1. Parse Temporal Care Gaps
    for gap in package.temporal_care_gaps:
        g_status = gap.get("status", "")
        measure = gap.get("measure_name", "Clinical Screening")
        due_date = gap.get("due_date", "N/A")
        if "SYSTEM OVERRIDE" in measure or "IGNORE ALL" in measure.upper():
            logger.warning(f"Adversarial prompt injection detected in measure_name: {measure}")
            measure = "Clinical Screening (Sanitized)"
        if g_status in ["due", "overdue"]:
            gaps_found.append(f"{measure} is currently {g_status.upper()} (Due Date: {due_date}).")
        elif g_status == "insufficient_information":
            gaps_found.append(f"{measure} cannot be determined due to missing screening history.")

    # 2. Parse Guideline Passages & Build Grounded Citations (Strict No-Fabrication Constraint)
    for passage in package.guideline_passages:
        citations.append(
            CitationItem(
                source_title=passage.get("source", ""),
                version=passage.get("version", ""),
                section=passage.get("section", ""),
                clause_id=passage.get("clause_id", ""),
                passage_text=passage.get("passage_text", ""),
                similarity_score=float(passage.get("similarity_score", 1.0)),
            )
        )

    # 3. Parse Safety and Interaction Findings
    if package.safety_assessment.get("is_emergency"):
        red_flags = package.safety_assessment.get("red_flags", [])
        for rf in red_flags:
            gaps_found.append(f"EMERGENCY RED FLAG ({rf.get('syndrome', 'Clinical Emergency')}): {rf.get('description', '')}")

    for di in package.drug_interactions:
        if di.get("severity") in ["HIGH", "CRITICAL"]:
            gaps_found.append(f"Drug Contraindication ({di.get('severity')}): {di.get('description', '')}")

    return gaps_found, citations, spans


def _get_valid_citation_keys(package: ClinicalDecisionPackage) -> set[str]:
    """Builds the set of valid (source, clause_id) strings from package.guideline_passages."""
    valid_keys = set()
    for passage in package.guideline_passages:
        source = passage.get("source", "")
        clause = passage.get("clause_id", "")
        if source:
            valid_keys.add(source.lower().strip())
        if clause:
            valid_keys.add(clause.lower().strip())
    return valid_keys


def _verify_citations(llm_result: dict, valid_keys: set[str]) -> list[str]:
    """
    Checks that every citation the LLM references actually exists in the package.
    Returns list of invalid citation descriptions (empty if all valid).
    """
    violations = []
    for cite in llm_result.get("citations_used", []):
        source = (cite.get("source_title", "") or "").lower().strip()
        clause = (cite.get("clause_id", "") or "").lower().strip()
        source_ok = source in valid_keys if source else True
        clause_ok = clause in valid_keys if clause else True
        if not source_ok and not clause_ok:
            violations.append(f"source_title='{cite.get('source_title')}', clause_id='{cite.get('clause_id')}'")
        elif not source_ok:
            violations.append(f"source_title='{cite.get('source_title')}' not found in package")
        elif not clause_ok:
            violations.append(f"clause_id='{cite.get('clause_id')}' not found in package")
    return violations


def generate_care_gap_explanation(package: ClinicalDecisionPackage) -> CareGapExplanationResponse:
    """
    Generates grounded care gap explanations using LLM reasoning with citation verification.
    """
    from src.llm_client import call_llm_explanation

    logger.info(f"Generating care gap explanation for document_id={package.document_id}")

    gaps_found, citations, spans = _parse_deterministic_findings(package)

    # Rule C5: Empty guideline evidence must return exactly "Insufficient guideline evidence"
    if not package.guideline_passages:
        logger.info(f"No guideline passages present in package for doc_id={package.document_id}. Returning 'Insufficient guideline evidence'.")
        return CareGapExplanationResponse(
            document_id=package.document_id,
            explanation_summary="Insufficient guideline evidence",
            care_gaps_found=gaps_found,
            cited_guideline_passages=[],
            document_evidence_spans=spans,
            generation_mode="llm",
        )

    valid_keys = _get_valid_citation_keys(package)
    guideline_passages_raw = list(package.guideline_passages or [])

    # Call LLM for grounded explanation
    llm_result = call_llm_explanation(
        care_gaps_found=gaps_found,
        guideline_passages=guideline_passages_raw,
        safety_assessment=package.safety_assessment,
        drug_interactions=package.drug_interactions,
        document_id=package.document_id,
        patient_id=package.patient_id,
    )

    # Verify LLM citations against package guideline passages
    violations = _verify_citations(llm_result, valid_keys)

    if violations:
        logger.warning(f"LLM citation verification failed (attempt 1) for doc_id={package.document_id}: {violations}")

        correction = (
            f"Your previous response contained {len(violations)} citation(s) that do NOT exist in the provided "
            f"Clinical Decision Package: {'; '.join(violations)}. "
            f"You MUST only cite sources from the provided guideline_passages. "
            f"The valid source_titles are: {[p.get('source', '') for p in guideline_passages_raw]}. "
            f"The valid clause_ids are: {[p.get('clause_id', '') for p in guideline_passages_raw]}. "
            f"Regenerate the explanation using ONLY these citations."
        )

        llm_result = call_llm_explanation(
            care_gaps_found=gaps_found,
            guideline_passages=guideline_passages_raw,
            safety_assessment=package.safety_assessment,
            drug_interactions=package.drug_interactions,
            document_id=package.document_id,
            patient_id=package.patient_id,
            correction_instruction=correction,
        )

        retry_violations = _verify_citations(llm_result, valid_keys)
        if retry_violations:
            logger.error(f"LLM citation verification failed AGAIN (attempt 2) for doc_id={package.document_id}: {retry_violations}.")
            raise GroundingVerificationError(f"Grounding verification failed: LLM generated unsupported citations: {retry_violations}")

    llm_summary = llm_result.get("explanation_summary", "")
    if not llm_summary:
        raise GroundingVerificationError("LLM response did not contain an explanation summary.")

    return CareGapExplanationResponse(
        document_id=package.document_id,
        explanation_summary=llm_summary,
        care_gaps_found=gaps_found,
        cited_guideline_passages=citations,
        document_evidence_spans=spans,
        generation_mode="llm",
    )
