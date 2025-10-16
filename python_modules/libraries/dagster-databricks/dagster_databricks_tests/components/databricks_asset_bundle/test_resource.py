from unittest import mock

import pytest
from dagster import (
    AssetsDefinition,
    DagsterEventType,
    _check as check,
    materialize,
)
from dagster.components.testing import create_defs_folder_sandbox
from dagster_databricks.components.databricks_asset_bundle.component import (
    DatabricksAssetBundleComponent,
)
from databricks.sdk.service.jobs import Run, RunResultState, RunState, RunTask

from dagster_databricks_tests.components.databricks_asset_bundle.conftest import (
    EXISTING_CLUSTER_CONFIG,
    NEW_CLUSTER_CONFIG,
    TEST_DATABRICKS_WORKSPACE_HOST,
    TEST_DATABRICKS_WORKSPACE_TOKEN,
)


@pytest.mark.parametrize(
    "use_existing_cluster, use_new_cluster",
    [
        (False, False),
        (True, False),
        (False, True),
    ],
    ids=[
        "serverless_compute_config",
        "new_cluster_compute_config",
        "existing_cluster_compute_config",
    ],
)
@mock.patch(
    "databricks.sdk.service.jobs.JobsAPI.wait_get_run_job_terminated_or_skipped", autospec=True
)
@mock.patch("databricks.sdk.mixins.jobs.JobsExt.get_run", autospec=True)
@mock.patch("databricks.sdk.service.jobs.JobsAPI.submit", autospec=True)
@mock.patch("databricks.sdk.service.jobs.SubmitTask", autospec=True)
def test_load_component(
    mock_submit_task: mock.MagicMock,
    mock_submit_fn: mock.MagicMock,
    mock_get_run_fn: mock.MagicMock,
    mock_wait_fn: mock.MagicMock,
    use_existing_cluster: bool,
    use_new_cluster: bool,
    databricks_config_path: str,
):
    mock_get_run_fn.side_effect = [
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=None),
            tasks=[
                RunTask(
                    task_key="data_processing_notebook",
                    state=RunState(result_state=None),
                ),
            ],
        ),
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=RunResultState.SUCCESS),
            tasks=[
                RunTask(
                    task_key="data_processing_notebook",
                    state=RunState(result_state=RunResultState.SUCCESS),
                ),
            ],
        ),
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=None),
            tasks=[
                RunTask(
                    task_key="hello_world_spark_task",
                    state=RunState(result_state=None),
                ),
            ],
        ),
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=RunResultState.SUCCESS),
            tasks=[
                RunTask(
                    task_key="hello_world_spark_task",
                    state=RunState(result_state=RunResultState.SUCCESS),
                ),
            ],
        ),
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=None),
            tasks=[
                RunTask(task_key="stage_documents", state=RunState(result_state=None)),
            ],
        ),
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=RunResultState.SUCCESS),
            tasks=[
                RunTask(
                    task_key="stage_documents", state=RunState(result_state=RunResultState.SUCCESS)
                ),
            ],
        ),
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=None),
            tasks=[
                RunTask(task_key="spark_processing_jar", state=RunState(result_state=None)),
            ],
        ),
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=RunResultState.SUCCESS),
            tasks=[
                RunTask(
                    task_key="spark_processing_jar",
                    state=RunState(result_state=RunResultState.SUCCESS),
                ),
            ],
        ),
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=None),
            tasks=[
                RunTask(
                    task_key="existing_job_with_references",
                    state=RunState(result_state=None),
                ),
            ],
        ),
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=RunResultState.SUCCESS),
            tasks=[
                RunTask(
                    task_key="existing_job_with_references",
                    state=RunState(result_state=RunResultState.SUCCESS),
                ),
            ],
        ),
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=None),
            tasks=[
                RunTask(task_key="check_data_quality", state=RunState(result_state=None)),
            ],
        ),
        Run(
            run_id=11111,
            job_id=22222,
            state=RunState(result_state=RunResultState.SUCCESS),
            tasks=[
                RunTask(
                    task_key="check_data_quality",
                    state=RunState(result_state=RunResultState.SUCCESS),
                ),
            ],
        ),
    ]

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
                    "compute_config": {
                        **(EXISTING_CLUSTER_CONFIG if use_existing_cluster else {}),
                        **(NEW_CLUSTER_CONFIG if use_new_cluster else {}),
                    },
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

            databricks_assets = list(defs.assets or [])
            databricks_assets = check.is_list(databricks_assets, of_type=AssetsDefinition)
            assert len(databricks_assets) == 6
            databricks_asset_keys_list = [
                databricks_asset_key
                for databricks_asset in databricks_assets
                for databricks_asset_key in databricks_asset.keys
            ]
            assert len(databricks_asset_keys_list) == 6
            databricks_asset_keys_set = set(databricks_asset_keys_list)
            assert len(databricks_asset_keys_list) == len(databricks_asset_keys_set)
            assert all(
                isinstance(databricks_asset, AssetsDefinition)
                for databricks_asset in databricks_assets
            )

            result = materialize(
                databricks_assets,
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
            assert databricks_asset_keys_set == materialized_asset_keys
            assert mock_submit_task.call_count == 6

            # task_key is expected in every submit tasks
            assert all(call for call in mock_submit_task.mock_calls if "task_key" in call.kwargs)

            # depends_on is expected in 4 of the 6 submit tasks we create
            assert (
                len([call for call in mock_submit_task.mock_calls if "depends_on" in call.kwargs])
                == 4
            )

            # libraries is expected in 4 of the 6 submit tasks we create
            assert (
                len([call for call in mock_submit_task.mock_calls if "libraries" in call.kwargs])
                == 4
            )

            # Serverless compute config is used by default
            # if no new cluster config or existing cluster config is passed.
            # Cluster config is expected in 4 of the 6 submit tasks we create if not using serverless compute,
            # otherwise not expected.
            expected_cluster_config_calls = 4 if use_existing_cluster or use_new_cluster else 0
            cluster_config_key = "existing_cluster_id" if use_existing_cluster else "new_cluster"
            assert (
                len(
                    [
                        call
                        for call in mock_submit_task.mock_calls
                        if cluster_config_key in call.kwargs
                    ]
                )
                == expected_cluster_config_calls
            )

            # 6 different types of submit task are created
            assert (
                len(
                    [call for call in mock_submit_task.mock_calls if "notebook_task" in call.kwargs]
                )
                == 1
            )
            assert (
                len(
                    [
                        call
                        for call in mock_submit_task.mock_calls
                        if "condition_task" in call.kwargs
                    ]
                )
                == 1
            )
            assert (
                len(
                    [
                        call
                        for call in mock_submit_task.mock_calls
                        if "spark_python_task" in call.kwargs
                    ]
                )
                == 1
            )
            assert (
                len(
                    [
                        call
                        for call in mock_submit_task.mock_calls
                        if "python_wheel_task" in call.kwargs
                    ]
                )
                == 1
            )
            assert (
                len(
                    [
                        call
                        for call in mock_submit_task.mock_calls
                        if "spark_jar_task" in call.kwargs
                    ]
                )
                == 1
            )
            assert (
                len([call for call in mock_submit_task.mock_calls if "run_job_task" in call.kwargs])
                == 1
            )
