from dagster._core.test_utils import environ
from dagster._utils.test import copy_directory
from dagster_dbt.dbt_project import DbtProject

from ..dbt_projects import test_jaffle_shop_path


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
