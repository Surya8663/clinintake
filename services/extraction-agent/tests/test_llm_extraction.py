"""
Real LLM extraction integration test.
Sends a realistic synthetic clinical text through the actual LLM call
and asserts the output has the correct shape (value, quote, confidence all present).

Requires OPENAI_API_KEY environment variable to be set.
"""
import os
import pytest
from src.extractor import perform_quote_grounded_extraction, create_grounded_field
from src.llm_client import call_llm_extraction

SAMPLE_CLINICAL_TEXT = (
    "Patient ID: PAT-77201\n"
    "Name: Maria Gonzalez   DOB: 1974-03-15\n"
    "Diagnosis: Type 2 Diabetes Mellitus (ICD-10: E11.65) - High Confidence\n"
    "Diagnosis: Essential Hypertension (ICD-10: I10) - High Confidence\n"
    "Medication: Metformin 500mg oral twice daily (RxNorm: 861004)\n"
    "Medication: Lisinopril 20mg oral daily (RxNorm: 314076)\n"
    "Lab: HbA1c 8.2 % (LOINC: 4548-4)\n"
    "Lab: Creatinine 1.1 mg/dL (LOINC: 2160-0)\n"
)

SAMPLE_OCR_WORDS = [
    {"text": "Patient", "bbox": {"x_min": 10, "y_min": 20, "x_max": 70, "y_max": 35}},
    {"text": "ID:", "bbox": {"x_min": 75, "y_min": 20, "x_max": 95, "y_max": 35}},
    {"text": "PAT-77201", "bbox": {"x_min": 100, "y_min": 20, "x_max": 170, "y_max": 35}},
]


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"),
    reason="No LLM API key set — skipping real LLM integration test"
)
def test_real_llm_extraction_output_shape():
    """
    Sends realistic clinical text through the real LLM and asserts:
    1. The response is valid JSON matching the extraction schema
    2. Every field has value, literal_quote, and confidence present
    3. Confidence is a float between 0.0 and 1.0
    4. literal_quote is a substring of the input OCR text
    """
    result = call_llm_extraction(ocr_text=SAMPLE_CLINICAL_TEXT, ocr_words=SAMPLE_OCR_WORDS)

    # --- Top-level schema ---
    assert "patient_id" in result, "Missing patient_id in LLM response"
    assert "diagnoses" in result, "Missing diagnoses in LLM response"
    assert "medications" in result, "Missing medications in LLM response"
    assert "labs" in result, "Missing labs in LLM response"

    # --- Patient ID field shape ---
    pat = result["patient_id"]
    assert "value" in pat and pat["value"], "patient_id.value missing or empty"
    assert "literal_quote" in pat and pat["literal_quote"], "patient_id.literal_quote missing or empty"
    assert "confidence" in pat, "patient_id.confidence missing"
    assert 0.0 <= float(pat["confidence"]) <= 1.0, f"patient_id.confidence out of range: {pat['confidence']}"
    assert pat["literal_quote"] in SAMPLE_CLINICAL_TEXT, (
        f"patient_id.literal_quote is not a substring of input: '{pat['literal_quote']}'"
    )

    # --- Diagnoses ---
    assert isinstance(result["diagnoses"], list), "diagnoses should be a list"
    assert len(result["diagnoses"]) >= 1, "Expected at least 1 diagnosis"
    for idx, diag in enumerate(result["diagnoses"]):
        for field_name in ["name", "icd10_code"]:
            field = diag[field_name]
            assert "value" in field, f"diagnoses[{idx}].{field_name}.value missing"
            assert "literal_quote" in field, f"diagnoses[{idx}].{field_name}.literal_quote missing"
            assert "confidence" in field, f"diagnoses[{idx}].{field_name}.confidence missing"
            assert 0.0 <= float(field["confidence"]) <= 1.0

    # --- Medications ---
    assert isinstance(result["medications"], list), "medications should be a list"
    assert len(result["medications"]) >= 1, "Expected at least 1 medication"
    for idx, med in enumerate(result["medications"]):
        for field_name in ["name", "rxnorm_code", "dosage"]:
            field = med[field_name]
            assert "value" in field, f"medications[{idx}].{field_name}.value missing"
            assert "literal_quote" in field, f"medications[{idx}].{field_name}.literal_quote missing"
            assert "confidence" in field, f"medications[{idx}].{field_name}.confidence missing"
            assert 0.0 <= float(field["confidence"]) <= 1.0

    # --- Labs ---
    assert isinstance(result["labs"], list), "labs should be a list"
    assert len(result["labs"]) >= 1, "Expected at least 1 lab result"
    for idx, lab in enumerate(result["labs"]):
        for field_name in ["name", "loinc_code", "value"]:
            field = lab[field_name]
            assert "value" in field, f"labs[{idx}].{field_name}.value missing"
            assert "literal_quote" in field, f"labs[{idx}].{field_name}.literal_quote missing"
            assert "confidence" in field, f"labs[{idx}].{field_name}.confidence missing"
            assert 0.0 <= float(field["confidence"]) <= 1.0


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"),
    reason="No LLM API key set (OPENAI_API_KEY or GOOGLE_API_KEY) — skipping real LLM integration test"
)
def test_real_llm_extraction_end_to_end():
    """
    Full end-to-end: OCR text → LLM → create_grounded_field() → ExtractionData.
    Asserts the complete pipeline produces valid GroundedField objects.
    """
    result = perform_quote_grounded_extraction(
        ocr_text=SAMPLE_CLINICAL_TEXT,
        ocr_words=SAMPLE_OCR_WORDS,
        threshold_override=0.70
    )

    # Patient ID should be a GroundedField with real values
    assert result.patient_id.value != "", "patient_id value should not be empty"
    assert result.patient_id.literal_quote != "", "patient_id literal_quote should not be empty"
    assert 0.0 <= result.patient_id.confidence <= 1.0
    assert isinstance(result.patient_id.bbox, list) and len(result.patient_id.bbox) == 4

    # Should have extracted diagnoses, medications, and labs
    assert len(result.diagnoses) >= 1, f"Expected >=1 diagnosis, got {len(result.diagnoses)}"
    assert len(result.medications) >= 1, f"Expected >=1 medication, got {len(result.medications)}"
    assert len(result.labs) >= 1, f"Expected >=1 lab, got {len(result.labs)}"

    # Verify GroundedField structure on first diagnosis
    diag = result.diagnoses[0]
    assert diag.name.value != ""
    assert diag.name.literal_quote != ""
    assert 0.0 <= diag.name.confidence <= 1.0
    assert diag.icd10_code.value != ""
