from fastapi import FastAPI, HTTPException

from src.config import settings
from src.drafting_engine import generate_referral_draft_letter
from src.logger import logger
from src.models import ReferralDraftRequest, ReferralDraftResponse

app = FastAPI(
    title=settings.service_name,
    description="Referral Drafting Agent for Grounded Specialist Letters",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name
    }

@app.post("/referral/draft", response_model=ReferralDraftResponse)
async def draft_referral_letter(request: ReferralDraftRequest):
    """Generates a real draft referral letter grounded in Clinical Decision Package context."""
    logger.info(f"Received referral drafting request for document_id={request.document_id}")

    if not request.document_id:
        raise HTTPException(status_code=400, detail="document_id must be provided")

    response = generate_referral_draft_letter(request)
    return response
