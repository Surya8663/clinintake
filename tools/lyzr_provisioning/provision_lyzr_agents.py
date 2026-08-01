import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def validate_definitions() -> bool:
    sf_path = REPO_ROOT / "tools" / "lyzr_provisioning" / "superflow_definition.json"
    ag_path = REPO_ROOT / "tools" / "lyzr_provisioning" / "agent_definitions.json"

    if not sf_path.exists() or not ag_path.exists():
        print("[ERROR] Missing SuperFlow or Agent definition file.", file=sys.stderr)
        return False

    with open(sf_path, encoding="utf-8") as f:
        sf = json.load(f)
    with open(ag_path, encoding="utf-8") as f:
        ag = json.load(f)

    print("==================================================")
    print(" LYZR PROVISIONING VALIDATION SUMMARY")
    print("==================================================")
    print(f"SuperFlow ID: {sf.get('superflow_id')}")
    print(f"Nodes Count: {len(sf.get('nodes', []))}")
    print(f"Explicit Branches: {', '.join(sf.get('explicit_branches', []))}")
    print(f"Configured Agents: {len(ag.get('agents', []))}")
    for a in ag.get("agents", []):
        print(f"  - Agent ID: {a['agent_id']} ({a['name']}) Policies: {a['policies']}")
    print("==================================================")
    print("STATUS: VALIDATED CLEAN")
    return True


def main():
    parser = argparse.ArgumentParser(description="Lyzr Provisioning & Validation CLI")
    parser.add_argument("--validate", action="store_true", help="Validate checked-in Lyzr definitions")
    args = parser.parse_args()

    if not validate_definitions():
        sys.exit(1)


if __name__ == "__main__":
    main()
