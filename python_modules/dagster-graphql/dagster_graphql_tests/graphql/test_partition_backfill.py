from dagster_graphql.client.query import LAUNCH_PARTITION_BACKFILL_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql, infer_repository_selector

from .graphql_context_test_suite import ExecutingGraphQLContextTestMatrix


class TestPartitionBackfill(ExecutingGraphQLContextTestMatrix):
    def test_get_partition_sets_for_pipeline(self, graphql_context):
        selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                'backfillParams': {
                    'selector': {
                        'repositorySelector': selector,
                        'partitionSetName': 'integer_partition',
                    },
                    'partitionNames': ['2', '3'],
                    'solidSelection': [],
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data['launchPartitionBackfill']['__typename'] == 'PartitionBackfillSuccess'
