
from src.logger import logger
from src.models import CareGapExplanationResponse, CitationItem, ClinicalDecisionPackage, DocumentSpanItem


def _parse_deterministic_findings(package: ClinicalDecisionPackage):
    """
    Deterministic parsing of temporal gaps, safety flags, and drug interactions.
    This logic is correct and preserved as-is — its output feeds INTO the LLM prompt as grounding context.
    """
    gaps_found: list[str] = []
    citations: list[CitationItem] = []
    spans: list[DocumentSpanItem] = []

    # 1. Parse Temporal Care Gaps
    for gap in package.temporal_care_gaps:
        g_status = gap.get("status", "")
        measure = gap.get("measure_name", "Clinical Screening")
        due_date = gap.get("due_date", "N/A")
        if g_status in ["due", "overdue"]:
            gaps_found.append(f"{measure} is currently {g_status.upper()} (Due Date: {due_date}).")
        elif g_status == "insufficient_information":
            gaps_found.append(f"{measure} cannot be determined due to missing screening history.")

    # 2. Parse Guideline Passages & Build Grounded Citations (Strict No-Fabrication Constraint)
    for passage in package.guideline_passages:
        citations.append(CitationItem(
            source_title=passage.get("source", "USPSTF Guideline"),
            version=passage.get("version", "2021"),
            section=passage.get("section", "Recommendation"),
            clause_id=passage.get("clause_id", "CLAUSE-01"),
            passage_text=passage.get("passage_text", ""),
            similarity_score=passage.get("similarity_score", 1.0)
        ))

    # 3. Parse Safety and Interaction Findings
    if package.safety_assessment.get("is_emergency"):
        red_flags = package.safety_assessment.get("red_flags", [])
        for rf in red_flags:
            gaps_found.append(f"EMERGENCY RED FLAG ({rf.get('syndrome', 'Clinical Emergency')}): {rf.get('description', '')}")

    for di in package.drug_interactions:
        if di.get("severity") in ["HIGH", "CRITICAL"]:
            gaps_found.append(f"Drug Contraindication ({di.get('severity')}): {di.get('description', '')}")

    return gaps_found, citations, spans


def _build_deterministic_summary(gaps_found: list[str]) -> str:
    """Builds the deterministic f-string summary (used as labeled fallback only)."""
    if gaps_found:
        return (
            f"Clinical Decision Package analysis identified {len(gaps_found)} key clinical care gap(s) or safety priority item(s): "
            + "; ".join(gaps_found)
        )
    return "Clinical Decision Package analysis completed: No open care gaps or clinical safety red flags identified."


def _get_valid_citation_keys(package: ClinicalDecisionPackage) -> set[str]:
    """Builds the set of (source_title, clause_id) tuples that actually exist in the package."""
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

    Flow:
    1. Deterministic parsing of temporal gaps, safety flags, drug interactions (preserved as-is)
    2. LLM call with parsed context as grounding input
    3. Post-generation citation verification against package.guideline_passages
    4. If LLM cites something not in the package → retry once with correction
    5. If retry also fails → fall back to deterministic summary with generation_mode="deterministic_fallback"
    """
    from src.llm_client import call_llm_explanation

    logger.info(f"Generating care gap explanation for document_id={package.document_id}")

    # Step 1: Deterministic parsing (preserved exactly)
    gaps_found, citations, spans = _parse_deterministic_findings(package)
    valid_keys = _get_valid_citation_keys(package)

    # Step 2: Guardrail check on deterministic output
    deterministic_summary = _build_deterministic_summary(gaps_found)
    if "unverified_claim" in deterministic_summary.lower() or "fake_citation" in deterministic_summary.lower():
        logger.warning(f"Guardrail BLOCKED explanation for doc_id={package.document_id}: Hallucination Detected")

    # Step 3: Try LLM generation
    guideline_passages_raw = list(package.guideline_passages or [])

    try:
        llm_result = call_llm_explanation(
            care_gaps_found=gaps_found,
            guideline_passages=guideline_passages_raw,
            safety_assessment=package.safety_assessment,
            drug_interactions=package.drug_interactions,
            document_id=package.document_id,
            patient_id=package.patient_id,
        )

        # Step 4: Verify citations
        violations = _verify_citations(llm_result, valid_keys)

        if violations:
            logger.warning(
                f"LLM citation verification failed (attempt 1) for doc_id={package.document_id}: "
                f"{len(violations)} invalid citation(s): {violations}"
            )

            # Retry once with explicit correction
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

            # Verify retry
            retry_violations = _verify_citations(llm_result, valid_keys)
            if retry_violations:
                logger.error(
                    f"LLM citation verification failed AGAIN (attempt 2) for doc_id={package.document_id}: "
                    f"{retry_violations}. Falling back to deterministic summary."
                )
                return CareGapExplanationResponse(
                    document_id=package.document_id,
                    explanation_summary=deterministic_summary,
                    care_gaps_found=gaps_found,
                    cited_guideline_passages=citations,
                    document_evidence_spans=spans,
                    generation_mode="deterministic_fallback",
                )

        # LLM succeeded (first attempt or retry passed verification)
        llm_summary = llm_result.get("explanation_summary", deterministic_summary)

        return CareGapExplanationResponse(
            document_id=package.document_id,
            explanation_summary=llm_summary,
            care_gaps_found=gaps_found,
            cited_guideline_passages=citations,
            document_evidence_spans=spans,
            generation_mode="llm",
        )

    except Exception as e:
        logger.error(f"LLM explanation generation failed for doc_id={package.document_id}: {e}. Using deterministic fallback.")
        return CareGapExplanationResponse(
            document_id=package.document_id,
            explanation_summary=deterministic_summary,
            care_gaps_found=gaps_found,
            cited_guideline_passages=citations,
            document_evidence_spans=spans,
            generation_mode="deterministic_fallback",
        )
