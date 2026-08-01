import os
from pathlib import Path


def get_secret(name: str, default: str | None = None) -> str:
    """
    Uniform secret loader across all ClinIntake services.

    Resolution Order:
    1. Mounted Docker secret file at `/run/secrets/{name}` or `/run/secrets/{name.lower()}`
    2. Secret file in directory specified by `SECRETS_DIR` environment variable
    3. Environment variable `{name.upper()}`
    4. Default value (if provided)

    Raises `RuntimeError` if the secret is missing and no default is provided.
    """
    # Check /run/secrets/
    for secret_path in [Path(f"/run/secrets/{name}"), Path(f"/run/secrets/{name.lower()}")]:
        if secret_path.is_file():
            try:
                val = secret_path.read_text(encoding="utf-8").strip()
                if val:
                    return val
            except OSError:
                pass

    # Check custom SECRETS_DIR if specified
    secrets_dir_env = os.getenv("SECRETS_DIR")
    if secrets_dir_env:
        secrets_dir = Path(secrets_dir_env)
        for secret_path in [secrets_dir / name, secrets_dir / name.lower()]:
            if secret_path.is_file():
                try:
                    val = secret_path.read_text(encoding="utf-8").strip()
                    if val:
                        return val
                except OSError:
                    pass

    # Check environment variable
    env_val = os.getenv(name.upper()) or os.getenv(name)
    if env_val:
        return env_val

    if default is not None:
        return default

    raise RuntimeError(
        f"CRITICAL: Required secret '{name}' is missing. "
        f"Mount a secret file at /run/secrets/{name} or set environment variable {name.upper()}."
    )
