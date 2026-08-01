#!/usr/bin/env python3
"""Scan for hardcoded localhost/127.0.0.1 URLs in application source.

Checks runtime code (not tests, not configs) for hardcoded localhost
references that would break in deployed environments.

Exit code 0 = clean, 1 = findings.
"""

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

LOCALHOST_PATTERNS = [
    (r"https?://localhost[:/]", "Hardcoded localhost URL"),
    (r"https?://127\.0\.0\.1[:/]", "Hardcoded 127.0.0.1 URL"),
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

# Files where localhost is expected (configs use Field defaults for local dev)
EXCLUDE_FILES = {
    ".env.example",
    "docker-compose.yml",
}

INCLUDE_EXTENSIONS = {".py", ".ts", ".tsx"}


def should_skip(path: Path) -> bool:
    parts = path.parts
    if any(d in parts for d in EXCLUDE_DIRS):
        return True
    if path.name in EXCLUDE_FILES:
        return True
    # Skip test files
    if "test" in path.name.lower() or "/tests/" in str(path).replace("\\", "/") or "\\tests\\" in str(path):
        return True
    return False


def scan() -> list[tuple[str, int, str, str, bool]]:
    """Returns (filepath, line_num, line, description, is_config)."""
    findings: list[tuple[str, int, str, str, bool]] = []

    for ext in INCLUDE_EXTENSIONS:
        for filepath in REPO_ROOT.rglob(f"*{ext}"):
            if should_skip(filepath):
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            is_config = filepath.name == "config.py"
            rel = str(filepath.relative_to(REPO_ROOT))

            for line_num, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    continue
                for pattern, description in LOCALHOST_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append((rel, line_num, stripped, description, is_config))

    return findings


def main() -> int:
    findings = scan()
    config_findings = [f for f in findings if f[4]]
    non_config_findings = [f for f in findings if not f[4]]

    if not findings:
        print("[PASS] LOCALHOST SCAN: No hardcoded localhost URLs found.")
        return 0

    exit_code = 0

    if non_config_findings:
        print(f"[FAIL] LOCALHOST (non-config): {len(non_config_findings)} finding(s)\n")
        for filepath, line_num, line_content, description, _ in non_config_findings:
            print(f"  {filepath}:{line_num}")
            print(f"    {description}: {line_content[:120]}")
            print()
        exit_code = 1

    if config_findings:
        print(f"[INFO] LOCALHOST (config defaults, acceptable for local dev): {len(config_findings)} instance(s)\n")
        for filepath, line_num, line_content, description, _ in config_findings:
            print(f"  {filepath}:{line_num}")
            print(f"    {description}: {line_content[:120]}")
            print()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
