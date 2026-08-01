#!/usr/bin/env python3
"""Scan for hardcoded secret patterns in source code.

Checks for patterns like API keys, passwords, tokens, and signing keys
embedded as string literals in Python and TypeScript source files.
Excludes .env.example, test files, docs, and node_modules.

Exit code 0 = clean, 1 = findings.
"""

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Patterns that strongly indicate a hardcoded secret value (not a variable name)
SECRET_PATTERNS = [
    # Known leaked values from baseline audit
    (r"clinintake_kms_master_", "Known hardcoded HMAC/JWT secret"),
    (r"sec_kms_ehr_write_token_", "Known hardcoded EHR client secret"),
    (r"key_live_fhir_write_access", "Known hardcoded EHR API key"),
    (r"test-secret-key-do-not-use", "Known hardcoded test JWT secret"),
    (r"L_U1X0b44v87gD2WvLgA_90f23JmH_fGfHjKsJ0G2k4=", "Known hardcoded Fernet key"),
    # Generic patterns for password/secret in default values
    (r'default\s*=\s*["\'].*(?:password|passwd|secret|token).*["\']', "Default value containing password/secret/token"),
    (r"dev_user:dev_password", "Hardcoded dev credentials in connection string"),
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
}

EXCLUDE_FILES = {
    ".env.example",
    "remediation-baseline.md",
    "repository-inventory.md",
    "scan_secrets.py",  # This script itself
}

INCLUDE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".yml", ".yaml", ".json", ".toml"}


def should_skip(path: Path) -> bool:
    parts = path.parts
    # Skip excluded directories
    if any(d in parts for d in EXCLUDE_DIRS):
        return True
    # Skip excluded files
    if path.name in EXCLUDE_FILES:
        return True
    # Skip test files
    if "test" in path.name.lower() or "/tests/" in str(path).replace("\\", "/"):
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
                for pattern, description in SECRET_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        rel = filepath.relative_to(REPO_ROOT)
                        findings.append((str(rel), line_num, line.strip(), description))

    return findings


def main() -> int:
    findings = scan()

    if not findings:
        print("[PASS] SECRET SCAN: No hardcoded secrets found.")
        return 0

    print(f"[FAIL] SECRET SCAN: {len(findings)} finding(s)\n")
    for filepath, line_num, line_content, description in findings:
        print(f"  {filepath}:{line_num}")
        print(f"    Pattern: {description}")
        print(f"    Line:    {line_content[:120]}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
