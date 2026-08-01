import os
import re
import subprocess
import sys
from pathlib import Path


def run_service_tests(service_dir: Path) -> tuple[int, int, int, str]:
    """
    Runs pytest for a specific service directory in an isolated Python subprocess.
    Returns (returncode, passed_count, failed_count, full_output).
    Uses subprocess returncode as the absolute source of truth.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(service_dir)

    test_dir = service_dir / "tests"
    cmd = [sys.executable, "-m", "pytest", "-v", str(test_dir)]

    result = subprocess.run(cmd, cwd=str(Path(__file__).parent.parent), env=env, capture_output=True, text=True)

    returncode = result.returncode
    passed = 0
    failed = 0

    full_output = f"--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}"

    for line in result.stdout.splitlines():
        if " passed" in line or " failed" in line:
            m_pass = re.search(r"(\d+) passed", line)
            m_fail = re.search(r"(\d+) failed", line)
            if m_pass:
                passed = int(m_pass.group(1))
            if m_fail:
                failed = int(m_fail.group(1))

    return returncode, passed, failed, full_output


def main():
    root_dir = Path(__file__).parent.parent
    services = [
        ("services/orchestrator", root_dir / "services/orchestrator"),
        ("services/extraction-agent", root_dir / "services/extraction-agent"),
        ("services/care-gap-explanation-agent", root_dir / "services/care-gap-explanation-agent"),
        ("services/referral-drafting-agent", root_dir / "services/referral-drafting-agent"),
    ]

    total_passed = 0
    total_failed = 0
    service_results = []
    has_failure = False

    print("=" * 70)
    print("      BLOCKER 1 ISOLATED TEST RUNNER      ")
    print("=" * 70)

    for name, path in services:
        print(f"Running test suite for {name}...")
        returncode, passed, failed, output = run_service_tests(path)

        total_passed += passed
        total_failed += failed

        # Returncode is the absolute source of truth
        if returncode != 0 or passed == 0:
            status = "FAILED"
            has_failure = True
        else:
            status = "PASSED"

        service_results.append((name, returncode, passed, failed, status, output))
        print(f"  Result: {status} (exit code: {returncode}, {passed} passed, {failed} failed)")

    print("=" * 70)
    print("SUMMARY BY SERVICE:")
    print("-" * 70)
    for name, returncode, passed, failed, status, output in service_results:
        print(f"  - {name:<36}: exit code {returncode}, {passed:>3} passed, {failed:>3} failed [{status}]")
    print("-" * 70)
    print(f"TOTAL AGGREGATED TESTS: {total_passed} passed, {total_failed} failed")
    print("=" * 70)

    if has_failure:
        print("\nFAILURE DETAILS:")
        for name, returncode, passed, failed, status, output in service_results:
            if returncode != 0 or status == "FAILED":
                print(f"\n==================== FULL OUTPUT FOR {name} (EXIT CODE {returncode}) ====================")
                print(output)
        sys.exit(1)
    else:
        print("\nALL BLOCKER 1 TEST SUITES PASSED CLEANLY.")
        sys.exit(0)


if __name__ == "__main__":
    main()
