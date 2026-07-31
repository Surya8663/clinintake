import asyncio
import datetime
import logging
import os

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import httpx

logger = logging.getLogger(__name__)
app = FastAPI()

QDRANT_URL = os.environ.get("QDRANT_URL", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "")


@app.get("/health/live")
async def liveness():
    """
    Liveness check: confirms the process is running and responding.
    Does not probe external dependencies - only confirms the process is alive.
    """
    return {"status": "alive", "timestamp": datetime.datetime.now(datetime.UTC).isoformat()}


@app.get("/health/ready")
async def readiness():
    """
    Readiness check: confirms all mandatory dependencies are reachable.
    Returns HTTP 503 Service Unavailable if any required dependency is offline.
    Services missing required config must not report ready.
    """
    if not QDRANT_URL:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail={"status": "not_ready", "reason": "QDRANT_URL environment variable not configured."})

    if not DATABASE_URL:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail={"status": "not_ready", "reason": "DATABASE_URL environment variable not configured."})

    dependency_results = {}

    # Check Qdrant connectivity
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{QDRANT_URL}/healthz")
            if resp.status_code == 200:
                dependency_results["qdrant"] = {"status": "healthy"}
            else:
                dependency_results["qdrant"] = {"status": "unhealthy", "http_code": resp.status_code}
    except Exception as e:
        dependency_results["qdrant"] = {"status": "unhealthy", "error": str(e)}

    # Check Kafka (Redpanda) connectivity
    if KAFKA_BOOTSTRAP_SERVERS:
        try:
            host, port = KAFKA_BOOTSTRAP_SERVERS.split(":")[0], int(KAFKA_BOOTSTRAP_SERVERS.split(":")[1])
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=2.0
            )
            writer.close()
            await writer.wait_closed()
            dependency_results["kafka"] = {"status": "healthy"}
        except Exception as e:
            dependency_results["kafka"] = {"status": "unhealthy", "error": str(e)}

    unhealthy = [k for k, v in dependency_results.items() if v.get("status") != "healthy"]
    if unhealthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "dependencies": dependency_results,
                "unhealthy": unhealthy
            }
        )

    return {
        "status": "ready",
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "dependencies": dependency_results
    }
