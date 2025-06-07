import os

from create_dagster.version_check import CREATE_DAGSTER_UPDATE_CHECK_ENABLED_ENV_VAR


# Configures test environment before any tests are run.
def pytest_configure():
    # Disable the update check for all tests because we don't want to bomb the PyPI API.
    # Tests that specifically want to test the update check should set this env var to "1".
    os.environ[CREATE_DAGSTER_UPDATE_CHECK_ENABLED_ENV_VAR] = "0"
