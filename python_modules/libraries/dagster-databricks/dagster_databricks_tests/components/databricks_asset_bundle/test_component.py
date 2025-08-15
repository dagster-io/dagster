from dagster import AssetDep, AssetKey
from dagster_databricks.components.databricks_asset_bundle.component import (
    DatabricksAssetBundleComponent,
    snake_case,
)

from dagster_databricks_tests.components.databricks_asset_bundle.conftest import (
    DATABRICKS_CONFIG_LOCATION_PATH,
)


def test_component_asset_spec():
    component = DatabricksAssetBundleComponent(
        databricks_config_path=DATABRICKS_CONFIG_LOCATION_PATH
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
            AssetDep(snake_case(dep_task_key)) for dep_task_key in task.depends_on
        ]
        if task.libraries:
            assert asset_spec.metadata["libraries"].value == task.libraries
        else:
            assert "libraries" not in asset_spec.metadata
