import os
import shutil
from pathlib import Path

import pytest
from dagster import AssetExecutionContext, Definitions, materialize_to_memory
from dagster._core.test_utils import environ
from dagster._utils.test import copy_directory
from dagster_dbt import dbt_assets
from dagster_dbt.core.resources_v2 import DbtCliResource
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

        @dbt_assets(manifest=my_project.manifest_path)
        def my_assets(context: AssetExecutionContext, dbt: DbtCliResource): ...

        defs = Definitions(
            assets=[my_assets],
            resources={"dbt": DbtCliResource(my_project)},
        )
        assert defs.get_all_job_defs()


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


def test_state_defer(tmp_path) -> None:
    def my_deployment_prep(project: DbtProject):
        prepare_for_deployment(project)

        shuffle_path = Path(tmp_path).joinpath("prod_manifest.json")
        state_dir = project.state_dir
        assert state_dir
        env = os.environ["DAGSTER_DBT_JAFFLE_SCHEMA"]
        if env == "staging":
            os.makedirs(state_dir, exist_ok=True)
            shutil.copyfile(
                shuffle_path,
                state_dir.joinpath("manifest.json"),
            )
        elif env == "prod":
            shutil.copyfile(
                project.manifest_path,
                shuffle_path,
            )
        else:
            assert False, env  # should not reach

    with copy_directory(test_jaffle_shop_path) as project_dir:
        # simulate deploying and running prod
        with environ({"DAGSTER_DBT_JAFFLE_SCHEMA": "prod"}):
            my_project = DbtProject(
                project_dir,
                state_dir="prod_artifacts",
            )
            dbt_resource = DbtCliResource(my_project)

            dbt_resource.cli(["seed"]).wait()  # test set-up

            my_deployment_prep(my_project)

            @dbt_assets(manifest=my_project.manifest_path)
            def my_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                defer_args = dbt.get_defer_args()
                if os.getenv("DAGSTER_DBT_JAFFLE_SCHEMA") == "staging":
                    assert defer_args, defer_args
                yield from dbt.cli(
                    ["run", *defer_args],
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
                resources={"dbt": DbtCliResource(my_project)},
                selection="orders",
                raise_on_error=False,
            )
            assert not result.success

            my_deployment_prep(my_project)

            # subselect with defer works
            result = materialize_to_memory(
                [my_assets],
                resources={"dbt": DbtCliResource(my_project)},
                selection="orders",
            )
            assert result.success
