import json

from dagster._core.test_utils import poll_for_finished_run
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._utils import file_relative_path
from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql, infer_job_selector

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)
from dagster_graphql_tests.graphql.utils import sync_execute_get_events

GET_EXPECTATIONS_FROM_STEP_STATS = """
query MaterializationsFromStepStatsQuery($runId: ID!) {
  runOrError(runId: $runId) {
    ... on PythonError {
      className
      message
      stack
    }
    ... on Run {
      stepStats {
        expectationResults {
            success
            label
            description
            metadataEntries {
                ... on TextMetadataEntry {
                    text
                }
                ... on JsonMetadataEntry {
                    jsonString
                }
            }
        }
      }
    }
  }
}
"""


def _create_run(
    graphql_context: WorkspaceRequestContext,
    pipeline_name: str,
) -> str:
    selector = infer_job_selector(
        graphql_context,
        pipeline_name,
    )
    result = execute_dagster_graphql(
        graphql_context,
        LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={
            "executionParams": {
                "selector": selector,
            }
        },
    )
    assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
    run_id = result.data["launchPipelineExecution"]["run"]["runId"]
    poll_for_finished_run(graphql_context.instance, run_id)
    return run_id


def get_expectation_results(logs, op_name: str):
    def _f():
        for log in logs:
            if log["__typename"] == "StepExpectationResultEvent" and log["stepKey"] == f"{op_name}":
                yield log

    return list(_f())


def get_expectation_result(logs, op_name: str):
    expt_results = get_expectation_results(logs, op_name)
    if len(expt_results) != 1:
        raise Exception("Only expected one expectation result")
    return expt_results[0]


class TestExpectations(ExecutingGraphQLContextTestMatrix):
    def test_basic_expectations_within_compute_step_events(
        self, graphql_context: WorkspaceRequestContext, snapshot
    ):
        selector = infer_job_selector(graphql_context, "job_with_expectations")
        logs = sync_execute_get_events(
            context=graphql_context,
            variables={"executionParams": {"selector": selector}},
        )

        emit_failed_expectation_event = get_expectation_result(logs, "emit_failed_expectation")
        assert emit_failed_expectation_event["expectationResult"]["success"] is False
        assert emit_failed_expectation_event["expectationResult"]["description"] == "Failure"
        failed_result_metadata = json.loads(
            emit_failed_expectation_event["expectationResult"]["metadataEntries"][0]["jsonString"]
        )
        assert emit_failed_expectation_event["expectationResult"]["label"] == "always_false"

        assert failed_result_metadata == {"reason": "Relentless pessimism."}

        emit_successful_expectation_event = get_expectation_result(
            logs, "emit_successful_expectation"
        )

        assert emit_successful_expectation_event["expectationResult"]["success"] is True
        assert emit_successful_expectation_event["expectationResult"]["description"] == "Successful"
        assert emit_successful_expectation_event["expectationResult"]["label"] == "always_true"
        successful_result_metadata = json.loads(
            emit_successful_expectation_event["expectationResult"]["metadataEntries"][0][
                "jsonString"
            ]
        )

        assert successful_result_metadata == {"reason": "Just because."}

        emit_no_metadata = get_expectation_result(logs, "emit_successful_expectation_no_metadata")
        assert not emit_no_metadata["expectationResult"]["metadataEntries"]

        snapshot.assert_match(get_expectation_results(logs, "emit_failed_expectation"))
        snapshot.assert_match(get_expectation_results(logs, "emit_successful_expectation"))
        snapshot.assert_match(
            get_expectation_results(logs, "emit_successful_expectation_no_metadata")
        )

    def test_get_expectation_results_from_step_stats(
        self, graphql_context: WorkspaceRequestContext
    ):
        run_id = _create_run(graphql_context, "job_with_expectations")
        result = execute_dagster_graphql(
            graphql_context, GET_EXPECTATIONS_FROM_STEP_STATS, {"runId": run_id}
        )
        assert result.data
        assert any(
            len(step["expectationResults"]) > 0
            and step["expectationResults"][0]
            == {
                "success": False,
                "label": "always_false",
                "description": "Failure",
                "metadataEntries": [
                    {"jsonString": json.dumps({"reason": "Relentless pessimism."})}
                ],
            }
            for step in result.data["runOrError"]["stepStats"]
        )

    def test_basic_input_output_expectations(
        self, graphql_context: WorkspaceRequestContext, snapshot
    ):
        selector = infer_job_selector(graphql_context, "csv_hello_world_with_expectations")
        logs = sync_execute_get_events(
            context=graphql_context,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": {
                        "ops": {
                            "sum_op": {
                                "inputs": {"num": file_relative_path(__file__, "../data/num.csv")}
                            }
                        }
                    },
                }
            },
        )

        expectation_results = get_expectation_results(logs, "df_expectations_op")
        assert len(expectation_results) == 2

        snapshot.assert_match(expectation_results)
