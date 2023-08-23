from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
)

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)

GET_ASSET_CHECKS = """
query GetAssetChecksQuery($assetKey: AssetKeyInput!) {
    assetChecksOrError(assetKey: $assetKey) {
        ... on AssetChecks {
            checks {
                name
                description
            }
        }
    }
}
"""


class TestAssetChecks(ExecutingGraphQLContextTestMatrix):
    def test_asset_checks(self, graphql_context: WorkspaceRequestContext, snapshot):
        res = execute_dagster_graphql(
            graphql_context, GET_ASSET_CHECKS, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetChecksOrError": {
                "checks": [
                    {
                        "name": "my_check",
                        "description": "asset_1 check",
                    }
                ]
            }
        }
