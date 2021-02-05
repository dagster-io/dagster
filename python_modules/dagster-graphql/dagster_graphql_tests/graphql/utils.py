from dagster import DagsterEventType, check
from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION, SUBSCRIPTION_QUERY
from dagster_graphql.implementation.context import RequestContext
from dagster_graphql.test.utils import execute_dagster_graphql


def get_all_logs_for_finished_run_via_subscription(context, run_id):
    """
    You should almost certainly ensure that this run has complete or terminated in order
    to get reliable results that you can test against.
    """
    check.inst_param(context, "context", RequestContext)

    run = context.instance.get_run_by_id(run_id)

    assert run.is_finished

    subscription = execute_dagster_graphql(context, SUBSCRIPTION_QUERY, variables={"runId": run_id})
    subscribe_results = []

    subscription.subscribe(subscribe_results.append)
    assert len(subscribe_results) == 1
    subscribe_result = subscribe_results[0]
    if subscribe_result.errors:
        raise Exception(subscribe_result.errors)
    assert not subscribe_result.errors
    assert subscribe_result.data

    # remove information that changes run-to-run
    assert "pipelineRunLogs" in subscribe_result.data
    assert "messages" in subscribe_result.data["pipelineRunLogs"]
    for msg in subscribe_result.data["pipelineRunLogs"]["messages"]:
        msg["runId"] = "<runId dummy value>"
        msg["timestamp"] = "<timestamp dummy value>"

    return subscribe_result.data


def sync_execute_get_payload(variables, context):
    check.inst_param(context, "context", RequestContext)

    result = execute_dagster_graphql(
        context, LAUNCH_PIPELINE_EXECUTION_MUTATION, variables=variables
    )

    assert result.data

    if result.data["launchPipelineExecution"]["__typename"] != "LaunchPipelineRunSuccess":
        raise Exception(result.data)

    context.instance.run_launcher.join()

    run_id = result.data["launchPipelineExecution"]["run"]["runId"]
    return get_all_logs_for_finished_run_via_subscription(context, run_id)


def sync_execute_get_run_log_data(variables, context):
    check.inst_param(context, "context", RequestContext)
    payload_data = sync_execute_get_payload(variables, context)
    return payload_data["pipelineRunLogs"]


def sync_execute_get_events(variables, context):
    check.inst_param(context, "context", RequestContext)
    return sync_execute_get_run_log_data(variables, context)["messages"]


def step_started(logs, step_key):
    return any(
        log["stepKey"] == step_key
        for log in logs
        if log["__typename"] in ("ExecutionStepStartEvent",)
    )


def step_did_not_run(logs, step_key):
    return not any(
        log["stepKey"] == step_key
        for log in logs
        if log["__typename"]
        in ("ExecutionStepSuccessEvent", "ExecutionStepSkippedEvent", "ExecutionStepFailureEvent")
    )


def step_did_succeed(logs, step_key):
    return any(
        log["__typename"] == "ExecutionStepSuccessEvent" and step_key == log["stepKey"]
        for log in logs
    )


def step_did_skip(logs, step_key):
    return any(
        log["__typename"] == "ExecutionStepSkippedEvent" and step_key == log["stepKey"]
        for log in logs
    )


def step_did_fail(logs, step_key):
    return any(
        log["__typename"] == "ExecutionStepFailureEvent" and step_key == log["stepKey"]
        for log in logs
    )


def step_did_fail_in_records(records, step_key):
    return any(
        record.step_key == step_key
        and record.dagster_event.event_type_value == DagsterEventType.STEP_FAILURE.value
        for record in records
        if record.is_dagster_event
    )


def step_did_succeed_in_records(records, step_key):
    return any(
        record.step_key == step_key
        and record.dagster_event.event_type_value == DagsterEventType.STEP_SUCCESS.value
        for record in records
        if record.is_dagster_event
    )


def step_did_not_run_in_records(records, step_key):
    return not any(
        record.step_key == step_key
        and record.dagster_event.event_type_value
        in (
            DagsterEventType.STEP_SUCCESS.value,
            DagsterEventType.STEP_FAILURE.value,
            DagsterEventType.STEP_SKIPPED.value,
        )
        for record in records
        if record.is_dagster_event
    )
