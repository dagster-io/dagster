import logging
import os
import time
from typing import Optional, Union

from dagster import (
    AssetKey,
    Output,
    _check as check,
    asset,
    define_asset_job,
)
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, TemporalContext
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.execution.asset_backfill import (
    AssetBackfillIterationResult,
    execute_asset_backfill_iteration,
    execute_asset_backfill_iteration_inner,
)
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.job_backfill import execute_job_backfill_iteration
from dagster._core.remote_representation.origin import RemotePartitionSetOrigin
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    BACKFILL_ID_TAG,
    PARENT_BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
    ROOT_BACKFILL_ID_TAG,
)
from dagster._core.test_utils import create_run_for_test, environ
from dagster._core.utils import make_new_backfill_id
from dagster._seven import get_system_temp_directory
from dagster._utils import safe_tempfile_path
from dagster_graphql.client.query import (
    LAUNCH_PARTITION_BACKFILL_MUTATION,
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
)
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    execute_dagster_graphql_and_finish_runs,
    infer_job_selector,
    infer_repository_selector,
    main_repo_location_name,
)

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
    ReadonlyGraphQLContextTestMatrix,
)
from dagster_graphql_tests.graphql.repo import get_workspace_process_context

PARTITION_PROGRESS_QUERY = """
  query PartitionProgressQuery($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        __typename
        id
        status
        numCancelable
        partitionNames
        numPartitions
        fromFailure
        reexecutionSteps
        partitionStatuses {
          results {
            partitionName
            runStatus
          }
        }
        hasCancelPermission
        hasResumePermission
        user
        title
        description
        cancelableRuns {
          id
          runId
        }
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
"""

BACKFILL_STATUS_BY_ASSET = """
  query BackfillStatusesByAsset($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      __typename
      ... on PartitionBackfill {
        assetBackfillData {
            assetBackfillStatuses {
                ... on AssetPartitionsStatusCounts {
                    assetKey {
                        path
                    }
                    numPartitionsTargeted
                    numPartitionsInProgress
                    numPartitionsMaterialized
                    numPartitionsFailed
                }
                ... on UnpartitionedAssetStatus {
                    assetKey {
                        path
                    }
                    inProgress
                    materialized
                    failed
                }
            }
            rootTargetedPartitions {
                partitionKeys
                ranges {
                start
                end
                }
            }
        }
      }
      ... on PythonError {
        message
        stack
      }
      ... on BackfillNotFoundError {
        message
      }
    }
  }
"""

CANCEL_BACKFILL_MUTATION = """
  mutation($backfillId: String!) {
    cancelPartitionBackfill(backfillId: $backfillId) {
      __typename
      ... on CancelBackfillSuccess {
        backfillId
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
"""

RESUME_BACKFILL_MUTATION = """
  mutation($backfillId: String!) {
    resumePartitionBackfill(backfillId: $backfillId) {
      __typename
      ... on ResumeBackfillSuccess {
        backfillId
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
"""

RETRY_BACKFILL_MUTATION = """
  mutation($reexecutionParams: ReexecutionParams) {
    reexecutePartitionBackfill(reexecutionParams: $reexecutionParams) {
      __typename
      ... on LaunchBackfillSuccess {
        backfillId
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
"""


GET_PARTITION_BACKFILLS_QUERY = """
  query PartitionBackfillsQuery($repositorySelector: RepositorySelector!, $partitionSetName: String!) {
    partitionSetOrError(repositorySelector: $repositorySelector, partitionSetName: $partitionSetName) {
      __typename
      ...on PartitionSet {
        name
        pipelineName
        backfills {
          id
          isAssetBackfill
        }
      }
    }
  }

"""


def _seed_runs(
    graphql_context,
    partition_runs: list[tuple[DagsterRunStatus, Union[str, PartitionKeyRange]]],
    backfill_id: str,
) -> None:
    for status, partition_or_range in partition_runs:
        partition_tags = (
            {PARTITION_NAME_TAG: partition_or_range}
            if isinstance(partition_or_range, str)
            else {
                ASSET_PARTITION_RANGE_START_TAG: partition_or_range.start,
                ASSET_PARTITION_RANGE_END_TAG: partition_or_range.end,
            }
        )
        create_run_for_test(
            instance=graphql_context.instance,
            status=status,
            tags={
                **DagsterRun.tags_for_backfill_id(backfill_id),
                **partition_tags,
            },
        )


def _get_run_stats(partition_statuses):
    return {
        "total": len(partition_statuses),
        "queued": len([status for status in partition_statuses if status["runStatus"] == "QUEUED"]),
        "in_progress": len(
            [status for status in partition_statuses if status["runStatus"] == "STARTED"]
        ),
        "success": len(
            [status for status in partition_statuses if status["runStatus"] == "SUCCESS"]
        ),
        "failure": len(
            [status for status in partition_statuses if status["runStatus"] == "FAILURE"]
        ),
        "canceled": len(
            [status for status in partition_statuses if status["runStatus"] == "CANCELED"]
        ),
    }


def _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id: str) -> None:
    """Executes an asset backfill iteration and updates the serialized asset backfill data.
    However, does not execute side effects i.e. launching runs.
    """
    backfill = graphql_context.instance.get_backfill(backfill_id)
    asset_backfill_data = backfill.asset_backfill_data
    result = None
    asset_graph_view = AssetGraphView(
        temporal_context=TemporalContext(
            effective_dt=asset_backfill_data.backfill_start_datetime, last_event_id=None
        ),
        instance=graphql_context.instance,
        asset_graph=graphql_context.asset_graph,
    )
    with environ({"ASSET_BACKFILL_CURSOR_DELAY_TIME": "0"}):
        for result in execute_asset_backfill_iteration_inner(
            backfill_id=backfill_id,
            asset_backfill_data=asset_backfill_data,
            asset_graph_view=asset_graph_view,
            backfill_start_timestamp=asset_backfill_data.backfill_start_timestamp,
            logger=logging.getLogger("fake_logger"),
        ):
            pass

    if not isinstance(result, AssetBackfillIterationResult):
        check.failed(
            "Expected execute_asset_backfill_iteration_inner to return an"
            " AssetBackfillIterationResult"
        )

    updated_backfill = backfill.with_asset_backfill_data(
        result.backfill_data.with_run_requests_submitted(
            result.run_requests,
            asset_graph_view=asset_graph_view,
        ),
        dynamic_partitions_store=graphql_context.instance,
        asset_graph=graphql_context.asset_graph,
    )
    graphql_context.instance.update_backfill(updated_backfill)


def _execute_backfill_iteration_with_side_effects(graphql_context, backfill_id):
    """Executes an asset backfill iteration with side effects (i.e. updates run status and bulk action status)."""
    with get_workspace_process_context(graphql_context.instance) as context:
        backfill = graphql_context.instance.get_backfill(backfill_id)
        list(
            execute_asset_backfill_iteration(
                backfill, logging.getLogger("fake_logger"), context, graphql_context.instance
            )
        )


def _execute_job_backfill_iteration_with_side_effects(graphql_context, backfill_id):
    """Executes a job backfill iteration with side effects (i.e. updates run status and bulk action status)."""
    with get_workspace_process_context(graphql_context.instance) as context:
        backfill = graphql_context.instance.get_backfill(backfill_id)
        list(
            execute_job_backfill_iteration(
                backfill=backfill,
                logger=logging.getLogger("fake_logger"),
                workspace_process_context=context,
                instance=graphql_context.instance,
                debug_crash_flags=None,
            )
        )


def _mock_asset_backfill_runs(
    graphql_context,
    asset_key: AssetKey,
    backfill_id: str,
    status: DagsterRunStatus,
    partition_key: Optional[str],
):
    partitions_def = graphql_context.asset_graph.get(asset_key).partitions_def

    @asset(
        partitions_def=partitions_def,
        name=asset_key.path[-1],
        key_prefix=asset_key.path[:-1] if len(asset_key.path) > 1 else None,
    )
    def dummy_asset():
        if status == DagsterRunStatus.FAILURE:
            raise Exception("fail")
        return Output(5)

    define_asset_job("my_job", [dummy_asset]).resolve(
        asset_graph=AssetGraph.from_assets([dummy_asset])
    ).execute_in_process(
        tags={**DagsterRun.tags_for_backfill_id(backfill_id)},
        partition_key=partition_key,
        raise_on_error=False,
        instance=graphql_context.instance,
    )


class TestPartitionBackillReadonlyFailure(ReadonlyGraphQLContextTestMatrix):
    def _create_backfill(self, graphql_context):
        code_location = graphql_context.get_code_location(main_repo_location_name())
        repository = code_location.get_repository("test_repo")

        backfill = PartitionBackfill(
            backfill_id=make_new_backfill_id(),
            partition_set_origin=RemotePartitionSetOrigin(
                repository_origin=repository.get_remote_origin(),
                partition_set_name="integer_partition",
            ),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=time.time(),
        )
        graphql_context.instance.add_backfill(backfill)
        return backfill.backfill_id

    def test_launch_backill_failure(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integer_partition",
                    },
                    "partitionNames": ["2", "3"],
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "UnauthorizedError"

    def test_cancel_backfill_failure(self, graphql_context):
        backfill_id = self._create_backfill(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            CANCEL_BACKFILL_MUTATION,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["cancelPartitionBackfill"]["__typename"] == "UnauthorizedError"

    def test_no_permission(self, graphql_context):
        backfill_id = self._create_backfill(graphql_context)

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )
        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["hasCancelPermission"] is False
        assert result.data["partitionBackfillOrError"]["hasResumePermission"] is False

    def test_bad_id(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context,
            BACKFILL_STATUS_BY_ASSET,
            variables={"backfillId": "Junk"},
        )
        assert not result.errors
        assert result.data
        assert (
            result.data["partitionBackfillOrError"]["__typename"] == "BackfillNotFoundError"
        ), result.data
        assert "Junk" in result.data["partitionBackfillOrError"]["message"]

    def test_resume_backfill_failure(self, graphql_context):
        backfill_id = self._create_backfill(graphql_context)

        result = execute_dagster_graphql(
            graphql_context,
            RESUME_BACKFILL_MUTATION,
            variables={"backfillId": backfill_id},
        )
        assert result.data
        assert result.data["resumePartitionBackfill"]["__typename"] == "UnauthorizedError", str(
            result.data
        )


class TestDaemonPartitionBackfill(ExecutingGraphQLContextTestMatrix):
    def test_launch_full_pipeline_backfill(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3"],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["numCancelable"] == 2
        assert result.data["partitionBackfillOrError"]["hasCancelPermission"] is True
        assert result.data["partitionBackfillOrError"]["hasResumePermission"] is True

        assert len(result.data["partitionBackfillOrError"]["partitionNames"]) == 2

    def test_get_partition_backfills(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        # launch a backfill for this partition set
        launch_result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3"],
                }
            },
        )
        backfill_id = launch_result.data["launchPartitionBackfill"]["backfillId"]
        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_BACKFILLS_QUERY,
            variables={
                "repositorySelector": repository_selector,
                "partitionSetName": "integers_partition_set",
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["partitionSetOrError"]["__typename"] == "PartitionSet"
        assert len(result.data["partitionSetOrError"]["backfills"]) == 1
        assert result.data["partitionSetOrError"]["backfills"][0]["id"] == backfill_id
        assert result.data["partitionSetOrError"]["backfills"][0]["isAssetBackfill"] is False

    def test_launch_partial_backfill(self, graphql_context):
        # execute a full pipeline, without the failure environment variable
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            "repositorySelector": repository_selector,
            "partitionSetName": "chained_failure_job_partition_set",
        }

        # reexecute a partial pipeline
        partial_steps = ["after_failure"]
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": partition_set_selector,
                    "partitionNames": ["2", "3"],
                    "reexecutionSteps": partial_steps,
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["numCancelable"] == 2
        assert len(result.data["partitionBackfillOrError"]["partitionNames"]) == 2
        assert result.data["partitionBackfillOrError"]["reexecutionSteps"] == ["after_failure"]

    def test_cancel_job_backfill(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "hanging_partitioned_job_partition_set",
                    },
                    "partitionNames": ["1", "2"],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"

        # Update backfill data to update the partition checkpoint, but manually launch the run
        # since launching the run via the backfill iteration loop will cause test process will hang forever.
        backfill = graphql_context.instance.get_backfill(backfill_id)
        partition_to_run = "1"
        graphql_context.instance.update_backfill(
            backfill.with_partition_checkpoint(partition_to_run)
        )

        # Launch the run that runs forever
        selector = infer_job_selector(graphql_context, "hanging_partitioned_job")
        with safe_tempfile_path() as path:
            result = execute_dagster_graphql(
                graphql_context,
                LAUNCH_PIPELINE_EXECUTION_MUTATION,
                variables={
                    "executionParams": {
                        "selector": selector,
                        "mode": "default",
                        "runConfigData": {
                            "resources": {"hanging_asset_resource": {"config": {"file": path}}}
                        },
                        "executionMetadata": {
                            "tags": [
                                {"key": "dagster/partition", "value": partition_to_run},
                                {"key": BACKFILL_ID_TAG, "value": backfill_id},
                            ]
                        },
                    }
                },
            )

            assert not result.errors
            assert result.data
            assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

            # ensure the execution has happened
            start = time.time()
            while not os.path.exists(path):
                time.sleep(0.1)
                assert time.time() - start < 60, "timed out waiting for file"

        runs = graphql_context.instance.get_runs(RunsFilter(tags={BACKFILL_ID_TAG: backfill_id}))
        assert len(runs) == 1
        assert runs[0].status == DagsterRunStatus.STARTED

        result = execute_dagster_graphql(
            graphql_context,
            CANCEL_BACKFILL_MUTATION,
            variables={"backfillId": backfill_id},
        )
        assert result.data
        assert result.data["cancelPartitionBackfill"]["__typename"] == "CancelBackfillSuccess"

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )
        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "CANCELING"

        while (
            graphql_context.instance.get_backfill(backfill_id).status != BulkActionStatus.CANCELED
        ):
            _execute_job_backfill_iteration_with_side_effects(graphql_context, backfill_id)

        runs = graphql_context.instance.get_runs(RunsFilter(tags={BACKFILL_ID_TAG: backfill_id}))
        assert len(runs) == 1
        assert runs[0].status == DagsterRunStatus.CANCELED

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )
        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "CANCELED"

    def test_cancel_then_retry_backfill(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3"],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context,
            CANCEL_BACKFILL_MUTATION,
            variables={"backfillId": backfill_id},
        )
        assert result.data
        assert result.data["cancelPartitionBackfill"]["__typename"] == "CancelBackfillSuccess"

        # run the backfill iteration until the backfill is canceled
        while (
            graphql_context.instance.get_backfill(backfill_id).status != BulkActionStatus.CANCELED
        ):
            _execute_job_backfill_iteration_with_side_effects(graphql_context, backfill_id)

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )
        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "CANCELED"

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "FROM_FAILURE"},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retried_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]
        retried_backfill = graphql_context.instance.get_backfill(retried_backfill_id)

        assert retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": retried_backfill_id},
        )
        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["numCancelable"] == 2
        assert len(result.data["partitionBackfillOrError"]["partitionNames"]) == 2
        assert result.data["partitionBackfillOrError"]["fromFailure"]

    def test_cancel_asset_backfill(self, graphql_context):
        asset_key = AssetKey("hanging_partition_asset")
        partitions = ["a"]
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "partitionNames": partitions,
                    "assetSelection": [asset_key.to_graphql_input()],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        # Update asset backfill data to contain requested partition, but does not execute side effects,
        # since launching the run will cause test process will hang forever.
        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)

        # Launch the run that runs forever
        selector = infer_job_selector(graphql_context, "hanging_partition_asset_job")
        with safe_tempfile_path() as path:
            result = execute_dagster_graphql(
                graphql_context,
                LAUNCH_PIPELINE_EXECUTION_MUTATION,
                variables={
                    "executionParams": {
                        "selector": selector,
                        "mode": "default",
                        "runConfigData": {
                            "resources": {"hanging_asset_resource": {"config": {"file": path}}}
                        },
                        "executionMetadata": {
                            "tags": [
                                {"key": "dagster/partition", "value": "a"},
                                {"key": BACKFILL_ID_TAG, "value": backfill_id},
                            ]
                        },
                    }
                },
            )

            assert not result.errors
            assert result.data
            assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

            # ensure the execution has happened
            start = time.time()
            while not os.path.exists(path):
                time.sleep(0.1)
                assert time.time() - start < 60, "timed out waiting for file"

            result = execute_dagster_graphql(
                graphql_context,
                CANCEL_BACKFILL_MUTATION,
                variables={"backfillId": backfill_id},
            )
            assert result.data
            assert result.data["cancelPartitionBackfill"]["__typename"] == "CancelBackfillSuccess"

            while (
                graphql_context.instance.get_backfill(backfill_id).status
                != BulkActionStatus.CANCELED
            ):
                _execute_backfill_iteration_with_side_effects(graphql_context, backfill_id)

            runs = graphql_context.instance.get_runs(
                RunsFilter(tags={BACKFILL_ID_TAG: backfill_id})
            )
            assert len(runs) == 1
            assert runs[0].status == DagsterRunStatus.CANCELED

    def test_cancel_then_retry_asset_backfill(self, graphql_context):
        asset_key = AssetKey("hanging_partition_asset")
        partitions = ["a"]
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "partitionNames": partitions,
                    "assetSelection": [asset_key.to_graphql_input()],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        # Update asset backfill data to contain requested partition, but does not execute side effects,
        # since launching the run will cause test process will hang forever.

        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)

        # Launch the run that runs forever
        selector = infer_job_selector(graphql_context, "hanging_partition_asset_job")
        with safe_tempfile_path() as path:
            result = execute_dagster_graphql(
                graphql_context,
                LAUNCH_PIPELINE_EXECUTION_MUTATION,
                variables={
                    "executionParams": {
                        "selector": selector,
                        "mode": "default",
                        "runConfigData": {
                            "resources": {"hanging_asset_resource": {"config": {"file": path}}}
                        },
                        "executionMetadata": {
                            "tags": [
                                {"key": "dagster/partition", "value": "a"},
                                {"key": BACKFILL_ID_TAG, "value": backfill_id},
                            ]
                        },
                    }
                },
            )

            assert not result.errors
            assert result.data
            assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

            # ensure the execution has happened
            start = time.time()
            while not os.path.exists(path):
                time.sleep(0.1)
                assert time.time() - start < 60, "timed out waiting for file"

            result = execute_dagster_graphql(
                graphql_context,
                CANCEL_BACKFILL_MUTATION,
                variables={"backfillId": backfill_id},
            )
            assert result.data
            assert result.data["cancelPartitionBackfill"]["__typename"] == "CancelBackfillSuccess"

            while (
                graphql_context.instance.get_backfill(backfill_id).status
                != BulkActionStatus.CANCELED
            ):
                _execute_backfill_iteration_with_side_effects(graphql_context, backfill_id)

            runs = graphql_context.instance.get_runs(
                RunsFilter(tags={BACKFILL_ID_TAG: backfill_id})
            )
            assert len(runs) == 1
            assert runs[0].status == DagsterRunStatus.CANCELED

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "FROM_FAILURE"},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retry_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]

        first_backfill = graphql_context.instance.get_backfill(backfill_id)
        retried_backfill = graphql_context.instance.get_backfill(retry_backfill_id)

        # no runs were successful for the first backfill, so the retry target should be the same
        # as the first backfill
        assert (
            first_backfill.asset_backfill_data.target_subset
            == retried_backfill.asset_backfill_data.target_subset
        )
        assert retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

    def test_resume_backfill(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3"],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["numCancelable"] == 2
        assert len(result.data["partitionBackfillOrError"]["partitionNames"]) == 2

        # manually mark as failed
        backfill = graphql_context.instance.get_backfill(backfill_id)
        graphql_context.instance.update_backfill(backfill.with_status(BulkActionStatus.FAILED))

        result = execute_dagster_graphql(
            graphql_context,
            RESUME_BACKFILL_MUTATION,
            variables={"backfillId": backfill_id},
        )
        assert result.data
        assert result.data["resumePartitionBackfill"]["__typename"] == "ResumeBackfillSuccess"

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )
        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"

    def test_backfill_run_stats(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3", "4", "5"],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        _seed_runs(
            graphql_context,
            [
                (DagsterRunStatus.SUCCESS, "5"),
                (DagsterRunStatus.STARTED, "2"),
                (DagsterRunStatus.STARTED, "3"),
                (DagsterRunStatus.STARTED, "4"),
                (DagsterRunStatus.STARTED, "5"),
                (DagsterRunStatus.CANCELED, "2"),
                (DagsterRunStatus.FAILURE, "3"),
                (DagsterRunStatus.SUCCESS, "4"),
            ],
            backfill_id,
        )

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["numPartitions"] == 4
        run_stats = _get_run_stats(
            result.data["partitionBackfillOrError"]["partitionStatuses"]["results"]
        )
        assert run_stats.get("total") == 4
        assert run_stats.get("queued") == 0
        assert run_stats.get("in_progress") == 1
        assert run_stats.get("success") == 1
        assert run_stats.get("failure") == 1
        assert run_stats.get("canceled") == 1

        backfill = graphql_context.instance.get_backfill(backfill_id)

        # Artificially mark the backfill as complete - verify run status is INCOMPLETE until the runs all succeed
        graphql_context.instance.update_backfill(
            backfill.with_status(BulkActionStatus.COMPLETED_SUCCESS)
        )

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )
        assert result.data["partitionBackfillOrError"]["status"] == "COMPLETED_SUCCESS"

    def test_asset_job_backfill_run_stats(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_asset_job_partition_set",
                    },
                    "partitionNames": ["2", "3", "4", "5"],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        _seed_runs(
            graphql_context,
            [
                (DagsterRunStatus.SUCCESS, PartitionKeyRange("2", "5")),
            ],
            backfill_id,
        )

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["numPartitions"] == 4
        run_stats = _get_run_stats(
            result.data["partitionBackfillOrError"]["partitionStatuses"]["results"]
        )
        assert run_stats.get("total") == 4
        assert run_stats.get("success") == 4

    def test_asset_backfill_stats_in_topological_order(self, graphql_context):
        asset_key_paths_in_topo_order = [
            ["upstream_static_partitioned_asset"],
            ["middle_static_partitioned_asset_1"],
            ["middle_static_partitioned_asset_2"],
            ["downstream_static_partitioned_asset"],
        ]

        partitions = ["a", "b", "c", "d", "e", "f"]
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "partitionNames": partitions,
                    "assetSelection": [
                        AssetKey(path).to_graphql_input() for path in asset_key_paths_in_topo_order
                    ],
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context,
            BACKFILL_STATUS_BY_ASSET,
            variables={"backfillId": backfill_id},
        )

        asset_status_counts = result.data["partitionBackfillOrError"]["assetBackfillData"][
            "assetBackfillStatuses"
        ]
        assert len(asset_status_counts) == 4
        for i, path in enumerate(asset_key_paths_in_topo_order):
            assert asset_status_counts[i]["assetKey"]["path"] == path

    def test_asset_backfill_partition_stats(self, graphql_context):
        asset_key = AssetKey("upstream_static_partitioned_asset")
        partitions = ["a", "b", "c", "d", "e", "f"]
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "partitionNames": partitions,
                    "assetSelection": [asset_key.to_graphql_input()],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)

        for partition, status in [
            ("a", DagsterRunStatus.SUCCESS),
            ("b", DagsterRunStatus.FAILURE),
            ("d", DagsterRunStatus.SUCCESS),
            ("e", DagsterRunStatus.SUCCESS),
            ("f", DagsterRunStatus.FAILURE),
        ]:
            _mock_asset_backfill_runs(graphql_context, asset_key, backfill_id, status, partition)

        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)

        result = execute_dagster_graphql(
            graphql_context,
            BACKFILL_STATUS_BY_ASSET,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        backfill_data = result.data["partitionBackfillOrError"]["assetBackfillData"]

        assert backfill_data["rootTargetedPartitions"]["ranges"] is None
        assert set(backfill_data["rootTargetedPartitions"]["partitionKeys"]) == set(partitions)

        asset_partition_status_counts = backfill_data["assetBackfillStatuses"]
        assert len(asset_partition_status_counts) == 1
        assert asset_partition_status_counts[0]["assetKey"]["path"] == [
            "upstream_static_partitioned_asset"
        ]
        assert asset_partition_status_counts[0]["numPartitionsTargeted"] == 6
        assert asset_partition_status_counts[0]["numPartitionsInProgress"] == 1
        assert asset_partition_status_counts[0]["numPartitionsMaterialized"] == 3
        assert asset_partition_status_counts[0]["numPartitionsFailed"] == 2

    def test_asset_backfill_status_with_upstream_failure(self, graphql_context):
        asset_keys = [
            AssetKey("unpartitioned_upstream_of_partitioned"),
            AssetKey("upstream_daily_partitioned_asset"),
            AssetKey("downstream_weekly_partitioned_asset"),
        ]
        partitions = ["2023-01-09"]
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "partitionNames": partitions,
                    "assetSelection": [asset_key.to_graphql_input() for asset_key in asset_keys],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)
        _mock_asset_backfill_runs(
            graphql_context,
            AssetKey("unpartitioned_upstream_of_partitioned"),
            backfill_id,
            DagsterRunStatus.SUCCESS,
            None,
        )
        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)
        _mock_asset_backfill_runs(
            graphql_context,
            AssetKey("upstream_daily_partitioned_asset"),
            backfill_id,
            DagsterRunStatus.FAILURE,
            "2023-01-09",
        )
        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)

        result = execute_dagster_graphql(
            graphql_context,
            BACKFILL_STATUS_BY_ASSET,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        backfill_data = result.data["partitionBackfillOrError"]["assetBackfillData"]

        assert backfill_data["rootTargetedPartitions"]["ranges"] == [
            {"start": "2023-01-09", "end": "2023-01-09"}
        ]

        asset_statuses = backfill_data["assetBackfillStatuses"]
        assert len(asset_statuses) == 3
        assert asset_statuses[0]["assetKey"]["path"] == ["unpartitioned_upstream_of_partitioned"]
        assert asset_statuses[0]["inProgress"] is False
        assert asset_statuses[0]["materialized"] is True
        assert asset_statuses[0]["failed"] is False

        assert asset_statuses[1]["assetKey"]["path"] == ["upstream_daily_partitioned_asset"]
        assert asset_statuses[1]["numPartitionsTargeted"] == 1
        assert asset_statuses[1]["numPartitionsInProgress"] == 0
        assert asset_statuses[1]["numPartitionsMaterialized"] == 0
        assert asset_statuses[1]["numPartitionsFailed"] == 1

        assert asset_statuses[2]["assetKey"]["path"] == ["downstream_weekly_partitioned_asset"]
        assert asset_statuses[2]["numPartitionsTargeted"] == 1
        assert asset_statuses[2]["numPartitionsInProgress"] == 0
        assert asset_statuses[2]["numPartitionsMaterialized"] == 0
        assert asset_statuses[2]["numPartitionsFailed"] == 1

    def test_backfill_run_completed(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3", "4", "5"],
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        backfill = graphql_context.instance.get_backfill(backfill_id)

        graphql_context.instance.update_backfill(
            backfill.with_status(BulkActionStatus.COMPLETED_SUCCESS)
        )

        _seed_runs(
            graphql_context,
            [
                (DagsterRunStatus.SUCCESS, "2"),
                (DagsterRunStatus.SUCCESS, "3"),
                (DagsterRunStatus.SUCCESS, "4"),
                (DagsterRunStatus.SUCCESS, "5"),
            ],
            backfill_id,
        )

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "COMPLETED_SUCCESS"
        assert result.data["partitionBackfillOrError"]["numPartitions"] == 4

        run_stats = _get_run_stats(
            result.data["partitionBackfillOrError"]["partitionStatuses"]["results"]
        )
        assert run_stats.get("total") == 4
        assert run_stats.get("queued") == 0
        assert run_stats.get("in_progress") == 0
        assert run_stats.get("success") == 4
        assert run_stats.get("failure") == 0

    def test_backfill_run_incomplete(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3", "4", "5"],
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        backfill = graphql_context.instance.get_backfill(backfill_id)

        graphql_context.instance.update_backfill(
            backfill.with_status(BulkActionStatus.COMPLETED_FAILED)
        )

        _seed_runs(
            graphql_context,
            [
                (DagsterRunStatus.SUCCESS, "2"),
                (DagsterRunStatus.SUCCESS, "3"),
                (DagsterRunStatus.STARTED, "4"),
                (DagsterRunStatus.CANCELED, "5"),
            ],
            backfill_id,
        )

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "COMPLETED_FAILED"
        assert result.data["partitionBackfillOrError"]["numPartitions"] == 4
        assert len(result.data["partitionBackfillOrError"]["cancelableRuns"]) == 1
        run_stats = _get_run_stats(
            result.data["partitionBackfillOrError"]["partitionStatuses"]["results"]
        )
        assert run_stats.get("total") == 4
        assert run_stats.get("queued") == 0
        assert run_stats.get("in_progress") == 1
        assert run_stats.get("success") == 2
        assert run_stats.get("failure") == 0
        assert run_stats.get("canceled") == 1

    def test_fetch_user_tag_from_backfill(self, graphql_context):
        user_email = "user123@abc.com"
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3"],
                    "tags": [{"key": "user", "value": user_email}],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["id"] == backfill_id
        assert result.data["partitionBackfillOrError"]["user"] == user_email

    def test_set_title_and_description_for_backfill(self, graphql_context):
        title = "Test backfill"
        description = "This is a test backfill"
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3"],
                    "title": title,
                    "description": description,
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["id"] == backfill_id
        assert result.data["partitionBackfillOrError"]["title"] == title
        assert result.data["partitionBackfillOrError"]["description"] == description

    def test_job_name_correctly_set(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3"],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        stored_backfill = graphql_context.instance.get_backfill(backfill_id)
        assert stored_backfill.job_name == "integers"

    def test_job_name_correctly_set_for_asset_backfills(self, graphql_context):
        asset_keys = [
            AssetKey("unpartitioned_upstream_of_partitioned"),
            AssetKey("upstream_daily_partitioned_asset"),
            AssetKey("downstream_weekly_partitioned_asset"),
        ]
        partitions = ["2023-01-09"]
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "partitionNames": partitions,
                    "assetSelection": [asset_key.to_graphql_input() for asset_key in asset_keys],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        stored_backfill = graphql_context.instance.get_backfill(backfill_id)
        assert stored_backfill.job_name is None

    def test_set_title_and_description_for_backfill_invalid_title(self, graphql_context):
        title = "Title with invalid characters * %"
        description = "This is a test backfill"
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3"],
                    "title": title,
                    "description": description,
                }
            },
        )

        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "PythonError"
        assert (
            '"Title with invalid characters * %" is not a valid title in Dagster'
            in result.data["launchPartitionBackfill"]["message"]
        )

    def test_asset_job_backfill_with_nonexistent_partition_key(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        # launch a backfill for this partition set
        launch_result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["1", "nonexistent1", "nonexistent2"],
                }
            },
        )
        assert (
            launch_result.data["launchPartitionBackfill"]["__typename"]
            == "PartitionKeysNotFoundError"
        )
        assert (
            "Partition keys `['nonexistent1', 'nonexistent2']` could not be found"
            in launch_result.data["launchPartitionBackfill"]["message"]
        )


class TestLaunchDaemonBackfillFromFailure(ExecutingGraphQLContextTestMatrix):
    def test_launch_from_failure(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            "repositorySelector": repository_selector,
            "partitionSetName": "chained_failure_job_partition_set",
        }

        # trigger failure in the conditionally_fail solid

        output_file = os.path.join(
            get_system_temp_directory(), "chained_failure_pipeline_conditionally_fail"
        )
        try:
            with open(output_file, "w", encoding="utf8"):
                result = execute_dagster_graphql_and_finish_runs(
                    graphql_context,
                    LAUNCH_PARTITION_BACKFILL_MUTATION,
                    variables={
                        "backfillParams": {
                            "selector": partition_set_selector,
                            "partitionNames": ["2", "3"],
                        }
                    },
                )
        finally:
            os.remove(output_file)

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"

        # re-execute from failure (without the failure file)
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": partition_set_selector,
                    "partitionNames": ["2", "3"],
                    "fromFailure": True,
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )
        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["numCancelable"] == 2
        assert len(result.data["partitionBackfillOrError"]["partitionNames"]) == 2
        assert result.data["partitionBackfillOrError"]["fromFailure"]

    def test_launch_backfill_with_all_partitions_flag(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            "repositorySelector": repository_selector,
            "partitionSetName": "chained_failure_job_partition_set",
        }

        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": partition_set_selector,
                    "allPartitions": True,
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": backfill_id},
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["numCancelable"] == 10
        assert len(result.data["partitionBackfillOrError"]["partitionNames"]) == 10

    def test_reexecute_asset_backfill_from_failure(self, graphql_context):
        asset_keys = [
            AssetKey("unpartitioned_upstream_of_partitioned"),
            AssetKey("upstream_daily_partitioned_asset"),
            AssetKey("downstream_weekly_partitioned_asset"),
        ]
        partitions = ["2023-01-09"]
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "partitionNames": partitions,
                    "assetSelection": [asset_key.to_graphql_input() for asset_key in asset_keys],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)
        _mock_asset_backfill_runs(
            graphql_context,
            AssetKey("unpartitioned_upstream_of_partitioned"),
            backfill_id,
            DagsterRunStatus.SUCCESS,
            None,
        )
        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)
        _mock_asset_backfill_runs(
            graphql_context,
            AssetKey("upstream_daily_partitioned_asset"),
            backfill_id,
            DagsterRunStatus.FAILURE,
            "2023-01-09",
        )
        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)

        # mark backfill as completed so we can retry it
        backfill = graphql_context.instance.get_backfill(backfill_id)
        graphql_context.instance.update_backfill(backfill.with_status(BulkActionStatus.COMPLETED))

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "FROM_FAILURE"},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retry_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]

        first_backfill = graphql_context.instance.get_backfill(backfill_id)
        retried_from_failure_backfill = graphql_context.instance.get_backfill(retry_backfill_id)

        assert (
            first_backfill.asset_backfill_data.failed_and_downstream_subset
            == retried_from_failure_backfill.asset_backfill_data.target_subset
        )
        assert retried_from_failure_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_from_failure_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "ALL_STEPS"},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retry_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]

        first_backfill = graphql_context.instance.get_backfill(backfill_id)
        retried_backfill = graphql_context.instance.get_backfill(retry_backfill_id)

        assert (
            first_backfill.asset_backfill_data.target_subset
            == retried_backfill.asset_backfill_data.target_subset
        )
        assert retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

    def test_reexecute_successful_asset_backfill(self, graphql_context):
        asset_keys = [
            AssetKey("unpartitioned_upstream_of_partitioned"),
            AssetKey("upstream_daily_partitioned_asset"),
        ]
        partitions = ["2023-01-09"]
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "partitionNames": partitions,
                    "assetSelection": [asset_key.to_graphql_input() for asset_key in asset_keys],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)
        _mock_asset_backfill_runs(
            graphql_context,
            AssetKey("unpartitioned_upstream_of_partitioned"),
            backfill_id,
            DagsterRunStatus.SUCCESS,
            None,
        )
        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)
        _mock_asset_backfill_runs(
            graphql_context,
            AssetKey("upstream_daily_partitioned_asset"),
            backfill_id,
            DagsterRunStatus.SUCCESS,
            "2023-01-09",
        )
        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)

        # mark backfill as complete so we can retry it
        backfill = graphql_context.instance.get_backfill(backfill_id)
        graphql_context.instance.update_backfill(backfill.with_status(BulkActionStatus.COMPLETED))

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "FROM_FAILURE"},
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "PythonError"
        assert (
            "Cannot re-execute from failure an asset backfill that has no missing materializations"
            in result.data["reexecutePartitionBackfill"]["message"]
        )

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "ALL_STEPS"},
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retry_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]

        first_backfill = graphql_context.instance.get_backfill(backfill_id)
        retried_backfill = graphql_context.instance.get_backfill(retry_backfill_id)

        assert (
            first_backfill.asset_backfill_data.target_subset
            == retried_backfill.asset_backfill_data.target_subset
        )
        assert retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

    def test_reexecute_asset_backfill_still_in_progress(self, graphql_context):
        asset_keys = [
            AssetKey("unpartitioned_upstream_of_partitioned"),
            AssetKey("upstream_daily_partitioned_asset"),
            AssetKey("downstream_weekly_partitioned_asset"),
        ]
        partitions = ["2023-01-09"]
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "partitionNames": partitions,
                    "assetSelection": [asset_key.to_graphql_input() for asset_key in asset_keys],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)
        _mock_asset_backfill_runs(
            graphql_context,
            AssetKey("unpartitioned_upstream_of_partitioned"),
            backfill_id,
            DagsterRunStatus.SUCCESS,
            None,
        )
        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)
        _mock_asset_backfill_runs(
            graphql_context,
            AssetKey("upstream_daily_partitioned_asset"),
            backfill_id,
            DagsterRunStatus.FAILURE,
            "2023-01-09",
        )
        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)

        # try to retry the backfill while it is still in progress
        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "FROM_FAILURE"},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "PythonError"
        assert "still in progress" in result.data["reexecutePartitionBackfill"]["message"]

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "ALL_STEPS"},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "PythonError"
        assert "still in progress" in result.data["reexecutePartitionBackfill"]["message"]

        # once the first backfill is in a completed state, we can retry it
        backfill = graphql_context.instance.get_backfill(backfill_id)
        graphql_context.instance.update_backfill(backfill.with_status(BulkActionStatus.FAILED))

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "FROM_FAILURE"},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retry_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]

        first_backfill = graphql_context.instance.get_backfill(backfill_id)
        retried_from_failure_backfill = graphql_context.instance.get_backfill(retry_backfill_id)

        assert (
            first_backfill.asset_backfill_data.failed_and_downstream_subset
            == retried_from_failure_backfill.asset_backfill_data.target_subset
        )
        assert retried_from_failure_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_from_failure_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "ALL_STEPS"},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retry_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]

        first_backfill = graphql_context.instance.get_backfill(backfill_id)
        retried_backfill = graphql_context.instance.get_backfill(retry_backfill_id)

        assert (
            first_backfill.asset_backfill_data.target_subset
            == retried_backfill.asset_backfill_data.target_subset
        )
        assert retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

    def test_reexecute_asset_backfill_twice(self, graphql_context):
        asset_keys = [
            AssetKey("unpartitioned_upstream_of_partitioned"),
            AssetKey("upstream_daily_partitioned_asset"),
            AssetKey("downstream_weekly_partitioned_asset"),
        ]
        partitions = ["2023-01-09"]
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "partitionNames": partitions,
                    "assetSelection": [asset_key.to_graphql_input() for asset_key in asset_keys],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)
        _mock_asset_backfill_runs(
            graphql_context,
            AssetKey("unpartitioned_upstream_of_partitioned"),
            backfill_id,
            DagsterRunStatus.SUCCESS,
            None,
        )
        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)
        _mock_asset_backfill_runs(
            graphql_context,
            AssetKey("upstream_daily_partitioned_asset"),
            backfill_id,
            DagsterRunStatus.FAILURE,
            "2023-01-09",
        )
        _execute_asset_backfill_iteration_no_side_effects(graphql_context, backfill_id)

        # mark backfill as completed so we can retry it
        backfill = graphql_context.instance.get_backfill(backfill_id)
        graphql_context.instance.update_backfill(backfill.with_status(BulkActionStatus.COMPLETED))

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "FROM_FAILURE"},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retry_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]

        first_backfill = graphql_context.instance.get_backfill(backfill_id)
        retried_backfill = graphql_context.instance.get_backfill(retry_backfill_id)

        assert (
            first_backfill.asset_backfill_data.failed_and_downstream_subset
            == retried_backfill.asset_backfill_data.target_subset
        )
        assert retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

        _execute_asset_backfill_iteration_no_side_effects(
            graphql_context, retried_backfill.backfill_id
        )
        # mark some partitions failed so we can retry again
        _mock_asset_backfill_runs(
            graphql_context,
            AssetKey("upstream_daily_partitioned_asset"),
            retried_backfill.backfill_id,
            DagsterRunStatus.FAILURE,
            "2023-01-09",
        )
        _execute_asset_backfill_iteration_no_side_effects(
            graphql_context, retried_backfill.backfill_id
        )

        # refetch the backfill to get the updated statuses of all assets
        retried_backfill = graphql_context.instance.get_backfill(retry_backfill_id)
        graphql_context.instance.update_backfill(
            retried_backfill.with_status(BulkActionStatus.COMPLETED)
        )

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": retry_backfill_id, "strategy": "FROM_FAILURE"},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        seconrd_retry_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]

        second_retried_backfill = graphql_context.instance.get_backfill(seconrd_retry_backfill_id)
        retried_backfill = graphql_context.instance.get_backfill(retry_backfill_id)

        assert (
            retried_backfill.asset_backfill_data.failed_and_downstream_subset
            == second_retried_backfill.asset_backfill_data.target_subset
        )
        assert second_retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == retry_backfill_id
        assert second_retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

    def test_retry_job_backfill(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            "repositorySelector": repository_selector,
            "partitionSetName": "chained_failure_job_partition_set",
        }

        # trigger failure in the conditionally_fail solid

        output_file = os.path.join(
            get_system_temp_directory(), "chained_failure_pipeline_conditionally_fail"
        )
        try:
            with open(output_file, "w", encoding="utf8"):
                result = execute_dagster_graphql_and_finish_runs(
                    graphql_context,
                    LAUNCH_PARTITION_BACKFILL_MUTATION,
                    variables={
                        "backfillParams": {
                            "selector": partition_set_selector,
                            "partitionNames": ["2", "3"],
                        }
                    },
                )
        finally:
            os.remove(output_file)

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        backfill = graphql_context.instance.get_backfill(backfill_id)
        graphql_context.instance.update_backfill(backfill.with_status(BulkActionStatus.COMPLETED))

        # re-execute from failure (without the failure file)
        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "FROM_FAILURE"}
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retried_from_failure_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]
        retried_from_failure_backfill = graphql_context.instance.get_backfill(
            retried_from_failure_backfill_id
        )

        assert retried_from_failure_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_from_failure_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": retried_from_failure_backfill_id},
        )
        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["numCancelable"] == 2
        assert len(result.data["partitionBackfillOrError"]["partitionNames"]) == 2
        assert result.data["partitionBackfillOrError"]["fromFailure"]

        # re-execute  (without the failure file)
        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={"reexecutionParams": {"parentRunId": backfill_id, "strategy": "ALL_STEPS"}},
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retried_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]
        retried_backfill = graphql_context.instance.get_backfill(retried_backfill_id)

        assert retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

        result = execute_dagster_graphql(
            graphql_context,
            PARTITION_PROGRESS_QUERY,
            variables={"backfillId": retried_backfill_id},
        )
        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["numCancelable"] == 2
        assert len(result.data["partitionBackfillOrError"]["partitionNames"]) == 2
        assert not result.data["partitionBackfillOrError"]["fromFailure"]

    def test_retry_in_progress_job_backfill(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            "repositorySelector": repository_selector,
            "partitionSetName": "chained_failure_job_partition_set",
        }

        # trigger failure in the conditionally_fail solid

        output_file = os.path.join(
            get_system_temp_directory(), "chained_failure_pipeline_conditionally_fail"
        )
        try:
            with open(output_file, "w", encoding="utf8"):
                result = execute_dagster_graphql_and_finish_runs(
                    graphql_context,
                    LAUNCH_PARTITION_BACKFILL_MUTATION,
                    variables={
                        "backfillParams": {
                            "selector": partition_set_selector,
                            "partitionNames": ["2", "3"],
                        }
                    },
                )
        finally:
            os.remove(output_file)

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "FROM_FAILURE"}
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "PythonError"
        assert "still in progress" in result.data["reexecutePartitionBackfill"]["message"]

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={"reexecutionParams": {"parentRunId": backfill_id, "strategy": "ALL_STEPS"}},
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "PythonError"
        assert "still in progress" in result.data["reexecutePartitionBackfill"]["message"]

        # mark backfill as complete and confirm that we can retry it
        backfill = graphql_context.instance.get_backfill(backfill_id)
        graphql_context.instance.update_backfill(backfill.with_status(BulkActionStatus.COMPLETED))

        # re-execute from failure (without the failure file)
        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "FROM_FAILURE"}
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retried_from_failure_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]
        retried_from_failure_backfill = graphql_context.instance.get_backfill(
            retried_from_failure_backfill_id
        )

        assert retried_from_failure_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_from_failure_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

        # re-execute (without the failure file)
        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={"reexecutionParams": {"parentRunId": backfill_id, "strategy": "ALL_STEPS"}},
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retried_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]
        retried_backfill = graphql_context.instance.get_backfill(retried_backfill_id)

        assert retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

    def test_retry_job_backfill_twice(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            "repositorySelector": repository_selector,
            "partitionSetName": "chained_failure_job_partition_set",
        }

        # trigger failure in the conditionally_fail solid

        output_file = os.path.join(
            get_system_temp_directory(), "chained_failure_pipeline_conditionally_fail"
        )
        with open(output_file, "w", encoding="utf8"):
            result = execute_dagster_graphql_and_finish_runs(
                graphql_context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "selector": partition_set_selector,
                        "partitionNames": ["2", "3"],
                    }
                },
            )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        # mark backfill as complete and confirm that we can retry it
        backfill = graphql_context.instance.get_backfill(backfill_id)
        graphql_context.instance.update_backfill(backfill.with_status(BulkActionStatus.COMPLETED))
        try:
            with open(output_file, "w", encoding="utf8"):
                # re-execute from failure (still with the failure file)
                result = execute_dagster_graphql(
                    graphql_context,
                    RETRY_BACKFILL_MUTATION,
                    variables={
                        "reexecutionParams": {
                            "parentRunId": backfill_id,
                            "strategy": "FROM_FAILURE",
                        }
                    },
                )
        finally:
            os.remove(output_file)

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retried_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]
        retried_backfill = graphql_context.instance.get_backfill(retried_backfill_id)

        assert retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

        graphql_context.instance.update_backfill(
            retried_backfill.with_status(BulkActionStatus.COMPLETED)
        )

        # re-execute from failure (without the failure file)
        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {
                    "parentRunId": retried_backfill.backfill_id,
                    "strategy": "FROM_FAILURE",
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        second_retried_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]
        second_retried_backfill = graphql_context.instance.get_backfill(second_retried_backfill_id)

        assert second_retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == retried_backfill_id
        assert second_retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id

    def test_retry_successful_job_backfill(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            "repositorySelector": repository_selector,
            "partitionSetName": "chained_failure_job_partition_set",
        }

        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": partition_set_selector,
                    "partitionNames": ["2", "3"],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        # mark backfill as complete
        backfill = graphql_context.instance.get_backfill(backfill_id)
        graphql_context.instance.update_backfill(backfill.with_status(BulkActionStatus.COMPLETED))

        result = execute_dagster_graphql(
            graphql_context,
            RETRY_BACKFILL_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": backfill_id, "strategy": "FROM_FAILURE"}
            },
        )
        # Unlike asset backfills, we don't currently have a way to see if a job backfill has runs that
        # failed without querying the DB. So we always allow retries
        assert not result.errors
        assert result.data
        assert result.data["reexecutePartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        retried_backfill_id = result.data["reexecutePartitionBackfill"]["backfillId"]
        retried_backfill = graphql_context.instance.get_backfill(retried_backfill_id)

        assert retried_backfill.tags.get(PARENT_BACKFILL_ID_TAG) == backfill_id
        assert retried_backfill.tags.get(ROOT_BACKFILL_ID_TAG) == backfill_id
