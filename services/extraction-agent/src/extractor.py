from typing import Any, List, Optional, Tuple

from pydantic import ValidationError

from src.config import settings
from src.logger import logger
from src.models import (
    ExtractionData,
    GroundedDiagnosis,
    GroundedField,
    GroundedLabResult,
    GroundedMedication,
    LyzrExtractionResponse,
    OCRBoundingBox,
)


def locate_bbox_for_quote(quote: Any, ocr_words: Optional[List[dict[str, Any]]]) -> Tuple[Optional[List[float]], str]:
    """
    Finds spatial bounding box [x_min, y_min, x_max, y_max] matching the literal quote from OCR words.
    Validates bounding box coordinates using OCRBoundingBox model.
    Returns (bbox, grounding_status).
    """
    if ocr_words is None or len(ocr_words) == 0:
        return None, "spatial_data_unavailable"

    quote_str = str(quote) if quote is not None else ""
    if not quote_str or not quote_str.strip():
        return None, "quote_not_located"

    quote_tokens = [tok.strip().lower() for tok in quote_str.strip().split() if tok.strip()]
    if not quote_tokens:
        return None, "quote_not_located"

    # Exact token sequence matching (no partial token containment allowed)
    for i in range(len(ocr_words) - len(quote_tokens) + 1):
        match = True
        for j, q_tok in enumerate(quote_tokens):
            w_text = str(ocr_words[i + j].get("text", "")).strip().lower()
            if q_tok != w_text:
                match = False
                break

        if match:
            matched_words = ocr_words[i : i + len(quote_tokens)]
            parsed_boxes: List[OCRBoundingBox] = []

            for w in matched_words:
                raw_bbox = w.get("bbox")
                if not isinstance(raw_bbox, dict):
                    logger.warning(f"OCR word '{w.get('text')}' missing bounding box dictionary.")
                    return None, "spatial_data_invalid"
                try:
                    box_obj = OCRBoundingBox(
                        x_min=raw_bbox["x_min"],
                        y_min=raw_bbox["y_min"],
                        x_max=raw_bbox["x_max"],
                        y_max=raw_bbox["y_max"],
                    )
                    parsed_boxes.append(box_obj)
                except (KeyError, TypeError, ValueError, ValidationError) as err:
                    logger.warning(f"Invalid OCR bounding box data for word '{w.get('text')}': {err}")
                    return None, "spatial_data_invalid"

            min_x = min(b.x_min for b in parsed_boxes)
            min_y = min(b.y_min for b in parsed_boxes)
            max_x = max(b.x_max for b in parsed_boxes)
            max_y = max(b.y_max for b in parsed_boxes)

            if max_x <= min_x or max_y <= min_y:
                return None, "spatial_data_invalid"

            return [min_x, min_y, max_x, max_y], "grounded"

    return None, "quote_not_located"


def create_grounded_field(
    raw_value: str,
    literal_quote: str,
    confidence: float,
    ocr_text: str = "",
    ocr_words: Optional[List[dict[str, Any]]] = None,
    custom_threshold: Optional[float] = None,
) -> GroundedField:
    """Creates a grounded field with spatial bounding box computation or null/unsupported status."""
    threshold = custom_threshold if custom_threshold is not None else settings.confidence_threshold

    quote_str = str(literal_quote) if literal_quote is not None else ""
    val_str = str(raw_value) if raw_value is not None else ""

    bbox, grounding_status = locate_bbox_for_quote(quote_str, ocr_words)

    # Validate literal quote substring match against OCR text
    if val_str and val_str.lower() not in ("unknown", "pat-unknown", "incomplete"):
        if ocr_text and quote_str and quote_str not in ocr_text:
            grounding_status = "quote_unsupported"

    final_value = val_str
    if confidence < threshold or not val_str or val_str.lower() in ("unknown", "pat-unknown", "incomplete"):
        logger.info(f"Field confidence {confidence} is below threshold {threshold} or value is empty. Marking value as 'Incomplete'.")
        final_value = "Incomplete"

    return GroundedField(value=final_value, literal_quote=quote_str, bbox=bbox, grounding_status=grounding_status, confidence=confidence)


def perform_quote_grounded_extraction(ocr_text: str, ocr_words: Optional[List[dict[str, Any]]] = None, threshold_override: Optional[float] = None) -> ExtractionData:
    """Extracts clinical entities using LLM-based structured extraction with strict quote grounding."""
    from src.llm_client import call_llm_extraction

    text = ocr_text or ""
    threshold = threshold_override if threshold_override is not None else settings.confidence_threshold

    if not text.strip():
        return ExtractionData(
            patient_id=create_grounded_field("", "", 0.0, ocr_text=text, ocr_words=ocr_words, custom_threshold=threshold),
            diagnoses=[],
            medications=[],
            labs=[],
        )

    # Call LLM boundary returning typed LyzrExtractionResponse model
    typed_response: LyzrExtractionResponse = call_llm_extraction(ocr_text=text, ocr_words=ocr_words)

    # Consume typed model attributes
    pat_field = create_grounded_field(
        raw_value=typed_response.patient_id.value,
        literal_quote=typed_response.patient_id.literal_quote,
        confidence=typed_response.patient_id.confidence,
        ocr_text=text,
        ocr_words=ocr_words,
        custom_threshold=threshold,
    )

    diagnoses: List[GroundedDiagnosis] = []
    for diag in typed_response.diagnoses:
        name_field = create_grounded_field(
            raw_value=diag.name.value,
            literal_quote=diag.name.literal_quote,
            confidence=diag.name.confidence,
            ocr_text=text,
            ocr_words=ocr_words,
            custom_threshold=threshold,
        )
        icd_field = create_grounded_field(
            raw_value=diag.icd10_code.value,
            literal_quote=diag.icd10_code.literal_quote,
            confidence=diag.icd10_code.confidence,
            ocr_text=text,
            ocr_words=ocr_words,
            custom_threshold=threshold,
        )
        diagnoses.append(GroundedDiagnosis(name=name_field, icd10_code=icd_field))

    medications: List[GroundedMedication] = []
    for med in typed_response.medications:
        name_field = create_grounded_field(
            raw_value=med.name.value,
            literal_quote=med.name.literal_quote,
            confidence=med.name.confidence,
            ocr_text=text,
            ocr_words=ocr_words,
            custom_threshold=threshold,
        )
        rx_field = create_grounded_field(
            raw_value=med.rxnorm_code.value,
            literal_quote=med.rxnorm_code.literal_quote,
            confidence=med.rxnorm_code.confidence,
            ocr_text=text,
            ocr_words=ocr_words,
            custom_threshold=threshold,
        )
        dosage_field = create_grounded_field(
            raw_value=med.dosage.value,
            literal_quote=med.dosage.literal_quote,
            confidence=med.dosage.confidence,
            ocr_text=text,
            ocr_words=ocr_words,
            custom_threshold=threshold,
        )
        medications.append(GroundedMedication(name=name_field, rxnorm_code=rx_field, dosage=dosage_field))

    labs: List[GroundedLabResult] = []
    for lab in typed_response.labs:
        name_field = create_grounded_field(
            raw_value=lab.name.value,
            literal_quote=lab.name.literal_quote,
            confidence=lab.name.confidence,
            ocr_text=text,
            ocr_words=ocr_words,
            custom_threshold=threshold,
        )
        loinc_field = create_grounded_field(
            raw_value=lab.loinc_code.value,
            literal_quote=lab.loinc_code.literal_quote,
            confidence=lab.loinc_code.confidence,
            ocr_text=text,
            ocr_words=ocr_words,
            custom_threshold=threshold,
        )
        val_field = create_grounded_field(
            raw_value=lab.value.value,
            literal_quote=lab.value.literal_quote,
            confidence=lab.value.confidence,
            ocr_text=text,
            ocr_words=ocr_words,
            custom_threshold=threshold,
        )
        labs.append(GroundedLabResult(name=name_field, loinc_code=loinc_field, value=val_field))

    return ExtractionData(patient_id=pat_field, diagnoses=diagnoses, medications=medications, labs=labs)
