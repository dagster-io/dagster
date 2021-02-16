from unittest import mock

from dagster import DagsterEventType, ModeDefinition, ResourceDefinition, execute_pipeline, pipeline

from ..repo import a, notif_all, selective_notif, slack_message_on_failure, slack_message_on_success


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
