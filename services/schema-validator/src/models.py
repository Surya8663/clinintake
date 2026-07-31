from typing import Any

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    field: str = Field(..., description="Field path causing schema violation (e.g. 'subject.reference', 'clinicalStatus')")
    issue_type: str = Field(..., description="Type of validation issue ('missing_required', 'invalid_type', 'invalid_enum', 'syntax_error')")
    description: str = Field(..., description="Detailed error explanation")
    severity: str = Field("error", description="'error' or 'warning'")

class ValidateSchemaRequest(BaseModel):
    resource_type: str = Field(..., description="FHIR R4 resource type name (e.g., 'Condition', 'MedicationStatement', 'Observation', 'Patient')")
    fhir_resource: dict[str, Any] = Field(..., description="Raw FHIR R4 JSON object to validate")

class ValidateSchemaResponse(BaseModel):
    is_valid: bool = Field(..., description="True if resource strictly satisfies FHIR R4 schema")
    resource_type: str
    issues: list[ValidationIssue] = Field(default_factory=list, description="Explicit list of validation errors")
    validated_resource: dict[str, Any] | None = None
