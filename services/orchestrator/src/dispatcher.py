import json
from typing import Any

from aiokafka import AIOKafkaProducer
import httpx
from pydantic import BaseModel

from src.config import settings
from src.logger import logger


class AuditEventBus:
    def __init__(self):
        self.producer = None
        self.enabled = False

    async def start(self) -> None:
        try:
            self.producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
            # Try to connect with a small timeout so local tests or startup don't hang
            await self.producer.start()
            self.enabled = True
            logger.info("Audit Event Bus (Kafka) connected successfully.")
        except Exception as e:
            logger.warning("Audit Event Bus (Kafka) connection failed. Logging events to standard audit log.", extra={"error": str(e)})
            self.enabled = False

    async def publish_event(self, event_type: str, document_id: str, payload: dict[str, Any]) -> None:
        event = {
            "event_type": event_type,
            "document_id": document_id,
            "payload": payload,
        }

        # Always output to structured json logging
        logger.info(f"Audit event: {event_type}", extra={"audit_event": event})

        if self.enabled and self.producer:
            try:
                # Asynchronously send log event
                await self.producer.send_and_wait(settings.audit_topic, json.dumps(event).encode("utf-8"))
            except Exception as e:
                logger.error("Failed to publish to Kafka Audit Event Bus", extra={"error": str(e), "document_id": document_id})

    async def stop(self) -> None:
        if self.producer:
            await self.producer.stop()
            self.producer = None
            self.enabled = False


audit_event_bus = AuditEventBus()


async def dispatch_downstream_call(service_name: str, url: str, payload: BaseModel) -> dict[str, Any]:
    """
    Single-hub dispatch function.
    All downstream calls MUST pass through this dispatcher.
    It logs to the Audit Event Bus before making the call.
    """
    document_id = getattr(payload, "document_id", "unknown")

    # Audit request before dispatching
    await audit_event_bus.publish_event(event_type=f"dispatch_request:{service_name}", document_id=document_id, payload=payload.model_dump())

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            logger.info(f"Dispatching call to {service_name} at {url}")
            response = await client.post(url, json=payload.model_dump())
            response.raise_for_status()
            resp_data = response.json()

            # Audit successful response
            await audit_event_bus.publish_event(event_type=f"dispatch_response_success:{service_name}", document_id=document_id, payload=resp_data)
            return resp_data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error calling {service_name}", extra={"status_code": e.response.status_code, "response": e.response.text})
            await audit_event_bus.publish_event(event_type=f"dispatch_response_error:{service_name}", document_id=document_id, payload={"error": str(e), "status_code": e.response.status_code})
            raise e
        except Exception as e:
            logger.error(f"Connection error or unexpected exception calling {service_name}", extra={"error": str(e)})
            await audit_event_bus.publish_event(event_type=f"dispatch_response_failed:{service_name}", document_id=document_id, payload={"error": str(e)})
            raise e
