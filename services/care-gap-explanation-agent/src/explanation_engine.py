from typing import Any, Dict, List, Set, Tuple

from pydantic import ValidationError

from src.logger import logger
from src.models import (
    CareGapExplanationResponse,
    CitationItem,
    ClinicalDecisionPackage,
    DocumentSpanItem,
    GuidelinePassage,
    LyzrExplanationResponse,
)


class GroundingVerificationError(Exception):
    """Raised when LLM-generated explanation citations cannot be verified against grounded guideline evidence."""


def _parse_deterministic_findings(package: ClinicalDecisionPackage):
    """
    Deterministic parsing of temporal gaps, safety flags, and drug interactions.
    Outputs feed INTO the LLM prompt as grounding context.
    """
    gaps_found: List[str] = []
    spans: List[DocumentSpanItem] = []

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

    if package.safety_assessment.get("is_emergency"):
        red_flags = package.safety_assessment.get("red_flags", [])
        for rf in red_flags:
            gaps_found.append(f"EMERGENCY RED FLAG ({rf.get('syndrome', 'Clinical Emergency')}): {rf.get('description', '')}")

    for di in package.drug_interactions:
        if di.get("severity") in ["HIGH", "CRITICAL"]:
            gaps_found.append(f"Drug Contraindication ({di.get('severity')}): {di.get('description', '')}")

    return gaps_found, spans


def _validate_and_get_valid_citation_tuples(package: ClinicalDecisionPackage) -> Tuple[Set[Tuple[str, str]], Dict[Tuple[str, str], dict]]:
    """Validates each supplied guideline passage and builds valid set of (source_title, clause_id) tuples."""
    valid_tuples = set()
    passage_by_tuple = {}

    for passage in package.guideline_passages:
        try:
            p_obj = GuidelinePassage(
                clause_id=passage.get("clause_id", ""),
                source=passage.get("source", ""),
                source_title=passage.get("source_title", passage.get("source", "")),
                version=passage.get("version", ""),
                section=passage.get("section", ""),
                passage_text=passage.get("passage_text", ""),
                similarity_score=passage.get("similarity_score", None),
            )
        except (ValidationError, TypeError, ValueError) as err:
            logger.warning(f"Invalid guideline passage in package: {err}")
            continue

        source = (p_obj.source_title or p_obj.source).strip().lower()
        clause = p_obj.clause_id.strip().lower()
        if source and clause:
            tup = (source, clause)
            valid_tuples.add(tup)
            passage_by_tuple[tup] = passage

    return valid_tuples, passage_by_tuple


def _verify_citations(typed_response: Any, valid_tuples: Set[Tuple[str, str]]) -> List[str]:
    """
    Checks that every citation referenced by LLM matches an exact (source_title, clause_id) tuple
    belonging to the SAME supplied guideline passage.
    """
    violations = []
    if isinstance(typed_response, dict):
        citations_used = typed_response.get("citations_used", [])
    elif hasattr(typed_response, "citations_used"):
        citations_used = typed_response.citations_used
    else:
        citations_used = []

    for cite in citations_used:
        if isinstance(cite, dict):
            source = (cite.get("source_title", "") or cite.get("source", "")).strip().lower()
            clause = (cite.get("clause_id", "") or "").strip().lower()
            raw_src = cite.get("source_title", cite.get("source", ""))
            raw_clause = cite.get("clause_id", "")
        else:
            source = cite.source_title.strip().lower()
            clause = cite.clause_id.strip().lower()
            raw_src = cite.source_title
            raw_clause = cite.clause_id

        if not source or not clause or (source, clause) not in valid_tuples:
            violations.append(
                f"Invalid citation tuple: (source_title='{raw_src}', clause_id='{raw_clause}') "
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

    # Empty guideline evidence returns exact summary "Insufficient guideline evidence"
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

    valid_tuples, passage_by_tuple = _validate_and_get_valid_citation_tuples(package)
    guideline_passages_raw = list(package.guideline_passages or [])

    # Call LLM for grounded explanation
    typed_response = call_llm_explanation(
        care_gaps_found=gaps_found,
        guideline_passages=guideline_passages_raw,
        safety_assessment=package.safety_assessment,
        drug_interactions=package.drug_interactions,
        document_id=package.document_id,
        patient_id=package.patient_id,
    )

    citations_list = typed_response.citations_used if hasattr(typed_response, "citations_used") else typed_response.get("citations_used", [])
    summary_str = typed_response.explanation_summary if hasattr(typed_response, "explanation_summary") else typed_response.get("explanation_summary", "")

    # Section 4 Rule: An explanation with citations_used = [] must not be accepted when care gaps and guideline evidence exist
    if gaps_found and valid_tuples and len(citations_list) == 0:
        raise GroundingVerificationError("Explanation discussing care gaps supported by guideline evidence contained zero cited guideline passages.")

    # Verify LLM citations against valid passage tuples
    violations = _verify_citations(typed_response, valid_tuples)

    if violations:
        logger.warning(f"LLM citation verification failed (attempt 1) for doc_id={package.document_id}: {violations}")

        correction = (
            f"Your previous response contained {len(violations)} citation(s) that do NOT match any single guideline passage: "
            f"{'; '.join(violations)}. "
            f"You MUST only cite exact (source_title, clause_id) tuples from the provided guideline_passages. "
            f"Regenerate the explanation using ONLY valid citations."
        )

        typed_response = call_llm_explanation(
            care_gaps_found=gaps_found,
            guideline_passages=guideline_passages_raw,
            safety_assessment=package.safety_assessment,
            drug_interactions=package.drug_interactions,
            document_id=package.document_id,
            patient_id=package.patient_id,
            correction_instruction=correction,
        )

        citations_list = typed_response.citations_used if hasattr(typed_response, "citations_used") else typed_response.get("citations_used", [])
        summary_str = typed_response.explanation_summary if hasattr(typed_response, "explanation_summary") else typed_response.get("explanation_summary", "")

        if gaps_found and valid_tuples and len(citations_list) == 0:
            raise GroundingVerificationError("Explanation discussing care gaps supported by guideline evidence contained zero cited guideline passages.")

        retry_violations = _verify_citations(typed_response, valid_tuples)
        if retry_violations:
            logger.error(f"LLM citation verification failed AGAIN (attempt 2) for doc_id={package.document_id}: {retry_violations}.")
            raise GroundingVerificationError(f"Grounding verification failed: LLM generated unsupported citations: {retry_violations}")

    # Populate cited_guideline_passages with ONLY passages actually referenced by the verified LLM output
    cited_items: List[CitationItem] = []
    used_tuples = set()
    for cite in citations_list:
        if isinstance(cite, dict):
            src = (cite.get("source_title", "") or cite.get("source", "")).strip().lower()
            clause = (cite.get("clause_id", "") or "").strip().lower()
        else:
            src = cite.source_title.strip().lower()
            clause = cite.clause_id.strip().lower()

        tup = (src, clause)
        if tup in passage_by_tuple and tup not in used_tuples:
            used_tuples.add(tup)
            p = passage_by_tuple[tup]
            raw_sim = p.get("similarity_score", None)
            sim_score = float(raw_sim) if raw_sim is not None else None

            cited_items.append(
                CitationItem(
                    source_title=p.get("source_title", p.get("source", "")),
                    version=p.get("version", ""),
                    section=p.get("section", ""),
                    clause_id=p.get("clause_id", ""),
                    passage_text=p.get("passage_text", ""),
                    similarity_score=sim_score,
                )
            )

    return CareGapExplanationResponse(
        document_id=package.document_id,
        explanation_summary=summary_str,
        care_gaps_found=gaps_found,
        cited_guideline_passages=cited_items,
        document_evidence_spans=spans,
        generation_mode="llm",
    )
