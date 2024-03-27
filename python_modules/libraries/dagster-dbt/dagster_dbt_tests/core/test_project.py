import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from dagster import AssetExecutionContext, Definitions, materialize_to_memory
from dagster._core.test_utils import environ
from dagster._utils.test import copy_directory
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core.resources_v2 import DbtCliResource
from dagster_dbt.dbt_project import DagsterDbtProjectManager, DbtProject
from dagster_dbt.errors import DagsterDbtManifestNotPreparedError

from ..dbt_projects import test_jaffle_shop_path


def test_expected_but_missing() -> None:
    with copy_directory(test_jaffle_shop_path) as project_dir:
        project = DbtProject(project_dir=project_dir)

        with pytest.raises(DagsterDbtManifestNotPreparedError):
            _ = project.manifest_path

        DagsterDbtProjectManager.prepare_for_deployment(project)
        assert project.manifest_path.exists()

        @dbt_assets(manifest=project.manifest_path)
        def my_assets(context: AssetExecutionContext, dbt: DbtCliResource): ...

        defs = Definitions(
            assets=[my_assets],
            resources={"dbt": DbtCliResource(project_dir=project)},
        )
        assert defs.get_all_job_defs()


def test_dagster_dev() -> None:
    with environ({"DAGSTER_IS_DEV_CLI": "1"}), copy_directory(test_jaffle_shop_path) as project_dir:
        dbt_artifacts = DbtProject(project_dir=project_dir)
        assert dbt_artifacts.manifest_path.exists()


def test_opt_in_env_var() -> None:
    with environ({"DAGSTER_DBT_PARSE_PROJECT_ON_LOAD": "1"}), copy_directory(
        test_jaffle_shop_path
    ) as project_dir:
        dbt_artifacts = DbtProject(project_dir=project_dir)
        assert dbt_artifacts.manifest_path.exists()


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_state_defer(temp_dir) -> None:
    class TestDbtProjectManager(DagsterDbtProjectManager):
        @classmethod
        def manage_state_artifacts(cls, project: "DbtProject"):
            state_artifacts_path = project.state_artifacts_path
            assert state_artifacts_path
            env = os.environ["DAGSTER_DBT_JAFFLE_SCHEMA"]
            if env == "staging":
                os.makedirs(state_artifacts_path, exist_ok=True)

                shutil.copyfile(
                    Path(temp_dir).joinpath("prod_manifest.json"),
                    state_artifacts_path.joinpath("manifest.json"),
                )
            elif env == "prod":
                shutil.copyfile(
                    project.manifest_path,
                    Path(temp_dir).joinpath("prod_manifest.json"),
                )
            else:
                assert False, env  # should not reach

    with copy_directory(test_jaffle_shop_path) as project_dir:
        # simulate deploying and running prod
        with environ({"DAGSTER_DBT_JAFFLE_SCHEMA": "prod"}):
            my_project = DbtProject(
                project_dir,
                state_artifacts_folder="prod_artifacts",
            )
            dbt_resource = DbtCliResource(my_project)

            dbt_resource.cli(["seed"]).wait()  # test set-up

            TestDbtProjectManager.prepare_for_deployment(my_project)

            @dbt_assets(manifest=my_project.manifest_path)
            def my_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                yield from dbt.cli(
                    [
                        "run",
                        *dbt.auto_defer_args(),
                    ],
                    context=context,
                ).stream()

            # produce all prod assets
            result = materialize_to_memory(
                [my_assets],
                resources={"dbt": dbt_resource},
            )
            assert result.success

        # and then deploying and running in staging
        with environ({"DAGSTER_DBT_JAFFLE_SCHEMA": "staging"}):
            # subselect but no defer fails
            result = materialize_to_memory(
                [my_assets],
                resources={"dbt": dbt_resource},
                selection="orders",
                raise_on_error=False,
            )
            assert not result.success

            TestDbtProjectManager.prepare_for_deployment(my_project)

            # subselect with defer works
            result = materialize_to_memory(
                [my_assets],
                resources={"dbt": dbt_resource},
                selection="orders",
            )
            assert result.success
