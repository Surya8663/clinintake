#!/usr/bin/env python3
"""Scan for broad exception swallowing and silent success patterns.

Detects:
  - except Exception: pass
  - except: pass
  - catch blocks that set success state

Exit code 0 = clean, 1 = findings.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

EXCLUDE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "scripts",
}

INCLUDE_EXTENSIONS = {".py", ".ts", ".tsx"}


def should_skip(path: Path) -> bool:
    parts = path.parts
    if any(d in parts for d in EXCLUDE_DIRS):
        return True
    # Skip test files
    if "test" in path.name.lower() or "/tests/" in str(path).replace("\\", "/") or "\\tests\\" in str(path):
        return True
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
                lines = filepath.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue

            rel = str(filepath.relative_to(REPO_ROOT))

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Python: except Exception: pass / except: pass
                if re.search(r'except\s*(?:Exception)?\s*:\s*pass', stripped):
                    findings.append((rel, i + 1, stripped, "Broad exception silently swallowed with pass"))
                elif re.search(r'except\s*(?:Exception)?\s*:\s*\.\.\.', stripped):
                    findings.append((rel, i + 1, stripped, "Broad exception silently swallowed with ellipsis"))

                # Python: except block followed immediately by pass on next line
                if re.match(r'except\s*(Exception)?\s*:', stripped) and i + 1 < len(lines):
                    next_stripped = lines[i + 1].strip()
                    if next_stripped == "pass":
                        findings.append((rel, i + 1, f"{stripped} -> {next_stripped}",
                                         "Broad exception followed by pass on next line"))

                # TypeScript/JS: catch block that sets success state
                if ext in {".ts", ".tsx", ".js", ".jsx"}:
                    if re.search(r'}\s*catch\s*\(', stripped) or re.match(r'catch\s*\(', stripped):
                        # Check next 5 lines for success-setting patterns
                        for j in range(i + 1, min(i + 6, len(lines))):
                            check_line = lines[j].strip()
                            if re.search(r"(?:success|approved|saved|completed)\s*(?:\(|=)", check_line, re.IGNORECASE):
                                findings.append((rel, j + 1, check_line,
                                                 "Success/approval state set inside catch block"))

    return findings


def main() -> int:
    findings = scan()

    if not findings:
        print("[PASS] SILENT EXCEPTIONS: No broad exception swallowing found.")
        return 0

    print(f"[FAIL] SILENT EXCEPTIONS: {len(findings)} finding(s)\n")
    for filepath, line_num, line_content, description in findings:
        print(f"  {filepath}:{line_num}")
        print(f"    Pattern: {description}")
        print(f"    Line:    {line_content[:120]}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
