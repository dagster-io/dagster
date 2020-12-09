import json

from dagster.utils import file_relative_path
from dagster_graphql.test.utils import infer_pipeline_selector

from .graphql_context_test_suite import ExecutingGraphQLContextTestMatrix
from .utils import sync_execute_get_events


def get_expectation_results(logs, solid_name):
    def _f():
        for log in logs:
            if log["__typename"] == "StepExpectationResultEvent" and log["stepKey"] == "{}".format(
                solid_name
            ):
                yield log

    return list(_f())


def get_expectation_result(logs, solid_name):
    expt_results = get_expectation_results(logs, solid_name)
    if len(expt_results) != 1:
        raise Exception("Only expected one expectation result")
    return expt_results[0]


class TestExpectations(ExecutingGraphQLContextTestMatrix):
    def test_basic_expectations_within_compute_step_events(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "pipeline_with_expectations")
        logs = sync_execute_get_events(
            context=graphql_context,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
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

    def test_basic_input_output_expectations(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "csv_hello_world_with_expectations")
        logs = sync_execute_get_events(
            context=graphql_context,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": {
                        "solids": {
                            "sum_solid": {
                                "inputs": {"num": file_relative_path(__file__, "../data/num.csv")}
                            }
                        }
                    },
                    "mode": "default",
                }
            },
        )

        expectation_results = get_expectation_results(logs, "df_expectations_solid")
        assert len(expectation_results) == 2

        snapshot.assert_match(expectation_results)
