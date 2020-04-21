from contextlib import contextmanager

import pytest
from dagster_graphql.implementation.fetch_pipelines import (
    _get_dauphin_pipeline_snapshot_from_instance,
)
from dagster_graphql.implementation.utils import UserFacingGraphQLError
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster import execute_pipeline
from dagster.core.instance import DagsterInstance
from dagster.seven import json, mock

from .setup import define_test_context, noop_pipeline

SNAPSHOT_QUERY = '''
query PipelineSnapshotQuery($snapshotId: String!) {
    pipelineSnapshot(snapshotId: $snapshotId) {
        __typename
        name
        pipelineSnapshotId
        description
        runtimeTypes { key }
        solids { name }
        modes { name }
        solidHandles { handleID }
        tags { key value }
    }
}
'''

SNAPSHOT_OR_ERROR_QUERY_BY_SNAPSHOT_ID = '''
query PipelineSnapshotQueryBySnapshotID($snapshotId: String!) {
    pipelineSnapshotOrError(snapshotId: $snapshotId) {
        __typename
        ... on PipelineSnapshot {
            name
            pipelineSnapshotId
            description
            runtimeTypes { key }
            solids { name }
            modes { name }
            solidHandles { handleID }
            tags { key value }
        }
        ... on PipelineSnapshotNotFoundError {
            snapshotId
        }
    }
}
'''

SNAPSHOT_OR_ERROR_QUERY_BY_PIPELINE_NAME = '''
query PipelineSnapshotQueryByActivePipelineName($activePipelineName: String!) {
    pipelineSnapshotOrError(activePipelineName: $activePipelineName) {
        __typename
        ... on PipelineSnapshot {
            name
            pipelineSnapshotId
            description
            runtimeTypes { key }
            solids { name }
            modes { name }
            solidHandles { handleID }
            tags { key value }
        }
        ... on PipelineSnapshotNotFoundError {
            snapshotId
        }
    }
}
'''

# makes snapshot tests much easier to debug
def pretty_dump(data):
    return json.dumps(data, indent=2, separators=(',', ': '))


@contextmanager
def create_ephemeral_instance():
    yield DagsterInstance.ephemeral()


@contextmanager
def create_local_temp_instance():
    yield DagsterInstance.local_temp()


class TestPipelineSnapshotGraphQL:
    __test__ = True

    @pytest.fixture(name='instance', params=[create_ephemeral_instance, create_local_temp_instance])
    def get_instance(self, request):
        with request.param() as s:
            yield s

    def test_fetch_snapshot_success(self, instance, snapshot):
        result = execute_pipeline(noop_pipeline, instance=instance)
        assert result.success
        run = instance.get_run_by_id(result.run_id)
        assert run.pipeline_snapshot_id

        result = execute_dagster_graphql(
            define_test_context(instance), SNAPSHOT_QUERY, {'snapshotId': run.pipeline_snapshot_id}
        )

        assert not result.errors
        assert result.data
        assert result.data['pipelineSnapshot']['__typename'] == 'PipelineSnapshot'
        snapshot.assert_match(pretty_dump(result.data))

    def test_fetch_snapshot_or_error_by_snapshot_id_success(self, instance, snapshot):
        result = execute_pipeline(noop_pipeline, instance=instance)
        assert result.success
        run = instance.get_run_by_id(result.run_id)
        assert run.pipeline_snapshot_id

        result = execute_dagster_graphql(
            define_test_context(instance),
            SNAPSHOT_OR_ERROR_QUERY_BY_SNAPSHOT_ID,
            {'snapshotId': run.pipeline_snapshot_id},
        )

        assert not result.errors
        assert result.data
        assert result.data['pipelineSnapshotOrError']['__typename'] == 'PipelineSnapshot'

        snapshot.assert_match(pretty_dump(result.data))

    def test_fetch_snapshot_or_error_by_snapshot_id_snapshot_not_found(self, instance, snapshot):
        result = execute_dagster_graphql(
            define_test_context(instance),
            SNAPSHOT_OR_ERROR_QUERY_BY_SNAPSHOT_ID,
            {'snapshotId': 'notthere'},
        )

        assert not result.errors
        assert result.data
        assert (
            result.data['pipelineSnapshotOrError']['__typename'] == 'PipelineSnapshotNotFoundError'
        )
        assert result.data['pipelineSnapshotOrError']['snapshotId'] == 'notthere'
        snapshot.assert_match(pretty_dump(result.data))

    def test_fetch_snapshot_or_error_by_active_pipeline_name_success(self, instance, snapshot):
        result = execute_dagster_graphql(
            define_test_context(instance),
            SNAPSHOT_OR_ERROR_QUERY_BY_PIPELINE_NAME,
            {'activePipelineName': 'csv_hello_world'},
        )

        assert not result.errors
        assert result.data
        assert result.data['pipelineSnapshotOrError']['__typename'] == 'PipelineSnapshot'
        assert result.data['pipelineSnapshotOrError']['name'] == 'csv_hello_world'

        snapshot.assert_match(pretty_dump(result.data))

    def test_fetch_snapshot_or_error_by_active_pipeline_name_not_found(self, instance, snapshot):
        result = execute_dagster_graphql(
            define_test_context(instance),
            SNAPSHOT_OR_ERROR_QUERY_BY_PIPELINE_NAME,
            {'activePipelineName': 'jkdjfkdj'},
        )

        assert not result.errors
        assert result.data
        assert result.data['pipelineSnapshotOrError']['__typename'] == 'PipelineNotFoundError'

        snapshot.assert_match(pretty_dump(result.data))


def test_temporary_error_or_deletion_after_instance_check():
    instance = mock.MagicMock()

    instance.has_pipeline_snapshot.return_value = True
    instance.get_pipeline_snapshot.return_value = None

    with pytest.raises(UserFacingGraphQLError):
        _get_dauphin_pipeline_snapshot_from_instance(instance, 'kjdkfjd')
