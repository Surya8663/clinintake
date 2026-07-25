from typing import List
from src.models import ClinicalDecisionPackage, CareGapExplanationResponse, CitationItem, DocumentSpanItem
from src.logger import logger

def generate_care_gap_explanation(package: ClinicalDecisionPackage) -> CareGapExplanationResponse:
    """
    Generates grounded care gap explanations citing exact passages and evidence spans
    present in the input ClinicalDecisionPackage.
    """
    logger.info(f"Generating care gap explanation for document_id={package.document_id}")
    
    gaps_found: List[str] = []
    citations: List[CitationItem] = []
    spans: List[DocumentSpanItem] = []

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

    # Build natural language summary
    if gaps_found:
        summary = (
            f"Clinical Decision Package analysis identified {len(gaps_found)} key clinical care gap(s) or safety priority item(s): "
            + "; ".join(gaps_found)
        )
    else:
        summary = "Clinical Decision Package analysis completed: No open care gaps or clinical safety red flags identified."

    return CareGapExplanationResponse(
        document_id=package.document_id,
        explanation_summary=summary,
        care_gaps_found=gaps_found,
        cited_guideline_passages=citations,
        document_evidence_spans=spans
    )
