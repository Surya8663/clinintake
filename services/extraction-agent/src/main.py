import uuid
from fastapi import FastAPI, HTTPException

from src.config import settings
from src.logger import logger
from src.models import ExtractRequest, ExtractResponse
from src.extractor import perform_quote_grounded_extraction
from src.fhir_validator import build_and_validate_fhir_resources

app = FastAPI(
    title=settings.service_name,
    description="Quote-Grounded LLM Extraction Agent with FHIR R4 Validation",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "confidence_threshold": settings.confidence_threshold
    }

@app.post("/extract", response_model=ExtractResponse)
async def extract_clinical_data(request: ExtractRequest):
    """Performs Quote-Grounded extraction, low-confidence field masking ('Incomplete'), and FHIR R4 validation."""
    logger.info(f"Extracting clinical data for document_id={request.document_id}")
    
    ocr_text = request.ocr_text or ""
    ocr_words = request.ocr_words or []
    
    if not ocr_text:
        raise HTTPException(status_code=400, detail="ocr_text must be provided")

    extracted_data = perform_quote_grounded_extraction(
        ocr_text=ocr_text,
        ocr_words=ocr_words,
        threshold_override=settings.confidence_threshold
    )

    fhir_resources = build_and_validate_fhir_resources(extracted_data)

    # Compute overall confidence
    scores = [extracted_data.patient_id.confidence]
    for d in extracted_data.diagnoses:
        scores.append(d.name.confidence)
    for m in extracted_data.medications:
        scores.append(m.name.confidence)
    for l in extracted_data.labs:
        scores.append(l.name.confidence)

    overall_confidence = round(sum(scores) / max(len(scores), 1), 2)

    return ExtractResponse(
        document_id=request.document_id,
        extracted_data=extracted_data,
        fhir_resources=fhir_resources,
        overall_confidence=overall_confidence
    )
