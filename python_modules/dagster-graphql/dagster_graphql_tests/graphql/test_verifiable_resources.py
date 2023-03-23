from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_repository_selector,
    infer_resource_selector,
)


TOP_LEVEL_RESOURCE_QUERY = """
query ResourceDetailsQuery($selector: ResourceSelector!) {
  topLevelResourceDetailsOrError(resourceSelector: $selector) {
    __typename
    ... on ResourceDetails {
        name
        description
        supportsVerification
    }
  }
}
"""


def test_fetch_top_level_resource_no_verification(definitions_graphql_context, snapshot):
    selector = infer_resource_selector(definitions_graphql_context, name="my_outer_resource")
    result = execute_dagster_graphql(
        definitions_graphql_context,
        TOP_LEVEL_RESOURCE_QUERY,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["topLevelResourceDetailsOrError"]
    my_resource = result.data["topLevelResourceDetailsOrError"]

    assert my_resource["supportsVerification"] == False

    snapshot.assert_match(result.data)


def test_fetch_top_level_resource(definitions_graphql_context, snapshot):
    selector = infer_resource_selector(definitions_graphql_context, name="my_resource")
    result = execute_dagster_graphql(
        definitions_graphql_context,
        TOP_LEVEL_RESOURCE_QUERY,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["topLevelResourceDetailsOrError"]
    my_resource = result.data["topLevelResourceDetailsOrError"]

    assert my_resource["supportsVerification"] == True

    snapshot.assert_match(result.data)
