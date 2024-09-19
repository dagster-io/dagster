from dagster._core.workspace.context import WorkspaceRequestContext
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
    query SolidsQuery($repositorySelector: RepositorySelector!, $solidName: String!) {
        repositoryOrError(repositorySelector: $repositorySelector) {
            ... on Repository {
                usedSolid(name: $solidName) {
                    definition {
                        name
                        assetNodes {
                            assetKey {
                                path
                            }
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


def test_query_all_solids(graphql_context: WorkspaceRequestContext, snapshot):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context, all_solids_query(), variables={"repositorySelector": selector}
    )
    snapshot.assert_match(result.data)


def test_query_get_solid_exists(graphql_context: WorkspaceRequestContext):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context,
        get_solid_query_exists(),
        variables={"repositorySelector": selector, "solidName": "sum_op"},
    )

    assert not result.errors
    print(result.data["repositoryOrError"])  # noqa: T201
    assert result.data["repositoryOrError"]["usedSolid"]["definition"]["name"] == "sum_op"


def test_asset_graph_node_asset_defs(graphql_context: WorkspaceRequestContext):
    # Verify that the node for an asset graph is correctly associated with its assets

    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context,
        get_solid_query_exists(),
        variables={"repositorySelector": selector, "solidName": "hanging_graph"},
    )

    assert not result.errors
    print(result.data["repositoryOrError"])  # noqa: T201
    assert result.data["repositoryOrError"]["usedSolid"]["definition"]["name"] == "hanging_graph"

    nodes = result.data["repositoryOrError"]["usedSolid"]["definition"]["assetNodes"]

    assert len(nodes) == 1
    assert nodes[0]["assetKey"]["path"] == ["hanging_graph"]
