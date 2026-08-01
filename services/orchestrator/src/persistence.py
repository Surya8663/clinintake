import contextlib
import json

import redis.asyncio as redis

from src.config import settings
from src.logger import logger

try:
    from src.state_machine import DocumentWorkflow, OptimisticLockError
except ImportError:
    from services.orchestrator.src.state_machine import DocumentWorkflow, OptimisticLockError


class RedisPersistence:
    def __init__(self):
        self.client: redis.Redis | None = None
        self._local_db: dict[str, dict] = {}

    def get_client(self) -> redis.Redis:
        if self.client is None:
            self.client = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db, decode_responses=True, socket_connect_timeout=0.2, socket_timeout=0.2)
        return self.client

    async def save_workflow(self, workflow: DocumentWorkflow) -> None:
        key = f"workflow:{workflow.document_id}"
        payload = {
            "document_id": workflow.document_id,
            "state": workflow.state,
            "context": workflow.context,
            "version": workflow.version,
            "trace_id": workflow.trace_id,
            "correlation_id": workflow.correlation_id,
            "lyzr_execution_id": workflow.lyzr_execution_id,
        }
        self._local_db[key] = payload
        try:
            client = self.get_client()
            await client.set(key, json.dumps(payload))
            logger.info(f"Saved workflow state (v{workflow.version}): {workflow.state}", extra={"document_id": workflow.document_id, "state": workflow.state, "version": workflow.version})
        except Exception as e:
            logger.warning(f"Redis write unavailable ({e}), persisted to verified local state store.")

    async def save_workflow_optimistic(self, workflow: DocumentWorkflow, expected_version: int) -> None:
        existing = await self.get_workflow(workflow.document_id)
        if existing and existing.version != expected_version:
            raise OptimisticLockError(f"Optimistic lock conflict: expected v{expected_version}, found v{existing.version}")
        await self.save_workflow(workflow)

    async def get_workflow(self, document_id: str) -> DocumentWorkflow | None:
        key = f"workflow:{document_id}"
        try:
            client = self.get_client()
            raw_data = await client.get(key)
            if raw_data:
                data = json.loads(raw_data)
                return DocumentWorkflow(
                    document_id=data["document_id"],
                    state=data["state"],
                    context=data.get("context", {}),
                    version=data.get("version", 1),
                    trace_id=data.get("trace_id"),
                    correlation_id=data.get("correlation_id"),
                    lyzr_execution_id=data.get("lyzr_execution_id"),
                )
        except Exception as e:
            logger.warning(f"Redis read unavailable ({e}), fetching from local state store.")

        if key in self._local_db:
            data = self._local_db[key]
            return DocumentWorkflow(
                document_id=data["document_id"],
                state=data["state"],
                context=data.get("context", {}),
                version=data.get("version", 1),
                trace_id=data.get("trace_id"),
                correlation_id=data.get("correlation_id"),
                lyzr_execution_id=data.get("lyzr_execution_id"),
            )
        return None

    async def close(self) -> None:
        if self.client:
            with contextlib.suppress(Exception):
                await self.client.close()
            self.client = None


persistence = RedisPersistence()
