import json
from typing import Optional
import redis.asyncio as redis
from src.config import settings
from src.logger import logger
from src.state_machine import DocumentWorkflow

class RedisPersistence:
    def __init__(self):
        self.client: Optional[redis.Redis] = None

    def get_client(self) -> redis.Redis:
        if self.client is None:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True
            )
        return self.client

    async def save_workflow(self, workflow: DocumentWorkflow) -> None:
        client = self.get_client()
        key = f"workflow:{workflow.document_id}"
        payload = {
            "document_id": workflow.document_id,
            "state": workflow.state,
            "context": workflow.context
        }
        try:
            await client.set(key, json.dumps(payload))
            logger.info(
                f"Saved workflow state to Redis: {workflow.state}",
                extra={"document_id": workflow.document_id, "state": workflow.state}
            )
        except Exception as e:
            logger.error(
                f"Failed to write to Redis for document {workflow.document_id}",
                extra={"document_id": workflow.document_id, "error": str(e)}
            )
            raise e

    async def get_workflow(self, document_id: str) -> Optional[DocumentWorkflow]:
        client = self.get_client()
        key = f"workflow:{document_id}"
        try:
            raw_data = await client.get(key)
            if not raw_data:
                logger.info(f"No workflow found in Redis for document {document_id}")
                return None
            
            data = json.loads(raw_data)
            return DocumentWorkflow(
                document_id=data["document_id"],
                state=data["state"],
                context=data.get("context", {})
            )
        except Exception as e:
            logger.error(
                f"Failed to read from Redis for document {document_id}",
                extra={"document_id": document_id, "error": str(e)}
            )
            raise e

    async def close(self) -> None:
        if self.client:
            await self.client.close()
            self.client = None

persistence = RedisPersistence()
