from dagster_graphql.test.utils import execute_dagster_graphql, infer_repository_selector


def all_solids_query():
    return """
    query AllSolidsQuery($repositorySelector: RepositorySelector!) {
        repositoryOrError(repositorySelector: $repositorySelector) {
           ... on Repository {
                usedSolids {
                    __typename
                    definition { name }
                    invocations { pipeline { name } solidHandle { handleID } }
                }
            }
        }
    }
    """


def get_solid_query_exists():
    return """
    query SolidsQuery($repositorySelector: RepositorySelector!) {
        repositoryOrError(repositorySelector: $repositorySelector) {
            ... on Repository {
                usedSolid(name: "sum_solid") {
                    definition { name }
                }
            }
            ... on PythonError {
                message
                stack
            }
        }
    }
    """


def test_query_all_solids(graphql_context, snapshot):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context, all_solids_query(), variables={"repositorySelector": selector}
    )
    snapshot.assert_match(result.data)


def test_query_get_solid_exists(graphql_context):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context, get_solid_query_exists(), variables={"repositorySelector": selector}
    )

    assert not result.errors
    print(result.data["repositoryOrError"])  # pylint: disable=print-call
    assert result.data["repositoryOrError"]["usedSolid"]["definition"]["name"] == "sum_solid"
