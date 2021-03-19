from dagster.core.storage.tags import RESUME_RETRY_TAG
from dagster_graphql.client.query import (
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
    LAUNCH_PIPELINE_REEXECUTION_MUTATION,
)
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    execute_dagster_graphql_and_finish_runs,
    infer_pipeline_selector,
)

from .utils import (
    get_all_logs_for_finished_run_via_subscription,
    step_did_fail,
    step_did_not_run,
    step_did_succeed,
)


def test_dynamic_resume_reexecution(graphql_context):
    selector = infer_pipeline_selector(graphql_context, "dynamic_pipeline")
    result = execute_dagster_graphql_and_finish_runs(
        graphql_context,
        LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={
            "executionParams": {
                "selector": selector,
                "runConfigData": {
                    "solids": {"multiply_inputs": {"inputs": {"should_fail": {"value": True}}}},
                    "storage": {"filesystem": {}},
                },
                "mode": "default",
            }
        },
    )

    assert not result.errors
    assert result.data
    assert result.data["launchPipelineExecution"]["__typename"] == "LaunchPipelineRunSuccess"
    assert result.data["launchPipelineExecution"]["run"]["pipeline"]["name"] == "dynamic_pipeline"

    parent_run_id = result.data["launchPipelineExecution"]["run"]["runId"]

    logs = get_all_logs_for_finished_run_via_subscription(graphql_context, parent_run_id)[
        "pipelineRunLogs"
    ]["messages"]

    assert step_did_succeed(logs, "emit")
    assert step_did_succeed(logs, "multiply_inputs[0]")
    assert step_did_succeed(logs, "multiply_inputs[1]")
    assert step_did_fail(logs, "multiply_inputs[2]")
    assert step_did_succeed(logs, "multiply_by_two[0]")
    assert step_did_succeed(logs, "multiply_by_two[1]")

    retry_one = execute_dagster_graphql_and_finish_runs(
        graphql_context,
        LAUNCH_PIPELINE_REEXECUTION_MUTATION,
        variables={
            "executionParams": {
                "mode": "default",
                "selector": selector,
                "runConfigData": {
                    "solids": {"multiply_inputs": {"inputs": {"should_fail": {"value": True}}}},
                    "storage": {"filesystem": {}},
                    "execution": {"multiprocess": {}},
                },
                "executionMetadata": {
                    "rootRunId": parent_run_id,
                    "parentRunId": parent_run_id,
                    "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                },
            }
        },
    )
    assert not retry_one.errors
    assert retry_one.data
    assert (
        retry_one.data["launchPipelineReexecution"]["__typename"] == "LaunchPipelineRunSuccess"
    ), retry_one.data["launchPipelineReexecution"].get("message")

    run_id = retry_one.data["launchPipelineReexecution"]["run"]["runId"]

    logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
        "pipelineRunLogs"
    ]["messages"]

    assert step_did_not_run(logs, "emit")
    assert step_did_not_run(logs, "multiply_inputs[0]")
    assert step_did_not_run(logs, "multiply_inputs[1]")
    assert step_did_succeed(logs, "multiply_inputs[2]")

    assert step_did_not_run(logs, "multiply_by_two[0]")
    assert step_did_not_run(logs, "multiply_by_two[1]")
    assert step_did_succeed(logs, "multiply_by_two[2]")
    assert step_did_succeed(logs, "double_total")


def test_dynamic_full_reexecution(graphql_context):
    selector = infer_pipeline_selector(graphql_context, "dynamic_pipeline")
    result = execute_dagster_graphql_and_finish_runs(
        graphql_context,
        LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={
            "executionParams": {
                "selector": selector,
                "runConfigData": {
                    "solids": {"multiply_inputs": {"inputs": {"should_fail": {"value": True}}}},
                    "storage": {"filesystem": {}},
                },
                "mode": "default",
            }
        },
    )

    assert not result.errors
    assert result.data
    assert result.data["launchPipelineExecution"]["__typename"] == "LaunchPipelineRunSuccess"
    assert result.data["launchPipelineExecution"]["run"]["pipeline"]["name"] == "dynamic_pipeline"

    parent_run_id = result.data["launchPipelineExecution"]["run"]["runId"]

    logs = get_all_logs_for_finished_run_via_subscription(graphql_context, parent_run_id)[
        "pipelineRunLogs"
    ]["messages"]

    assert step_did_succeed(logs, "emit")
    assert step_did_succeed(logs, "multiply_inputs[0]")
    assert step_did_succeed(logs, "multiply_inputs[1]")
    assert step_did_fail(logs, "multiply_inputs[2]")
    assert step_did_succeed(logs, "multiply_by_two[0]")
    assert step_did_succeed(logs, "multiply_by_two[1]")

    retry_one = execute_dagster_graphql_and_finish_runs(
        graphql_context,
        LAUNCH_PIPELINE_REEXECUTION_MUTATION,
        variables={
            "executionParams": {
                "mode": "default",
                "selector": selector,
                "runConfigData": {
                    "solids": {"multiply_inputs": {"inputs": {"should_fail": {"value": True}}}},
                    "storage": {"filesystem": {}},
                    "execution": {"multiprocess": {}},
                },
                "executionMetadata": {
                    "rootRunId": parent_run_id,
                    "parentRunId": parent_run_id,
                },
                "stepKeys": None,
            }
        },
    )
    assert not retry_one.errors
    assert retry_one.data
    assert (
        retry_one.data["launchPipelineReexecution"]["__typename"] == "LaunchPipelineRunSuccess"
    ), retry_one.data["launchPipelineReexecution"].get("message")

    run_id = retry_one.data["launchPipelineReexecution"]["run"]["runId"]

    logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
        "pipelineRunLogs"
    ]["messages"]

    assert step_did_succeed(logs, "emit")
    assert step_did_succeed(logs, "multiply_inputs[0]")
    assert step_did_succeed(logs, "multiply_inputs[1]")
    assert step_did_succeed(logs, "multiply_inputs[2]")

    assert step_did_succeed(logs, "multiply_by_two[0]")
    assert step_did_succeed(logs, "multiply_by_two[1]")
    assert step_did_succeed(logs, "multiply_by_two[2]")
    assert step_did_succeed(logs, "double_total")


def test_dynamic_subset(graphql_context):
    selector = infer_pipeline_selector(graphql_context, "dynamic_pipeline")
    result = execute_dagster_graphql_and_finish_runs(
        graphql_context,
        LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={
            "executionParams": {
                "selector": selector,
                "runConfigData": {
                    "solids": {"multiply_inputs": {"inputs": {"should_fail": {"value": True}}}},
                    "storage": {"filesystem": {}},
                },
                "mode": "default",
            }
        },
    )

    assert not result.errors
    assert result.data
    assert result.data["launchPipelineExecution"]["__typename"] == "LaunchPipelineRunSuccess"
    assert result.data["launchPipelineExecution"]["run"]["pipeline"]["name"] == "dynamic_pipeline"

    parent_run_id = result.data["launchPipelineExecution"]["run"]["runId"]

    logs = get_all_logs_for_finished_run_via_subscription(graphql_context, parent_run_id)[
        "pipelineRunLogs"
    ]["messages"]

    assert step_did_succeed(logs, "emit")
    assert step_did_succeed(logs, "multiply_inputs[0]")
    assert step_did_succeed(logs, "multiply_inputs[1]")
    assert step_did_fail(logs, "multiply_inputs[2]")
    assert step_did_succeed(logs, "multiply_by_two[0]")
    assert step_did_succeed(logs, "multiply_by_two[1]")

    retry_one = execute_dagster_graphql_and_finish_runs(
        graphql_context,
        LAUNCH_PIPELINE_REEXECUTION_MUTATION,
        variables={
            "executionParams": {
                "mode": "default",
                "selector": selector,
                "runConfigData": {
                    "solids": {"multiply_inputs": {"inputs": {"should_fail": {"value": True}}}},
                    "storage": {"filesystem": {}},
                    "execution": {"multiprocess": {}},
                },
                "executionMetadata": {
                    "rootRunId": parent_run_id,
                    "parentRunId": parent_run_id,
                },
                # manual version of from-failure above
                "stepKeys": [
                    "multiply_inputs[2]",
                    "multiply_by_two[2]",
                    "sum_numbers",
                    "double_total",
                ],
            }
        },
    )
    assert not retry_one.errors
    assert retry_one.data
    assert (
        retry_one.data["launchPipelineReexecution"]["__typename"] == "LaunchPipelineRunSuccess"
    ), retry_one.data["launchPipelineReexecution"].get("message")

    run_id = retry_one.data["launchPipelineReexecution"]["run"]["runId"]

    logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
        "pipelineRunLogs"
    ]["messages"]

    assert step_did_not_run(logs, "emit")
    assert step_did_not_run(logs, "multiply_inputs[0]")
    assert step_did_not_run(logs, "multiply_inputs[1]")
    assert step_did_succeed(logs, "multiply_inputs[2]")

    assert step_did_not_run(logs, "multiply_by_two[0]")
    assert step_did_not_run(logs, "multiply_by_two[1]")
    assert step_did_succeed(logs, "multiply_by_two[2]")
    assert step_did_succeed(logs, "double_total")


DEP_QUERY = """
query PresetsQuery($selector: PipelineSelector!) {
  pipelineOrError(params: $selector) {
    ... on Pipeline {
      name
      solids {
        name
        isDynamicMapped
        inputs {
          isDynamicCollect
          dependsOn {
            solid { name }
          }
        }
        outputs {
          definition {
            name
            isDynamic
          }
        }
      }
    }
  }
}
"""


def test_dynamic_dep_fields(graphql_context):
    selector = infer_pipeline_selector(graphql_context, "dynamic_pipeline")
    result = execute_dagster_graphql(graphql_context, DEP_QUERY, variables={"selector": selector})
    assert not result.errors
    solids = {solid["name"]: solid for solid in result.data["pipelineOrError"]["solids"]}

    assert solids["emit_ten"]["isDynamicMapped"] == False
    assert solids["emit_ten"]["outputs"][0]["definition"]["isDynamic"] == False

    assert solids["emit"]["isDynamicMapped"] == False
    assert solids["emit"]["outputs"][0]["definition"]["isDynamic"] == True

    assert solids["multiply_inputs"]["isDynamicMapped"] == True

    assert solids["multiply_by_two"]["isDynamicMapped"] == True

    assert solids["sum_numbers"]["isDynamicMapped"] == False
    assert solids["sum_numbers"]["inputs"][0]["isDynamicCollect"] == True

    assert solids["double_total"]["isDynamicMapped"] == False
    assert solids["double_total"]["inputs"][0]["isDynamicCollect"] == False
