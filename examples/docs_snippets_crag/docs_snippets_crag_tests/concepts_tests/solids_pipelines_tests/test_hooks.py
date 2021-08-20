from unittest import mock

from dagster import DagsterEventType, ModeDefinition, ResourceDefinition, execute_pipeline, pipeline
from dagster.core.definitions import solid
from docs_snippets_crag.concepts.solids_pipelines.solid_hooks import (
    a,
    notif_all,
    selective_notif,
    slack_message_on_failure,
    slack_message_on_success,
    test_my_success_hook,
)
from docs_snippets_crag.concepts.solids_pipelines.solid_hooks_context import my_failure_hook


def test_notif_all_pipeline():
    result = execute_pipeline(notif_all, mode="dev", raise_on_error=False)
    assert not result.success

    for event in result.event_list:
        if event.is_hook_event:
            if event.event_type == DagsterEventType.HOOK_SKIPPED:
                assert event.step_key == "a"

            if event.event_type == DagsterEventType.HOOK_COMPLETED:
                assert event.step_key == "b"


def test_selective_notif_pipeline():
    result = execute_pipeline(selective_notif, mode="dev", raise_on_error=False)
    assert not result.success

    for event in result.event_list:
        if event.is_hook_event:
            if event.event_type == DagsterEventType.HOOK_SKIPPED:
                assert event.step_key == "a"
            if event.event_type == DagsterEventType.HOOK_COMPLETED:
                assert event.step_key == "a"


def test_hook_resource():
    slack_mock = mock.MagicMock()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                "unittest",
                resource_defs={"slack": ResourceDefinition.hardcoded_resource(slack_mock)},
            ),
        ]
    )
    def foo():
        a.with_hooks({slack_message_on_success, slack_message_on_failure})()

    execute_pipeline(foo)
    assert slack_mock.chat.post_message.call_count == 1


def test_failure_hook_solid_exception():
    @solid
    def failed_solid():
        raise Exception("my failure")

    @my_failure_hook
    @pipeline
    def foo():
        failed_solid()

    result = execute_pipeline(foo, raise_on_error=False)
    assert not result.success


def test_hook_testing_example():
    test_my_success_hook()
