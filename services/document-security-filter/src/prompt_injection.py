import re

from src.logger import logger


class PromptInjectionDetector:
    PATTERNS = [
        # Instruction ignore / override commands
        r"(?i)ignore\s+(?:all\s+|previous\s+|prior\s+)?(?:instructions|rules|directives|prompts|guidelines)",
        r"(?i)override\s+(?:the\s+)?(?:system|instruction|prompt|rules)",
        r"(?i)forget\s+(?:everything\s+)?(?:written\s+)?(?:above|before|previously)",

        # Role emulation / masquerading
        r"(?i)you\s+are\s+now\s+(?:an?\s+)?(?:admin|root|system|assistant|jailbroken|reviewer)",
        r"(?i)new\s+role\s*:",
        r"(?i)instead\s+of\s+doing\s+what\s+you\s+were\s+told",

        # Execution overrides
        r"(?i)do\s+not\s+(?:follow|perform|execute)\s+(?:the\s+)?(?:previous|above|below)\s+(?:instructions|rules)",
        r"(?i)system\s*override\b",
        r"(?i)stop\s+processing\s+and\s+output",
        r"(?i)print\s+the\s+following\s+text\s+instead"
    ]

    def __init__(self):
        self.compiled_patterns = [re.compile(p) for p in self.PATTERNS]

    def scan_text(self, text: str) -> tuple[bool, str]:
        """
        Scans document text for prompt injection overrides.
        Returns (is_safe, description).
        """
        if not text or not text.strip():
            return True, "No text found in PDF"

        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                snippet = text[max(0, match.start()-40):min(len(text), match.end()+40)].replace('\n', ' ')
                logger.warning(
                    "Prompt injection trigger matched!",
                    extra={"pattern": pattern.pattern, "matched_text": snippet}
                )
                return False, f"Prompt injection payload matched: '{pattern.pattern}' in text snippet: '...{snippet}...'"

        return True, "No prompt injection patterns matched"
