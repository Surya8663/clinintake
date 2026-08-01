#!/usr/bin/env python3
"""Run all quality gate scripts and report pass/fail summary.

Exit code 0 = all gates passed, 1 = at least one gate failed.
"""

from pathlib import Path
import subprocess
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent

GATES = [
    ("Secret Scan", "scan_secrets.py"),
    ("Forbidden Runtime Terms", "scan_forbidden_terms.py"),
    ("Silent Exceptions", "scan_silent_exceptions.py"),
    ("Missing Dockerfiles", "scan_missing_dockerfiles.py"),
    ("Hardcoded Localhost URLs", "scan_hardcoded_localhost.py"),
    ("Test Imports in Runtime", "scan_test_imports_in_runtime.py"),
    ("Duplicate Env Defaults", "scan_duplicate_env_defaults.py"),
]


def main() -> int:
    results: list[tuple[str, int, str]] = []
    any_failed = False

    print("=" * 70)
    print("  ClinIntake Quality Gate Runner")
    print("=" * 70)
    print()

    for name, script_name in GATES:
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            results.append((name, -1, "Script not found"))
            any_failed = True
            continue

        print(f"--- Running: {name} ---")
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            results.append((name, result.returncode, "PASS" if result.returncode == 0 else "FAIL"))
            if result.returncode != 0:
                any_failed = True
        except subprocess.TimeoutExpired:
            results.append((name, -1, "TIMEOUT"))
            any_failed = True
        except Exception as e:
            results.append((name, -1, f"ERROR: {e}"))
            any_failed = True

    # Summary
    print()
    print("=" * 70)
    print("  QUALITY GATE SUMMARY")
    print("=" * 70)
    for name, code, status in results:
        tag = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"  {tag} {name}: {status} (exit code: {code})")
    print()

    if any_failed:
        print("[FAIL] OVERALL: Some quality gates failed.")
        return 1
    else:
        print("[PASS] OVERALL: All quality gates passed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
