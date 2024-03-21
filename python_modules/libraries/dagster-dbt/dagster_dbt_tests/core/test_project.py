import pytest
from dagster._core.test_utils import environ
from dagster._utils.test import copy_directory
from dagster_dbt import dbt_assets
from dagster_dbt.dbt_project import DbtProject, prepare_for_deployment
from dagster_dbt.errors import DagsterDbtManifestNotFoundError

from ..dbt_projects import test_jaffle_shop_path


def test_deployed() -> None:
    with copy_directory(test_jaffle_shop_path) as project_dir:
        my_project = DbtProject(project_dir)

        with pytest.raises(DagsterDbtManifestNotFoundError):

            @dbt_assets(manifest=my_project.manifest_path)
            def _(): ...

        prepare_for_deployment(my_project)
        assert my_project.manifest_path.exists()


def test_local_dev() -> None:
    with environ({"DAGSTER_IS_DEV_CLI": "1"}), copy_directory(test_jaffle_shop_path) as project_dir:
        my_project = DbtProject(project_dir)
        assert my_project.manifest_path.exists()


def test_opt_in_env_var() -> None:
    with environ({"DAGSTER_DBT_PARSE_PROJECT_ON_LOAD": "1"}), copy_directory(
        test_jaffle_shop_path
    ) as project_dir:
        my_project = DbtProject(project_dir)
        assert my_project.manifest_path.exists()
