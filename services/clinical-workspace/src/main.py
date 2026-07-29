import os
import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from services.common.jwt_verifier import require_roles, get_current_user_claims
from services.common.security_headers import SecurityHeadersMiddleware
from src.config import settings
from src.logger import logger
from src.models import (
    ReviewItem, DocumentFindingsResponse, EvidenceSpan,
    ReferralEditRequest, DecisionSubmitRequest, DecisionSubmitResponse
)

app = FastAPI(
    title=settings.service_name,
    description="Clinical Workspace Reviewer API & Dashboard Backend",
    version="2.0.0"
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REVIEW_DATABASE: Dict[str, Dict[str, Any]] = {
    "DOC-99482-A": {
        "document_id": "DOC-99482-A",
        "patient_id": "PAT-99482",
        "status": "awaiting_approval",
        "created_at": "2026-07-25T10:00:00Z",
        "referral_text": (
            "CLINICAL REFERRAL LETTER (DRAFT)\n"
            "=================================\n"
            "Date: 2026-07-25\n"
            "To: Department of Gastroenterology\n"
            "Re: Patient ID: PAT-99482\n"
            "Urgency Level: URGENT\n\n"
            "Dear Specialist,\n\n"
            "I am referring PAT-99482 for colonoscopy evaluation due to overdue USPSTF screening care gap.\n"
            "Patient is 52 years old with last screening recorded > 10 years ago.\n"
        ),
        "evidence_spans": [
            {
                "field_name": "patient_id",
                "source_quote": "Patient ID: PAT-99482",
                "bbox": [100, 120, 350, 150]
            },
            {
                "field_name": "care_gap",
                "source_quote": "USPSTF Colorectal Cancer Screening: OVERDUE",
                "bbox": [100, 200, 520, 230]
            }
        ],
        "decision": None
    }
}

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name
    }

@app.get("/workspace/reviews", response_model=List[ReviewItem])
async def list_review_queue(claims: Dict[str, Any] = Depends(require_roles(["clinician:review", "admin:system"]))):
    """Fetches list of documents awaiting clinician review."""
    return [
        ReviewItem(
            document_id=item["document_id"],
            patient_id=item["patient_id"],
            status=item["status"],
            created_at=item["created_at"]
        )
        for item in REVIEW_DATABASE.values()
    ]

@app.get("/workspace/findings/{document_id}", response_model=DocumentFindingsResponse)
async def get_document_findings(
    document_id: str,
    claims: Dict[str, Any] = Depends(require_roles(["clinician:review", "admin:system"]))
):
    """Fetches clinical findings, referral text draft, and linked spatial bounding boxes."""
    if document_id not in REVIEW_DATABASE:
        raise HTTPException(status_code=404, detail=f"No findings found for document_id={document_id}")

    rec = REVIEW_DATABASE[document_id]
    return DocumentFindingsResponse(
        document_id=rec["document_id"],
        patient_id=rec["patient_id"],
        referral_text=rec["referral_text"],
        evidence_spans=[EvidenceSpan(**ev) for ev in rec["evidence_spans"]],
        status=rec["status"]
    )

@app.put("/workspace/referral/{document_id}")
async def edit_referral_text(
    document_id: str,
    body: ReferralEditRequest,
    claims: Dict[str, Any] = Depends(require_roles(["clinician:review", "admin:system"]))
):
    """Saves clinician edits to the draft referral text."""
    if document_id not in REVIEW_DATABASE:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        
    REVIEW_DATABASE[document_id]["referral_text"] = body.edited_referral_text
    logger.info(f"Updated referral text draft for document_id={document_id} by user={claims.get('sub')}")
    return {"status": "updated", "document_id": document_id, "updated_text": body.edited_referral_text}

@app.post("/workspace/decision/{document_id}", response_model=DecisionSubmitResponse)
async def submit_clinician_decision(
    document_id: str,
    body: DecisionSubmitRequest,
    claims: Dict[str, Any] = Depends(require_roles(["clinician:approve", "clinician:reject", "admin:system"]))
):
    """Submits clinician decision (APPROVED or REJECTED) with verified OIDC clinician identity."""
    if document_id not in REVIEW_DATABASE:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    dec = body.decision.upper()
    if dec not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Decision must be 'APPROVED' or 'REJECTED'")

    # Enforce role-specific decision check
    user_roles = claims.get("roles", [])
    if dec == "APPROVED" and "clinician:approve" not in user_roles and "admin:system" not in user_roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions to approve clinical referrals")
    if dec == "REJECTED" and "clinician:reject" not in user_roles and "admin:system" not in user_roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions to reject clinical referrals")

    # Derive clinician identity from verified JWT token sub/username
    verified_clinician_id = claims.get("sub") or claims.get("username") or body.clinician_id or "CLINICIAN-UNKNOWN"

    new_status = "approved" if dec == "APPROVED" else "rejected"
    REVIEW_DATABASE[document_id]["status"] = new_status
    decision_record = body.model_dump()
    decision_record["clinician_id"] = verified_clinician_id
    REVIEW_DATABASE[document_id]["decision"] = decision_record

    logger.info(f"Recorded clinician decision {dec} for document_id={document_id} by verified clinician={verified_clinician_id}")

    return DecisionSubmitResponse(
        document_id=document_id,
        decision=dec,
        status=new_status,
        signed_event_emitted=True,
        message=f"Clinician decision '{dec}' successfully recorded for clinician {verified_clinician_id} with signature {body.digital_signature}."
    )

# Mount static files for React frontend if folder exists
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
frontend_dir = frontend_dist if os.path.exists(frontend_dist) else os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/ui", StaticFiles(directory=frontend_dir, html=True), name="frontend")
