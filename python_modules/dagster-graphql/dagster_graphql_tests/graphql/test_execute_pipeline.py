import json
import time
import uuid
from typing import Any, Optional

from dagster._core.storage.dagster_run import RunsFilter
from dagster._core.test_utils import wait_for_runs_to_finish
from dagster._core.utils import make_new_run_id
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._utils import file_relative_path
from dagster_graphql.client.query import (
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
    METADATA_ENTRY_FRAGMENT,
    RUN_EVENTS_QUERY,
    SUBSCRIPTION_QUERY,
)
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    execute_dagster_graphql_subscription,
    infer_job_selector,
)
from typing_extensions import Dict

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
    ReadonlyGraphQLContextTestMatrix,
)
from dagster_graphql_tests.graphql.repo import csv_hello_world_ops_config
from dagster_graphql_tests.graphql.utils import (
    step_did_not_run,
    step_did_succeed,
    sync_execute_get_run_log_data,
)

STEP_FAILURE_EVENTS_QUERY = (
    """
query pipelineRunEvents($runId: ID!) {
  logsForRun(runId: $runId) {
    __typename
    ... on EventConnection {
      events {
        __typename
        ... on ExecutionStepFailureEvent {
          stepKey
          message
          level
          failureMetadata {
            metadataEntries {
              ...metadataEntryFragment
            }
          }
          error {
            message
            className
            stack
            causes {
              message
              className
              stack
            }
            errorChain {
              error {
                message
                stack
              }
              isExplicitLink
            }
          }
        }
      }
      cursor
    }
  }
}
"""
    + METADATA_ENTRY_FRAGMENT
)


class TestExecutePipeline(ExecutingGraphQLContextTestMatrix):
    def test_start_pipeline_execution(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_ops_config(),
                }
            },
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
        assert uuid.UUID(result.data["launchPipelineExecution"]["run"]["runId"])
        assert (
            result.data["launchPipelineExecution"]["run"]["pipeline"]["name"] == "csv_hello_world"
        )

    def test_start_pipeline_execution_serialized_config(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": json.dumps(csv_hello_world_ops_config()),
                }
            },
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
        assert uuid.UUID(result.data["launchPipelineExecution"]["run"]["runId"])
        assert (
            result.data["launchPipelineExecution"]["run"]["pipeline"]["name"] == "csv_hello_world"
        )

    def test_start_pipeline_execution_malformed_config(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": '{"foo": {{{{',
                }
            },
        )

        assert not result.errors
        assert result.data

        assert result.data["launchPipelineExecution"]["__typename"] == "PythonError"
        assert "yaml.parser.ParserError" in result.data["launchPipelineExecution"]["message"]

    def test_basic_start_pipeline_execution_with_pipeline_def_tags(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(graphql_context, "hello_world_with_tags")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                },
            },
        )

        assert not result.errors
        tags_by_key = {
            tag["key"]: tag["value"]
            for tag in result.data["launchPipelineExecution"]["run"]["tags"]
        }
        assert tags_by_key["tag_key"] == "tag_value"

        # just test existence
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
        assert uuid.UUID(result.data["launchPipelineExecution"]["run"]["runId"])
        assert (
            result.data["launchPipelineExecution"]["run"]["pipeline"]["name"]
            == "hello_world_with_tags"
        )

        # ensure provided tags override def tags
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "executionMetadata": {
                        "tags": [{"key": "tag_key", "value": "new_tag_value"}],
                    },
                },
            },
        )

        assert not result.errors

        tags_by_key = {
            tag["key"]: tag["value"]
            for tag in result.data["launchPipelineExecution"]["run"]["tags"]
        }
        assert tags_by_key["tag_key"] == "new_tag_value"

    def test_basic_start_pipeline_execution_with_non_existent_preset(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(graphql_context, "csv_hello_world")

        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "preset": "undefined_preset",
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPipelineExecution"]["__typename"] == "PresetNotFoundError"
        assert (
            result.data["launchPipelineExecution"]["message"]
            == "Preset undefined_preset not found in pipeline csv_hello_world."
        )

    def test_basic_start_pipeline_execution_config_failure(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": {"ops": {"sum_op": {"inputs": {"num": 384938439}}}},
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPipelineExecution"]["__typename"] == "RunConfigValidationInvalid"

    def test_basis_start_pipeline_not_found_error(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "sjkdfkdjkf")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": {"ops": {"sum_op": {"inputs": {"num": "test.csv"}}}},
                }
            },
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert result.data["launchPipelineExecution"]["__typename"] == "PipelineNotFoundError"
        assert result.data["launchPipelineExecution"]["pipelineName"] == "sjkdfkdjkf"

    def _csv_hello_world_event_sequence(self):
        # expected non engine event sequence from executing csv_hello_world pipeline

        return [
            "RunStartingEvent",
            "RunStartEvent",
            "ResourceInitStartedEvent",
            "ResourceInitSuccessEvent",
            "LogsCapturedEvent",
            "ExecutionStepStartEvent",
            "ExecutionStepInputEvent",
            "ExecutionStepOutputEvent",
            "LogMessageEvent",
            "HandledOutputEvent",
            "ExecutionStepSuccessEvent",
            "ExecutionStepStartEvent",
            "LogMessageEvent",
            "LoadedInputEvent",
            "ExecutionStepInputEvent",
            "ExecutionStepOutputEvent",
            "LogMessageEvent",
            "HandledOutputEvent",
            "ExecutionStepSuccessEvent",
            "RunSuccessEvent",
        ]

    def _legacy_csv_hello_world_event_sequence(self):
        # same as above, but matching when the instance has a legacy compute log manager which emits
        # event for every step

        return [
            "RunStartingEvent",
            "RunStartEvent",
            "ResourceInitStartedEvent",
            "ResourceInitSuccessEvent",
            "LogsCapturedEvent",
            "ExecutionStepStartEvent",
            "ExecutionStepInputEvent",
            "ExecutionStepOutputEvent",
            "LogMessageEvent",
            "HandledOutputEvent",
            "ExecutionStepSuccessEvent",
            "LogsCapturedEvent",
            "ExecutionStepStartEvent",
            "LogMessageEvent",
            "LoadedInputEvent",
            "ExecutionStepInputEvent",
            "ExecutionStepOutputEvent",
            "LogMessageEvent",
            "HandledOutputEvent",
            "ExecutionStepSuccessEvent",
            "RunSuccessEvent",
        ]

    def test_basic_start_pipeline_execution_and_subscribe(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        run_logs = sync_execute_get_run_log_data(
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

        assert run_logs["__typename"] == "PipelineRunLogsSubscriptionSuccess"
        non_engine_event_types = [
            message["__typename"]
            for message in run_logs["messages"]
            if message["__typename"] not in ("EngineEvent", "RunEnqueuedEvent", "RunDequeuedEvent")
        ]

        assert (
            non_engine_event_types == self._csv_hello_world_event_sequence()
            or non_engine_event_types == self._legacy_csv_hello_world_event_sequence()
        )

    def test_basic_start_pipeline_and_fetch(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        exc_result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
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

        assert not exc_result.errors
        assert exc_result.data
        assert exc_result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        # block until run finishes
        wait_for_runs_to_finish(graphql_context.instance)

        events_result = execute_dagster_graphql(
            graphql_context,
            RUN_EVENTS_QUERY,
            variables={"runId": exc_result.data["launchPipelineExecution"]["run"]["runId"]},
        )

        assert not events_result.errors
        assert events_result.data
        assert events_result.data["logsForRun"]["__typename"] == "EventConnection"

        non_engine_event_types = [
            message["__typename"]
            for message in events_result.data["logsForRun"]["events"]
            if message["__typename"] not in ("EngineEvent", "RunEnqueuedEvent", "RunDequeuedEvent")
        ]
        assert (
            non_engine_event_types == self._csv_hello_world_event_sequence()
            or non_engine_event_types == self._legacy_csv_hello_world_event_sequence()
        )

    def test_basic_start_pipeline_and_poll(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        exc_result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
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

        assert not exc_result.errors
        assert exc_result.data
        assert exc_result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        def _fetch_events(cursor):
            events_result = execute_dagster_graphql(
                graphql_context,
                RUN_EVENTS_QUERY,
                variables={
                    "runId": exc_result.data["launchPipelineExecution"]["run"]["runId"],
                    "cursor": cursor,
                },
            )
            assert not events_result.errors
            assert events_result.data
            assert events_result.data["logsForRun"]["__typename"] == "EventConnection"
            return (
                events_result.data["logsForRun"]["events"],
                events_result.data["logsForRun"]["cursor"],
            )

        full_logs = []
        cursor = None
        iters = 0

        # do 3 polls, then fetch after waiting for execution to finish
        while iters < 3:
            _events, _cursor = _fetch_events(cursor)
            full_logs.extend(_events)
            cursor = _cursor
            iters += 1
            time.sleep(0.05)  # 50ms

        # block until run finishes
        wait_for_runs_to_finish(graphql_context.instance)
        _events, _cursor = _fetch_events(cursor)
        full_logs.extend(_events)

        non_engine_event_types = [
            message["__typename"]
            for message in full_logs
            if message["__typename"] not in ("EngineEvent", "RunEnqueuedEvent", "RunDequeuedEvent")
        ]
        assert (
            non_engine_event_types == self._csv_hello_world_event_sequence()
            or non_engine_event_types == self._legacy_csv_hello_world_event_sequence()
        )

    def test_step_failure(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "naughty_programmer_job")

        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                }
            },
        )

        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess", str(
            result.data
        )
        run_id = result.data["launchPipelineExecution"]["run"]["runId"]

        wait_for_runs_to_finish(graphql_context.instance)

        logs_result = execute_dagster_graphql(
            graphql_context,
            STEP_FAILURE_EVENTS_QUERY,
            variables={
                "runId": run_id,
            },
        )

        assert not logs_result.errors
        assert logs_result.data
        assert logs_result.data["logsForRun"]["__typename"] == "EventConnection"

        run_logs = logs_result.data["logsForRun"]["events"]

        step_run_log_entry = _get_step_run_log_entry(
            run_logs, "throw_a_thing", "ExecutionStepFailureEvent"
        )

        assert step_run_log_entry

        assert step_run_log_entry["message"] == 'Execution of step "throw_a_thing" failed.'
        assert step_run_log_entry["error"]
        assert step_run_log_entry["level"] == "ERROR"

        assert step_run_log_entry["failureMetadata"]
        assert step_run_log_entry["failureMetadata"]["metadataEntries"] == [
            {
                "__typename": "BoolMetadataEntry",
                "label": "top_level",
                "description": None,
                "boolValue": True,
            }
        ]

        causes = step_run_log_entry["error"]["causes"]
        assert len(causes) == 2
        assert [cause["message"] for cause in causes] == [
            "Exception: Outer exception\n",
            "Exception: bad programmer, bad\n",
        ]
        assert all([len(cause["stack"]) > 0 for cause in causes])

        error_chain = step_run_log_entry["error"]["errorChain"]
        assert len(error_chain) == 3
        assert [
            (chain_link["error"]["message"], chain_link["isExplicitLink"])
            for chain_link in error_chain
        ] == [
            ("Exception: Outer exception\n", True),
            ("Exception: bad programmer, bad\n", True),
            ("Exception: The inner sanctum\n", False),
        ]

    def test_subscribe_bad_run_id(self, graphql_context: WorkspaceRequestContext):
        run_id = make_new_run_id()
        subscribe_results = execute_dagster_graphql_subscription(
            graphql_context, SUBSCRIPTION_QUERY, variables={"runId": run_id}
        )

        assert len(subscribe_results) == 1
        subscribe_result = subscribe_results[0]

        assert (
            subscribe_result.data["pipelineRunLogs"]["__typename"]
            == "PipelineRunLogsSubscriptionFailure"
        )
        assert subscribe_result.data["pipelineRunLogs"]["missingRunId"] == run_id

    def test_basic_sync_execution_no_config(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "no_config_job")
        result = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": None,
                }
            },
        )
        logs = result["messages"]
        assert isinstance(logs, list)
        assert has_event_of_type(logs, "RunStartEvent")
        assert has_event_of_type(logs, "RunSuccessEvent")
        assert not has_event_of_type(logs, "RunFailureEvent")

    def test_basic_filesystem_sync_execution(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        result = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_ops_config(),
                }
            },
        )

        logs = result["messages"]
        assert isinstance(logs, list)
        assert has_event_of_type(logs, "RunStartEvent")
        assert has_event_of_type(logs, "RunSuccessEvent")
        assert not has_event_of_type(logs, "RunFailureEvent")

        run_start_event = first_event_of_type(logs, "RunStartEvent")
        assert run_start_event and run_start_event["level"] == "DEBUG"

        sum_op_output = get_step_output_event(logs, "sum_op")
        assert sum_op_output
        assert sum_op_output["stepKey"] == "sum_op"
        assert sum_op_output["outputName"] == "result"

    def test_basic_start_pipeline_execution_with_tags(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_ops_config(),
                    "executionMetadata": {
                        "tags": [{"key": "dagster/test_key", "value": "test_value"}]
                    },
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        run = result.data["launchPipelineExecution"]["run"]
        run_id = run["runId"]
        assert len(run["tags"]) > 0
        assert any(
            [x["key"] == "dagster/test_key" and x["value"] == "test_value" for x in run["tags"]]
        )

        # Check run storage
        runs_with_tag = graphql_context.instance.get_runs(
            filters=RunsFilter(tags={"dagster/test_key": "test_value"})
        )
        assert len(runs_with_tag) == 1
        assert runs_with_tag[0].run_id == run_id

    def test_start_job_execution_with_default_config(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(graphql_context, "job_with_default_config")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                }
            },
        )
        # should succeed for this job, even when not providing config because it should
        # pick up the job default run_config
        assert not result.errors
        assert result.data
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

    def test_two_ins_job_subset_and_config(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "two_ins_job", ["op_1", "op_with_2_ins"])
        run_config = {
            "ops": {"op_with_2_ins": {"inputs": {"in_2": {"value": 2}}}},
        }
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": run_config,
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
        assert set(result.data["launchPipelineExecution"]["run"]["resolvedOpSelection"]) == set(
            [
                "op_1",
                "op_with_2_ins",
            ]
        )

    def test_nested_graph_op_selection_and_config(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(
            graphql_context, "nested_job", ["subgraph.adder", "subgraph.op_1"]
        )
        run_config = {"ops": {"subgraph": {"ops": {"adder": {"inputs": {"num2": 20}}}}}}
        result = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": run_config,
                }
            },
        )
        logs = result["messages"]
        assert isinstance(logs, list)
        assert step_did_succeed(logs, "subgraph.adder")
        assert step_did_succeed(logs, "subgraph.op_1")
        assert step_did_not_run(logs, "plus_one")
        assert step_did_not_run(logs, "subgraph.op_2")

    def test_nested_graph_op_selection_and_config_with_non_null_asset_and_check_selection(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(
            graphql_context,
            "nested_job",
            ["subgraph.adder", "subgraph.op_1"],
            asset_selection=[],
            asset_check_selection=[],
        )
        run_config = {"ops": {"subgraph": {"ops": {"adder": {"inputs": {"num2": 20}}}}}}
        result = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": run_config,
                }
            },
        )
        logs = result["messages"]
        assert isinstance(logs, list)
        assert step_did_succeed(logs, "subgraph.adder")
        assert step_did_succeed(logs, "subgraph.op_1")
        assert step_did_not_run(logs, "plus_one")
        assert step_did_not_run(logs, "subgraph.op_2")


def _get_step_run_log_entry(pipeline_run_logs, step_key, typename):
    for message_data in pipeline_run_logs:
        if message_data["__typename"] == typename:
            if message_data["stepKey"] == step_key:
                return message_data


def first_event_of_type(logs, message_type) -> Optional[Dict[str, Any]]:
    for log in logs:
        if log["__typename"] == message_type:
            return log
    return None


def has_event_of_type(logs, message_type):
    return first_event_of_type(logs, message_type) is not None


def get_step_output_event(logs, step_key, output_name="result"):
    for log in logs:
        if (
            log["__typename"] == "ExecutionStepOutputEvent"
            and log["stepKey"] == step_key
            and log["outputName"] == output_name
        ):
            return log

    return None


class TestExecutePipelineReadonlyFailure(ReadonlyGraphQLContextTestMatrix):
    def test_start_pipeline_execution_readonly_failure(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(graphql_context, "csv_hello_world")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_ops_config(),
                }
            },
        )

        assert not result.errors
        assert result.data

        assert result.data["launchPipelineExecution"]["__typename"] == "UnauthorizedError"
