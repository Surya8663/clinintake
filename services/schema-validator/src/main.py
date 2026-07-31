from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from src.config import settings
from src.logger import logger
from src.models import ValidateSchemaRequest, ValidateSchemaResponse
from src.validator_engine import validate_fhir_resource_schema

app = FastAPI(
    title=settings.service_name,
    description="FHIR R4 Schema Validation Microservice",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name
    }

@app.post("/validate/schema", response_model=ValidateSchemaResponse)
async def validate_schema(request: ValidateSchemaRequest):
    """Validates FHIR R4 JSON object and returns field-level error messages if invalid."""
    logger.info(f"Validating FHIR schema for resourceType={request.resource_type}")
    response = validate_fhir_resource_schema(request.resource_type, request.fhir_resource)
    
    if not response.is_valid:
        logger.warning(f"Rejecting malformed FHIR resource '{request.resource_type}' with {len(response.issues)} errors.")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump(mode="json")
        )
        
    return response
