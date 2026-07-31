from typing import Any

from src.models import GuidelineQueryResponse
from src.qdrant_repository import qdrant_repo


class GuidelineVectorStore:
    """Qdrant-backed hybrid RAG vector store facade."""
    
    def search_guidelines(
        self,
        query: str,
        threshold_override: float | None = None,
        metadata_filter: dict[str, Any] | None = None
    ) -> GuidelineQueryResponse:
        """Queries Qdrant hybrid vector store with dense and sparse fusion."""
        return qdrant_repo.search_guidelines(
            query=query,
            threshold_override=threshold_override,
            metadata_filter=metadata_filter
        )

vector_store = GuidelineVectorStore()
