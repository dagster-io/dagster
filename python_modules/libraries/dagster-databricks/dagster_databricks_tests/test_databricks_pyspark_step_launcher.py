import os

import pytest
from dagster_databricks.databricks_pyspark_step_launcher import (
    DAGSTER_SYSTEM_ENV_VARS,
    DatabricksPySparkStepLauncher,
)


@pytest.fixture
def mock_step_launcher_factory():
    def _mocked(add_dagster_env_variables: bool, env_variables: dict):
        return DatabricksPySparkStepLauncher(
            run_config={"some": "config"},
            permissions={"some": "permissions"},
            databricks_host="databricks.host.com",
            databricks_token="abc123",
            secrets_to_env_variables=[{"some": "secret"}],
            staging_prefix="/a/prefix",
            wait_for_logs=False,
            max_completion_wait_time_seconds=100,
            env_variables=env_variables,
            add_dagster_env_variables=add_dagster_env_variables,
            local_dagster_job_package_path="some/local/path",
        )

    return _mocked


class TestCreateRemoteConfig:
    def test_given_add_dagster_env_vars_retrieves_dagster_system_vars(
        self, mock_step_launcher_factory, monkeypatch
    ):
        test_env_variables = {"add": "this"}
        test_launcher = mock_step_launcher_factory(
            add_dagster_env_variables=True, env_variables=test_env_variables
        )
        system_vars = {}
        for var in DAGSTER_SYSTEM_ENV_VARS:
            system_vars[var] = f"{var}_value"
            monkeypatch.setenv(var, f"{var}_value")

        correct_vars = dict(**system_vars, **test_env_variables)
        env_vars = test_launcher.create_remote_config()
        assert env_vars.env_variables == correct_vars

    def test_given_no_add_dagster_env_vars_no_system_vars_added(
        self, mock_step_launcher_factory, monkeypatch
    ):
        vars_to_add = {"add": "this"}
        test_launcher = mock_step_launcher_factory(
            add_dagster_env_variables=False, env_variables=vars_to_add
        )
        for var in DAGSTER_SYSTEM_ENV_VARS:
            monkeypatch.setenv(var, f"{var}_value")

        env_vars = test_launcher.create_remote_config()
        assert env_vars.env_variables == vars_to_add

    def test_given_no_dagster_system_vars_none_added(self, mock_step_launcher_factory):
        vars_to_add = {"add": "this"}
        test_launcher = mock_step_launcher_factory(
            add_dagster_env_variables=True, env_variables=vars_to_add
        )
        for var in DAGSTER_SYSTEM_ENV_VARS:
            assert not os.getenv(var)

        env_vars = test_launcher.create_remote_config()
        assert env_vars.env_variables == vars_to_add
