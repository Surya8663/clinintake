import httpx
import difflib
from typing import Optional, Tuple
from src.models import TerminologyMapResponse
from src.config import settings
from src.logger import logger

# Comprehensive clinical terminology subset index for LOINC & SNOMED CT
CLINICAL_SNOMED_INDEX = {
    "essential hypertension": ("59621000", "Essential hypertension", 0.98),
    "hypertension": ("38341003", "Hypertensive disorder", 0.95),
    "type 2 diabetes mellitus": ("44054006", "Type 2 diabetes mellitus", 0.98),
    "diabetes mellitus": ("73211009", "Diabetes mellitus", 0.92),
    "diabetes": ("73211009", "Diabetes mellitus", 0.88),
    "hyperlipidemia": ("55822004", "Hyperlipidemia", 0.95),
    "asthma": ("195967001", "Asthma", 0.95),
    "coronary artery disease": ("53741008", "Coronary artery disease", 0.98),
    "major depressive disorder": ("370143000", "Major depressive disorder", 0.95),
}

CLINICAL_LOINC_INDEX = {
    "hba1c": ("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", 0.98),
    "hemoglobin a1c": ("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", 0.98),
    "glucose": ("2345-7", "Glucose [Mass/volume] in Blood", 0.95),
    "total cholesterol": ("2093-3", "Cholesterol [Mass/volume] in Blood", 0.95),
    "serum creatinine": ("2160-0", "Creatinine [Mass/volume] in Serum or Plasma", 0.95),
    "blood pressure": ("85354-9", "Blood pressure panel with all children optional", 0.95),
    "systolic blood pressure": ("8480-6", "Systolic blood pressure", 0.95),
}

CLINICAL_RXNORM_INDEX = {
    "lisinopril": ("314076", "Lisinopril 10 MG Oral Tablet", 0.95),
    "metformin": ("860975", "Metformin hydrochloride 500 MG Oral Tablet", 0.95),
    "atorvastatin": ("617314", "Atorvastatin 20 MG Oral Tablet", 0.95),
}

async def map_rxnorm_term(term: str) -> Tuple[Optional[str], Optional[str], float, str]:
    """Queries NLM RxNav REST API for live RxCUI resolution with fuzzy index fallback."""
    url = f"{settings.rxnav_api_base_url}/rxcui.json"
    params = {"name": term}
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                rxcui_group = data.get("idGroup", {})
                rxcui_list = rxcui_group.get("rxnormId", [])
                if rxcui_list:
                    rxcui = rxcui_list[0]
                    prop_url = f"{settings.rxnav_api_base_url}/rxcui/{rxcui}/properties.json"
                    prop_resp = await client.get(prop_url)
                    display_name = term
                    if prop_resp.status_code == 200:
                        prop_data = prop_resp.json().get("properties", {})
                        display_name = prop_data.get("name", term)
                    return rxcui, display_name, 0.98, "NLM_RxNav_API"

            # Fallback to approximateTerm search
            approx_url = f"{settings.rxnav_api_base_url}/approximateTerm.json"
            approx_resp = await client.get(approx_url, params={"term": term, "maxEntries": 1})
            if approx_resp.status_code == 200:
                approx_data = approx_resp.json().get("approximateGroup", {})
                candidates = approx_data.get("candidate", [])
                if candidates:
                    cand = candidates[0]
                    rxcui = cand.get("rxcui")
                    cand_name = cand.get("name", term)
                    score = float(cand.get("score", 50)) / 100.0
                    if score >= 0.70:
                        return rxcui, cand_name, round(min(score, 0.95), 2), "NLM_RxNav_Approximate"
    except Exception as e:
        logger.warning(f"NLM RxNav API request failed or timed out: {e}")
        
    # Local fallback for offline/test environment with fuzzy matching for misspelled drug names
    clean_term = term.lower().strip()
    for key, (rxcui, name, conf) in CLINICAL_RXNORM_INDEX.items():
        if key in clean_term:
            return rxcui, name, conf, "RxNorm_Index"

    # Fuzzy matching for misspelled drug names (e.g. metformn, lisinoprl)
    close_matches = difflib.get_close_matches(clean_term, CLINICAL_RXNORM_INDEX.keys(), n=1, cutoff=0.65)
    if close_matches:
        matched_key = close_matches[0]
        rxcui, name, conf = CLINICAL_RXNORM_INDEX[matched_key]
        logger.info(f"Fuzzy terminology match for misspelled drug '{term}' -> '{matched_key}'")
        return rxcui, name, round(conf * 0.88, 2), "RxNorm_Fuzzy_Index"

    return None, None, 0.0, "NLM_RxNav_API"

def map_snomed_term(term: str) -> Tuple[Optional[str], Optional[str], float, str]:
    """Normalizes term to SNOMED CT code system with exact and fuzzy matching."""
    clean_term = term.lower().strip()
    if clean_term in CLINICAL_SNOMED_INDEX:
        code, name, conf = CLINICAL_SNOMED_INDEX[clean_term]
        return code, name, conf, "SNOMED_CT_Index"
        
    for key, (code, name, conf) in CLINICAL_SNOMED_INDEX.items():
        if key in clean_term or clean_term in key:
            return code, name, round(conf * 0.85, 2), "SNOMED_CT_Index"

    # Fuzzy matching for misspelled condition names
    close_matches = difflib.get_close_matches(clean_term, CLINICAL_SNOMED_INDEX.keys(), n=1, cutoff=0.65)
    if close_matches:
        matched_key = close_matches[0]
        code, name, conf = CLINICAL_SNOMED_INDEX[matched_key]
        logger.info(f"Fuzzy terminology match for misspelled condition '{term}' -> '{matched_key}'")
        return code, name, round(conf * 0.85, 2), "SNOMED_CT_Fuzzy_Index"

    return None, None, 0.0, "SNOMED_CT_Index"

def map_loinc_term(term: str) -> Tuple[Optional[str], Optional[str], float, str]:
    """Normalizes term to LOINC code system with exact and fuzzy matching."""
    clean_term = term.lower().strip()
    if clean_term in CLINICAL_LOINC_INDEX:
        code, name, conf = CLINICAL_LOINC_INDEX[clean_term]
        return code, name, conf, "LOINC_Index"
        
    for key, (code, name, conf) in CLINICAL_LOINC_INDEX.items():
        if key in clean_term or clean_term in key:
            return code, name, round(conf * 0.85, 2), "LOINC_Index"

    # Fuzzy matching for misspelled lab names
    close_matches = difflib.get_close_matches(clean_term, CLINICAL_LOINC_INDEX.keys(), n=1, cutoff=0.65)
    if close_matches:
        matched_key = close_matches[0]
        code, name, conf = CLINICAL_LOINC_INDEX[matched_key]
        logger.info(f"Fuzzy terminology match for misspelled lab '{term}' -> '{matched_key}'")
        return code, name, round(conf * 0.85, 2), "LOINC_Fuzzy_Index"

    return None, None, 0.0, "LOINC_Index"

async def resolve_terminology(term: str, code_system: str) -> TerminologyMapResponse:
    """Normalizes clinical terms across RxNorm, LOINC, and SNOMED CT with unmapped escalation handling."""
    system_upper = code_system.upper()
    code, display_name, conf, source_api = None, None, 0.0, "Unknown"

    if "SNOMED" in system_upper or "DIAG" in system_upper:
        code, display_name, conf, source_api = map_snomed_term(term)
        target_system = "SNOMED CT"
    elif "LOINC" in system_upper or "LAB" in system_upper:
        code, display_name, conf, source_api = map_loinc_term(term)
        target_system = "LOINC"
    else:  # RxNorm / Medication
        code, display_name, conf, source_api = await map_rxnorm_term(term)
        target_system = "RxNorm"

    is_mapped = (code is not None) and (conf >= settings.confidence_threshold)
    requires_escalation = not is_mapped

    if requires_escalation:
        logger.info(f"Term '{term}' could not be mapped to {target_system} (conf={conf}). Marking for escalation.")

    return TerminologyMapResponse(
        raw_term=term,
        code_system=target_system,
        code=code if is_mapped else None,
        display_name=display_name if is_mapped else None,
        confidence_score=conf,
        is_mapped=is_mapped,
        requires_unmapped_escalation=requires_escalation,
        source_api=source_api
    )
