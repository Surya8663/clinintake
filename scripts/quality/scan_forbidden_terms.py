#!/usr/bin/env python3
"""Scan for forbidden runtime terms outside tests/docs.

Detects mock, dummy, fake, demo, canned, fabricated fallback records,
and fixed signature strings in runtime (non-test) code.

Exit code 0 = clean, 1 = findings.
"""

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

FORBIDDEN_PATTERNS = [
    (r"\bmock\b", "Forbidden term: 'mock' in runtime code"),
    (r"\bdummy\b", "Forbidden term: 'dummy' in runtime code"),
    (r"\bfake\b", "Forbidden term: 'fake' in runtime code"),
    (r"\bdemo\b", "Forbidden term: 'demo' in runtime code"),
    (r"\bcanned\b", "Forbidden term: 'canned' in runtime code"),
    (r"\bsample_patient\b", "Fabricated patient record"),
    (r"\bfallback.*record\b", "Fabricated fallback record"),
    (r"\bdefault.*entry\b", "Fabricated default entry"),
    (r'"SIG-ECDSA-[^"]*"', "Hardcoded fixed signature string"),
]

EXCLUDE_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "scripts",  # Allow quality scripts to reference these terms
}

EXCLUDE_FILES = {
    ".env.example",
    "remediation-baseline.md",
    "repository-inventory.md",
}

INCLUDE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx"}


def should_skip(path: Path) -> bool:
    parts = path.parts
    if any(d in parts for d in EXCLUDE_DIRS):
        return True
    if path.name in EXCLUDE_FILES:
        return True
    # Skip test files and test directories
    if "test" in path.name.lower() or "/tests/" in str(path).replace("\\", "/") or "\\tests\\" in str(path):
        return True
    # Skip docs
    if "docs" in parts:
        return True
    return False


def scan() -> list[tuple[str, int, str, str]]:
    findings: list[tuple[str, int, str, str]] = []

    for ext in INCLUDE_EXTENSIONS:
        for filepath in REPO_ROOT.rglob(f"*{ext}"):
            if should_skip(filepath):
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for line_num, line in enumerate(content.splitlines(), start=1):
                # Skip comment lines
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                    continue
                for pattern, description in FORBIDDEN_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        rel = filepath.relative_to(REPO_ROOT)
                        findings.append((str(rel), line_num, line.strip(), description))

    return findings


def main() -> int:
    findings = scan()

    if not findings:
        print("[PASS] FORBIDDEN TERMS: No forbidden runtime terms found.")
        return 0

    print(f"[FAIL] FORBIDDEN TERMS: {len(findings)} finding(s)\n")
    for filepath, line_num, line_content, description in findings:
        print(f"  {filepath}:{line_num}")
        print(f"    Pattern: {description}")
        print(f"    Line:    {line_content[:120]}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
