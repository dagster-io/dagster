from dagster_graphql.test.utils import execute_dagster_graphql, infer_repository_selector

INPUT_OUTPUT_DEFINITIONS_QUERY = """
    query InputOutputDefinitionsQuery($repositorySelector: RepositorySelector!) {
        repositoryOrError(repositorySelector: $repositorySelector) {
           ... on Repository {
                usedSolid(name: "solid_with_input_output_metadata") {
                    __typename
                    definition {
                        inputDefinitions {
                            metadataEntries {
                                label
                            }
                        }
                        outputDefinitions {
                            metadataEntries {
                                label
                            }
                        }
                    }
                }
            }
        }
    }
"""


def test_query_inputs_outputs(graphql_context, snapshot):
    selector = infer_repository_selector(graphql_context)
    result = execute_dagster_graphql(
        graphql_context, INPUT_OUTPUT_DEFINITIONS_QUERY, variables={"repositorySelector": selector}
    )
    assert result.data
    snapshot.assert_match(result.data)
