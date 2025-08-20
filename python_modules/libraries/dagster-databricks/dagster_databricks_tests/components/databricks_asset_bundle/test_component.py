import os
from typing import Optional

import pytest
from dagster import AssetDep, AssetKey, AssetsDefinition
from dagster.components.testing import create_defs_folder_sandbox
from dagster_databricks.components.databricks_asset_bundle.component import (
    DatabricksAssetBundleComponent,
    snake_case,
)
from dagster_databricks.components.databricks_asset_bundle.configs import (
    ResolvedDatabricksNewClusterConfig,
)
from dagster_databricks.components.databricks_asset_bundle.resource import DatabricksWorkspace

from dagster_databricks_tests.components.databricks_asset_bundle.conftest import (
    DATABRICKS_CONFIG_LOCATION_PATH,
    TEST_DATABRICKS_WORKSPACE_HOST,
    TEST_DATABRICKS_WORKSPACE_TOKEN,
)

NEW_CLUSTER_CONFIG = {
    "spark_version": "test_spark_version",
    "node_type_id": "test_node_type_id",
    "num_workers": 2,
}

PARTIAL_NEW_CLUSTER_CONFIG = {"spark_version": "test_spark_version"}


@pytest.mark.parametrize(
    "compute_config",
    [
        ({}),
        (NEW_CLUSTER_CONFIG),
        (PARTIAL_NEW_CLUSTER_CONFIG),
    ],
    ids=[
        "no_new_cluster_config",
        "new_cluster_config",
        "partial_new_cluster_config",
    ],
)
def test_component_asset_spec(compute_config: Optional[ResolvedDatabricksNewClusterConfig]):
    component = DatabricksAssetBundleComponent(
        databricks_config_path=DATABRICKS_CONFIG_LOCATION_PATH,
        compute_config=compute_config,
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


@pytest.mark.parametrize(
    "custom_op_name",
    [
        None,
        "test_op_name",
    ],
    ids=[
        "no_custom_op_name",
        "custom_op_name",
    ],
)
def test_load_component(custom_op_name: Optional[str], databricks_config_path: str):
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DatabricksAssetBundleComponent,
            scaffold_params={
                "databricks_config_path": databricks_config_path,
                "databricks_workspace_host": TEST_DATABRICKS_WORKSPACE_HOST,
                "databricks_workspace_token": TEST_DATABRICKS_WORKSPACE_TOKEN,
            },
            defs_yaml_contents={
                "type": "dagster_databricks.components.databricks_asset_bundle.component.DatabricksAssetBundleComponent",
                "attributes": {
                    "databricks_config_path": databricks_config_path,
                    "cluster_config": {},
                    "op": {"name": "test_op_name"} if custom_op_name else None,
                    "workspace": {
                        "host": TEST_DATABRICKS_WORKSPACE_HOST,
                        "token": TEST_DATABRICKS_WORKSPACE_TOKEN,
                    },
                },
            },
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, DatabricksAssetBundleComponent)
            assert component.compute_config == ResolvedDatabricksNewClusterConfig()

            assets = list(defs.assets or [])
            assert len(assets) == 1
            databricks_assets = assets[0]
            assert isinstance(databricks_assets, AssetsDefinition)

            test_component_defs_path_as_python_str = str(
                os.path.relpath(sandbox.defs_folder_path, start=sandbox.project_root)
            ).replace("/", "_")
            test_op_name = (
                custom_op_name if custom_op_name else test_component_defs_path_as_python_str
            )

            assert test_op_name in databricks_assets.node_def.name

            assert defs.resolve_asset_graph().get_all_asset_keys() == {
                AssetKey(["check_data_quality"]),
                AssetKey(["data_processing_notebook"]),
                AssetKey(["existing_job_with_references"]),
                AssetKey(["hello_world_spark_task"]),
                AssetKey(["spark_processing_jar"]),
                AssetKey(["stage_documents"]),
            }
