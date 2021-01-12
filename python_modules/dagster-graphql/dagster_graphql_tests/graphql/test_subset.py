import re

from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from .graphql_context_test_suite import ReadonlyGraphQLContextTestMatrix

SCHEMA_OR_ERROR_SUBSET_QUERY = """
query EnvironmentQuery($selector: PipelineSelector!){
    runConfigSchemaOrError(selector: $selector) {
        __typename
        ... on RunConfigSchema {
            allConfigTypes {
                __typename
                key
                ... on CompositeConfigType {
                    __typename
                    fields {
                        __typename
                        name
                        configType {
                            key
                            __typename
                        }
                    }
                }
            }
        }
        ... on InvalidSubsetError {
            message
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""


def field_names_of(type_dict, typename):
    return {field_data["name"] for field_data in type_dict[typename]["fields"]}


def types_dict_of_result(subset_result, top_key):
    return {
        type_data["name"]: type_data for type_data in subset_result.data[top_key]["configTypes"]
    }


class TestSolidSelections(ReadonlyGraphQLContextTestMatrix):
    def test_csv_hello_world_pipeline_or_error_subset_wrong_solid_name(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "csv_hello_world", ["nope"])
        result = execute_dagster_graphql(
            graphql_context, SCHEMA_OR_ERROR_SUBSET_QUERY, {"selector": selector}
        )

        assert not result.errors
        assert result.data
        assert result.data["runConfigSchemaOrError"]["__typename"] == "InvalidSubsetError"
        assert '"nope" does not exist' in result.data["runConfigSchemaOrError"]["message"]

    def test_pipeline_with_invalid_definition_error(self, graphql_context):
        selector = infer_pipeline_selector(
            graphql_context, "pipeline_with_invalid_definition_error", ["fail_subset"]
        )
        result = execute_dagster_graphql(
            graphql_context, SCHEMA_OR_ERROR_SUBSET_QUERY, {"selector": selector}
        )
        assert not result.errors
        assert result.data
        assert result.data["runConfigSchemaOrError"]["__typename"] == "InvalidSubsetError"

        assert re.match(
            (
                r".*DagsterInvalidSubsetError[\s\S]*"
                r'add a dagster_type_loader for the type "InputTypeWithoutHydration"'
            ),
            result.data["runConfigSchemaOrError"]["message"],
        )
