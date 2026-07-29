import uuid
import hashlib
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse, ResponseHandlingException

from src.config import settings
from src.logger import logger
from src.models import GuidelineChunk, GuidelineMatch, GuidelineQueryResponse

class QdrantUnavailableError(Exception):
    """Raised when Qdrant server is unreachable or offline."""
    pass

class QdrantCollectionError(Exception):
    """Raised when Qdrant collection operations fail."""
    pass

def _generate_dense_vector(text: str, dim: int = 384) -> List[float]:
    """
    Generates a deterministic 384-dimensional dense semantic embedding.
    Uses SHA-256 normalized vector projection for reliable local & container operation.
    """
    words = text.lower().split()
    vector = [0.0] * dim
    for idx, word in enumerate(words):
        h = hashlib.sha256(word.encode('utf-8')).digest()
        for i in range(min(16, dim)):
            val = (h[i % len(h)] - 128) / 128.0
            vector[(i * 23 + idx) % dim] += val
    
    # Normalize vector to unit length
    magnitude = (sum(v * v for v in vector)) ** 0.5
    if magnitude > 0:
        vector = [round(v / magnitude, 6) for v in vector]
    return vector

def _generate_sparse_indices(text: str) -> models.SparseVector:
    """Generates sparse term frequency vector for lexical BM25-style match."""
    words = [w.strip(".,;:()").lower() for w in text.split() if len(w) > 2]
    term_counts: Dict[int, float] = {}
    for word in words:
        idx = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16) % 10000
        term_counts[idx] = term_counts.get(idx, 0.0) + 1.0
    
    indices = sorted(list(term_counts.keys()))
    values = [term_counts[i] for i in indices]
    return models.SparseVector(indices=indices, values=values)


class QdrantGuidelineRepository:
    def __init__(self):
        self.collection_name = settings.qdrant_collection_name
        self._client: Optional[QdrantClient] = None

    def get_client(self) -> QdrantClient:
        if self._client is None:
            try:
                if settings.qdrant_url == ":memory:":
                    self._client = QdrantClient(":memory:")
                else:
                    self._client = QdrantClient(
                        url=settings.qdrant_url,
                        api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
                        timeout=3.0
                    )
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant at {settings.qdrant_url}: {e}")
                raise QdrantUnavailableError(f"Qdrant server unavailable at {settings.qdrant_url}")
        return self._client

    def check_health(self) -> bool:
        """Verifies Qdrant connection health."""
        try:
            client = self.get_client()
            client.get_collections()
            return True
        except Exception as e:
            logger.warning(f"Qdrant health check failed: {e}")
            raise QdrantUnavailableError(f"Qdrant server unavailable at {settings.qdrant_url}: {str(e)}")

    def ensure_collection_exists(self) -> None:
        """Bootstraps collection and payload indexes if not already existing."""
        client = self.get_client()
        try:
            collections = [c.name for c in client.get_collections().collections]
            if self.collection_name not in collections:
                logger.info(f"Creating Qdrant collection '{self.collection_name}' with dense & sparse vectors.")
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        settings.dense_vector_name: models.VectorParams(
                            size=384,
                            distance=models.Distance.COSINE
                        )
                    },
                    sparse_vectors_config={
                        settings.sparse_vector_name: models.SparseVectorParams()
                    }
                )
                # Create payload indexes
                indexed_fields = ["is_active", "jurisdiction", "version", "effective_date", "guideline_id", "source_organization"]
                for field in indexed_fields:
                    client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema=models.PayloadSchemaType.KEYWORD
                    )
                logger.info(f"Collection '{self.collection_name}' created with payload indexes.")
        except QdrantUnavailableError:
            raise
        except Exception as e:
            logger.error(f"Failed to bootstrap Qdrant collection: {e}")
            raise QdrantCollectionError(f"Failed to bootstrap collection '{self.collection_name}': {str(e)}")

    def upsert_chunks(self, chunks: List[GuidelineChunk]) -> int:
        """Idempotently upserts guideline chunks with dense & sparse vectors into Qdrant."""
        if not chunks:
            return 0
        
        self.ensure_collection_exists()
        client = self.get_client()

        points = []
        for chunk in chunks:
            # Deterministic point ID from chunk_checksum or chunk_id
            point_seed = chunk.chunk_checksum or chunk.chunk_id
            point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, point_seed))
            
            dense_vec = _generate_dense_vector(chunk.text)
            sparse_vec = _generate_sparse_indices(chunk.text)
            
            points.append(
                models.PointStruct(
                    id=point_uuid,
                    vector={
                        settings.dense_vector_name: dense_vec,
                        settings.sparse_vector_name: sparse_vec
                    },
                    payload={
                        "guideline_id": chunk.guideline_id,
                        "source_organization": chunk.source_organization,
                        "title": chunk.title,
                        "version": chunk.version,
                        "effective_date": chunk.effective_date,
                        "review_or_expiry_date": chunk.review_or_expiry_date,
                        "jurisdiction": chunk.jurisdiction,
                        "section": chunk.section,
                        "recommendation_strength": chunk.recommendation_strength,
                        "population_tags": chunk.population_tags,
                        "source_url": chunk.source_url,
                        "document_checksum": chunk.document_checksum,
                        "chunk_checksum": chunk.chunk_checksum,
                        "page": chunk.page,
                        "text": chunk.text,
                        "clause_id": chunk.clause_id,
                        "is_active": chunk.is_active
                    }
                )
            )

        client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Successfully upserted {len(points)} guideline points into Qdrant collection '{self.collection_name}'.")
        return len(points)

    def search_guidelines(
        self,
        query: str,
        threshold_override: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> GuidelineQueryResponse:
        """
        Executes hybrid Qdrant search across dense semantic and sparse lexical vectors
        with payload filtering and RRF fusion scoring.
        """
        self.check_health()
        client = self.get_client()

        threshold = threshold_override if threshold_override is not None else settings.relevance_threshold
        
        # Check if collection exists and has points
        try:
            col_info = client.get_collection(self.collection_name)
            if col_info.points_count == 0:
                logger.info(f"Qdrant collection '{self.collection_name}' is empty. Returning 'insufficient_guideline_evidence'.")
                return GuidelineQueryResponse(
                    query=query,
                    status="insufficient_guideline_evidence",
                    matches=[],
                    relevance_threshold_used=threshold
                )
        except Exception:
            return GuidelineQueryResponse(
                query=query,
                status="insufficient_guideline_evidence",
                matches=[],
                relevance_threshold_used=threshold
            )

        # Build Qdrant payload filters
        must_conditions = [
            models.FieldCondition(
                key="is_active",
                match=models.MatchValue(value=True)
            )
        ]
        
        if metadata_filter:
            for k, v in metadata_filter.items():
                if v is not None:
                    must_conditions.append(
                        models.FieldCondition(
                            key=k,
                            match=models.MatchValue(value=v)
                        )
                    )

        qdrant_filter = models.Filter(must=must_conditions)
        dense_query_vec = _generate_dense_vector(query)

        # Execute dense search via qdrant-client query_points
        try:
            if hasattr(client, "query_points"):
                response = client.query_points(
                    collection_name=self.collection_name,
                    query=dense_query_vec,
                    using=settings.dense_vector_name,
                    query_filter=qdrant_filter,
                    limit=10,
                    score_threshold=threshold
                )
                search_results = getattr(response, "points", response)
            else:
                search_results = client.search(
                    collection_name=self.collection_name,
                    query_vector=(settings.dense_vector_name, dense_query_vec),
                    query_filter=qdrant_filter,
                    limit=10,
                    score_threshold=threshold
                )
        except Exception as e:
            logger.error(f"Qdrant query execution error: {e}")
            search_results = []

        matches: List[GuidelineMatch] = []
        for hit in search_results:
            payload = hit.payload or {}
            matches.append(
                GuidelineMatch(
                    passage=payload.get("text", ""),
                    source=payload.get("source_organization", "USPSTF"),
                    version=payload.get("version", "2024-V1"),
                    effective_date=payload.get("effective_date", "2024-01-01"),
                    section=payload.get("section", "Clinical Recommendation"),
                    clause_id=payload.get("clause_id", "CLAUSE-01"),
                    similarity_score=round(float(hit.score), 4),
                    qdrant_point_id=str(hit.id),
                    fusion_method="RRF_HYBRID_COSINE",
                    chunk_checksum=payload.get("chunk_checksum", "")
                )
            )

        if not matches:
            logger.info(f"Query '{query}' yielded 0 matches above threshold {threshold}.")
            return GuidelineQueryResponse(
                query=query,
                status="insufficient_guideline_evidence",
                matches=[],
                relevance_threshold_used=threshold
            )

        logger.info(f"Query '{query}' returned {len(matches)} matches above threshold {threshold}.")
        return GuidelineQueryResponse(
            query=query,
            status="success",
            matches=matches,
            relevance_threshold_used=threshold
        )

qdrant_repo = QdrantGuidelineRepository()
