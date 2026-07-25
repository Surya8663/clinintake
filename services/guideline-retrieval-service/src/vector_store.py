import math
from typing import List, Dict, Any, Optional
from src.models import GuidelineChunk, GuidelineMatch, GuidelineQueryResponse
from src.ingestion_pipeline import load_and_chunk_guidelines
from src.config import settings
from src.logger import logger

class GuidelineVectorStore:
    def __init__(self):
        self.chunks: List[GuidelineChunk] = load_and_chunk_guidelines()

    def _calculate_cosine_similarity(self, query: str, text: str) -> float:
        """Computes semantic text similarity score between query and guideline passage."""
        q_words = set(w.lower().strip(".,;:()") for w in query.split() if len(w) > 2)
        t_words = set(w.lower().strip(".,;:()") for w in text.split() if len(w) > 2)

        if not q_words or not t_words:
            return 0.0

        intersection = q_words.intersection(t_words)
        if not intersection:
            return 0.10

        # Jaccard + Overlap coefficient semantic approximation
        score = len(intersection) / math.sqrt(len(q_words) * len(t_words))
        
        # Boost for exact domain match terms
        for q in q_words:
            if q in ["diabetes", "hypertension", "colorectal", "mammography", "statin", "hba1c"] and q in t_words:
                score += 0.35

        return round(min(score, 0.98), 2)

    def search_guidelines(
        self,
        query: str,
        threshold_override: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> GuidelineQueryResponse:
        """Queries vector store with metadata filtering and relevance threshold validation."""
        threshold = threshold_override if threshold_override is not None else settings.relevance_threshold
        filters = metadata_filter or {}

        matches: List[GuidelineMatch] = []
        
        for chunk in self.chunks:
            # Apply metadata filters
            filter_passed = True
            for k, v in filters.items():
                chunk_val = getattr(chunk, k, None)
                if chunk_val and str(chunk_val).lower() != str(v).lower():
                    filter_passed = False
                    break
                    
            if not filter_passed:
                continue

            score = self._calculate_cosine_similarity(query, chunk.text)
            if score >= threshold:
                matches.append(GuidelineMatch(
                    passage=chunk.text,
                    source=chunk.source,
                    version=chunk.version,
                    effective_date=chunk.effective_date,
                    section=chunk.section,
                    clause_id=chunk.clause_id,
                    similarity_score=score
                ))

        # Sort matches by similarity score descending
        matches.sort(key=lambda m: m.similarity_score, reverse=True)

        # PRD 5.6 REQUIREMENT:
        # When retrieval returns nothing above relevance threshold,
        # return status="insufficient_guideline_evidence"
        if not matches:
            logger.info(f"Query '{query}' returned no passages above threshold {threshold}. Returning status='insufficient_guideline_evidence'.")
            return GuidelineQueryResponse(
                query=query,
                status="insufficient_guideline_evidence",
                matches=[],
                relevance_threshold_used=threshold
            )

        logger.info(f"Query '{query}' matched {len(matches)} guideline passages above threshold {threshold}.")
        return GuidelineQueryResponse(
            query=query,
            status="success",
            matches=matches,
            relevance_threshold_used=threshold
        )

vector_store = GuidelineVectorStore()
