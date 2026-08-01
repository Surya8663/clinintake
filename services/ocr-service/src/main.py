import io
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

from src.config import settings
from src.logger import logger
from src.models import OCRResponse
from src.ocr_engine import process_image_with_tesseract, process_pdf_with_pypdf

app = FastAPI(title=settings.service_name, description="Spatial Optical Character Recognition (OCR) Service", version="1.0.0")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}


@app.post("/ocr/process", response_model=OCRResponse)
async def process_document(file: UploadFile = File(...)):
    """Processes document (Image/PDF) and returns full text with spatial bounding box coordinates."""
    logger.info(f"Processing document upload: {file.filename}, content_type={file.content_type}")
    doc_id = str(uuid.uuid4())
    content = await file.read()

    pages = []
    engine_used = "tesseract_spatial"

    filename_lower = (file.filename or "").lower()
    if filename_lower.endswith(".pdf") or file.content_type == "application/pdf":
        logger.info("PDF document detected, parsing PDF spatial bounding boxes")
        pages = process_pdf_with_pypdf(content)
        engine_used = "pypdf_spatial"
    else:
        try:
            image = Image.open(io.BytesIO(content))
            page = process_image_with_tesseract(image, page_number=1)
            pages.append(page)
        except Exception as e:
            logger.error(f"Failed to open image for OCR: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid image file: {e!s}")

    full_text = "\n\n".join([p.text for p in pages])

    return OCRResponse(document_id=doc_id, pages=pages, full_text=full_text, engine_used=engine_used)
