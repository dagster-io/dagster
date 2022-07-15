from dagster_msteams.hooks import teams_on_failure, teams_on_success
from dagster_msteams.resources import msteams_resource
from mock import patch

from dagster import ModeDefinition, execute_pipeline
from dagster._legacy import pipeline, solid


class SomeUserException(Exception):
    pass


def my_message_fn(_):
    return "Some custom text"


@solid
def pass_solid(_):
    pass


@solid
def fail_solid(_):
    raise SomeUserException()


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_failure_hook_on_solid_instance(mock_teams_post_message):
    @pipeline(mode_defs=[ModeDefinition(resource_defs={"msteams": msteams_resource})])
    def a_pipeline():
        pass_solid.with_hooks(hook_defs={teams_on_failure()})()
        pass_solid.alias("fail_solid_with_hook").with_hooks(hook_defs={teams_on_failure()})()
        fail_solid.alias("fail_solid_without_hook")()
        fail_solid.with_hooks(
            hook_defs={teams_on_failure(message_fn=my_message_fn, dagit_base_url="localhost:3000")}
        )()

    result = execute_pipeline(
        a_pipeline,
        run_config={"resources": {"msteams": {"config": {"hook_url": "https://some_url_here/"}}}},
        raise_on_error=False,
    )
    assert not result.success
    assert mock_teams_post_message.call_count == 1


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_success_hook_on_solid_instance(mock_teams_post_message):
    @pipeline(mode_defs=[ModeDefinition(resource_defs={"msteams": msteams_resource})])
    def a_pipeline():
        pass_solid.with_hooks(hook_defs={teams_on_success()})()
        pass_solid.alias("success_solid_with_hook").with_hooks(hook_defs={teams_on_success()})()
        fail_solid.alias("success_solid_without_hook")()
        fail_solid.with_hooks(
            hook_defs={teams_on_success(message_fn=my_message_fn, dagit_base_url="localhost:3000")}
        )()

    result = execute_pipeline(
        a_pipeline,
        run_config={"resources": {"msteams": {"config": {"hook_url": "https://some_url_here/"}}}},
        raise_on_error=False,
    )
    assert not result.success
    assert mock_teams_post_message.call_count == 2


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_failure_hook_decorator(mock_teams_post_message):
    @teams_on_failure(dagit_base_url="http://localhost:3000/")
    @pipeline(mode_defs=[ModeDefinition(resource_defs={"msteams": msteams_resource})])
    def a_pipeline():
        pass_solid()
        fail_solid()
        fail_solid.alias("another_fail_solid")()

    result = execute_pipeline(
        a_pipeline,
        run_config={"resources": {"msteams": {"config": {"hook_url": "https://some_url_here/"}}}},
        raise_on_error=False,
    )
    assert not result.success
    assert mock_teams_post_message.call_count == 2


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_success_hook_decorator(mock_teams_post_message):
    @teams_on_success(message_fn=my_message_fn, dagit_base_url="http://localhost:3000/")
    @pipeline(mode_defs=[ModeDefinition(resource_defs={"msteams": msteams_resource})])
    def a_pipeline():
        pass_solid()
        pass_solid.alias("another_pass_solid")()
        fail_solid()

    result = execute_pipeline(
        a_pipeline,
        run_config={"resources": {"msteams": {"config": {"hook_url": "https://some_url_here/"}}}},
        raise_on_error=False,
    )
    assert not result.success
    assert mock_teams_post_message.call_count == 2
