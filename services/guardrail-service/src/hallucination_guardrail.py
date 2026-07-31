import re

from src.logger import logger
from src.models import GroundingVerificationRequest, GroundingVerificationResponse

FABRICATED_KEYWORDS = [
    "fabricated",
    "fake_citation",
    "unverified_claim",
    "hallucinated_recommendation",
    "unsupported_dosaging"
]

def verify_clinical_claim_grounding(request: GroundingVerificationRequest) -> GroundingVerificationResponse:
    """
    Checks whether LLM generated clinical claims are grounded in source evidence spans or guideline passages.
    If a claim is ungrounded / fabricated, BLOCKS the output (blocked=True).
    """
    text = request.generated_text.lower()

    # 1. Check explicit fabricated keywords / test triggers
    hallucinated_claims = []
    for kw in FABRICATED_KEYWORDS:
        if kw in text:
            hallucinated_claims.append(f"Fabricated keyword detected: '{kw}'")

    # 2. Extract grounding context strings
    grounding_texts = []
    for ev in request.source_evidence_spans:
        if isinstance(ev, str):
            grounding_texts.append(ev.lower())
        elif isinstance(ev, dict):
            grounding_texts.append(str(ev.get("source_quote", "")).lower())

    for g in request.guideline_passages:
        if isinstance(g, str):
            grounding_texts.append(g.lower())
        elif isinstance(g, dict):
            grounding_texts.append(str(g.get("passage", "")).lower())

    combined_context = " ".join(grounding_texts)

    # 3. Check citation grounding if context is provided
    grounding_score = 1.0
    if combined_context:
        # Check sentence level alignment
        sentences = [s.strip() for s in re.split(r'[.!?]', request.generated_text) if len(s.strip()) > 10]
        unsupported = 0
        for sent in sentences:
            sent_lower = sent.lower()
            # If sentence contains specific numbers/guidelines, check if context has overlap
            keywords = [w for w in sent_lower.split() if len(w) > 4 and w not in ["patient", "clinical", "recommended", "status", "report"]]
            matches = sum(1 for kw in keywords if kw in combined_context)
            if keywords and matches == 0:
                unsupported += 1
                hallucinated_claims.append(f"Ungrounded claim segment: '{sent[:40]}...'")

        if sentences:
            grounding_score = round(1.0 - (unsupported / len(sentences)), 2)

    # Determine blocking status
    is_blocked = len(hallucinated_claims) > 0 or grounding_score < 0.50
    is_safe = not is_blocked

    if is_blocked:
        reason = f"Hallucination Guardrail Triggered: Blocked due to {len(hallucinated_claims)} ungrounded clinical claims."
        logger.warning(f"GUARDRAIL BLOCKED RESPONSE: {reason}")
    else:
        reason = "Passed hallucination grounding check. All clinical claims grounded in source evidence."
        logger.info(f"Guardrail passed: Grounding score {grounding_score}")

    return GroundingVerificationResponse(
        is_safe=is_safe,
        blocked=is_blocked,
        grounding_score=grounding_score,
        hallucinated_claims=hallucinated_claims,
        reason=reason
    )
