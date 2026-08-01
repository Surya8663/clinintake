from fastapi.testclient import TestClient

from src.extractor import perform_quote_grounded_extraction
from src.main import app

client = TestClient(app)


def test_extraction_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["confidence_threshold"] == 0.70


def test_valid_clinical_document_extraction_and_fhir():
    sample_text = (
        "Patient ID: PAT-88491\n" "Diagnosis: Essential Hypertension (ICD-10: I10) - High Confidence\n" "Medication: Lisinopril 10mg oral daily (RxNorm: 314076)\n" "Lab: HbA1c 6.8 % (LOINC: 4548-4)"
    )

    response = client.post("/extract", json={"document_id": "DOC-TEST-100", "ocr_text": sample_text})

    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "DOC-TEST-100"

    extracted = data["extracted_data"]
    assert extracted["patient_id"]["value"] == "PAT-88491"
    assert extracted["patient_id"]["confidence"] >= 0.70
    assert extracted["patient_id"]["literal_quote"] == "Patient ID: PAT-88491"

    # Check FHIR R4 resources generated
    fhir_res = data["fhir_resources"]
    assert len(fhir_res) >= 3  # Patient, Condition, MedicationStatement, Observation
    resource_types = [r["resourceType"] for r in fhir_res]
    assert "Patient" in resource_types
    assert "Condition" in resource_types
    assert "MedicationStatement" in resource_types


def test_deliberately_ambiguous_document_triggers_incomplete():
    """
    CRITICAL PRD REQUIREMENT TEST:
    Proves that for a deliberately ambiguous document with confidence below threshold (< 0.70),
    the agent returns 'Incomplete' for that field instead of a guessed value.
    """
    ambiguous_text = "Patient ID: PAT-UNKNOWN\n" "Diagnosis: Unclear blurry text (ICD-10: I10) - Ambiguous Confidence\n" "Medication: Ambiguous blurry dosage\n" "Lab: Ambiguous result value"

    # Using strict confidence threshold of 0.70
    result = perform_quote_grounded_extraction(ocr_text=ambiguous_text, threshold_override=0.70)

    # 1. Patient ID should be marked 'Incomplete' due to low confidence (0.30 < 0.70)
    assert result.patient_id.value == "Incomplete"
    assert result.patient_id.confidence < 0.70

    # 2. Ambiguous Diagnosis name should be marked 'Incomplete'
    assert len(result.diagnoses) > 0
    diag = result.diagnoses[0]
    assert diag.name.value == "Incomplete"
    assert diag.name.confidence < 0.70
    assert diag.name.literal_quote != ""

    # 3. Ambiguous Medication should be marked 'Incomplete'
    assert len(result.medications) > 0
    med = result.medications[0]
    assert med.name.value == "Incomplete"
    assert med.name.confidence < 0.70


def test_quote_grounding_spatial_bbox_reference():
    sample_text = "Patient ID: PAT-9901 Diagnosis: Diabetes Mellitus (ICD-10: E11)"
    ocr_words = [
        {"text": "Patient", "bbox": {"x_min": 10, "y_min": 20, "x_max": 60, "y_max": 35}},
        {"text": "ID:", "bbox": {"x_min": 65, "y_min": 20, "x_max": 85, "y_max": 35}},
        {"text": "PAT-9901", "bbox": {"x_min": 90, "y_min": 20, "x_max": 150, "y_max": 35}},
    ]

    result = perform_quote_grounded_extraction(ocr_text=sample_text, ocr_words=ocr_words, threshold_override=0.70)

    # Verify exact bounding box reference match
    assert result.patient_id.bbox == [10, 20, 150, 35]
