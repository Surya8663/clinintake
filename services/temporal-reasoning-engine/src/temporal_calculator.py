import datetime

from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

from src.logger import logger
from src.models import TemporalEvaluateRequest, TemporalEvaluateResponse


def calculate_temporal_care_gap(request: TemporalEvaluateRequest) -> TemporalEvaluateResponse:
    """Calculates exact temporal screening care gap state using real date arithmetic."""
    # 1. Edge Case: Missing last screening date or age
    if not request.last_screening_date or request.last_screening_date.strip().lower() in ["none", "", "incomplete"]:
        return TemporalEvaluateResponse(
            procedure_name=request.procedure_name,
            status="insufficient-information",
            months_since_last_screening=None,
            next_due_date=None,
            rationale="Missing last screening date in patient clinical record.",
        )

    if request.patient_age is None or request.patient_age <= 0:
        return TemporalEvaluateResponse(
            procedure_name=request.procedure_name,
            status="insufficient-information",
            months_since_last_screening=None,
            next_due_date=None,
            rationale="Missing or invalid patient age for guideline evaluation.",
        )

    try:
        last_date = parse_date(request.last_screening_date).date()
    except Exception as e:
        logger.error(f"Failed to parse last_screening_date='{request.last_screening_date}': {e}")
        return TemporalEvaluateResponse(
            procedure_name=request.procedure_name,
            status="insufficient-information",
            months_since_last_screening=None,
            next_due_date=None,
            rationale=f"Invalid date format: {request.last_screening_date}",
        )

    ref_date = parse_date(request.reference_date).date() if request.reference_date else datetime.date.today()

    # Guideline Age Boundaries (e.g. Colonoscopy 45-75 yrs, Mammogram 40-74 yrs)
    interval_months = request.guideline_interval_months
    if request.risk_category in ["high", "very_high"]:
        interval_months = max(6, int(interval_months * 0.5))

    next_due = last_date + relativedelta(months=interval_months)

    delta = relativedelta(ref_date, last_date)
    months_elapsed = round(delta.years * 12 + delta.months + (delta.days / 30.44), 1)

    # State Calculation Logic:
    # overdue: elapsed > interval + 0.5 months
    # due: interval - 1.0 <= elapsed <= interval + 0.5 months
    # not-due: elapsed < interval - 1.0 months
    if months_elapsed > (interval_months + 0.5):
        status = "overdue"
        rationale = f"Screening is OVERDUE by {round(months_elapsed - interval_months, 1)} months (Last done: {last_date}, Guideline interval: {interval_months}m)."
    elif months_elapsed >= (interval_months - 1.0):
        status = "due"
        rationale = f"Screening is DUE now (Next due date: {next_due}, Guideline interval: {interval_months}m)."
    else:
        status = "not-due"
        rationale = f"Screening is NOT DUE yet (Next due date: {next_due}, {round(interval_months - months_elapsed, 1)} months remaining)."

    logger.info(f"Temporal evaluation procedure='{request.procedure_name}': status={status}, months_elapsed={months_elapsed}")

    return TemporalEvaluateResponse(procedure_name=request.procedure_name, status=status, months_since_last_screening=months_elapsed, next_due_date=next_due.isoformat(), rationale=rationale)
