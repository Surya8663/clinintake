from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.config import settings
from src.logger import logger

app = FastAPI(
    title=settings.service_name,
    description="Base FastAPI service template for healthcare monorepo",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting up {settings.service_name} in {settings.environment} environment")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.service_name}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", extra={"error": str(exc), "path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/health")
async def health_check():
    """Health check endpoint to verify service is running."""
    return {"status": "ok", "service": settings.service_name}
