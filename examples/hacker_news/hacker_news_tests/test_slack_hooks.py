from dagster import (
    DagsterEventType,
    ModeDefinition,
    ResourceDefinition,
    execute_pipeline,
    pipeline,
    solid,
)
from hacker_news.hooks.slack_hooks import slack_on_success
from mock import MagicMock


def test_slack_on_success():
    @solid
    def passing_solid(_):
        pass

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "slack": ResourceDefinition.hardcoded_resource(MagicMock()),
                    "base_url": ResourceDefinition.hardcoded_resource("foo"),
                }
            )
        ]
    )
    def basic_pipeline():
        passing_solid.with_hooks(hook_defs={slack_on_success})()

    result = execute_pipeline(basic_pipeline)

    assert result.success

    assert not any(
        [event.event_type == DagsterEventType.HOOK_ERRORED for event in result.event_list]
    )
    assert any([event.event_type == DagsterEventType.HOOK_COMPLETED for event in result.event_list])
