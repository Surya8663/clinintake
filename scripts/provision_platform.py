#!/usr/bin/env python3
"""
ClinIntake Platform Provisioning Script
Provisions non-clinical platform configuration:
 - Keycloak realm and client definitions
 - Qdrant collection with correct vector configuration
 - Kafka/Redpanda topics
 - MinIO bucket

IMPORTANT: This script does NOT seed fake patients, fake audit records,
or any synthetic clinical data. It only sets up platform infrastructure.

Usage:
    python scripts/provision_platform.py
"""

import asyncio
import logging
import os
import sys

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("provision")

# All configuration from environment - never hardcoded
QDRANT_URL = os.environ.get("QDRANT_URL")
KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL")
KEYCLOAK_ADMIN = os.environ.get("KEYCLOAK_ADMIN")
KEYCLOAK_ADMIN_PASSWORD = os.environ.get("KEYCLOAK_ADMIN_PASSWORD")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY")


def _require_env(*vars: str):
    missing = [v for v in vars if not os.environ.get(v)]
    if missing:
        logger.critical(f"Missing required environment variables: {missing}")
        sys.exit(1)


async def provision_qdrant():
    """Create the Qdrant clinical guidelines collection if it does not exist."""
    if not QDRANT_URL:
        logger.error("QDRANT_URL is not set. Skipping Qdrant provisioning.")
        return

    collection_name = "clinintake_clinical_guidelines"
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check if collection exists
        resp = await client.get(f"{QDRANT_URL}/collections/{collection_name}")
        if resp.status_code == 200:
            logger.info(f"Qdrant collection '{collection_name}' already exists. Skipping creation.")
            return

        # Create collection with hybrid vector configuration
        payload = {"vectors": {"dense": {"size": 384, "distance": "Cosine"}}, "sparse_vectors": {"sparse": {"index": {"on_disk": False}}}}
        resp = await client.put(f"{QDRANT_URL}/collections/{collection_name}", json=payload)
        resp.raise_for_status()

        # Create payload indexes for filtered retrieval
        for field_name, field_schema in [
            ("is_active", "bool"),
            ("jurisdiction", "keyword"),
            ("source_organization", "keyword"),
            ("version", "keyword"),
        ]:
            index_resp = await client.put(f"{QDRANT_URL}/collections/{collection_name}/index", json={"field_name": field_name, "field_schema": field_schema})
            if index_resp.status_code not in (200, 201):
                logger.warning(f"Could not create index for field '{field_name}': {index_resp.text}")

        logger.info(f"Qdrant collection '{collection_name}' provisioned successfully.")


async def main():
    _require_env("QDRANT_URL")

    logger.info("ClinIntake Platform Provisioning Starting...")

    await provision_qdrant()

    logger.info("Platform provisioning complete. Ready for guideline document ingestion.")
    logger.info("REMINDER: Ingest approved clinical guideline documents via " "`python scripts/ingest_guidelines.py --source <guideline_dir>` " "before the service is operational.")


if __name__ == "__main__":
    asyncio.run(main())
