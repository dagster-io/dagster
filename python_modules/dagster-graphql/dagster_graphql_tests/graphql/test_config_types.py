import json
from collections.abc import Sequence

import dagster._check as check
from dagster._config import ALL_CONFIG_BUILTINS
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._utils import file_relative_path
from dagster_graphql.test.utils import GqlResult, execute_dagster_graphql, infer_job_selector

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    NonLaunchableGraphQLContextTestMatrix,
)
from dagster_graphql_tests.graphql.repo import csv_hello_world_ops_config

CONFIG_VALIDATION_QUERY = """
query PipelineQuery(
    $runConfigData: RunConfigData,
    $pipeline: PipelineSelector!,
    $mode: String!
) {
    isPipelineConfigValid(
        runConfigData: $runConfigData,
        pipeline: $pipeline,
        mode: $mode
    ) {
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
        ... on PythonError {
            message
            stack
        }
    }
}
"""


def field_stack(error_data):
    return [
        entry["fieldName"]
        for entry in error_data["stack"]["entries"]
        if entry["__typename"] == "EvaluationStackPathEntry"
    ]


def single_error_data(result: GqlResult):
    assert len(result.data["isPipelineConfigValid"]["errors"]) == 1
    return result.data["isPipelineConfigValid"]["errors"][0]


def find_error(result: GqlResult, field_stack_to_find: Sequence[str], reason: str):
    llist = list(find_errors(result, field_stack_to_find, reason))
    assert len(llist) == 1
    return llist[0]


def find_errors(result: GqlResult, field_stack_to_find: Sequence[str], reason: str):
    error_datas = result.data["isPipelineConfigValid"]["errors"]
    for error_data in error_datas:
        if field_stack_to_find == field_stack(error_data) and error_data["reason"] == reason:
            yield error_data


def execute_config_graphql(
    context: WorkspaceRequestContext, job_name: str, run_config
) -> GqlResult:
    selector = infer_job_selector(context, job_name)
    return execute_dagster_graphql(
        context,
        CONFIG_VALIDATION_QUERY,
        {
            "runConfigData": run_config,
            "pipeline": selector,
            "mode": "default",
        },
    )


class TestConfigTypes(NonLaunchableGraphQLContextTestMatrix):
    def test_pipeline_not_found(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="nope",
            run_config={},
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "PipelineNotFoundError"
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "nope"

    def test_basic_valid_config(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="csv_hello_world",
            run_config=csv_hello_world_ops_config(),
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "PipelineConfigValidationValid"
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "csv_hello_world"

    def test_basic_valid_config_serialized_config(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="csv_hello_world",
            run_config=json.dumps(csv_hello_world_ops_config()),
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "PipelineConfigValidationValid"
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "csv_hello_world"

    def test_basic_valid_config_empty_string_config(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="csv_hello_world",
            run_config="",
        )

        assert not result.errors
        assert result.data
        assert (
            result.data["isPipelineConfigValid"]["__typename"] == "RunConfigValidationInvalid"
        ), result.data
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "csv_hello_world"

    def test_basic_valid_config_non_dict_config(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="csv_hello_world",
            run_config="daggy",
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "RunConfigValidationInvalid"
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "csv_hello_world"

    def test_root_field_not_defined(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="csv_hello_world",
            run_config={
                "ops": {
                    "sum_op": {"inputs": {"num": file_relative_path(__file__, "../data/num.csv")}}
                },
                "nope": {},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "RunConfigValidationInvalid"
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "csv_hello_world"
        errors = result.data["isPipelineConfigValid"]["errors"]
        assert len(errors) == 1
        error = errors[0]
        assert error["__typename"] == "FieldNotDefinedConfigError"
        assert error["fieldName"] == "nope"
        assert not error["stack"]["entries"]

    def test_basic_invalid_not_defined_field(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="csv_hello_world",
            run_config={"ops": {"sum_op": {"inputs": {"num": "foo.txt", "extra": "nope"}}}},
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "RunConfigValidationInvalid"
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "csv_hello_world"
        assert len(result.data["isPipelineConfigValid"]["errors"]) == 1
        error_data = result.data["isPipelineConfigValid"]["errors"][0]
        assert ["ops", "sum_op", "inputs"] == field_stack(error_data)
        assert error_data["reason"] == "FIELD_NOT_DEFINED"
        assert error_data["fieldName"] == "extra"

    def test_multiple_not_defined_fields(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="csv_hello_world",
            run_config={
                "ops": {
                    "sum_op": {
                        "inputs": {"num": "foo.txt", "extra_one": "nope", "extra_two": "nope"}
                    }
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "RunConfigValidationInvalid"
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "csv_hello_world"
        assert len(result.data["isPipelineConfigValid"]["errors"]) == 1
        error_data = result.data["isPipelineConfigValid"]["errors"][0]
        assert ["ops", "sum_op", "inputs"] == field_stack(error_data)
        assert error_data["reason"] == "FIELDS_NOT_DEFINED"
        assert error_data["fieldNames"] == ["extra_one", "extra_two"]

    def test_root_wrong_type(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(graphql_context, job_name="csv_hello_world", run_config=123)

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "RunConfigValidationInvalid"
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "csv_hello_world"
        assert len(result.data["isPipelineConfigValid"]["errors"]) == 1
        error_data = result.data["isPipelineConfigValid"]["errors"][0]
        assert error_data["reason"] == "RUNTIME_TYPE_MISMATCH"

    def test_basic_invalid_config_type_mismatch(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="csv_hello_world",
            run_config={"ops": {"sum_op": {"inputs": {"num": 123}}}},
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "RunConfigValidationInvalid"
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "csv_hello_world"
        assert len(result.data["isPipelineConfigValid"]["errors"]) == 1
        error_data = result.data["isPipelineConfigValid"]["errors"][0]
        assert error_data["message"]
        assert error_data["stack"]
        assert error_data["stack"]["entries"]
        assert error_data["reason"] == "RUNTIME_TYPE_MISMATCH"
        assert error_data["valueRep"] == "123"

        assert ["ops", "sum_op", "inputs", "num"] == field_stack(error_data)

    def test_basic_invalid_config_missing_field(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="csv_hello_world",
            run_config={"ops": {"sum_op": {"inputs": {}}}},
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "RunConfigValidationInvalid"
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "csv_hello_world"
        assert len(result.data["isPipelineConfigValid"]["errors"]) == 1
        error_data = result.data["isPipelineConfigValid"]["errors"][0]

        assert ["ops", "sum_op", "inputs"] == field_stack(error_data)
        assert error_data["reason"] == "MISSING_REQUIRED_FIELD"
        assert error_data["field"]["name"] == "num"

    def test_resource_config_works(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="required_resource_job",
            run_config={"resources": {"R1": {"config": 2}}},
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "PipelineConfigValidationValid"
        assert result.data["isPipelineConfigValid"]["pipelineName"] == "required_resource_job"

    def test_missing_resource(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="required_resource_config_job",
            run_config={"resources": {}},
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "RunConfigValidationInvalid"
        error_data = single_error_data(result)
        assert error_data["reason"] == "MISSING_REQUIRED_FIELD"
        assert error_data["field"]["name"] == "R1"

    def test_undefined_resource(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="required_resource_job",
            run_config={"resources": {"nope": {}}},
        )

        assert not result.errors
        assert result.data
        assert result.data["isPipelineConfigValid"]["__typename"] == "RunConfigValidationInvalid"
        assert {"FieldNotDefinedConfigError"} == {
            error_data["__typename"]
            for error_data in result.data["isPipelineConfigValid"]["errors"]
        }

    def test_more_complicated_works(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="more_complicated_nested_config",
            run_config={
                "ops": {
                    "op_with_multilayered_config": {
                        "config": {
                            "field_any": {"123": 123},
                            "field_one": "foo.txt",
                            "field_two": "yup",
                            "field_three": "mmmhmmm",
                            "nested_field": {"field_four_str": "yaya", "field_five_int": 234},
                        }
                    }
                }
            },
        )
        assert not result.errors
        assert result.data
        valid_data = result.data["isPipelineConfigValid"]
        assert valid_data["__typename"] == "PipelineConfigValidationValid"
        assert valid_data["pipelineName"] == "more_complicated_nested_config"

    def test_multiple_missing_fields(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="more_complicated_nested_config",
            run_config={"ops": {"op_with_multilayered_config": {"config": {}}}},
        )

        assert not result.errors
        assert result.data
        valid_data = result.data["isPipelineConfigValid"]

        assert valid_data["__typename"] == "RunConfigValidationInvalid"
        assert valid_data["pipelineName"] == "more_complicated_nested_config"
        assert len(valid_data["errors"]) == 1
        error_data = valid_data["errors"][0]
        missing_names = {field_data["name"] for field_data in error_data["fields"]}
        assert missing_names == {"nested_field", "field_one", "field_any"}
        assert field_stack(error_data) == ["ops", "op_with_multilayered_config", "config"]

    def test_more_complicated_multiple_errors(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="more_complicated_nested_config",
            run_config={
                "ops": {
                    "op_with_multilayered_config": {
                        "config": {
                            "field_any": [],
                            # 'field_one': 'foo.txt', # missing
                            "field_two": "yup",
                            "field_three": "mmmhmmm",
                            "extra_one": "kjsdkfjd",  # extra
                            "nested_field": {
                                "field_four_str": 23434,  # runtime type
                                "field_five_int": 234,
                                "extra_two": "ksjdkfjd",  # another extra
                            },
                        }
                    }
                }
            },
        )

        assert not result.errors
        assert result.data
        valid_data = result.data["isPipelineConfigValid"]

        assert valid_data["__typename"] == "RunConfigValidationInvalid"
        assert valid_data["pipelineName"] == "more_complicated_nested_config"
        assert len(valid_data["errors"]) == 4

        missing_error_one = find_error(
            result,
            ["ops", "op_with_multilayered_config", "config"],
            "MISSING_REQUIRED_FIELD",
        )
        assert ["ops", "op_with_multilayered_config", "config"] == field_stack(missing_error_one)
        assert missing_error_one["reason"] == "MISSING_REQUIRED_FIELD"
        assert missing_error_one["field"]["name"] == "field_one"

        not_defined_one = find_error(
            result, ["ops", "op_with_multilayered_config", "config"], "FIELD_NOT_DEFINED"
        )
        assert ["ops", "op_with_multilayered_config", "config"] == field_stack(not_defined_one)
        assert not_defined_one["reason"] == "FIELD_NOT_DEFINED"
        assert not_defined_one["fieldName"] == "extra_one"

        dagster_type_error = find_error(
            result,
            [
                "ops",
                "op_with_multilayered_config",
                "config",
                "nested_field",
                "field_four_str",
            ],
            "RUNTIME_TYPE_MISMATCH",
        )
        assert [
            "ops",
            "op_with_multilayered_config",
            "config",
            "nested_field",
            "field_four_str",
        ] == field_stack(dagster_type_error)
        assert dagster_type_error["reason"] == "RUNTIME_TYPE_MISMATCH"
        assert dagster_type_error["valueRep"] == "23434"

        not_defined_two = find_error(
            result,
            ["ops", "op_with_multilayered_config", "config", "nested_field"],
            "FIELD_NOT_DEFINED",
        )

        assert [
            "ops",
            "op_with_multilayered_config",
            "config",
            "nested_field",
        ] == field_stack(not_defined_two)
        assert not_defined_two["reason"] == "FIELD_NOT_DEFINED"
        assert not_defined_two["fieldName"] == "extra_two"

        # TODO: two more errors

    def test_config_list(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="job_with_list",
            run_config={"ops": {"op_with_list": {"config": [1, 2]}}},
        )

        assert not result.errors
        assert result.data
        valid_data = result.data["isPipelineConfigValid"]
        assert valid_data["__typename"] == "PipelineConfigValidationValid"
        assert valid_data["pipelineName"] == "job_with_list"

    def test_config_list_invalid(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="job_with_list",
            run_config={"ops": {"op_with_list": {"config": "foo"}}},
        )

        assert not result.errors
        assert result.data
        valid_data = result.data["isPipelineConfigValid"]
        assert valid_data["__typename"] == "RunConfigValidationInvalid"
        assert valid_data["pipelineName"] == "job_with_list"
        assert len(valid_data["errors"]) == 1
        assert ["ops", "op_with_list", "config"] == field_stack(valid_data["errors"][0])

    def test_config_list_item_invalid(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="job_with_list",
            run_config={"ops": {"op_with_list": {"config": [1, "foo"]}}},
        )

        assert not result.errors
        assert result.data
        valid_data = result.data["isPipelineConfigValid"]
        assert valid_data["__typename"] == "RunConfigValidationInvalid"
        assert valid_data["pipelineName"] == "job_with_list"
        assert len(valid_data["errors"]) == 1
        entries = valid_data["errors"][0]["stack"]["entries"]
        assert len(entries) == 4
        assert ["ops", "op_with_list", "config"] == field_stack(valid_data["errors"][0])

        last_entry = entries[3]
        assert last_entry["__typename"] == "EvaluationStackListItemEntry"
        assert last_entry["listIndex"] == 1

    def test_config_map(self, graphql_context: WorkspaceRequestContext):
        # Check validity
        result = execute_config_graphql(
            graphql_context,
            job_name="config_with_map",
            run_config={"ops": {"op_with_map_config": {"config": {"field_one": {"test": 5}}}}},
        )

        assert not result.errors
        assert result.data
        valid_data = result.data["isPipelineConfigValid"]
        assert valid_data["__typename"] == "PipelineConfigValidationValid"
        assert valid_data["pipelineName"] == "config_with_map"

        # Sanity check GraphQL result for types
        selector = infer_job_selector(graphql_context, "config_with_map")
        result = execute_dagster_graphql(
            graphql_context,
            ALL_CONFIG_TYPES_QUERY,
            {"selector": selector, "mode": "default"},
        )
        config_types_data = result.data["runConfigSchemaOrError"]["allConfigTypes"]
        # Ensure the first config type, Map(str, int, name="username") is in the result
        assert any(
            config_type_data.get("keyLabelName") == "username"
            and config_type_data.get("keyType", {}).get("key", "") == "String"
            and config_type_data.get("valueType", {}).get("key", "") == "Int"
            for config_type_data in config_types_data
        )

    def test_config_map_invalid(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="config_with_map",
            run_config={"ops": {"op_with_map_config": {"config": {"field_one": "not_a_map"}}}},
        )

        assert not result.errors
        assert result.data
        valid_data = result.data["isPipelineConfigValid"]
        assert valid_data["__typename"] == "RunConfigValidationInvalid"
        assert valid_data["pipelineName"] == "config_with_map"
        assert len(valid_data["errors"]) == 1
        assert ["ops", "op_with_map_config", "config", "field_one"] == field_stack(
            valid_data["errors"][0]
        )

    def test_config_map_key_invalid(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="config_with_map",
            run_config={"ops": {"op_with_map_config": {"config": {"field_one": {5: 5}}}}},
        )

        assert not result.errors
        assert result.data
        valid_data = result.data["isPipelineConfigValid"]
        assert valid_data["__typename"] == "RunConfigValidationInvalid"
        assert valid_data["pipelineName"] == "config_with_map"
        assert len(valid_data["errors"]) == 1
        entries = valid_data["errors"][0]["stack"]["entries"]
        assert len(entries) == 5
        assert ["ops", "op_with_map_config", "config", "field_one"] == field_stack(
            valid_data["errors"][0]
        )

        last_entry = entries[4]
        assert last_entry["__typename"] == "EvaluationStackMapKeyEntry"
        assert last_entry["mapKey"] == 5

    def test_config_map_value_invalid(self, graphql_context: WorkspaceRequestContext):
        result = execute_config_graphql(
            graphql_context,
            job_name="config_with_map",
            run_config={
                "ops": {
                    "op_with_map_config": {
                        "config": {"field_one": {"test": "not_a_valid_int_value"}}
                    }
                }
            },
        )

        assert not result.errors
        assert result.data
        valid_data = result.data["isPipelineConfigValid"]
        assert valid_data["__typename"] == "RunConfigValidationInvalid"
        assert valid_data["pipelineName"] == "config_with_map"
        assert len(valid_data["errors"]) == 1
        entries = valid_data["errors"][0]["stack"]["entries"]
        assert len(entries) == 5
        assert ["ops", "op_with_map_config", "config", "field_one"] == field_stack(
            valid_data["errors"][0]
        )

        last_entry = entries[4]
        assert last_entry["__typename"] == "EvaluationStackMapValueEntry"
        assert last_entry["mapKey"] == "test"

    def test_smoke_test_config_type_system(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "more_complicated_nested_config")
        result = execute_dagster_graphql(
            graphql_context,
            ALL_CONFIG_TYPES_QUERY,
            {"selector": selector, "mode": "default"},
        )

        config_types_data = result.data["runConfigSchemaOrError"]["allConfigTypes"]

        assert has_config_type_with_key_prefix(config_types_data, "Shape.")

        for builtin_config_type in ALL_CONFIG_BUILTINS:
            assert has_config_type(config_types_data, builtin_config_type.given_name)


def pipeline_named(result, name):
    for pipeline_data in result.data["pipelines"]["nodes"]:
        if pipeline_data["name"] == name:
            return pipeline_data
    check.failed("Did not find")


def has_config_type_with_key_prefix(config_types_data, prefix):
    for config_type_data in config_types_data:
        if config_type_data["key"].startswith(prefix):
            return True

    return False


def has_config_type(config_types_data, name):
    for config_type_data in config_types_data:
        if config_type_data.get("givenName") == name:
            return True

    return False


ALL_CONFIG_TYPES_QUERY = """
fragment configTypeFragment on ConfigType {
  __typename
  key
  description
  isSelector
  typeParamKeys
  recursiveConfigTypes {
    key
    description
    ... on CompositeConfigType {
        fields {
            name
            isRequired
            description
        }
    }
    ... on WrappingConfigType {
        ofType { key }
    }
  }
  ... on EnumConfigType {
    givenName
    values {
      value
      description
    }
  }
  ... on RegularConfigType {
    givenName
  }
  ... on CompositeConfigType {
    fields {
      name
      isRequired
      description
    }
  }
  ... on WrappingConfigType {
    ofType { key }
  }
  ... on MapConfigType {
    keyType { key }
    valueType { key }
    keyLabelName
  }
  ... on ScalarUnionConfigType {
    scalarType { key }
    nonScalarType { key }
  }
}

query allConfigTypes($selector: PipelineSelector!, $mode: String!) {
  runConfigSchemaOrError(selector: $selector, mode: $mode ) {
    ... on RunConfigSchema {
      allConfigTypes {
        ...configTypeFragment
      }
    }
  }
}
"""


def get_field_data(config_type_data, name):
    for field_data in config_type_data["fields"]:
        if field_data["name"] == name:
            return field_data


def get_field_names(config_type_data):
    return {field_data["name"] for field_data in config_type_data.get("fields", [])}
