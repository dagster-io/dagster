from dagster_graphql.test.utils import execute_dagster_graphql

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)

MUTATION = """
mutation SetAutoMaterializePausedMutation($paused: Boolean!) {
    setAutoMaterializePaused(paused: $paused)
}
"""

QUERY = """
query GetAutoMaterializePausedQuery {
    instance {
        autoMaterializePaused
    }
}
"""


class TestDaemonHealth(ExecutingGraphQLContextTestMatrix):
    def test_paused(self, graphql_context):
        results = execute_dagster_graphql(graphql_context, QUERY)
        assert results.data == {
            "instance": {
                "autoMaterializePaused": True,
            }
        }

        results = execute_dagster_graphql(graphql_context, MUTATION, variables={"paused": False})
        assert results.data == {
            "setAutoMaterializePaused": False,
        }

        results = execute_dagster_graphql(graphql_context, QUERY)
        assert results.data == {
            "instance": {
                "autoMaterializePaused": False,
            }
        }

        results = execute_dagster_graphql(graphql_context, MUTATION, variables={"paused": True})
        assert results.data == {
            "setAutoMaterializePaused": True,
        }

        results = execute_dagster_graphql(graphql_context, QUERY)
        assert results.data == {
            "instance": {
                "autoMaterializePaused": True,
            }
        }

        results = execute_dagster_graphql(graphql_context, MUTATION, variables={"paused": False})
        assert results.data == {
            "setAutoMaterializePaused": False,
        }

        results = execute_dagster_graphql(graphql_context, QUERY)
        assert results.data == {
            "instance": {
                "autoMaterializePaused": False,
            }
        }
