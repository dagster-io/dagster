from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_repository_selector,
    infer_resource_selector,
)

TOP_LEVEL_RESOURCES_QUERY = """
query ResourceDetailsListQuery($selector: RepositorySelector!) {
  allTopLevelResourceDetailsOrError(repositorySelector: $selector) {
    __typename
    ... on ResourceDetailsList {
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
            type
        }
      }
    }
  }
}
"""

TOP_LEVEL_RESOURCE_QUERY = """
query ResourceDetailsQuery($selector: ResourceSelector!) {
  topLevelResourceDetailsOrError(resourceSelector: $selector) {
    __typename
    ... on ResourceDetails {
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
            type
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
    assert result.data["allTopLevelResourceDetailsOrError"]
    assert result.data["allTopLevelResourceDetailsOrError"]["results"]

    assert len(result.data["allTopLevelResourceDetailsOrError"]["results"]) == 4

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

    assert my_resource["description"] == "my description"
    assert len(my_resource["configFields"]) == 2
    assert sorted(my_resource["configuredValues"], key=lambda cv: cv["key"]) == [
        {
            "key": "a_string",
            "value": '"foo"',
            "type": "VALUE",
        },
        {
            "key": "an_unset_string",
            "value": '"defaulted"',
            "type": "VALUE",
        },
    ]

    snapshot.assert_match(result.data)


def test_fetch_top_level_resource_env_var(definitions_graphql_context, snapshot):
    selector = infer_resource_selector(definitions_graphql_context, name="my_resource_env_vars")
    result = execute_dagster_graphql(
        definitions_graphql_context,
        TOP_LEVEL_RESOURCE_QUERY,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["topLevelResourceDetailsOrError"]
    my_resource = result.data["topLevelResourceDetailsOrError"]

    assert my_resource["description"] == "my description"
    assert len(my_resource["configFields"]) == 2
    assert sorted(my_resource["configuredValues"], key=lambda cv: cv["key"]) == [
        {
            "key": "a_string",
            "value": "MY_STRING",
            "type": "ENV_VAR",
        },
        {
            "key": "an_unset_string",
            "value": '"defaulted"',
            "type": "VALUE",
        },
    ]

    snapshot.assert_match(result.data)
