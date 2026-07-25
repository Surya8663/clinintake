from typing import List, Dict, Any, Optional
from fhir.resources.condition import Condition
from fhir.resources.medicationstatement import MedicationStatement
from fhir.resources.observation import Observation
from fhir.resources.patient import Patient

from src.models import ExtractionData
from src.logger import logger

def build_and_validate_fhir_resources(extraction_data: ExtractionData) -> List[Dict[str, Any]]:
    """Builds and validates FHIR R4 JSON resources using real fhir.resources library models."""
    validated_resources: List[Dict[str, Any]] = []

    # 1. Patient Resource
    if extraction_data.patient_id.value != "Incomplete":
        try:
            patient = Patient.model_validate({
                "resourceType": "Patient",
                "id": extraction_data.patient_id.value,
                "active": True
            })
            validated_resources.append(patient.model_dump(mode="json"))
        except Exception as e:
            logger.error(f"FHIR Patient validation error: {e}")

    # 2. Condition Resources (Diagnoses)
    for idx, diag in enumerate(extraction_data.diagnoses):
        if diag.name.value != "Incomplete":
            code_str = diag.icd10_code.value if diag.icd10_code.value != "Incomplete" else "UNKNOWN"
            try:
                condition = Condition.model_validate({
                    "resourceType": "Condition",
                    "id": f"cond-{idx+1}",
                    "clinicalStatus": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": "active"
                        }]
                    },
                    "verificationStatus": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                            "code": "confirmed"
                        }]
                    },
                    "code": {
                        "coding": [{
                            "system": "http://hl7.org/fhir/sid/icd-10-cm",
                            "code": code_str,
                            "display": diag.name.value
                        }],
                        "text": diag.name.literal_quote
                    },
                    "subject": {
                        "reference": f"Patient/{extraction_data.patient_id.value}"
                    }
                })
                validated_resources.append(condition.model_dump(mode="json"))
            except Exception as e:
                logger.error(f"FHIR Condition validation error: {e}")

    # 3. MedicationStatement Resources
    for idx, med in enumerate(extraction_data.medications):
        if med.name.value != "Incomplete":
            rx_code = med.rxnorm_code.value if med.rxnorm_code.value != "Incomplete" else "000000"
            try:
                med_stmt = MedicationStatement.model_validate({
                    "resourceType": "MedicationStatement",
                    "id": f"med-{idx+1}",
                    "status": "recorded",
                    "medication": {
                        "concept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": rx_code,
                                "display": med.name.value
                            }],
                            "text": med.name.literal_quote
                        }
                    },
                    "dosage": [{
                        "text": med.dosage.value if med.dosage.value != "Incomplete" else "as directed"
                    }],
                    "subject": {
                        "reference": f"Patient/{extraction_data.patient_id.value}"
                    }
                })
                validated_resources.append(med_stmt.model_dump(mode="json"))
            except Exception as e:
                logger.error(f"FHIR MedicationStatement validation error: {e}")

    # 4. Observation Resources (Labs)
    for idx, lab in enumerate(extraction_data.labs):
        if lab.name.value != "Incomplete":
            loinc = lab.loinc_code.value if lab.loinc_code.value != "Incomplete" else "0000-0"
            try:
                obs = Observation.model_validate({
                    "resourceType": "Observation",
                    "id": f"obs-{idx+1}",
                    "status": "final",
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": loinc,
                            "display": lab.name.value
                        }],
                        "text": lab.name.literal_quote
                    },
                    "valueString": lab.value.value,
                    "subject": {
                        "reference": f"Patient/{extraction_data.patient_id.value}"
                    }
                })
                validated_resources.append(obs.model_dump(mode="json"))
            except Exception as e:
                logger.error(f"FHIR Observation validation error: {e}")

    return validated_resources
