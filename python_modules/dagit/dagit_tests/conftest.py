import os

import pytest


@pytest.fixture(scope='session', autouse=True)
def disable_telemetry():
    old_env = os.getenv('DAGSTER_TELEMETRY_ENABLED')
    if old_env != 'False':
        os.environ['DAGSTER_TELEMETRY_ENABLED'] = 'False'
    yield
    if old_env is not None:
        os.environ['DAGSTER_TELEMETRY_ENABLED'] = old_env


@pytest.fixture(scope='session', autouse=True)
def unset_dagster_home():
    old_env = os.getenv('DAGSTER_HOME')
    if old_env is not None:
        del os.environ['DAGSTER_HOME']
    yield
    if old_env is not None:
        os.environ['DAGSTER_HOME'] = old_env
