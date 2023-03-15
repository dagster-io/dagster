import os
from time import sleep

from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.storage.pipeline_run import DagsterRunStatus
from dagster._core.storage.tags import RESUME_RETRY_TAG
from dagster._core.test_utils import create_run_for_test, poll_for_finished_run
from dagster._core.utils import make_new_run_id
from dagster._seven.temp_dir import get_system_temp_directory
from dagster_graphql.client.query import (
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
    LAUNCH_PIPELINE_REEXECUTION_MUTATION,
    PIPELINE_REEXECUTION_INFO_QUERY,
)
from dagster_graphql.schema.inputs import GrapheneReexecutionStrategy
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    execute_dagster_graphql_and_finish_runs,
    infer_pipeline_selector,
)

from .graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
    ReadonlyGraphQLContextTestMatrix,
)
from .repo import csv_hello_world_solids_config, get_retry_multi_execution_params, retry_config
from .utils import (
    get_all_logs_for_finished_run_via_subscription,
    step_did_fail,
    step_did_fail_in_records,
    step_did_not_run,
    step_did_not_run_in_records,
    step_did_skip,
    step_did_succeed,
    step_did_succeed_in_records,
    step_started,
    sync_execute_get_events,
)


def first_event_of_type(logs, message_type):
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


class TestRetryExecutionReadonly(ReadonlyGraphQLContextTestMatrix):
    def test_retry_execution_permission_failure(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "eventually_successful")

        repository_location = graphql_context.get_repository_location("test")
        repository = repository_location.get_repository("test_repo")
        external_pipeline_origin = repository.get_full_external_job(
            "eventually_successful"
        ).get_external_origin()

        run_id = create_run_for_test(
            graphql_context.instance,
            "eventually_successful",
            external_pipeline_origin=external_pipeline_origin,
        ).run_id

        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "mode": "default",
                    "selector": selector,
                    "runConfigData": {},
                    "executionMetadata": {
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                        "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                    },
                }
            },
        )
        assert result.data["launchPipelineReexecution"]["__typename"] == "UnauthorizedError"


class TestRetryExecution(ExecutingGraphQLContextTestMatrix):
    def test_retry_pipeline_execution(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "eventually_successful")
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "mode": "default",
                    "selector": selector,
                    "runConfigData": retry_config(0),
                }
            },
        )

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            "pipelineRunLogs"
        ]["messages"]

        assert step_did_succeed(logs, "spawn")
        assert step_did_fail(logs, "fail")
        assert step_did_not_run(logs, "fail_2")
        assert step_did_not_run(logs, "fail_3")
        assert step_did_not_run(logs, "reset")
        assert step_did_not_run(logs, "collect")

        retry_one = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "mode": "default",
                    "selector": selector,
                    "runConfigData": retry_config(1),
                    "executionMetadata": {
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                        "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                    },
                }
            },
        )

        run_id = retry_one.data["launchPipelineReexecution"]["run"]["runId"]
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            "pipelineRunLogs"
        ]["messages"]
        assert step_did_not_run(logs, "spawn")
        assert step_did_succeed(logs, "fail")
        assert step_did_fail(logs, "fail_2")
        assert step_did_not_run(logs, "fail_3")
        assert step_did_not_run(logs, "reset")
        assert step_did_not_run(logs, "collect")

        retry_two = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "mode": "default",
                    "selector": selector,
                    "runConfigData": retry_config(2),
                    "executionMetadata": {
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                        "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                    },
                }
            },
        )

        run_id = retry_two.data["launchPipelineReexecution"]["run"]["runId"]
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            "pipelineRunLogs"
        ]["messages"]

        assert step_did_not_run(logs, "spawn")
        assert step_did_not_run(logs, "fail")
        assert step_did_succeed(logs, "fail_2")
        assert step_did_fail(logs, "fail_3")
        assert step_did_not_run(logs, "reset")
        assert step_did_not_run(logs, "collect")

        retry_three = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "mode": "default",
                    "selector": selector,
                    "runConfigData": retry_config(3),
                    "executionMetadata": {
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                        "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                    },
                }
            },
        )

        run_id = retry_three.data["launchPipelineReexecution"]["run"]["runId"]
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            "pipelineRunLogs"
        ]["messages"]

        assert step_did_not_run(logs, "spawn")
        assert step_did_not_run(logs, "fail")
        assert step_did_not_run(logs, "fail_2")
        assert step_did_succeed(logs, "fail_3")
        assert step_did_succeed(logs, "reset")
        assert step_did_succeed(logs, "collect")

    def test_retry_resource_pipeline(self, graphql_context):
        context = graphql_context
        selector = infer_pipeline_selector(graphql_context, "retry_resource_pipeline")
        result = execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "mode": "default",
                    "selector": selector,
                }
            },
        )

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        logs = get_all_logs_for_finished_run_via_subscription(context, run_id)["pipelineRunLogs"][
            "messages"
        ]
        assert step_did_succeed(logs, "start")
        assert step_did_fail(logs, "will_fail")

        retry_one = execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "mode": "default",
                    "selector": selector,
                    "executionMetadata": {
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                        "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                    },
                }
            },
        )
        run_id = retry_one.data["launchPipelineReexecution"]["run"]["runId"]
        logs = get_all_logs_for_finished_run_via_subscription(context, run_id)["pipelineRunLogs"][
            "messages"
        ]
        assert step_did_not_run(logs, "start")
        assert step_did_fail(logs, "will_fail")

    def test_retry_multi_output(self, graphql_context):
        context = graphql_context
        result = execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": get_retry_multi_execution_params(context, should_fail=True)
            },
        )

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        logs = get_all_logs_for_finished_run_via_subscription(context, run_id)["pipelineRunLogs"][
            "messages"
        ]
        assert step_did_succeed(logs, "multi")
        assert step_did_skip(logs, "child_multi_skip")
        assert step_did_fail(logs, "can_fail")
        assert step_did_not_run(logs, "child_fail")
        assert step_did_not_run(logs, "child_skip")
        assert step_did_not_run(logs, "grandchild_fail")

        retry_one = execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": get_retry_multi_execution_params(
                    context, should_fail=True, retry_id=run_id
                )
            },
        )

        run_id = retry_one.data["launchPipelineReexecution"]["run"]["runId"]
        logs = get_all_logs_for_finished_run_via_subscription(context, run_id)["pipelineRunLogs"][
            "messages"
        ]
        assert step_did_not_run(logs, "multi")
        assert step_did_not_run(logs, "child_multi_skip")
        assert step_did_fail(logs, "can_fail")
        assert step_did_not_run(logs, "child_fail")
        assert step_did_not_run(logs, "child_skip")
        assert step_did_not_run(logs, "grandchild_fail")

        retry_two = execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": get_retry_multi_execution_params(
                    context, should_fail=False, retry_id=run_id
                )
            },
        )

        run_id = retry_two.data["launchPipelineReexecution"]["run"]["runId"]
        logs = get_all_logs_for_finished_run_via_subscription(context, run_id)["pipelineRunLogs"][
            "messages"
        ]
        assert step_did_not_run(logs, "multi")
        assert step_did_not_run(logs, "child_multi_skip")
        assert step_did_succeed(logs, "can_fail")
        assert step_did_succeed(logs, "child_fail")
        assert step_did_skip(logs, "child_skip")
        assert step_did_succeed(logs, "grandchild_fail")

    def test_successful_pipeline_reexecution(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "csv_hello_world")
        run_id = make_new_run_id()
        result_one = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_solids_config(),
                    "executionMetadata": {"runId": run_id},
                    "mode": "default",
                }
            },
        )

        assert result_one.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        result = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)
        logs = result["pipelineRunLogs"]["messages"]
        assert get_step_output_event(logs, "sum_solid")
        assert get_step_output_event(logs, "sum_sq_solid")

        # retry
        new_run_id = make_new_run_id()

        result_two = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_solids_config(),
                    "stepKeys": ["sum_sq_solid"],
                    "executionMetadata": {
                        "runId": new_run_id,
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                        "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                    },
                    "mode": "default",
                }
            },
        )

        query_result = result_two.data["launchPipelineReexecution"]
        assert query_result["__typename"] == "LaunchRunSuccess"

        result = get_all_logs_for_finished_run_via_subscription(graphql_context, new_run_id)
        logs = result["pipelineRunLogs"]["messages"]

        assert isinstance(logs, list)
        assert has_event_of_type(logs, "RunStartEvent")
        assert has_event_of_type(logs, "RunSuccessEvent")
        assert not has_event_of_type(logs, "RunFailureEvent")

        assert not get_step_output_event(logs, "sum_solid")
        assert get_step_output_event(logs, "sum_sq_solid")

    def test_pipeline_reexecution_info_query(self, graphql_context, snapshot):
        context = graphql_context
        selector = infer_pipeline_selector(graphql_context, "csv_hello_world")

        run_id = make_new_run_id()
        execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_solids_config(),
                    "executionMetadata": {"runId": run_id},
                    "mode": "default",
                }
            },
        )

        # retry
        new_run_id = make_new_run_id()
        execute_dagster_graphql_and_finish_runs(
            context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_solids_config(),
                    "stepKeys": ["sum_sq_solid"],
                    "executionMetadata": {
                        "runId": new_run_id,
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                        "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                    },
                    "mode": "default",
                }
            },
        )

        result_one = execute_dagster_graphql_and_finish_runs(
            context, PIPELINE_REEXECUTION_INFO_QUERY, variables={"runId": run_id}
        )
        query_result_one = result_one.data["pipelineRunOrError"]
        assert query_result_one["__typename"] == "Run"
        assert query_result_one["stepKeysToExecute"] is None

        result_two = execute_dagster_graphql_and_finish_runs(
            context, PIPELINE_REEXECUTION_INFO_QUERY, variables={"runId": new_run_id}
        )
        query_result_two = result_two.data["pipelineRunOrError"]
        assert query_result_two["__typename"] == "Run"
        stepKeysToExecute = query_result_two["stepKeysToExecute"]
        assert stepKeysToExecute is not None
        snapshot.assert_match(stepKeysToExecute)

    def test_pipeline_reexecution_invalid_step_in_subset(self, graphql_context):
        run_id = make_new_run_id()
        selector = infer_pipeline_selector(graphql_context, "csv_hello_world")
        result_one = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_solids_config(),
                    "executionMetadata": {"runId": run_id},
                    "mode": "default",
                }
            },
        )
        assert result_one.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        # retry
        new_run_id = make_new_run_id()

        result_two = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_solids_config(),
                    "stepKeys": ["nope"],
                    "executionMetadata": {
                        "runId": new_run_id,
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                        "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                    },
                    "mode": "default",
                }
            },
        )

        query_result = result_two.data["launchPipelineReexecution"]
        assert query_result["__typename"] == "PythonError"
        assert query_result["className"] == "DagsterExecutionStepNotFoundError"
        assert "Can not build subset plan from unknown step: nope" in query_result["message"]


class TestHardFailures(ExecutingGraphQLContextTestMatrix):
    def test_retry_hard_failure(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "hard_failer")
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "mode": "default",
                    "selector": selector,
                    "runConfigData": {"solids": {"hard_fail_or_0": {"config": {"fail": True}}}},
                }
            },
        )

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            "pipelineRunLogs"
        ]["messages"]

        assert step_started(logs, "hard_fail_or_0")
        assert step_did_not_run(logs, "hard_fail_or_0")
        assert step_did_not_run(logs, "increment")

        retry = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "mode": "default",
                    "selector": selector,
                    "runConfigData": {"solids": {"hard_fail_or_0": {"config": {"fail": False}}}},
                    "executionMetadata": {
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                        "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                    },
                }
            },
        )

        run_id = retry.data["launchPipelineReexecution"]["run"]["runId"]
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            "pipelineRunLogs"
        ]["messages"]
        assert step_did_succeed(logs, "hard_fail_or_0")
        assert step_did_succeed(logs, "increment")

    def test_retry_failure_all_steps_with_reexecution_params(self, graphql_context):
        """Test with providng reexecutionParams rather than executionParams."""
        selector = infer_pipeline_selector(graphql_context, "chained_failure_pipeline")

        # trigger failure in the conditionally_fail solid
        output_file = os.path.join(
            get_system_temp_directory(), "chained_failure_pipeline_conditionally_fail"
        )
        try:
            with open(output_file, "w", encoding="utf8"):
                result = execute_dagster_graphql_and_finish_runs(
                    graphql_context,
                    LAUNCH_PIPELINE_EXECUTION_MUTATION,
                    variables={
                        "executionParams": {
                            "mode": "default",
                            "selector": selector,
                        }
                    },
                )
        finally:
            os.remove(output_file)

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        assert graphql_context.instance.get_run_by_id(run_id).status == DagsterRunStatus.FAILURE

        retry = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={"reexecutionParams": {"parentRunId": run_id, "strategy": "ALL_STEPS"}},
        )

        assert retry.data["launchPipelineReexecution"].get("run"), retry.data[
            "launchPipelineReexecution"
        ]
        run_id = retry.data["launchPipelineReexecution"]["run"]["runId"]
        assert graphql_context.instance.get_run_by_id(run_id).status == DagsterRunStatus.SUCCESS
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            "pipelineRunLogs"
        ]["messages"]
        assert step_did_succeed(logs, "always_succeed")
        assert step_did_succeed(logs, "conditionally_fail")
        assert step_did_succeed(logs, "after_failure")

    def test_retry_hard_failure_with_reexecution_params_run_config_changed(self, graphql_context):
        """Test that reexecution fails if the run config changes."""
        selector = infer_pipeline_selector(graphql_context, "chained_failure_pipeline")

        # trigger failure in the conditionally_fail solid
        output_file = os.path.join(
            get_system_temp_directory(), "chained_failure_pipeline_conditionally_fail"
        )
        try:
            with open(output_file, "w", encoding="utf8"):
                result = execute_dagster_graphql_and_finish_runs(
                    graphql_context,
                    LAUNCH_PIPELINE_EXECUTION_MUTATION,
                    variables={
                        "executionParams": {
                            "mode": "default",
                            "selector": selector,
                        }
                    },
                )
        finally:
            os.remove(output_file)

        parent_run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        parent_run = graphql_context.instance.get_run_by_id(parent_run_id)
        assert parent_run.status == DagsterRunStatus.FAILURE

        # override run config to make it fail
        graphql_context.instance.delete_run(parent_run_id)
        graphql_context.instance.add_run(parent_run._replace(run_config={"bad": "config"}))

        retry = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "reexecutionParams": {"parentRunId": parent_run_id, "strategy": "FROM_FAILURE"}
            },
        )
        assert "DagsterInvalidConfigError" in str(
            retry.data["launchPipelineReexecution"]["message"]
        )

    def test_retry_failure_with_reexecution_params(self, graphql_context):
        """Test with providng reexecutionParams rather than executionParams."""
        selector = infer_pipeline_selector(graphql_context, "chained_failure_pipeline")

        # trigger failure in the conditionally_fail solid
        output_file = os.path.join(
            get_system_temp_directory(), "chained_failure_pipeline_conditionally_fail"
        )
        try:
            with open(output_file, "w", encoding="utf8"):
                result = execute_dagster_graphql_and_finish_runs(
                    graphql_context,
                    LAUNCH_PIPELINE_EXECUTION_MUTATION,
                    variables={
                        "executionParams": {
                            "mode": "default",
                            "selector": selector,
                        }
                    },
                )
        finally:
            os.remove(output_file)

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        assert graphql_context.instance.get_run_by_id(run_id).status == DagsterRunStatus.FAILURE

        retry = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={"reexecutionParams": {"parentRunId": run_id, "strategy": "FROM_FAILURE"}},
        )

        run_id = retry.data["launchPipelineReexecution"]["run"]["runId"]
        assert graphql_context.instance.get_run_by_id(run_id).status == DagsterRunStatus.SUCCESS
        logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
            "pipelineRunLogs"
        ]["messages"]
        assert step_did_not_run(logs, "always_succeed")
        assert step_did_succeed(logs, "conditionally_fail")
        assert step_did_succeed(logs, "after_failure")


def test_graphene_reexecution_strategy():
    """Check that graphene enum has corresponding values in the ReexecutionStrategy enum."""
    for strategy in GrapheneReexecutionStrategy.__enum__:
        assert ReexecutionStrategy[strategy.value]


def _do_retry_intermediates_test(graphql_context, run_id, reexecution_run_id):
    selector = infer_pipeline_selector(graphql_context, "eventually_successful")
    logs = sync_execute_get_events(
        context=graphql_context,
        variables={
            "executionParams": {
                "mode": "default",
                "selector": selector,
                "executionMetadata": {"runId": run_id},
            }
        },
    )

    assert step_did_succeed(logs, "spawn")
    assert step_did_fail(logs, "fail")
    assert step_did_not_run(logs, "fail_2")
    assert step_did_not_run(logs, "fail_3")
    assert step_did_not_run(logs, "reset")

    retry_one = execute_dagster_graphql_and_finish_runs(
        graphql_context,
        LAUNCH_PIPELINE_REEXECUTION_MUTATION,
        variables={
            "executionParams": {
                "mode": "default",
                "selector": selector,
                "executionMetadata": {
                    "runId": reexecution_run_id,
                    "rootRunId": run_id,
                    "parentRunId": run_id,
                    "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                },
            }
        },
    )

    return retry_one


class TestRetryExecutionAsyncOnlyBehavior(ExecutingGraphQLContextTestMatrix):
    def test_retry_requires_intermediates_async_only(self, graphql_context):
        run_id = make_new_run_id()
        reexecution_run_id = make_new_run_id()

        _do_retry_intermediates_test(graphql_context, run_id, reexecution_run_id)
        reexecution_run = graphql_context.instance.get_run_by_id(reexecution_run_id)

        assert reexecution_run.is_failure_or_canceled

    def test_retry_early_terminate(self, graphql_context):
        instance = graphql_context.instance
        selector = infer_pipeline_selector(
            graphql_context, "retry_multi_input_early_terminate_pipeline"
        )
        run_id = make_new_run_id()
        execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "mode": "default",
                    "selector": selector,
                    "runConfigData": {
                        "solids": {
                            "get_input_one": {"config": {"wait_to_terminate": True}},
                            "get_input_two": {"config": {"wait_to_terminate": True}},
                        },
                    },
                    "executionMetadata": {"runId": run_id},
                }
            },
        )
        # Wait until the first step succeeded
        while instance.get_run_stats(run_id).steps_succeeded < 1:
            sleep(0.1)
        # Terminate the current pipeline run at the second step
        graphql_context.instance.run_launcher.terminate(run_id)

        records = instance.all_logs(run_id)

        # The first step should succeed, the second should fail or not start,
        # and the following steps should not appear in records
        assert step_did_succeed_in_records(records, "return_one")
        assert not step_did_fail_in_records(records, "return_one")
        assert any(
            [
                step_did_fail_in_records(records, "get_input_one"),
                step_did_not_run_in_records(records, "get_input_one"),
            ]
        )
        assert step_did_not_run_in_records(records, "get_input_two")
        assert step_did_not_run_in_records(records, "sum_inputs")

        # Wait for the original run to finish
        poll_for_finished_run(instance, run_id, timeout=30)
        assert instance.get_run_by_id(run_id).status == DagsterRunStatus.CANCELED

        # Start retry
        new_run_id = make_new_run_id()

        execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "mode": "default",
                    "selector": selector,
                    "runConfigData": {
                        "solids": {
                            "get_input_one": {"config": {"wait_to_terminate": False}},
                            "get_input_two": {"config": {"wait_to_terminate": False}},
                        },
                    },
                    "executionMetadata": {
                        "runId": new_run_id,
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                        "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
                    },
                }
            },
        )

        retry_records = instance.all_logs(new_run_id)
        # The first step should not run and the other three steps should succeed in retry
        assert step_did_not_run_in_records(retry_records, "return_one")
        assert step_did_succeed_in_records(retry_records, "get_input_one")
        assert step_did_succeed_in_records(retry_records, "get_input_two")
        assert step_did_succeed_in_records(retry_records, "sum_inputs")
