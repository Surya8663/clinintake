from typing import Tuple, Optional
from src.models import VitalsMeasurement
from src.logger import logger

def calculate_news2_points(vitals: Optional[VitalsMeasurement]) -> Tuple[Optional[int], Optional[int], str, str]:
    """
    Calculates NEWS2 and qSOFA scores.
    Enforces pessimistic safety requirement: If required vitals are missing, returns
    assessment_status='incomplete' and rationale='Safety assessment incomplete — required clinical measurements unavailable'.
    """
    if vitals is None:
        return None, None, "incomplete", "Safety assessment incomplete — required clinical measurements unavailable"

    # Strict check for required vital parameters
    missing_fields = []
    if vitals.respiratory_rate is None:
        missing_fields.append("respiratory_rate")
    if vitals.spo2 is None:
        missing_fields.append("spo2")
    if vitals.systolic_bp is None:
        missing_fields.append("systolic_bp")
    if vitals.heart_rate is None:
        missing_fields.append("heart_rate")

    if missing_fields:
        logger.warning(f"Pessimistic safety trigger: Missing required vitals {missing_fields}")
        return None, None, "incomplete", "Safety assessment incomplete — required clinical measurements unavailable"

    score = 0
    
    # 1. Respiration Rate
    rr = vitals.respiratory_rate
    if rr <= 8 or rr >= 25:
        score += 3
    elif rr >= 21:
        score += 2
    elif rr >= 9 and rr <= 11:
        score += 1

    # 2. SpO2
    sat = vitals.spo2
    if sat <= 91:
        score += 3
    elif sat <= 93:
        score += 2
    elif sat <= 95:
        score += 1

    # 3. Supplemental Oxygen
    if vitals.uses_supplemental_oxygen:
        score += 2

    # 4. Systolic BP
    sbp = vitals.systolic_bp
    if sbp <= 90 or sbp >= 220:
        score += 3
    elif sbp <= 100:
        score += 2
    elif sbp <= 110:
        score += 1

    # 5. Heart Rate
    hr = vitals.heart_rate
    if hr <= 40 or hr >= 131:
        score += 3
    elif hr >= 111:
        score += 2
    elif (hr >= 41 and hr <= 50) or (hr >= 91 and hr <= 110):
        score += 1

    # 6. Consciousness (ACVPU)
    c_level = (vitals.consciousness_level or "Alert").lower()
    if c_level != "alert":
        score += 3

    # 7. Temperature
    temp = vitals.temperature if vitals.temperature is not None else 37.0
    if temp <= 35.0:
        score += 3
    elif temp >= 39.1:
        score += 2
    elif (temp >= 35.1 and temp <= 36.0) or (temp >= 38.1 and temp <= 39.0):
        score += 1

    # Calculate qSOFA
    qsofa = 0
    if rr >= 22:
        qsofa += 1
    if c_level != "alert":
        qsofa += 1
    if sbp <= 100:
        qsofa += 1

    rationale = f"NEWS2 score calculated: {score} points (qSOFA: {qsofa})."
    return score, qsofa, "complete", rationale
