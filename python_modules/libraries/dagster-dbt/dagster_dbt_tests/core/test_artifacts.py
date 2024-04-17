import pytest
from dagster._core.test_utils import environ
from dagster._utils.test import copy_directory
from dagster_dbt.dbt_artifacts import DbtArtifacts
from dagster_dbt.errors import DagsterDbtManifestNotPreparedError

from ..dbt_projects import test_jaffle_shop_path


def test_expected_but_missing() -> None:
    with copy_directory(test_jaffle_shop_path) as project_dir:
        dbt_artifacts = DbtArtifacts(project_dir=project_dir)

        with pytest.raises(DagsterDbtManifestNotPreparedError):
            _ = dbt_artifacts.manifest_path

        dbt_artifacts.prepare()
        assert dbt_artifacts.manifest_path.exists()


def test_dagster_dev() -> None:
    with environ({"DAGSTER_IS_DEV_CLI": "1"}), copy_directory(test_jaffle_shop_path) as project_dir:
        dbt_artifacts = DbtArtifacts(project_dir=project_dir)
        assert dbt_artifacts.manifest_path.exists()


def test_opt_in_env_var() -> None:
    with environ({"DAGSTER_DBT_PARSE_PROJECT_ON_LOAD": "1"}), copy_directory(
        test_jaffle_shop_path
    ) as project_dir:
        dbt_artifacts = DbtArtifacts(project_dir=project_dir)
        assert dbt_artifacts.manifest_path.exists()
