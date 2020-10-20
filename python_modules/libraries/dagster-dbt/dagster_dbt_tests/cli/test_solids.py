import pytest
from dagster import configured, execute_solid
from dagster_dbt import (
    dbt_cli_compile,
    dbt_cli_run,
    dbt_cli_run_operation,
    dbt_cli_snapshot,
    dbt_cli_snapshot_freshness,
    dbt_cli_test,
)
from dagster_dbt.errors import DagsterDbtCliFatalRuntimeError


class TestDbtCliSolids:
    def test_dbt_cli_with_unset_env_var_in_profile(
        self, dbt_seed, test_project_dir, dbt_config_dir, monkeypatch
    ):  # pylint: disable=unused-argument

        monkeypatch.delenv("POSTGRES_TEST_DB_DBT_HOST")
        test_solid = configured(dbt_cli_run, name="test_solid")(
            {"project-dir": test_project_dir, "profiles-dir": dbt_config_dir}
        )
        with pytest.raises(DagsterDbtCliFatalRuntimeError) as exc:
            execute_solid(test_solid)

        failure: DagsterDbtCliFatalRuntimeError = exc.value
        assert "Env var required but not provided:" in failure.metadata_entries[1].entry_data.text

    def test_dbt_cli_run(
        self, dbt_seed, test_project_dir, dbt_config_dir
    ):  # pylint: disable=unused-argument
        test_solid = configured(dbt_cli_run, name="test_solid")(
            {"project-dir": test_project_dir, "profiles-dir": dbt_config_dir}
        )

        result = execute_solid(test_solid)
        assert result.success

    def test_dbt_cli_run_with_extra_config(
        self, dbt_seed, test_project_dir, dbt_config_dir
    ):  # pylint: disable=unused-argument
        test_solid = configured(dbt_cli_run, name="test_solid")(
            {
                "project-dir": test_project_dir,
                "profiles-dir": dbt_config_dir,
                "threads": 1,
                "models": ["least_caloric"],
                "fail-fast": True,
            }
        )

        result = execute_solid(test_solid)
        assert result.success

    def test_dbt_cli_test(
        self, dbt_seed, test_project_dir, dbt_config_dir
    ):  # pylint: disable=unused-argument
        test_solid = configured(dbt_cli_test, name="test_solid")(
            {"project-dir": test_project_dir, "profiles-dir": dbt_config_dir}
        )

        result = execute_solid(test_solid)
        assert result.success

    def test_dbt_cli_snapshot(
        self, dbt_seed, test_project_dir, dbt_config_dir
    ):  # pylint: disable=unused-argument
        test_solid = configured(dbt_cli_snapshot, name="test_solid")(
            {"project-dir": test_project_dir, "profiles-dir": dbt_config_dir}
        )

        result = execute_solid(test_solid)
        assert result.success

    def test_dbt_cli_run_operation(
        self, dbt_seed, test_project_dir, dbt_config_dir
    ):  # pylint: disable=unused-argument
        test_solid = configured(dbt_cli_run_operation, name="test_solid")(
            {
                "project-dir": test_project_dir,
                "profiles-dir": dbt_config_dir,
                "macro": "log_macro",
                "args": {"msg": "<<test succeded!>>"},
            }
        )

        result = execute_solid(test_solid)
        assert result.success
        assert any(
            "Log macro: <<test succeded!>>" in log["message"]
            for log in result.output_value()["logs"]
        )

    def test_dbt_cli_snapshot_freshness(
        self, dbt_seed, test_project_dir, dbt_config_dir
    ):  # pylint: disable=unused-argument
        """This command will is a no-op without more arguments, but this test shows that it can invoked successfully."""
        test_solid = configured(dbt_cli_snapshot_freshness, name="test_solid")(
            {"project-dir": test_project_dir, "profiles-dir": dbt_config_dir}
        )

        result = execute_solid(test_solid)
        assert result.success

    def test_dbt_cli_compile(
        self, dbt_seed, test_project_dir, dbt_config_dir
    ):  # pylint: disable=unused-argument
        test_solid = configured(dbt_cli_compile, name="test_solid")(
            {"project-dir": test_project_dir, "profiles-dir": dbt_config_dir}
        )

        result = execute_solid(test_solid)
        assert result.success
