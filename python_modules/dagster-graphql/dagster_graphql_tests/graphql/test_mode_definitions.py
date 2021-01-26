import graphql
import pytest
from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from .graphql_context_test_suite import ReadonlyGraphQLContextTestMatrix
from .utils import sync_execute_get_events

MODE_QUERY = """
query ModesQuery($selector: PipelineSelector!, $mode: String!)
{
  runConfigSchemaOrError(selector: $selector, mode: $mode ) {
    __typename
    ... on RunConfigSchema {
      rootConfigType {
        key
        ... on CompositeConfigType {
          fields {
            configType {
              key
            }
          }
        }
      }
      allConfigTypes {
        key
      }
    }
    ... on PythonError {
      message
      stack
    }
  }
}
"""


def get_step_output(logs, step_key):
    for log in logs:
        if log["__typename"] == "ExecutionStepOutputEvent" and log["stepKey"] == step_key:
            return log


def execute_modes_query(context, pipeline_name, mode):
    selector = infer_pipeline_selector(context, pipeline_name)
    return execute_dagster_graphql(
        context, MODE_QUERY, variables={"selector": selector, "mode": mode,},
    )


def test_multi_mode_successful(graphql_context):
    selector = infer_pipeline_selector(graphql_context, "multi_mode_with_resources")
    add_mode_logs = sync_execute_get_events(
        context=graphql_context,
        variables={
            "executionParams": {
                "selector": selector,
                "mode": "add_mode",
                "runConfigData": {"resources": {"op": {"config": 2}}},
            }
        },
    )
    assert get_step_output(add_mode_logs, "apply_to_three")

    mult_mode_logs = sync_execute_get_events(
        context=graphql_context,
        variables={
            "executionParams": {
                "selector": selector,
                "mode": "mult_mode",
                "runConfigData": {"resources": {"op": {"config": 2}}},
            }
        },
    )
    assert get_step_output(mult_mode_logs, "apply_to_three")

    double_adder_mode_logs = sync_execute_get_events(
        context=graphql_context,
        variables={
            "executionParams": {
                "selector": selector,
                "mode": "double_adder",
                "runConfigData": {"resources": {"op": {"config": {"num_one": 2, "num_two": 4}}}},
            }
        },
    )
    get_step_output(double_adder_mode_logs, "apply_to_three")


class TestModeDefinitions(ReadonlyGraphQLContextTestMatrix):
    def test_query_multi_mode(self, graphql_context):
        with pytest.raises(graphql.error.base.GraphQLError):
            execute_modes_query(graphql_context, "multi_mode_with_resources", mode=None)

        modeful_result = execute_modes_query(
            graphql_context, "multi_mode_with_resources", mode="add_mode"
        )
        assert modeful_result.data["runConfigSchemaOrError"]["__typename"] == "RunConfigSchema"
