from dagster_graphql.test.utils import execute_dagster_graphql

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

INSTANCE_QUERY = """
query InstanceDetailSummaryQuery {
    instance {
        runQueuingSupported
        hasInfo
    }
}
"""


class TestInstanceSettings(
    make_graphql_context_test_suite(
        context_variants=[
            GraphQLContextVariant.sqlite_with_queued_run_coordinator_managed_grpc_env(),
        ]
    )
):
    def test_instance_settings(self, graphql_context):
        results = execute_dagster_graphql(graphql_context, INSTANCE_QUERY)
        assert results.data == {"instance": {"runQueuingSupported": True, "hasInfo": True}}
