#!/usr/bin/env python3
"""Scan for test fixture imports in runtime (non-test) code.

Detects patterns like:
  - from tests.* import ...
  - import tests.*
  - from conftest import ...

Exit code 0 = clean, 1 = findings.
"""

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

TEST_IMPORT_PATTERNS = [
    (r"^\s*from\s+tests[\.\s]", "Import from tests package in runtime code"),
    (r"^\s*import\s+tests[\.\s]", "Import of tests package in runtime code"),
    (r"^\s*from\s+conftest\s+import", "Import from conftest in runtime code"),
    (r"^\s*from\s+\.+tests\s+import", "Relative import from tests in runtime code"),
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
    "scripts",
    "docs",
}

INCLUDE_EXTENSIONS = {".py"}


def should_skip(path: Path) -> bool:
    parts = path.parts
    if any(d in parts for d in EXCLUDE_DIRS):
        return True
    # Skip test files and test directories
    if "test" in path.name.lower() or "/tests/" in str(path).replace("\\", "/") or "\\tests\\" in str(path):
        return True
    if path.name == "conftest.py":
        return True
    return False


def scan() -> list[tuple[str, int, str, str]]:
    findings: list[tuple[str, int, str, str]] = []

    for filepath in REPO_ROOT.rglob("*.py"):
        if should_skip(filepath):
            continue
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel = str(filepath.relative_to(REPO_ROOT))
        for line_num, line in enumerate(content.splitlines(), start=1):
            for pattern, description in TEST_IMPORT_PATTERNS:
                if re.search(pattern, line):
                    findings.append((rel, line_num, line.strip(), description))

    return findings


def main() -> int:
    findings = scan()

    if not findings:
        print("[PASS] TEST IMPORTS: No test fixture imports found in runtime code.")
        return 0

    print(f"[FAIL] TEST IMPORTS: {len(findings)} finding(s)\n")
    for filepath, line_num, line_content, description in findings:
        print(f"  {filepath}:{line_num}")
        print(f"    {description}: {line_content[:120]}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
