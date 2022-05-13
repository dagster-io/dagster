from unittest import mock

from dagster import DagsterEventType, ResourceDefinition, job, op
from docs_snippets.concepts.ops_jobs_graphs.op_hooks import (
    a,
    notif_all,
    notif_all_dev,
    notif_all_prod,
    selective_notif,
    slack_message_on_failure,
    slack_message_on_success,
    test_my_success_hook,
)
from docs_snippets.concepts.ops_jobs_graphs.op_hooks_context import my_failure_hook


def test_notif_all():
    result = notif_all.execute_in_process(
        run_config={"resources": {"slack": {"config": {"token": "..."}}}},
        raise_on_error=False,
    )
    assert not result.success

    for event in result.all_node_events:
        if event.is_hook_event:
            if event.event_type == DagsterEventType.HOOK_SKIPPED:
                assert event.step_key == "a"

            if event.event_type == DagsterEventType.HOOK_COMPLETED:
                assert event.step_key == "b"


def test_selective_notif():
    result = selective_notif.execute_in_process(
        run_config={"resources": {"slack": {"config": {"token": "..."}}}},
        raise_on_error=False,
    )
    assert not result.success

    for event in result.all_node_events:
        if event.is_hook_event:
            if event.event_type == DagsterEventType.HOOK_SKIPPED:
                assert event.step_key == "a"
            if event.event_type == DagsterEventType.HOOK_COMPLETED:
                assert event.step_key == "a"


def test_notif_all_dev():
    result = notif_all_dev.execute_in_process(
        run_config={"resources": {"slack": {"config": {"token": "..."}}}},
        raise_on_error=False,
    )
    assert not result.success

    for event in result.all_node_events:
        if event.is_hook_event:
            if event.event_type == DagsterEventType.HOOK_SKIPPED:
                assert event.step_key == "a"

            if event.event_type == DagsterEventType.HOOK_COMPLETED:
                assert event.step_key == "b"


def test_notif_all_prod():
    result = notif_all_prod.execute_in_process(
        run_config={"resources": {"slack": {"config": {"token": "..."}}}},
        raise_on_error=False,
    )
    assert not result.success

    for event in result.all_node_events:
        if event.is_hook_event:
            if event.event_type == DagsterEventType.HOOK_SKIPPED:
                assert event.step_key == "a"

            if event.event_type == DagsterEventType.HOOK_COMPLETED:
                assert event.step_key == "b"


def test_hook_resource():
    slack_mock = mock.MagicMock()

    @job(
        resource_defs={"slack": ResourceDefinition.hardcoded_resource(slack_mock)},
    )
    def foo():
        a.with_hooks({slack_message_on_success, slack_message_on_failure})()

    foo.execute_in_process()
    assert slack_mock.chat_postMessage.call_count == 1


def test_failure_hook_solid_exception():
    @op
    def failed_op():
        raise Exception("my failure")

    @job(hooks={my_failure_hook})
    def foo():
        failed_op()

    result = foo.execute_in_process(raise_on_error=False)
    assert not result.success


def test_hook_testing_example():
    test_my_success_hook()
