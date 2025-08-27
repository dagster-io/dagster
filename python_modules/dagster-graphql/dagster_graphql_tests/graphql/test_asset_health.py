from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)

GET_ASSET_HEALTH = """
query GetAssetHealth($assetKey: AssetKeyInput!) {
    assetsOrError(assetKeys: [$assetKey]) {
        ... on AssetConnection {
            nodes {
                assetHealth {
                    assetHealth
                    materializationStatus
                    assetChecksStatus
                    freshnessStatus
                }
            }
        }
    }
}
"""


# There is a separate implementation for plus graphql tests.
class TestAssetHealth(ExecutingGraphQLContextTestMatrix):
    def test_asset_health_status(self, graphql_context: WorkspaceRequestContext):
        instance = graphql_context.instance
        assert not instance.dagster_asset_health_queries_supported()
        res = execute_dagster_graphql(
            graphql_context, GET_ASSET_HEALTH, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {"assetsOrError": {"nodes": [{"assetHealth": None}]}}
