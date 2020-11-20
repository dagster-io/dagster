from dagster_graphql.test.utils import execute_dagster_graphql, infer_repository_selector

from .graphql_context_test_suite import ReadonlyGraphQLContextTestMatrix

GET_SENSORS_QUERY = """
query SensorsQuery($repositorySelector: RepositorySelector!) {
  sensorsOrError(repositorySelector: $repositorySelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on Sensors {
      results {
        id
        name
        pipelineName
        solidSelection
        mode
        status
        runs {
            id
            runId
        }
        runsCount
        ticks {
            id
            status
            timestamp
            runId
            error {
                message
                stack
            }
            runKey
        }
      }
    }
  }
}
"""


class TestSensors(ReadonlyGraphQLContextTestMatrix):
    def test_get_sensors(self, graphql_context, snapshot):
        selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context, GET_SENSORS_QUERY, variables={"repositorySelector": selector},
        )

        assert result.data
        assert result.data["sensorsOrError"]
        assert result.data["sensorsOrError"]["__typename"] == "Sensors"
        results = result.data["sensorsOrError"]["results"]
        snapshot.assert_match(results)
