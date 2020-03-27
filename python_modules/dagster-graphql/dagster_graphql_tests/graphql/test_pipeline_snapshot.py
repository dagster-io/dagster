from dagster_graphql.test.utils import execute_dagster_graphql

from .setup import define_test_context

SNAPSHOT_QUERY = '''
query PipelineSnapshotQuery($snapshotId: String!) {
    pipelineSnapshot(snapshotId: $snapshotId) {
        name
        description
        runtimeTypes { key }
        solids { name }
        runs { runId } 
        modes { name }
        solidHandles { handleID }
        tags { key value }
    }
}
'''


def test_query_snapshot(snapshot):
    result = execute_dagster_graphql(
        define_test_context(), SNAPSHOT_QUERY, {'snapshotId': 'csv_hello_world'}
    )

    assert not result.errors
    assert result.data

    snapshot.assert_match(result.data)
