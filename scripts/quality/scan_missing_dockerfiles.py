#!/usr/bin/env python3
"""Check that every Docker Compose build context has a Dockerfile.

Parses docker-compose.yml and verifies that a Dockerfile exists
in each service's build context directory.

Exit code 0 = all present, 1 = missing Dockerfiles.
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"


def scan() -> list[tuple[str, str]]:
    """Return list of (service_name, build_context) where Dockerfile is missing."""
    if not COMPOSE_FILE.exists():
        print("[WARN] docker-compose.yml not found - skipping.")
        return []

    content = COMPOSE_FILE.read_text(encoding="utf-8")
    missing: list[tuple[str, str]] = []

    # Simple YAML parsing for build contexts
    current_service = None
    in_build = False

    for line in content.splitlines():
        stripped = line.strip()

        # Detect top-level service name (2-space indent under services:)
        if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            current_service = stripped.rstrip(":")
            in_build = False

        # Detect build: section
        if stripped.startswith("build:"):
            in_build = True

        # Detect context: under build:
        if in_build and stripped.startswith("context:"):
            context_path = stripped.split(":", 1)[1].strip()
            dockerfile = REPO_ROOT / context_path / "Dockerfile"
            if not dockerfile.exists():
                missing.append((current_service or "unknown", context_path))
            in_build = False

    return missing


def main() -> int:
    missing = scan()

    if not missing:
        print("[PASS] DOCKERFILES: All build contexts have Dockerfiles.")
        return 0

    print(f"[FAIL] DOCKERFILES: {len(missing)} build context(s) missing Dockerfile\n")
    for service, context in missing:
        print(f"  Service: {service}")
        print(f"  Context: {context}")
        print(f"  Missing: {context}/Dockerfile")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
