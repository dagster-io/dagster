from dagster_graphql.test.utils import execute_dagster_graphql

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

RUN_QUEUING_QUERY = """
query InstanceDetailSummaryQuery {
    instance {
        runQueuingSupported
    }
}
"""


class TestQueued(
    make_graphql_context_test_suite(
        context_variants=[
            GraphQLContextVariant.sqlite_with_queued_run_coordinator_managed_grpc_env(),
        ]
    )
):
    def test_get_individual_daemons(self, graphql_context):
        results = execute_dagster_graphql(graphql_context, RUN_QUEUING_QUERY)
        assert results.data == {"instance": {"runQueuingSupported": True}}
