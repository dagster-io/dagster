import os

from dagster_databricks.databricks_pyspark_step_launcher import (
    DAGSTER_SYSTEM_ENV_VARS,
    DatabricksPySparkStepLauncher,
)


class TestCreateRemoteConfig:
    def test_given_add_dagster_env_vars_retrieves_dagster_system_vars(self, monkeypatch):
        test_launcher = DatabricksPySparkStepLauncher(
            run_config={"some": "config"},
            permissions={"some": "permissions"},
            databricks_host="databricks.host.com",
            databricks_token="abc123",
            secrets_to_env_variables=[{"some": "secret"}],
            staging_prefix="/a/prefix",
            wait_for_logs=False,
            max_completion_wait_time_seconds=100,
            env_variables={"add": "this"},
            add_dagster_env_variables=True,
            local_dagster_job_package_path="some/local/path",
        )
        system_vars = {}
        for i, var in enumerate(DAGSTER_SYSTEM_ENV_VARS):
            system_vars[var] = f"{var}_value"
            monkeypatch.setenv(var, f"{var}_value")

        correct_vars = dict(**system_vars, add="this")
        env_vars = test_launcher.create_remote_config()
        assert env_vars.env_variables == correct_vars

    def test_given_no_add_dagster_env_vars_no_system_vars_added(self, monkeypatch):
        vars_to_add = {"add": "this"}
        test_launcher = DatabricksPySparkStepLauncher(
            run_config={"some": "config"},
            permissions={"some": "permissions"},
            databricks_host="databricks.host.com",
            databricks_token="abc123",
            secrets_to_env_variables=[{"some": "secret"}],
            staging_prefix="/a/prefix",
            wait_for_logs=False,
            max_completion_wait_time_seconds=100,
            env_variables=vars_to_add,
            add_dagster_env_variables=False,
            local_dagster_job_package_path="some/local/path",
        )
        system_vars = {}
        for i, var in enumerate(DAGSTER_SYSTEM_ENV_VARS):
            system_vars[var] = f"{var}_value"
            monkeypatch.setenv(var, f"{var}_value")

        env_vars = test_launcher.create_remote_config()
        assert env_vars.env_variables == vars_to_add

    def test_given_no_dagster_system_vars_none_added(self):
        vars_to_add = {"add": "this"}
        test_launcher = DatabricksPySparkStepLauncher(
            run_config={"some": "config"},
            permissions={"some": "permissions"},
            databricks_host="databricks.host.com",
            databricks_token="abc123",
            secrets_to_env_variables=[{"some": "secret"}],
            staging_prefix="/a/prefix",
            wait_for_logs=False,
            max_completion_wait_time_seconds=100,
            env_variables=vars_to_add,
            add_dagster_env_variables=True,
            local_dagster_job_package_path="some/local/path",
        )
        system_vars = {}
        for i, var in enumerate(DAGSTER_SYSTEM_ENV_VARS):
            assert not os.getenv(var)

        env_vars = test_launcher.create_remote_config()
        assert env_vars.env_variables == vars_to_add
