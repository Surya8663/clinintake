from src.logger import logger
from src.models import GuidelineChunk
from src.qdrant_repository import qdrant_repo


def ingest_guideline_chunks(chunks: list[GuidelineChunk]) -> int:
    """Ingests clinical guideline chunks idempotently into Qdrant collection."""
    logger.info(f"Ingesting {len(chunks)} clinical guideline chunks into Qdrant vector store.")
    return qdrant_repo.upsert_chunks(chunks)
