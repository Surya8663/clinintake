import os
import re
import subprocess
import sys
from pathlib import Path


def run_service_tests(service_dir: Path) -> tuple[int, int, str]:
    """Runs pytest for a specific service directory in an isolated Python subprocess with custom PYTHONPATH."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(service_dir)

    test_dir = service_dir / "tests"
    cmd = [sys.executable, "-m", "pytest", "-v", str(test_dir)]

    result = subprocess.run(cmd, cwd=str(Path(__file__).parent.parent), env=env, capture_output=True, text=True)

    passed = 0
    failed = 0

    # Parse passed/failed counts from pytest output
    for line in result.stdout.splitlines():
        if " passed" in line or " failed" in line:
            m_pass = re.search(r"(\d+) passed", line)
            m_fail = re.search(r"(\d+) failed", line)
            if m_pass:
                passed = int(m_pass.group(1))
            if m_fail:
                failed = int(m_fail.group(1))

    return passed, failed, result.stdout + "\n" + result.stderr


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
        passed, failed, output = run_service_tests(path)
        total_passed += passed
        total_failed += failed
        status = "PASSED" if failed == 0 and passed > 0 else "FAILED"
        if failed > 0 or passed == 0:
            has_failure = True
        service_results.append((name, passed, failed, status, output))
        print(f"  Result: {status} ({passed} passed, {failed} failed)")

    print("=" * 70)
    print("SUMMARY BY SERVICE:")
    print("-" * 70)
    for name, passed, failed, status, output in service_results:
        print(f"  - {name:<36}: {passed:>3} passed, {failed:>3} failed [{status}]")
    print("-" * 70)
    print(f"TOTAL AGGREGATED TESTS: {total_passed} passed, {total_failed} failed")
    print("=" * 70)

    if has_failure:
        print("\nFAILURE DETAILS:")
        for name, passed, failed, status, output in service_results:
            if failed > 0:
                print(f"\n--- Output for {name} ---")
                print(output)
        sys.exit(1)
    else:
        print("\nALL BLOCKER 1 TEST SUITES PASSED CLEANLY.")
        sys.exit(0)


if __name__ == "__main__":
    main()
