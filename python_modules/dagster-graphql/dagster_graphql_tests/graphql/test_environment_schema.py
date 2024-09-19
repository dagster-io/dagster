from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.test.utils import execute_dagster_graphql, infer_job_selector

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    NonLaunchableGraphQLContextTestMatrix,
)
from dagster_graphql_tests.graphql.repo import csv_hello_world_ops_config

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
      rootDefaultYaml
    }
  }
}
"""

RUN_CONFIG_SCHEMA_ROOT_DEFAULT_YAML_QUERY = """
query($selector: PipelineSelector! $mode: String!)
{
  runConfigSchemaOrError(selector: $selector, mode: $mode){
    __typename
    ... on RunConfigSchema {
      rootDefaultYaml
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
        ... on RunConfigValidationInvalid {
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
                        ... on EvaluationStackMapKeyEntry {
                            mapKey
                        }
                        ... on EvaluationStackMapValueEntry {
                            mapKey
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


class TestEnvironmentSchema(NonLaunchableGraphQLContextTestMatrix):
    def test_successful_run_config_schema(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "required_resource_job")
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_QUERY,
            variables={
                "selector": selector,
                "mode": "default",
            },
        )
        assert result.data["runConfigSchemaOrError"]["__typename"] == "RunConfigSchema"

    def test_run_config_schema_pipeline_not_found(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "jkdjfkdjfd")
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_QUERY,
            variables={"selector": selector, "mode": "default"},
        )
        assert result.data["runConfigSchemaOrError"]["__typename"] == "PipelineNotFoundError"

    def test_run_config_schema_op_not_found(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "required_resource_job", ["kdjfkdj"])
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_QUERY,
            variables={
                "selector": selector,
                "mode": "default",
            },
        )
        assert result.data["runConfigSchemaOrError"]["__typename"] == "InvalidSubsetError"

    def test_run_config_schema_mode_not_found(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "required_resource_job")
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_QUERY,
            variables={"selector": selector, "mode": "kdjfdk"},
        )
        assert result.data["runConfigSchemaOrError"]["__typename"] == "ModeNotFoundError"

    def test_basic_valid_config_on_run_config_schema(
        self, graphql_context: WorkspaceRequestContext, snapshot
    ):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_CONFIG_VALIDATION_QUERY,
            variables={
                "selector": selector,
                "mode": "default",
                "runConfigData": csv_hello_world_ops_config(),
            },
        )

        assert not result.errors
        assert result.data
        assert (
            result.data["runConfigSchemaOrError"]["isRunConfigValid"]["__typename"]
            == "PipelineConfigValidationValid"
        )
        snapshot.assert_match(result.data)

    def test_full_yaml(self, graphql_context, snapshot):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CONFIG_SCHEMA_ROOT_DEFAULT_YAML_QUERY,
            variables={
                "selector": selector,
                "mode": "default",
                "runConfigData": csv_hello_world_ops_config(),
            },
        )

        assert result
        assert not result.errors
        assert result.data
        snapshot.assert_match(result.data)

    def test_basic_invalid_config_on_run_config_schema(
        self, graphql_context: WorkspaceRequestContext, snapshot
    ):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
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
            == "RunConfigValidationInvalid"
        )
        snapshot.assert_match(result.data)
