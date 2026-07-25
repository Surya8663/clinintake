from typing import Dict, Any, List, Tuple
from src.models import CQLRuleResult, CQLEvaluateResponse
from src.logger import logger

def evaluate_cql_rules(patient_id: str, clinical_data: Dict[str, Any], rule_libraries: List[str]) -> CQLEvaluateResponse:
    """Evaluates CQL Clinical Quality Language inclusion and exclusion rules deterministically."""
    results: List[CQLRuleResult] = []
    inclusions: List[str] = []
    exclusions: List[str] = []

    diagnoses = clinical_data.get("diagnoses", [])
    medications = clinical_data.get("medications", [])
    labs = clinical_data.get("labs", [])

    diag_names = [d.get("name", {}).get("value", "").lower() for d in diagnoses if isinstance(d, dict)]
    diag_codes = [d.get("icd10_code", {}).get("value", "") for d in diagnoses if isinstance(d, dict)]
    
    med_names = [m.get("name", {}).get("value", "").lower() for m in medications if isinstance(m, dict)]
    rx_codes = [m.get("rxnorm_code", {}).get("value", "") for m in medications if isinstance(m, dict)]

    lab_names = [l.get("name", {}).get("value", "").lower() for l in labs if isinstance(l, dict)]
    loinc_codes = [l.get("loinc_code", {}).get("value", "") for l in labs if isinstance(l, dict)]

    # Rule 1: Diabetes Care Management Rule (CQL Rule)
    if "Diabetes_Screening" in rule_libraries:
        has_dm_diag = any("diabetes" in d or "e11" in c.lower() for d, c in zip(diag_names, diag_codes))
        has_dm_med = any("metformin" in m or "insulin" in m for m in med_names)
        has_hba1c = any("hba1c" in l or "4548-4" in c for l, c in zip(lab_names, loinc_codes))
        
        satisfied = has_dm_diag or has_dm_med or has_hba1c
        rationale = "Patient meets inclusion for Diabetes Care Protocol (Diabetes diagnosis, medication, or HbA1c lab present)." if satisfied else "No Diabetes indicators found."
        
        if satisfied:
            inclusions.append("Diabetes_Care_Management_Protocol")
            
        results.append(CQLRuleResult(
            rule_name="Diabetes_Screening",
            is_satisfied=satisfied,
            rationale=rationale,
            matched_codes=[c for c in diag_codes + rx_codes + loinc_codes if c and c != "Incomplete"]
        ))

    # Rule 2: Hypertension Management Rule
    if "Hypertension_Control" in rule_libraries:
        has_htn_diag = any("hypertension" in d or "i10" in c.lower() for d, c in zip(diag_names, diag_codes))
        has_htn_med = any("lisinopril" in m or "amlodipine" in m or "losartan" in m for m in med_names)
        
        satisfied = has_htn_diag or has_htn_med
        rationale = "Patient meets inclusion for Hypertension Control Protocol." if satisfied else "No Hypertension diagnosis or antihypertensive medication detected."
        
        if satisfied:
            inclusions.append("Hypertension_Control_Protocol")

        results.append(CQLRuleResult(
            rule_name="Hypertension_Control",
            is_satisfied=satisfied,
            rationale=rationale,
            matched_codes=[c for c in diag_codes + rx_codes if c and c != "Incomplete"]
        ))

    # Rule 3: End-Stage Exclusion Rule
    has_terminal_exclusion = any("hospice" in d or "end stage" in d for d in diag_names)
    if has_terminal_exclusion:
        exclusions.append("Hospice_EndStage_Exclusion")

    is_eligible = len(inclusions) > 0 and len(exclusions) == 0

    logger.info(f"CQL evaluation completed for patient={patient_id}: is_eligible={is_eligible}, inclusions={len(inclusions)}, exclusions={len(exclusions)}")
    
    return CQLEvaluateResponse(
        patient_id=patient_id,
        is_eligible=is_eligible,
        evaluated_rules=results,
        inclusion_criteria_met=inclusions,
        exclusion_criteria_met=exclusions
    )
