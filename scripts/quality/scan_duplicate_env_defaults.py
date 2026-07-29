#!/usr/bin/env python3
"""Scan for duplicate environment variable definitions with conflicting defaults.

Checks across all config.py files for env vars defined in multiple places
with different default values.

Exit code 0 = clean, 1 = conflicts found.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def extract_env_vars(filepath: Path) -> list[tuple[str, str, int]]:
    """Extract (VAR_NAME, default_value, line_num) from a config file."""
    results = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return results

    for line_num, line in enumerate(content.splitlines(), start=1):
        # Match os.getenv("VAR", "default")
        m = re.search(r'os\.getenv\(\s*["\'](\w+)["\']\s*,\s*["\']([^"\']*)["\']', line)
        if m:
            results.append((m.group(1), m.group(2), line_num))
            continue

        # Match Field(default="value") with env_prefix from pydantic-settings
        # The field name maps to ENV_VAR_NAME via pydantic-settings uppercase convention
        m = re.search(r'(\w+)\s*:\s*\w+\s*=\s*Field\(\s*default\s*=\s*["\']([^"\']*)["\']', line)
        if m:
            field_name = m.group(1)
            env_name = field_name.upper()
            results.append((env_name, m.group(2), line_num))

    return results


def scan() -> list[tuple[str, list[tuple[str, str, int]]]]:
    """Find env vars with conflicting defaults across config files."""
    env_registry: dict[str, list[tuple[str, str, int]]] = defaultdict(list)

    for config_file in REPO_ROOT.rglob("*/src/config.py"):
        rel = str(config_file.relative_to(REPO_ROOT))
        for var_name, default_val, line_num in extract_env_vars(config_file):
            env_registry[var_name].append((rel, default_val, line_num))

    conflicts = []
    for var_name, occurrences in sorted(env_registry.items()):
        if len(occurrences) < 2:
            continue
        defaults = set(o[1] for o in occurrences)
        if len(defaults) > 1:
            conflicts.append((var_name, occurrences))

    return conflicts


def main() -> int:
    conflicts = scan()

    if not conflicts:
        print("[PASS] DUPLICATE ENV VARS: No conflicting environment variable defaults found.")
        return 0

    print(f"[FAIL] DUPLICATE ENV VARS: {len(conflicts)} conflicting variable(s)\n")
    for var_name, occurrences in conflicts:
        print(f"  Variable: {var_name}")
        for filepath, default_val, line_num in occurrences:
            print(f"    {filepath}:{line_num} -> default=\"{default_val}\"")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
