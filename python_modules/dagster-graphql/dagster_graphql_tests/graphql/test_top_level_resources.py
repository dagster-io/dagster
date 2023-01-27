from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_repository_selector,
    infer_resource_selector,
)

TOP_LEVEL_RESOURCES_QUERY = """
query TopLevelResourcesQuery($selector: RepositorySelector!) {
  topLevelResourcesOrError(repositorySelector: $selector) {
    __typename
    ... on TopLevelResources {
      results {
        name
        description
        configFields {
            name
            description
            configType {
                key
                ... on CompositeConfigType {
                fields {
                    name
                    configType {
                        key
                        }
                    }
                }
            }
        }
        configuredValues {
            key
            value
        }
      }
    }
  }
}
"""

TOP_LEVEL_RESOURCE_QUERY = """
query TopLevelResourceQuery($selector: ResourceSelector!) {
  topLevelResourceOrError(resourceSelector: $selector) {
    __typename
    ... on TopLevelResource {
        name
        description
        configFields {
            name
            description
            configType {
                key
                ... on CompositeConfigType {
                fields {
                    name
                    configType {
                        key
                        }
                    }
                }
            }
        }
        configuredValues {
            key
            value
        }
    }
  }
}
"""


def test_fetch_top_level_resources(definitions_graphql_context, snapshot):
    selector = infer_repository_selector(definitions_graphql_context)
    result = execute_dagster_graphql(
        definitions_graphql_context,
        TOP_LEVEL_RESOURCES_QUERY,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["topLevelResourcesOrError"]
    assert result.data["topLevelResourcesOrError"]["results"]

    assert len(result.data["topLevelResourcesOrError"]["results"]) == 2

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
    assert result.data["topLevelResourceOrError"]
    my_resource = result.data["topLevelResourceOrError"]

    assert my_resource["description"] == "my description"
    assert len(my_resource["configFields"]) == 3
    assert sorted(my_resource["configuredValues"], key=lambda cv: cv["key"]) == [
        {
            "key": "a_bool",
            "value": "true",
        },
        {
            "key": "a_string",
            "value": '"foo"',
        },
    ]

    snapshot.assert_match(result.data)
