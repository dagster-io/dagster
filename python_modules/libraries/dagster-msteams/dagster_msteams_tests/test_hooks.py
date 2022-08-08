from dagster_msteams.hooks import teams_on_failure, teams_on_success
from dagster_msteams.resources import msteams_resource
from mock import patch

from dagster import op
from dagster._legacy import ModeDefinition, execute_pipeline, pipeline


class SomeUserException(Exception):
    pass


def my_message_fn(_):
    return "Some custom text"


@op
def pass_op(_):
    pass


@op
def fail_op(_):
    raise SomeUserException()


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_failure_hook_on_solid_instance(mock_teams_post_message):
    @pipeline(mode_defs=[ModeDefinition(resource_defs={"msteams": msteams_resource})])
    def a_pipeline():
        pass_op.with_hooks(hook_defs={teams_on_failure()})()
        pass_op.alias("fail_op_with_hook").with_hooks(hook_defs={teams_on_failure()})()
        fail_op.alias("fail_op_without_hook")()
        fail_op.with_hooks(
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
        pass_op.with_hooks(hook_defs={teams_on_success()})()
        pass_op.alias("success_solid_with_hook").with_hooks(hook_defs={teams_on_success()})()
        fail_op.alias("success_solid_without_hook")()
        fail_op.with_hooks(
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
        pass_op()
        fail_op()
        fail_op.alias("another_fail_op")()

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
        pass_op()
        pass_op.alias("another_pass_op")()
        fail_op()

    result = execute_pipeline(
        a_pipeline,
        run_config={"resources": {"msteams": {"config": {"hook_url": "https://some_url_here/"}}}},
        raise_on_error=False,
    )
    assert not result.success
    assert mock_teams_post_message.call_count == 2
