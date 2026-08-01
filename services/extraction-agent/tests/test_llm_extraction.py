import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

os.environ["LYZR_API_KEY"] = "test_lyzr_api_key_2026"
os.environ["LLM_API_KEY"] = "test_llm_api_key_2026"
os.environ["SAFETY_SUB_AGENT_URL"] = "http://localhost:8011"

from src.extractor import create_grounded_field, perform_quote_grounded_extraction
from src.llm_client import call_llm_extraction

SAMPLE_CLINICAL_TEXT = (
    "Patient ID: PAT-10552\n"
    "Name: Maria Gonzalez   DOB: 1974-03-15\n"
    "Diagnosis: Type 2 Diabetes Mellitus (ICD-10: E11.65) - High Confidence\n"
    "Medication: Metformin 500mg oral twice daily (RxNorm: 861004)\n"
    "Lab: HbA1c 8.2 % (LOINC: 4548-4)\n"
)

SAMPLE_OCR_WORDS = [
    {"text": "Patient", "bbox": {"x_min": 10, "y_min": 20, "x_max": 70, "y_max": 35}},
    {"text": "ID:", "bbox": {"x_min": 75, "y_min": 20, "x_max": 95, "y_max": 35}},
    {"text": "PAT-10552", "bbox": {"x_min": 100, "y_min": 20, "x_max": 170, "y_max": 35}},
]


def test_extraction_llm_boundary_payload_sent():
    """Verifies prompt and request payload sent to external Lyzr/LLM boundary."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "response": {
            "patient_id": {"value": "PAT-10552", "literal_quote": "Patient ID: PAT-10552", "confidence": 0.95},
            "diagnoses": [{"name": {"value": "Type 2 Diabetes Mellitus", "literal_quote": "Type 2 Diabetes Mellitus", "confidence": 0.90}, "icd10_code": {"value": "E11.65", "literal_quote": "ICD-10: E11.65", "confidence": 0.90}}],
            "medications": [],
            "labs": [],
        }
    }

    with patch.object(httpx.Client, "post", return_value=mock_resp) as mock_post:
        res = call_llm_extraction(ocr_text=SAMPLE_CLINICAL_TEXT, ocr_words=SAMPLE_OCR_WORDS)
        assert res["patient_id"]["value"] == "PAT-10552"

        mock_post.assert_called_once()
        sent_body = mock_post.call_args.kwargs["json"]
        assert "prompt" in sent_body
        assert "system_prompt" in sent_body
        assert "PAT-10552" in sent_body["prompt"]
