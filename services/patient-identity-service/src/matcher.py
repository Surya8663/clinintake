import datetime
from typing import Any

from rapidfuzz.distance import JaroWinkler

from src.config import settings
from src.logger import logger
from src.models import Patient


def parse_dob(dob_str: str) -> datetime.date | None:
    if not dob_str:
        return None
    
    # Try parsing common DOB formats
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(dob_str.strip(), fmt).date()
        except ValueError:
            continue
    logger.warning(f"Unable to parse Date of Birth string format: '{dob_str}'")
    return None

def compute_match_score(
    first_name_in: str, 
    last_name_in: str, 
    dob_in: datetime.date | None,
    patient: Patient
) -> tuple[float, dict]:
    """
    Computes name similarity and DOB match to derive a confidence score.
    """
    # Jaro-Winkler name similarity: rapidfuzz returns 0.0–1.0 natively
    fn_sim = JaroWinkler.similarity(first_name_in.strip().lower(), patient.first_name.strip().lower())
    ln_sim = JaroWinkler.similarity(last_name_in.strip().lower(), patient.last_name.strip().lower())
    name_score = (fn_sim + ln_sim) / 2.0
    
    # Date of Birth score (exact match weight)
    dob_score = 0.0
    if dob_in and patient.date_of_birth == dob_in:
        dob_score = 1.0
        
    # Aggregate weighted score: 60% name similarity, 40% DOB exact match
    total_score = (name_score * 0.6) + (dob_score * 0.4)
    
    details = {
        "first_name_similarity": fn_sim,
        "last_name_similarity": ln_sim,
        "name_score_weighted": name_score * 0.6,
        "dob_match_weighted": dob_score * 0.4,
        "total_score": total_score
    }
    return total_score, details

def resolve_patient_identity(
    first_name: str, 
    last_name: str, 
    dob_str: str, 
    patients: list[Patient]
) -> tuple[Patient | None, float, list[dict]]:
    """
    Evaluates patient demographics against list of database patients.
    Returns (matched_patient, highest_score, candidate_logs).
    """
    dob_parsed = parse_dob(dob_str)
    
    candidates: list[dict[str, Any]] = []
    best_patient = None
    best_score = 0.0
    
    for p in patients:
        score, details = compute_match_score(first_name, last_name, dob_parsed, p)
        candidates.append({
            "patient_id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "date_of_birth": p.date_of_birth.isoformat(),
            "match_details": details
        })
        
        if score > best_score:
            best_score = score
            best_patient = p
            
    # Sort candidates list descending by total score
    candidates.sort(key=lambda x: x["match_details"]["total_score"], reverse=True)
    
    threshold = settings.patient_match_threshold
    
    if best_patient and best_score >= threshold:
        logger.info(
            f"Patient identity resolved successfully with score {best_score:.4f}",
            extra={"matched_patient_id": best_patient.id, "score": best_score, "threshold": threshold}
        )
        return best_patient, best_score, candidates
        
    logger.warning(
        f"Patient identity could not be resolved confidently. Highest score: {best_score:.4f}",
        extra={"highest_score": best_score, "threshold": threshold}
    )
    return None, best_score, candidates
