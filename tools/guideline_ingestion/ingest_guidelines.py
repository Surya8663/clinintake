import os
import sys
import json
import hashlib
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "services" / "guideline-retrieval-service"))

from src.config import settings
from src.models import GuidelineChunk
from src.qdrant_repository import qdrant_repo

def compute_sha256(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode('utf-8')).hexdigest()

def ingest_from_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        raw_items = json.load(f)

    chunks = []
    for idx, item in enumerate(raw_items):
        text = item.get("text", "")
        chunk_checksum = compute_sha256(text)
        doc_checksum = item.get("document_checksum") or compute_sha256(item.get("title", "") + text)
        chunk_id = f"{item.get('guideline_id', 'G')}-C{idx + 1}"

        chunk = GuidelineChunk(
            chunk_id=chunk_id,
            guideline_id=item.get("guideline_id", "USPSTF-GENERIC"),
            source_organization=item.get("source_organization", "USPSTF"),
            title=item.get("title", "Clinical Recommendation"),
            version=item.get("version", "2024-V1"),
            effective_date=item.get("effective_date", "2024-01-01"),
            review_or_expiry_date=item.get("review_or_expiry_date"),
            jurisdiction=item.get("jurisdiction", "US"),
            section=item.get("section", "General Recommendation"),
            recommendation_strength=item.get("recommendation_strength", "Grade A"),
            population_tags=item.get("population_tags", []),
            source_url=item.get("source_url"),
            document_checksum=doc_checksum,
            chunk_checksum=chunk_checksum,
            page=item.get("page", 1),
            text=text,
            clause_id=item.get("clause_id", f"CLAUSE-{idx + 1}"),
            is_active=item.get("is_active", True)
        )
        chunks.append(chunk)

    inserted_count = qdrant_repo.upsert_chunks(chunks)

    report = {
        "status": "SUCCESS",
        "manifest_path": str(manifest_path),
        "total_documents": len(raw_items),
        "total_chunks_upserted": inserted_count,
        "collection_name": qdrant_repo.collection_name,
        "qdrant_url": getattr(qdrant_repo.get_client(), "url", str(settings.qdrant_url))
    }
    return report

def main():
    parser = argparse.ArgumentParser(description="Clinical Guideline Qdrant Hybrid RAG Ingestion CLI")
    parser.add_argument("--manifest", type=str, default=str(REPO_ROOT / "tools" / "guideline_ingestion" / "sample_uspstf_guidelines.json"), help="Path to guideline JSON manifest file")
    args = parser.parse_args()

    manifest_p = Path(args.manifest)
    print(f"[INGEST] Starting clinical guideline ingestion from {manifest_p.name}...")
    try:
        report = ingest_from_manifest(manifest_p)
        print("==================================================")
        print(" CLINICAL GUIDELINE QDRANT INGESTION REPORT")
        print("==================================================")
        print(json.dumps(report, indent=2))
        print("==================================================")
    except Exception as e:
        print(f"[ERROR] Ingestion failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
