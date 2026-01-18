import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def enable_defensive_checks():
    os.environ["DAGSTER_RECORD_DEFENSIVE_CHECKS"] = "true"
