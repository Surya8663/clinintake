echo "=== git status --short ==="
git status --short
echo "=== git branch --show-current ==="
git branch --show-current
echo "=== git rev-parse HEAD ==="
git rev-parse HEAD
echo "=== git diff --stat backup/completed-implementation-before-final-audit..HEAD ==="
git diff --stat backup/completed-implementation-before-final-audit..HEAD
echo "=== git diff --name-only backup/completed-implementation-before-final-audit..HEAD ==="
git diff --name-only backup/completed-implementation-before-final-audit..HEAD
echo "=== git ls-files .env.example ==="
git ls-files .env.example
echo "=== python scripts/quality/scan_secrets.py ==="
python scripts/quality/scan_secrets.py
echo "=== python scripts/quality/scan_forbidden_terms.py ==="
python scripts/quality/scan_forbidden_terms.py
echo "=== python scripts/quality/run_all_gates.py ==="
python scripts/quality/run_all_gates.py
echo "=== make security-scan ==="
make security-scan
echo "=== make verify-no-runtime-fakes ==="
make verify-no-runtime-fakes
echo "=== make contract-check ==="
make contract-check
echo "=== make test-unit ==="
make test-unit
echo "=== pre-commit run --all-files ==="
python -m pre_commit run --all-files
echo "=== docker compose config --services ==="
docker compose config --services
echo "=== docker compose build ==="
docker compose build
echo "=== docker compose up -d ==="
docker compose up -d
echo "=== docker compose ps ==="
docker compose ps
echo "=== python -m compileall -q services shared tools scripts tests ==="
python -m compileall -q services shared tools scripts tests
echo "=== pytest -q ==="
pytest -q
