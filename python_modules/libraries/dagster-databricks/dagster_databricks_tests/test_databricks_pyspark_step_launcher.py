import os
from typing import Dict, Optional
from unittest import mock

import pytest
from dagster_databricks.databricks_pyspark_step_launcher import (
    DAGSTER_SYSTEM_ENV_VARS,
    DatabricksPySparkStepLauncher,
)


@pytest.fixture
def mock_step_launcher_factory():
    def _mocked(
        add_dagster_env_variables: bool = True,
        env_variables: Optional[dict] = None,
        databricks_token: Optional[str] = None,
        oauth_creds: Optional[dict[str, str]] = None,
        azure_creds: Optional[dict[str, str]] = None,
    ):
        return DatabricksPySparkStepLauncher(
            run_config={"some": "config"},
            permissions={"some": "permissions"},
            databricks_host="databricks.host.com",
            databricks_token=databricks_token,
            secrets_to_env_variables=[{"some": "secret"}],
            staging_prefix="/a/prefix",
            wait_for_logs=False,
            max_completion_wait_time_seconds=100,
            env_variables=env_variables,
            add_dagster_env_variables=add_dagster_env_variables,
            local_dagster_job_package_path="some/local/path",
            oauth_credentials=oauth_creds,
            azure_credentials=azure_creds,
        )

    return _mocked


class TestCreateRemoteConfig:
    def test_given_add_dagster_env_vars_retrieves_dagster_system_vars(
        self, mock_step_launcher_factory, monkeypatch
    ):
        test_env_variables = {"add": "this"}
        test_launcher = mock_step_launcher_factory(
            add_dagster_env_variables=True,
            env_variables=test_env_variables,
            databricks_token="abc123",
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
            add_dagster_env_variables=False, env_variables=vars_to_add, databricks_token="abc123"
        )
        for var in DAGSTER_SYSTEM_ENV_VARS:
            monkeypatch.setenv(var, f"{var}_value")

        env_vars = test_launcher.create_remote_config()
        assert env_vars.env_variables == vars_to_add

    def test_given_no_dagster_system_vars_none_added(self, mock_step_launcher_factory):
        vars_to_add = {"add": "this"}
        test_launcher = mock_step_launcher_factory(
            add_dagster_env_variables=True, env_variables=vars_to_add, databricks_token="abc123"
        )
        for var in DAGSTER_SYSTEM_ENV_VARS:
            assert not os.getenv(var)

        env_vars = test_launcher.create_remote_config()
        assert env_vars.env_variables == vars_to_add

    @mock.patch("dagster_databricks.databricks.Config")
    def test_given_bad_config_raises_ValueError(
        self, mock_workspace_client_config, mock_step_launcher_factory
    ):
        with pytest.raises(
            ValueError,
            match=(
                "If using databricks service principal oauth credentials, both oauth_client_id and"
                " oauth_client_secret must be provided"
            ),
        ):
            mock_step_launcher_factory(
                oauth_creds={"client_id": "abc123"},
            )
        with pytest.raises(
            ValueError,
            match=(
                "If using azure service principal auth, azure_client_id, azure_client_secret, and"
                " azure_tenant_id must be provided"
            ),
        ):
            mock_step_launcher_factory(azure_creds={"azure_client_id": "abc123"})
