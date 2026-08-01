from src.models import RedFlagTrigger, VitalsMeasurement

REDFLAG_SYNDROMES = [
    ("sepsis", ["sepsis", "septic shock", "bacteremia", "qsofa positive"], "Possible Sepsis Syndrome"),
    ("stroke", ["stroke", "facial droop", "slurred speech", "hemiparesis", "acute CVA"], "Possible Acute Stroke / CVA"),
    ("anaphylaxis", ["anaphylaxis", "airway swelling", "stridor", "laryngeal edema"], "Possible Anaphylaxis Emergency"),
    ("major_bleeding", ["massive bleeding", "active hemorrhage", "hematemesis", "hypovolemic shock"], "Possible Major Bleeding / Hemorrhage"),
    ("suicidal_ideation", ["suicidal ideation", "suicide attempt", "want to die", "self-harm plan"], "Active Suicidal Ideation / Self-Harm Risk"),
    ("chest_pain", ["crushing chest pain", "acute coronary syndrome", "myocardial infarction", "st-elevation"], "Acute Chest Pain / Possible MI"),
    ("severe_respiratory_distress", ["severe respiratory distress", "cyanosis", "respiratory arrest", "gasping"], "Severe Respiratory Distress"),
]


def detect_clinical_redflags(clinical_text: str | None, symptoms: list[str] | None, vitals: VitalsMeasurement | None, news2_score: int | None, qsofa_score: int | None) -> list[RedFlagTrigger]:
    """Detects 7 emergency clinical red-flag categories using published clinical criteria."""
    red_flags: list[RedFlagTrigger] = []
    text_content = (clinical_text or "").lower() + " " + " ".join([s.lower() for s in (symptoms or [])])

    # 1. Sepsis Evaluation via qSOFA and NEWS2
    if qsofa_score is not None and qsofa_score >= 2:
        red_flags.append(
            RedFlagTrigger(syndrome="sepsis", severity="EMERGENCY", description=f"qSOFA score = {qsofa_score} (>= 2 indicates high risk of Sepsis mortality).", trigger_source="qSOFA_Criteria")
        )
    elif news2_score is not None and news2_score >= 7:
        red_flags.append(
            RedFlagTrigger(
                syndrome="sepsis", severity="EMERGENCY", description=f"NEWS2 score = {news2_score} (>= 7 indicates high clinical risk / emergency response required).", trigger_source="NEWS2_Score"
            )
        )

    # 2. Vitals-driven Respiratory / Hypoxia Red Flags
    if vitals and vitals.spo2 is not None and vitals.spo2 < 90.0:
        red_flags.append(RedFlagTrigger(syndrome="severe_respiratory_distress", severity="EMERGENCY", description=f"Critical Hypoxia: SpO2 = {vitals.spo2}% (< 90%).", trigger_source="NEWS2_Score"))

    # 3. Keyword / Syndrome-based Red Flag Detection
    for category, keywords, desc in REDFLAG_SYNDROMES:
        for kw in keywords:
            if kw in text_content:
                # Avoid duplicate syndrome entries
                if not any(rf.syndrome == category for rf in red_flags):
                    red_flags.append(RedFlagTrigger(syndrome=category, severity="EMERGENCY", description=f"Clinical Red Flag: {desc} (Trigger: '{kw}').", trigger_source="Heuristic_RedFlag_Keywords"))
                break

    return red_flags
