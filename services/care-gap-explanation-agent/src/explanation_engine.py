from typing import Dict, List, Set, Tuple

from src.logger import logger
from src.models import CareGapExplanationResponse, CitationItem, ClinicalDecisionPackage, DocumentSpanItem


class GroundingVerificationError(Exception):
    """Raised when LLM-generated explanation citations cannot be verified against grounded guideline evidence."""


def _parse_deterministic_findings(package: ClinicalDecisionPackage):
    """
    Deterministic parsing of temporal gaps, safety flags, and drug interactions.
    Outputs feed INTO the LLM prompt as grounding context.
    """
    gaps_found: List[str] = []
    spans: List[DocumentSpanItem] = []

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

    # 2. Parse Safety and Interaction Findings
    if package.safety_assessment.get("is_emergency"):
        red_flags = package.safety_assessment.get("red_flags", [])
        for rf in red_flags:
            gaps_found.append(f"EMERGENCY RED FLAG ({rf.get('syndrome', 'Clinical Emergency')}): {rf.get('description', '')}")

    for di in package.drug_interactions:
        if di.get("severity") in ["HIGH", "CRITICAL"]:
            gaps_found.append(f"Drug Contraindication ({di.get('severity')}): {di.get('description', '')}")

    return gaps_found, spans


def _get_valid_citation_tuples(package: ClinicalDecisionPackage) -> Tuple[Set[Tuple[str, str]], Dict[Tuple[str, str], dict]]:
    """Builds valid set of (source_title, clause_id) tuples from supplied guideline passages."""
    valid_tuples = set()
    passage_by_tuple = {}

    for passage in package.guideline_passages:
        source = (passage.get("source_title", "") or passage.get("source", "")).strip().lower()
        clause = passage.get("clause_id", "").strip().lower()
        if source and clause:
            tup = (source, clause)
            valid_tuples.add(tup)
            passage_by_tuple[tup] = passage

    return valid_tuples, passage_by_tuple


def _verify_citations(llm_result: dict, valid_tuples: Set[Tuple[str, str]]) -> List[str]:
    """
    Checks that every citation referenced by LLM matches an exact (source_title, clause_id) tuple
    belonging to the SAME supplied guideline passage.
    """
    violations = []
    citations_used = llm_result.get("citations_used", [])

    for cite in citations_used:
        source = (cite.get("source_title", "") or cite.get("source", "")).strip().lower()
        clause = (cite.get("clause_id", "") or "").strip().lower()

        if not source or not clause or (source, clause) not in valid_tuples:
            violations.append(
                f"Invalid citation tuple: (source_title='{cite.get('source_title')}', clause_id='{cite.get('clause_id')}') "
                f"does not exist together in any single supplied guideline passage."
            )

    return violations


def generate_care_gap_explanation(package: ClinicalDecisionPackage) -> CareGapExplanationResponse:
    """
    Generates grounded care gap explanations using LLM reasoning with strict atomic tuple citation verification.
    """
    from src.llm_client import call_llm_explanation

    logger.info(f"Generating care gap explanation for document_id={package.document_id}")

    gaps_found, spans = _parse_deterministic_findings(package)

    # Rule C5: Empty guideline evidence must return exactly "Insufficient guideline evidence"
    if not package.guideline_passages:
        logger.info(f"No guideline passages present in package for doc_id={package.document_id}. Returning 'Insufficient guideline evidence'.")
        return CareGapExplanationResponse(
            document_id=package.document_id,
            explanation_summary="Insufficient guideline evidence",
            care_gaps_found=gaps_found,
            cited_guideline_passages=[],
            document_evidence_spans=spans,
            generation_mode="insufficient_evidence",
        )

    valid_tuples, passage_by_tuple = _get_valid_citation_tuples(package)
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

    # Verify LLM citations against valid passage tuples
    violations = _verify_citations(llm_result, valid_tuples)

    if violations:
        logger.warning(f"LLM citation verification failed (attempt 1) for doc_id={package.document_id}: {violations}")

        correction = (
            f"Your previous response contained {len(violations)} citation(s) that do NOT match any single guideline passage: "
            f"{'; '.join(violations)}. "
            f"You MUST only cite exact (source_title, clause_id) tuples from the provided guideline_passages. "
            f"Regenerate the explanation using ONLY valid citations."
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

        retry_violations = _verify_citations(llm_result, valid_tuples)
        if retry_violations:
            logger.error(f"LLM citation verification failed AGAIN (attempt 2) for doc_id={package.document_id}: {retry_violations}.")
            raise GroundingVerificationError(f"Grounding verification failed: LLM generated unsupported citations: {retry_violations}")

    llm_summary = llm_result.get("explanation_summary", "")
    if not llm_summary:
        raise GroundingVerificationError("LLM response did not contain an explanation summary.")

    # Populate cited_guideline_passages with ONLY passages actually referenced by the verified LLM output
    cited_items: List[CitationItem] = []
    used_tuples = set()
    for cite in llm_result.get("citations_used", []):
        src = (cite.get("source_title", "") or cite.get("source", "")).strip().lower()
        clause = (cite.get("clause_id", "") or "").strip().lower()
        tup = (src, clause)
        if tup in passage_by_tuple and tup not in used_tuples:
            used_tuples.add(tup)
            p = passage_by_tuple[tup]
            cited_items.append(
                CitationItem(
                    source_title=p.get("source_title", p.get("source", "")),
                    version=p.get("version", ""),
                    section=p.get("section", ""),
                    clause_id=p.get("clause_id", ""),
                    passage_text=p.get("passage_text", ""),
                    similarity_score=float(p.get("similarity_score", 1.0)),
                )
            )

    return CareGapExplanationResponse(
        document_id=package.document_id,
        explanation_summary=llm_summary,
        care_gaps_found=gaps_found,
        cited_guideline_passages=cited_items,
        document_evidence_spans=spans,
        generation_mode="llm",
    )
