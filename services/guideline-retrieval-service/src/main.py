from fastapi import FastAPI, HTTPException

from src.config import settings
from src.logger import logger
from src.models import GuidelineQueryRequest, GuidelineQueryResponse
from src.vector_store import vector_store

app = FastAPI(
    title=settings.service_name,
    description="Guideline RAG Vector Store & Semantic Retrieval Microservice",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "relevance_threshold": settings.relevance_threshold
    }

@app.post("/guidelines/retrieve", response_model=GuidelineQueryResponse)
async def retrieve_guideline_passages(request: GuidelineQueryRequest):
    """Retrieves semantic guideline passages with section/clause metadata filtering and threshold validation."""
    logger.info(f"Retrieving guidelines for query='{request.query}'")
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query string cannot be empty")

    response = vector_store.search_guidelines(
        query=request.query,
        threshold_override=request.min_relevance_score,
        metadata_filter=request.metadata_filter
    )
    return response
