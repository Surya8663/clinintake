import uuid
import httpx
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status

from src.config import settings
from src.logger import logger
from src.auth import verify_jwt_token
from src.kms_store import doc_store

app = FastAPI(
    title=settings.service_name,
    description="Document Gateway - Clinical Boundary API",
    version="0.1.0"
)

@app.post("/gateway/upload")
async def upload_document(
    file: UploadFile = File(...),
    auth_payload: dict = Depends(verify_jwt_token)
):
    document_id = str(uuid.uuid4())
    logger.info(
        f"Multipart upload request from user '{auth_payload.get('sub')}'",
        extra={"uploaded_file_name": file.filename, "document_id": document_id}
    )
    
    file_bytes = await file.read()
    
    # Enforce Architecture: Must scan with security-filter BEFORE writing to storage
    async with httpx.AsyncClient() as client:
        files = {"file": (file.filename, file_bytes, file.content_type)}
        try:
            logger.info(f"Forwarding document {document_id} to security filter at {settings.security_filter_url}")
            response = await client.post(
                settings.security_filter_url,
                files=files,
                timeout=15.0
            )
            response.raise_for_status()
            scan_result = response.json()
        except Exception as e:
            logger.error(
                "Clinical DMZ Scan invocation failed. Failing closed.",
                extra={"error": str(e), "document_id": document_id}
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Clinical boundary safety check unavailable: {str(e)}"
            )

    # Rejection logic based on scan results
    if not scan_result.get("is_safe"):
        logger.warning(
            "Upload blocked: Document failed security filter guidelines",
            extra={"document_id": document_id, "reason": scan_result.get("reason")}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security violation detected: {scan_result.get('reason')}"
        )

    # If cleared, write to KMS-managed AES-256 storage
    try:
        stored_path = doc_store.write_encrypted_file(document_id, file_bytes)
    except Exception as e:
        logger.error(
            "Document persistence failure in KMS store",
            extra={"document_id": document_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store sanitized document."
        )

    return {
        "status": "success",
        "document_id": document_id,
        "filename": file.filename,
        "storage_path": stored_path,
        "message": "Document uploaded, sanitized, and stored securely."
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}
