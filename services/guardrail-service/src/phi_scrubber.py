import re
from typing import List, Tuple
from src.models import PHIScrubRequest, PHIScrubResponse
from src.logger import logger

# Regex patterns for clinical PHI entity detection
PHI_PATTERNS = [
    ("SSN", r'\b\d{3}-\d{2}-\d{4}\b', "[REDACTED_SSN]"),
    ("PHONE", r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b', "[REDACTED_PHONE]"),
    ("EMAIL", r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[REDACTED_EMAIL]"),
    ("DOB", r'\b(DOB|Date of Birth):\s?\d{4}-\d{2}-\d{2}\b', "[REDACTED_DOB]"),
    ("PATIENT_NAME", r'\b(Patient Name|Pt Name):\s?[A-Z][a-z]+\s[A-Z][a-z]+\b', "[REDACTED_NAME]")
]

def scrub_phi_from_text(request: PHIScrubRequest) -> PHIScrubResponse:
    """Scrubs PHI entity instances from text using entity detection rules."""
    text = request.raw_text
    total_redacted = 0
    redacted_types = []

    for name, pattern, replacement in PHI_PATTERNS:
        matches = len(re.findall(pattern, text, flags=re.IGNORECASE))
        if matches > 0:
            total_redacted += matches
            redacted_types.append(name)
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    logger.info(f"PHI Scrubbing complete: Redacted {total_redacted} entities ({redacted_types})")

    return PHIScrubResponse(
        scrubbed_text=text,
        entities_redacted_count=total_redacted,
        redacted_types=redacted_types
    )
