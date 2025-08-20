import os
from collections.abc import Mapping
from typing import Any, Optional

import pytest
from dagster import AssetDep, AssetKey, AssetsDefinition
from dagster.components.testing import create_defs_folder_sandbox
from dagster_databricks.components.databricks_asset_bundle.component import (
    DatabricksAssetBundleComponent,
    snake_case,
)
from dagster_databricks.components.databricks_asset_bundle.configs import (
    ResolvedDatabricksClusterConfig,
)
from dagster_databricks.components.databricks_asset_bundle.resource import DatabricksWorkspace

from dagster_databricks_tests.components.databricks_asset_bundle.conftest import (
    DATABRICKS_CONFIG_LOCATION_PATH,
    TEST_DATABRICKS_WORKSPACE_HOST,
    TEST_DATABRICKS_WORKSPACE_TOKEN,
)

CLUSTER_CONFIG = {
    "spark_version": "test_spark_version",
    "node_type_id": "test_node_type_id",
    "num_workers": 2,
}

PARTIAL_CLUSTER_CONFIG = {"spark_version": "test_spark_version"}


@pytest.mark.parametrize(
    "cluster_config",
    [
        (None),
        (CLUSTER_CONFIG),
        (PARTIAL_CLUSTER_CONFIG),
    ],
    ids=[
        "no_cluster_config",
        "cluster_config",
        "partial_cluster_config",
    ],
)
def test_component_asset_spec(cluster_config: Optional[Mapping[str, Any]]):
    component = DatabricksAssetBundleComponent(
        databricks_config_path=DATABRICKS_CONFIG_LOCATION_PATH,
        compute_config=cluster_config,
        workspace=DatabricksWorkspace(
            host=TEST_DATABRICKS_WORKSPACE_HOST, token=TEST_DATABRICKS_WORKSPACE_TOKEN
        ),
    )
    for task in component.databricks_config.tasks:
        asset_spec = component.get_asset_spec(task)
        assert asset_spec.key == AssetKey(task.task_key)
        assert asset_spec.description == f"{task.task_key} task from {task.job_name} job"
        assert "databricks" in asset_spec.kinds
        assert asset_spec.skippable
        assert asset_spec.metadata["task_key"].value == task.task_key
        assert asset_spec.metadata["task_type"].value == task.task_type
        assert asset_spec.metadata["task_config"].value == task.task_config_metadata
        assert asset_spec.deps == [
            AssetDep(snake_case(dep_config.task_key)) for dep_config in task.depends_on
        ]
        if task.libraries:
            assert asset_spec.metadata["libraries"].value == task.libraries
        else:
            assert "libraries" not in asset_spec.metadata


def test_load_component(databricks_config_path: str):
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DatabricksAssetBundleComponent,
            scaffold_params={
                "databricks_config_path": databricks_config_path,
                "databricks_workspace_host": TEST_DATABRICKS_WORKSPACE_HOST,
                "databricks_workspace_token": TEST_DATABRICKS_WORKSPACE_TOKEN,
            },
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert component.compute_config == ResolvedDatabricksClusterConfig()

            assets = list(defs.assets or [])
            assert len(assets) == 1
            databricks_assets = assets[0]
            assert isinstance(databricks_assets, AssetsDefinition)

            test_component_defs_path_as_python_str = str(
                os.path.relpath(sandbox.defs_folder_path, start=sandbox.project_root)
            ).replace("/", "_")
            assert test_component_defs_path_as_python_str in databricks_assets.node_def.name

            assert defs.resolve_asset_graph().get_all_asset_keys() == {
                AssetKey(["check_data_quality"]),
                AssetKey(["data_processing_notebook"]),
                AssetKey(["existing_job_with_references"]),
                AssetKey(["hello_world_spark_task"]),
                AssetKey(["spark_processing_jar"]),
                AssetKey(["stage_documents"]),
            }
