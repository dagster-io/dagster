from unittest import mock

import pytest
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.implementation.fetch_pipelines import _get_job_snapshot_from_instance
from dagster_graphql.implementation.utils import UserFacingGraphQLError
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    main_repo_location_name,
    main_repo_name,
)
from dagster_shared.seven import json

from dagster_graphql_tests.graphql.repo import noop_job

SNAPSHOT_OR_ERROR_QUERY_BY_SNAPSHOT_ID = """
query PipelineSnapshotQueryBySnapshotID($snapshotId: String!) {
    pipelineSnapshotOrError(snapshotId: $snapshotId) {
        __typename
        ... on PipelineSnapshot {
            name
            pipelineSnapshotId
            description
            dagsterTypes { key }
            solids { name }
            modes { name }
            solidHandles { handleID }
            tags { key value }
            runTags { key value }
        }
        ... on PipelineSnapshotNotFoundError {
            snapshotId
        }
    }
}
"""

SNAPSHOT_OR_ERROR_QUERY_BY_PIPELINE_NAME = """
query PipelineSnapshotQueryByActivePipelineName($activePipelineSelector: PipelineSelector!) {
    pipelineSnapshotOrError(activePipelineSelector: $activePipelineSelector) {
        __typename
        ... on PipelineSnapshot {
            name
            pipelineSnapshotId
            description
            dagsterTypes { key }
            solids { name }
            modes { name }
            solidHandles { handleID }
            tags { key value }
            runTags { key value }
        }
        ... on PipelineSnapshotNotFoundError {
            snapshotId
        }
    }
}
"""


# makes snapshot tests much easier to debug
def pretty_dump(data) -> str:
    return json.dumps(data, indent=2, separators=(",", ": "))


def test_fetch_snapshot_or_error_by_snapshot_id_success(
    graphql_context: WorkspaceRequestContext, snapshot
):
    instance = graphql_context.instance
    result = noop_job.execute_in_process(instance=instance)
    assert result.success
    run = instance.get_run_by_id(result.run_id)
    assert run and run.job_snapshot_id

    result = execute_dagster_graphql(
        graphql_context,
        SNAPSHOT_OR_ERROR_QUERY_BY_SNAPSHOT_ID,
        {"snapshotId": run.job_snapshot_id},
    )

    assert not result.errors
    assert result.data
    assert result.data["pipelineSnapshotOrError"]["__typename"] == "PipelineSnapshot"

    snapshot.assert_match(pretty_dump(result.data))


def test_fetch_snapshot_or_error_by_snapshot_id_snapshot_not_found(
    graphql_context: WorkspaceRequestContext, snapshot
):
    result = execute_dagster_graphql(
        graphql_context,
        SNAPSHOT_OR_ERROR_QUERY_BY_SNAPSHOT_ID,
        {"snapshotId": "notthere"},
    )

    assert not result.errors
    assert result.data
    assert result.data["pipelineSnapshotOrError"]["__typename"] == "PipelineSnapshotNotFoundError"
    assert result.data["pipelineSnapshotOrError"]["snapshotId"] == "notthere"
    snapshot.assert_match(pretty_dump(result.data))


def test_fetch_snapshot_or_error_by_active_pipeline_name_success(
    graphql_context: WorkspaceRequestContext, snapshot
):
    result = execute_dagster_graphql(
        graphql_context,
        SNAPSHOT_OR_ERROR_QUERY_BY_PIPELINE_NAME,
        {
            "activePipelineSelector": {
                "pipelineName": "tagged_job",
                "repositoryName": main_repo_name(),
                "repositoryLocationName": main_repo_location_name(),
            }
        },
    )

    assert not result.errors
    assert result.data
    assert result.data["pipelineSnapshotOrError"]["__typename"] == "PipelineSnapshot"
    assert result.data["pipelineSnapshotOrError"]["name"] == "tagged_job"
    assert result.data["pipelineSnapshotOrError"]["tags"] == [{"key": "foo", "value": "bar"}]
    assert result.data["pipelineSnapshotOrError"]["runTags"] == [{"key": "baz", "value": "quux"}]

    snapshot.assert_match(pretty_dump(result.data))


def test_fetch_snapshot_or_error_by_active_pipeline_name_not_found(
    graphql_context: WorkspaceRequestContext, snapshot
):
    result = execute_dagster_graphql(
        graphql_context,
        SNAPSHOT_OR_ERROR_QUERY_BY_PIPELINE_NAME,
        {
            "activePipelineSelector": {
                "pipelineName": "jkdjfkdj",
                "repositoryName": main_repo_name(),
                "repositoryLocationName": main_repo_location_name(),
            }
        },
    )

    assert not result.errors
    assert result.data
    assert result.data["pipelineSnapshotOrError"]["__typename"] == "PipelineNotFoundError"

    snapshot.assert_match(pretty_dump(result.data))


def test_temporary_error_or_deletion_after_instance_check():
    instance = mock.MagicMock()

    instance.has_historical_job.return_value = True
    instance.get_historical_job.return_value = None

    with pytest.raises(UserFacingGraphQLError):
        _get_job_snapshot_from_instance(instance, "kjdkfjd")


def test_fetch_snapshot_or_error_by_snap_and_selector(
    graphql_context: WorkspaceRequestContext, snapshot
):
    # falls back to selector on snap id miss
    result = execute_dagster_graphql(
        graphql_context,
        SNAPSHOT_OR_ERROR_QUERY_BY_PIPELINE_NAME,
        {
            "snapshotId": "notthere",
            "activePipelineSelector": {
                "pipelineName": "csv_hello_world",
                "repositoryName": main_repo_name(),
                "repositoryLocationName": main_repo_location_name(),
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data["pipelineSnapshotOrError"]["__typename"] == "PipelineSnapshot"
    assert result.data["pipelineSnapshotOrError"]["name"] == "csv_hello_world"

    instance = graphql_context.instance
    result = noop_job.execute_in_process(instance=instance)
    assert result.success
    run = instance.get_run_by_id(result.run_id)
    assert run and run.job_snapshot_id

    # valid snap id but bad selector works (snap preferred)
    result = execute_dagster_graphql(
        graphql_context,
        SNAPSHOT_OR_ERROR_QUERY_BY_SNAPSHOT_ID,
        {
            "snapshotId": run.job_snapshot_id,
            "activePipelineSelector": {
                "pipelineName": "does_not_exist",
                "repositoryName": main_repo_name(),
                "repositoryLocationName": main_repo_location_name(),
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data["pipelineSnapshotOrError"]["__typename"] == "PipelineSnapshot"
