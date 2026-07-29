from typing import Dict, Any, Optional
from src.models import GuidelineQueryResponse
from src.qdrant_repository import qdrant_repo

class GuidelineVectorStore:
    """Qdrant-backed hybrid RAG vector store facade."""
    
    def search_guidelines(
        self,
        query: str,
        threshold_override: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> GuidelineQueryResponse:
        """Queries Qdrant hybrid vector store with dense and sparse fusion."""
        return qdrant_repo.search_guidelines(
            query=query,
            threshold_override=threshold_override,
            metadata_filter=metadata_filter
        )

vector_store = GuidelineVectorStore()
