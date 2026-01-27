import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

REQUIRED_VARS_FOR_INTEGRATION_TESTS = [
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_SCHEMA",
    "SNOWFLAKE_WAREHOUSE",
]


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "skip_if_no_snowflake_credentials: skip test if snowflake credentials not available",
    )


def pytest_runtest_setup(item):
    if "skip_if_no_snowflake_credentials" in item.keywords:
        if os.getenv("BUILDKITE") is None:
            # Look for .env file in dagster-snowflake directory
            env_path = Path(__file__).parent.parent / ".env"

            for k, v in dotenv_values(env_path).items():
                if v:
                    os.environ[k] = v

        missing = [var for var in REQUIRED_VARS_FOR_INTEGRATION_TESTS if not os.getenv(var)]
        if missing:
            pytest.skip(f"Missing required environment variables: {missing}")
