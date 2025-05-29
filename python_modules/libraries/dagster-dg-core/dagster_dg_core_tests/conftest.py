import os

from dagster_dg_core.context import DG_UPDATE_CHECK_ENABLED_ENV_VAR


# Runs once before every test
def pytest_configure():
    # Disable the update check for all tests because we don't want to bomb the PyPI API.
    # Tests that specifically want to test the update check should set this env var to "1".
    os.environ[DG_UPDATE_CHECK_ENABLED_ENV_VAR] = "0"
