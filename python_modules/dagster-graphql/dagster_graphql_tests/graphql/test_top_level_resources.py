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

    assert len(result.data["allTopLevelResourceDetailsOrError"]["results"]) == 5

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

    assert my_resource["description"] == "My description."
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

    assert my_resource["description"] == "My description."
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


TOP_LEVEL_RESOURCE_USES_QUERY = """
query ResourceDetailsQuery($selector: ResourceSelector!) {
    topLevelResourceDetailsOrError(resourceSelector: $selector) {
        __typename
        ... on ResourceDetails {
            name

            schedulesUsing
            sensorsUsing

            jobsOpsUsing {
                job {
                    name
                }
                opsUsing {
                    solid {
                        name
                    }
                }
            }

            assetKeysUsing {
                path
            }
        }
    }
}
"""


def test_fetch_top_level_resource_uses(definitions_graphql_context, snapshot) -> None:
    selector = infer_resource_selector(definitions_graphql_context, name="my_resource")
    result = execute_dagster_graphql(
        definitions_graphql_context,
        TOP_LEVEL_RESOURCE_USES_QUERY,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["topLevelResourceDetailsOrError"]
    my_resource = result.data["topLevelResourceDetailsOrError"]

    assert my_resource["name"] == "my_resource"

    assert my_resource["schedulesUsing"] == ["my_schedule"]
    assert my_resource["sensorsUsing"] == ["my_sensor", "my_sensor_two"]

    jobs = my_resource["jobsOpsUsing"]
    assert len(jobs) == 1
    assert jobs[0]["job"]["name"] == "my_asset_job"
    assert len(jobs[0]["opsUsing"]) == 1
    assert jobs[0]["opsUsing"][0]["solid"]["name"] == "my_asset"

    assets = my_resource["assetKeysUsing"]
    assert len(assets) == 2
    paths = [asset["path"] for asset in assets]
    assert ["my_asset"] in paths
    assert ["my_observable_source_asset"] in paths

    snapshot.assert_match(result.data)
