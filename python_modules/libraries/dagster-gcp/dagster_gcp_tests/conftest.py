import os

import pytest

REQUIRED_GCP_ENV_VARS = [
    "GCP_PROJECT_ID",
    "GOOGLE_APPLICATION_CREDENTIALS",
]


def _missing_gcp_env_vars() -> list[str]:
    missing = [var for var in REQUIRED_GCP_ENV_VARS if not os.getenv(var)]
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and not os.path.exists(creds_path):
        missing.append("GOOGLE_APPLICATION_CREDENTIALS (file not found)")
    return missing


def pytest_runtest_setup(item):
    if "integration" not in item.keywords:
        return

    missing = _missing_gcp_env_vars()
    if missing:
        pytest.skip(f"Missing required GCP environment variables: {missing}")
