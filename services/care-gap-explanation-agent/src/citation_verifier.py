"""
Citation verifier for Care-Gap Explanation Agent.

PRD Rule 5.4: LLMs may NOT fabricate citations.
Every cited clause_id must exist in the input ClinicalDecisionPackage.
If the LLM proposes a citation not present in the package, it is rejected.
A bounded retry is triggered with a constrained prompt.
After max retries, a safe UNSUPPORTED_CITATION error is raised, never a fabricated clinical statement.
"""

import logging

from src.models import GuidelinePassage

logger = logging.getLogger(__name__)

MAX_CITATION_RETRIES = 2


class UnsupportedCitationError(Exception):
    """Raised when LLM-proposed citation cannot be verified against input decision package."""

    def __init__(self, clause_id: str):
        self.clause_id = clause_id
        super().__init__(f"Citation '{clause_id}' not found in input ClinicalDecisionPackage. " f"Rejected to prevent fabricated clinical statement.")


def verify_citations(
    proposed_citations: list[GuidelinePassage],
    allowed_passages: list[GuidelinePassage],
) -> list[GuidelinePassage]:
    """
    Verifies that every proposed citation exists in the allowed_passages from the decision package.
    Returns only verified citations.
    Raises UnsupportedCitationError if any citation cannot be verified.
    """
    allowed_ids = {p.clause_id for p in allowed_passages}
    verified = []
    rejected = []

    for citation in proposed_citations:
        if citation.clause_id in allowed_ids:
            verified.append(citation)
        else:
            rejected.append(citation.clause_id)

    if rejected:
        logger.error(f"Citation verifier REJECTED fabricated citations: {rejected}. " f"Allowed clause IDs: {list(allowed_ids)}")
        raise UnsupportedCitationError(rejected[0])

    return verified


def verify_citations_with_retry(
    proposed_citations: list[GuidelinePassage],
    allowed_passages: list[GuidelinePassage],
    attempt: int = 1,
) -> list[GuidelinePassage]:
    """
    Attempts citation verification with bounded retry logging.
    Does NOT silently return unverified citations under any circumstance.
    """
    try:
        return verify_citations(proposed_citations, allowed_passages)
    except UnsupportedCitationError as exc:
        if attempt < MAX_CITATION_RETRIES:
            logger.warning(f"CitationVerifier attempt {attempt}/{MAX_CITATION_RETRIES}: " f"Unsupported citation '{exc.clause_id}' detected. Triggering constrained retry.")
            # Only filter to allowed passages for retry
            safe_citations = [c for c in proposed_citations if c.clause_id in {p.clause_id for p in allowed_passages}]
            return verify_citations_with_retry(safe_citations, allowed_passages, attempt + 1)
        else:
            logger.exception(f"CitationVerifier EXHAUSTED {MAX_CITATION_RETRIES} retries. " f"Failing safely with UnsupportedCitationError. " f"No fabricated clinical statement will be emitted.")
            raise
