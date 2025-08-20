from unittest import mock

import pytest
from dagster import AssetsDefinition, DagsterEventType, materialize
from dagster.components.testing import create_defs_folder_sandbox
from dagster_databricks.components.databricks_asset_bundle.component import (
    DatabricksAssetBundleComponent,
)

from dagster_databricks_tests.components.databricks_asset_bundle.conftest import (
    TEST_DATABRICKS_WORKSPACE_HOST,
    TEST_DATABRICKS_WORKSPACE_TOKEN,
)


@pytest.mark.parametrize(
    "use_existing_cluster",
    [
        False,
        True,
    ],
    ids=[
        "no_custom_config",
        "custom_config",
    ],
)
@mock.patch("databricks.sdk.service.jobs.SubmitTask", autospec=True)
def test_load_component(
    mock_submit_task: mock.MagicMock,
    use_existing_cluster: bool,
    databricks_config_path: str,
):
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
                    "cluster_config": {"existing_cluster_id": "test"}
                    if use_existing_cluster
                    else None,
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

            assets = list(defs.assets or [])
            assert len(assets) == 1
            databricks_assets = assets[0]
            assert isinstance(databricks_assets, AssetsDefinition)

            result = materialize(
                [databricks_assets],
                resources={"databricks": component.workspace},
            )
            assert result.success
            asset_materializations = [
                event
                for event in result.all_events
                if event.event_type_value == DagsterEventType.ASSET_MATERIALIZATION
            ]
            assert len(asset_materializations) == 6
            materialized_asset_keys = {
                asset_materialization.asset_key for asset_materialization in asset_materializations
            }
            assert len(materialized_asset_keys) == 6
            assert databricks_assets.keys == materialized_asset_keys
            assert mock_submit_task.call_count == 6

            # task_key is expected in every submit tasks
            assert all(call for call in mock_submit_task.mock_calls if "task_key" in call.kwargs)

            # depends_on is expected in 4 of the 6 submit tasks we create
            assert (
                len([call for call in mock_submit_task.mock_calls if "depends_on" in call.kwargs])
                == 4
            )

            cluster_config_key = "existing_cluster_id" if use_existing_cluster else "new_cluster"
            # new_cluster is expected in 4 of the 6 submit tasks we create
            assert (
                len(
                    [
                        call
                        for call in mock_submit_task.mock_calls
                        if cluster_config_key in call.kwargs
                    ]
                )
                == 4
            )
