from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from services.common.security_headers import SecurityHeadersMiddleware
from packages.clinical_contracts import ApiErrorEnvelope
from src.config import settings
from src.logger import logger
from src.models import GuidelineQueryRequest, GuidelineQueryResponse
from src.qdrant_repository import qdrant_repo, QdrantUnavailableError, QdrantCollectionError

app = FastAPI(
    title=settings.service_name,
    description="Guideline Hybrid RAG Vector Store & Retrieval Microservice",
    version="2.0.0"
)

app.add_middleware(SecurityHeadersMiddleware)

@app.get("/health")
async def health_check():
    qdrant_connected = False
    try:
        qdrant_connected = qdrant_repo.check_health()
    except Exception:
        qdrant_connected = False

    return {
        "status": "ok" if qdrant_connected else "degraded",
        "service": settings.service_name,
        "qdrant_connected": qdrant_connected,
        "qdrant_url": settings.qdrant_url,
        "relevance_threshold": settings.relevance_threshold
    }

@app.post("/guidelines/retrieve", response_model=GuidelineQueryResponse)
async def retrieve_guideline_passages(request: GuidelineQueryRequest):
    """Retrieves evidence passages using Qdrant hybrid search (dense + sparse fusion) with payload filtering."""
    logger.info(f"Retrieving guidelines for query='{request.query}'")
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query string cannot be empty")

    try:
        response = qdrant_repo.search_guidelines(
            query=request.query,
            threshold_override=request.min_relevance_score,
            metadata_filter=request.metadata_filter
        )
        return response
    except QdrantUnavailableError as e:
        logger.error(f"Qdrant server unavailable: {e}")
        err_envelope = ApiErrorEnvelope(
            code="GUIDELINE_VECTOR_DB_UNAVAILABLE",
            message=f"Guideline retrieval vector database unavailable at {settings.qdrant_url}. Fallback forbidden.",
            retryable=True,
            dependency="qdrant"
        )
        return JSONResponse(status_code=503, content=err_envelope.model_dump())
    except Exception as e:
        logger.error(f"Error querying guideline vector store: {e}")
        err_envelope = ApiErrorEnvelope(
            code="GUIDELINE_RETRIEVAL_ERROR",
            message=f"An error occurred while executing guideline hybrid search: {str(e)}",
            retryable=False,
            dependency="guideline-retrieval-service"
        )
        return JSONResponse(status_code=500, content=err_envelope.model_dump())
