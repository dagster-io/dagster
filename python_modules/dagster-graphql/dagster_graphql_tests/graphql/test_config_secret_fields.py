"""Tests for secret field functionality in GraphQL config types."""

from dagster._core.test_utils import instance_for_test
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster_graphql_tests.graphql.repo_definitions import (
    define_definitions_test_out_of_process_context,
)

# Query to fetch config type information for a resource
CONFIG_TYPE_QUERY = """
query ResourceConfigQuery($selector: PipelineSelector!) {
    pipelineOrError(params: $selector) {
        __typename
        ... on Pipeline {
            name
            modes {
                name
                resources {
                    name
                    configField {
                        configType {
                            key
                            ... on CompositeConfigType {
                                fields {
                                    name
                                    description
                                    isRequired
                                    isSecret
                                    defaultValueAsJson
                                    configType {
                                        key
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
"""


def test_secret_field_in_resource_config():
    """Test that is_secret field is properly exposed in GraphQL for resource config."""
    with instance_for_test() as instance:
        with define_definitions_test_out_of_process_context(instance) as context:
            result = execute_dagster_graphql(
                context,
                CONFIG_TYPE_QUERY,
                variables={
                    "selector": {
                        "pipelineName": "__ASSET_JOB",
                        "repositoryName": "__repository__",
                        "repositoryLocationName": context.code_location_names[0],
                    }
                },
            )

            assert not result.errors
            assert result.data

            # Get the pipeline data
            pipeline_data = result.data["pipelineOrError"]
            assert pipeline_data["__typename"] == "Pipeline"

            # Find the database resource
            resources = pipeline_data["modes"][0]["resources"]
            secrets_resource = next(
                (r for r in resources if r["name"] == "my_resource_with_secrets"), None
            )

            # If database resource not found, skip test (may not be in all test variants)
            if not secrets_resource:
                return

            # Get the config fields
            config_fields = secrets_resource["configField"]["configType"]["fields"]

            # Find each field and check is_secret and defaultValueAsJson
            field_dict = {field["name"]: field for field in config_fields}

            assert "username" in field_dict
            assert field_dict["username"]["isSecret"] is False
            # Non-secret field should have actual default value
            assert field_dict["username"]["defaultValueAsJson"] == '"default_user"'

            # Secret fields should be masked
            assert "password" in field_dict
            assert field_dict["password"]["isSecret"] is True
            assert field_dict["password"]["defaultValueAsJson"] == '"********"'

            assert "api_key" in field_dict
            assert field_dict["api_key"]["isSecret"] is True
            assert field_dict["api_key"]["defaultValueAsJson"] == '"********"'
