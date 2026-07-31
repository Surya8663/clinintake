from typing import Any

from fhir.resources.condition import Condition
from fhir.resources.encounter import Encounter
from fhir.resources.medicationstatement import MedicationStatement
from fhir.resources.observation import Observation
from fhir.resources.patient import Patient
from fhir.resources.resource import Resource
from pydantic import ValidationError

from src.logger import logger
from src.models import ValidateSchemaResponse, ValidationIssue

FHIR_RESOURCE_MAP = {
    "Condition": Condition,
    "MedicationStatement": MedicationStatement,
    "Observation": Observation,
    "Patient": Patient,
    "Encounter": Encounter
}

def validate_fhir_resource_schema(resource_type: str, fhir_resource: dict[str, Any]) -> ValidateSchemaResponse:
    """Strictly validates FHIR R4 JSON object against official fhir.resources models."""
    issues: list[ValidationIssue] = []

    if not isinstance(fhir_resource, dict):
        issues.append(ValidationIssue(
            field="root",
            issue_type="invalid_type",
            description="Payload must be a JSON object",
            severity="error"
        ))
        return ValidateSchemaResponse(
            is_valid=False,
            resource_type=resource_type,
            issues=issues
        )

    res_type = fhir_resource.get("resourceType") or resource_type
    if res_type not in FHIR_RESOURCE_MAP:
        # Fallback to generic Resource model validation
        model_cls = Resource
    else:
        model_cls = FHIR_RESOURCE_MAP[res_type]  # type: ignore[assignment]

    try:
        validated_obj = model_cls.model_validate(fhir_resource)
        logger.info(f"FHIR schema validation successful for resourceType={res_type}")
        return ValidateSchemaResponse(
            is_valid=True,
            resource_type=res_type,
            issues=[],
            validated_resource=validated_obj.model_dump(mode="json")
        )
    except ValidationError as val_err:
        logger.warning(f"FHIR schema validation failed for resourceType={res_type}: {len(val_err.errors())} errors found.")
        for err in val_err.errors():
            field_loc = " -> ".join([str(loc) for loc in err.get("loc", [])]) or "root"
            err_type = err.get("type", "invalid_value")
            msg = err.get("msg", "Invalid value for FHIR field")
            
            issue_type = "missing_required" if "missing" in err_type else "invalid_type"
            
            issues.append(ValidationIssue(
                field=field_loc,
                issue_type=issue_type,
                description=f"Field '{field_loc}': {msg}",
                severity="error"
            ))

        return ValidateSchemaResponse(
            is_valid=False,
            resource_type=res_type,
            issues=issues,
            validated_resource=None
        )
    except Exception as e:
        logger.error(f"Unexpected error during FHIR validation: {e}")
        issues.append(ValidationIssue(
            field="root",
            issue_type="syntax_error",
            description=f"Malformed FHIR payload: {e!s}",
            severity="error"
        ))
        return ValidateSchemaResponse(
            is_valid=False,
            resource_type=res_type,
            issues=issues
        )
