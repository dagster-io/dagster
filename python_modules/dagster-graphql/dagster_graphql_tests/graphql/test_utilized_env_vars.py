from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_repository_selector,
)

UTILIZED_ENV_VARS_QUERY = """
query UtilizedEnvVarsQuery($selector: RepositorySelector!) {
  utilizedEnvVarsOrError(repositorySelector: $selector) {
    __typename
    ... on EnvVarWithConsumersList{
      results {
        envVarName
        envVarConsumers {
            type
            name
        }
      }
    }
  }
}
"""


def test_get_used_env_vars(definitions_graphql_context, snapshot) -> None:
    selector = infer_repository_selector(definitions_graphql_context)
    result = execute_dagster_graphql(
        definitions_graphql_context,
        UTILIZED_ENV_VARS_QUERY,
        {"selector": selector},
    )
    assert not result.errors
    assert result.data
    assert result.data["utilizedEnvVarsOrError"]

    assert sorted(
        result.data["utilizedEnvVarsOrError"]["results"], key=lambda x: x["envVarName"]
    ) == [
        {
            "envVarName": "MY_OTHER_STRING",
            "envVarConsumers": [
                {
                    "type": "RESOURCE",
                    "name": "my_resource_two_env_vars",
                }
            ],
        },
        {
            "envVarName": "MY_STRING",
            "envVarConsumers": [
                {
                    "type": "RESOURCE",
                    "name": "my_resource_env_vars",
                },
                {
                    "type": "RESOURCE",
                    "name": "my_resource_two_env_vars",
                },
            ],
        },
    ]

    snapshot.assert_match(result.data)
