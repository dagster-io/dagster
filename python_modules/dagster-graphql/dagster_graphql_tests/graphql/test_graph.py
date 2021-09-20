from .graphql_context_test_suite import NonLaunchableGraphQLContextTestMatrix
from .utils import execute_dagster_graphql

REPOSITORY_QUERY = """
query {
   workspaceOrError {
      __typename
      ... on Workspace {
        locationEntries {
          __typename
          id
          name
          locationOrLoadError {
            __typename
            ... on RepositoryLocation {
                id
                name
                repositories {
                    name
                    pipelines {
                        name
                        graphName
                    }
                }
                isReloadSupported
            }
            ... on PythonError {
              message
            }
          }
        }
      }
      ... on PythonError {
          message
          stack
      }
    }
}
"""


class TestGraphs(NonLaunchableGraphQLContextTestMatrix):
    def test_basic_jobs(self, graphql_context):
        result = execute_dagster_graphql(graphql_context, REPOSITORY_QUERY)

        assert result
        assert result.data
        assert result.data["workspaceOrError"]["__typename"] == "Workspace"
        repo_locations = {
            blob["name"]: blob for blob in result.data["workspaceOrError"]["locationEntries"]
        }
        assert "test" in repo_locations
        assert repo_locations["test"]["locationOrLoadError"]["__typename"] == "RepositoryLocation"

        jobs = {
            blob["name"]: blob
            for blob in repo_locations["test"]["locationOrLoadError"]["repositories"][0][
                "pipelines"
            ]
        }

        assert "simple_job_a" in jobs
        assert jobs["simple_job_a"]["graphName"] == "simple_graph"
        assert "simple_job_b" in jobs
        assert jobs["simple_job_b"]["graphName"] == "simple_graph"
