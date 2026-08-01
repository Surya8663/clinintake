import io

from fastapi import FastAPI, File, UploadFile
import filetype
from pypdf import PdfReader

from src.clamav import ClamAVScanner
from src.config import settings
from src.logger import logger
from src.prompt_injection import PromptInjectionDetector

app = FastAPI(title=settings.service_name, description="Document Security Filter - Clinical DMZ Scanner", version="0.1.0")

clamav_scanner = ClamAVScanner()
injection_detector = PromptInjectionDetector()


@app.post("/filter/scan")
async def scan_document(file: UploadFile = File(...)):
    logger.info(f"Initiating security scan for document: {file.filename}")

    file_bytes = await file.read()

    # 1. MIME Validation
    kind = filetype.guess(file_bytes)
    if not kind or kind.mime != "application/pdf":
        mime_found = kind.mime if kind else "unknown"
        logger.warning(f"MIME type validation failed for {file.filename}", extra={"mime_found": mime_found})
        return {"is_safe": False, "reason": f"MIME check failed. Expected application/pdf, but resolved as {mime_found}."}

    # 2. Malware Scan (ClamAV)
    is_malware_safe, malware_reason = clamav_scanner.scan_bytes(file_bytes)
    if not is_malware_safe:
        logger.warning(f"Malware detection scanner triggered for {file.filename}", extra={"reason": malware_reason})
        return {"is_safe": False, "reason": malware_reason}

    # 3. Prompt Injection (extract text and evaluate)
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        is_injection_safe, injection_reason = injection_detector.scan_text(full_text)
        if not is_injection_safe:
            logger.warning(f"Prompt injection validation triggered for {file.filename}", extra={"reason": injection_reason})
            return {"is_safe": False, "reason": injection_reason}

    except Exception as e:
        logger.error(f"Error processing PDF structure for prompt injection check on {file.filename}", extra={"error": str(e)})
        return {"is_safe": False, "reason": f"Failed to extract document contents: {e!s}"}

    logger.info(f"Document {file.filename} passed all Clinical DMZ scanning stages successfully.")
    return {"is_safe": True, "reason": "Document cleared scan validation."}


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}
