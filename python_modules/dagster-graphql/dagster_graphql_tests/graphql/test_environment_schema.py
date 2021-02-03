from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from .graphql_context_test_suite import ReadonlyGraphQLContextTestMatrix
from .setup import csv_hello_world_solids_config

RUN_CONFIG_SCHEMA_QUERY = """
query($selector: PipelineSelector! $mode: String!)
{
  runConfigSchemaOrError(selector: $selector, mode: $mode){
    __typename
    ... on RunConfigSchema {
      rootConfigType {
        key
      }
      allConfigTypes {
        key
      }
    }
  }
}
"""

RUN_CONFIG_SCHEMA_CONFIG_TYPE_QUERY = """
query($selector: PipelineSelector! $mode: String! $configTypeName: String!)
{
  runConfigSchemaOrError(selector: $selector, mode: $mode){
    __typename
    ... on RunConfigSchema {
      configTypeOrError(configTypeName: $configTypeName) {
        __typename
        ... on EnumConfigType {
          name
        }
        ... on RegularConfigType {
          name
        }
        ... on CompositeConfigType {
          name
        }
      }
    }
  }
}
"""


RUN_CONFIG_SCHEMA_CONFIG_VALIDATION_QUERY = """
query PipelineQuery(
    $runConfigData: RunConfigData,
    $selector: PipelineSelector!,
    $mode: String!
) {
  runConfigSchemaOrError(selector: $selector mode: $mode) {
    ... on RunConfigSchema {
      isRunConfigValid(runConfigData: $runConfigData) {
        __typename
        ... on PipelineConfigValidationValid {
            pipelineName
        }
        ... on PipelineConfigValidationInvalid {
            pipelineName
            errors {
                __typename
                ... on RuntimeMismatchConfigError {
                    valueRep
                }
                ... on MissingFieldConfigError {
                    field { name }
                }
                ... on MissingFieldsConfigError {
                    fields { name }
                }
                ... on FieldNotDefinedConfigError {
                    fieldName
                }
                ... on FieldsNotDefinedConfigError {
                    fieldNames
                }
                ... on SelectorTypeConfigError {
                    incomingFields
                }
                message
                reason
                stack {
                    entries {
                        __typename
                        ... on EvaluationStackPathEntry {
                            fieldName
                        }
                        ... on EvaluationStackListItemEntry {
                            listIndex
                        }
                    }
                }
            }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
      }
    }
  }
}
"""


class TestEnvironmentSchema(ReadonlyGraphQLContextTestMatrix):
    def test_successful_run_config_schema(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "multi_mode_with_resources")
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_QUERY,
            variables={
                "selector": selector,
                "mode": "add_mode",
            },
        )
        assert result.data["runConfigSchemaOrError"]["__typename"] == "RunConfigSchema"

    def test_run_config_schema_pipeline_not_found(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "jkdjfkdjfd")
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_QUERY,
            variables={"selector": selector, "mode": "add_mode"},
        )
        assert result.data["runConfigSchemaOrError"]["__typename"] == "PipelineNotFoundError"

    def test_run_config_schema_solid_not_found(self, graphql_context):
        selector = infer_pipeline_selector(
            graphql_context, "multi_mode_with_resources", ["kdjfkdj"]
        )
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_QUERY,
            variables={
                "selector": selector,
                "mode": "add_mode",
            },
        )
        assert result.data["runConfigSchemaOrError"]["__typename"] == "InvalidSubsetError"

    def test_run_config_schema_mode_not_found(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "multi_mode_with_resources")
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_QUERY,
            variables={"selector": selector, "mode": "kdjfdk"},
        )
        assert result.data["runConfigSchemaOrError"]["__typename"] == "ModeNotFoundError"

    def test_basic_valid_config_on_run_config_schema(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "csv_hello_world")
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_CONFIG_VALIDATION_QUERY,
            variables={
                "selector": selector,
                "mode": "default",
                "runConfigData": csv_hello_world_solids_config(),
            },
        )

        assert not result.errors
        assert result.data
        assert (
            result.data["runConfigSchemaOrError"]["isRunConfigValid"]["__typename"]
            == "PipelineConfigValidationValid"
        )
        snapshot.assert_match(result.data)

    def test_basic_invalid_config_on_run_config_schema(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "csv_hello_world")
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_CONFIG_VALIDATION_QUERY,
            variables={
                "selector": selector,
                "mode": "default",
                "runConfigData": {"nope": "kdjfd"},
            },
        )

        assert not result.errors
        assert result.data
        assert (
            result.data["runConfigSchemaOrError"]["isRunConfigValid"]["__typename"]
            == "PipelineConfigValidationInvalid"
        )
        snapshot.assert_match(result.data)
