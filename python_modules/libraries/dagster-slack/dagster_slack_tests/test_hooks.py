from dagster_slack import slack_resource
from dagster_slack.hooks import slack_on_failure, slack_on_success
from mock import patch

from dagster._legacy import ModeDefinition, execute_pipeline, pipeline, solid


class SomeUserException(Exception):
    pass


@patch("slack_sdk.WebClient.api_call")
def test_failure_hook_on_solid_instance(mock_api_call):
    @op
    def pass_op(_):
        pass

    @op
    def fail_op(_):
        raise SomeUserException()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"slack": slack_resource})])
    def a_pipeline():
        pass_op.with_hooks(hook_defs={slack_on_failure("#foo")})()
        pass_op.alias("solid_with_hook").with_hooks(
            hook_defs={slack_on_failure("#foo")}
        )()
        fail_op.alias("fail_op_without_hook")()
        fail_op.with_hooks(
            hook_defs={
                slack_on_failure(channel="#foo", dagit_base_url="localhost:3000")
            }
        )()

    result = execute_pipeline(
        a_pipeline,
        run_config={
            "resources": {
                "slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}
            }
        },
        raise_on_error=False,
    )
    assert not result.success
    assert mock_api_call.call_count == 1


@patch("slack_sdk.WebClient.api_call")
def test_failure_hook_decorator(mock_api_call):
    @op
    def pass_op(_):
        pass

    @op
    def fail_op(_):
        raise SomeUserException()

    @slack_on_failure("#foo")
    @pipeline(mode_defs=[ModeDefinition(resource_defs={"slack": slack_resource})])
    def a_pipeline():
        pass_op()
        fail_op()
        fail_op.alias("another_fail_op")()

    result = execute_pipeline(
        a_pipeline,
        run_config={
            "resources": {
                "slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}
            }
        },
        raise_on_error=False,
    )
    assert not result.success
    assert mock_api_call.call_count == 2


@patch("slack_sdk.WebClient.api_call")
def test_success_hook_on_solid_instance(mock_api_call):
    def my_message_fn(_):
        return "Some custom text"

    @op
    def pass_op(_):
        pass

    @op
    def fail_op(_):
        raise SomeUserException()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"slack": slack_resource})])
    def a_pipeline():
        pass_op.with_hooks(hook_defs={slack_on_success("#foo")})()
        pass_op.alias("solid_with_hook").with_hooks(
            hook_defs={slack_on_success("#foo")}
        )()
        pass_op.alias("solid_without_hook")()
        fail_op.with_hooks(
            hook_defs={slack_on_success("#foo", message_fn=my_message_fn)}
        )()

    result = execute_pipeline(
        a_pipeline,
        run_config={
            "resources": {
                "slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}
            }
        },
        raise_on_error=False,
    )
    assert not result.success
    assert mock_api_call.call_count == 2


@patch("slack_sdk.WebClient.api_call")
def test_success_hook_decorator(mock_api_call):
    @op
    def pass_op(_):
        pass

    @op
    def fail_op(_):
        raise SomeUserException()

    @slack_on_success("#foo")
    @pipeline(mode_defs=[ModeDefinition(resource_defs={"slack": slack_resource})])
    def a_pipeline():
        pass_op()
        pass_op.alias("another_pass_op")()
        fail_op()

    result = execute_pipeline(
        a_pipeline,
        run_config={
            "resources": {
                "slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}
            }
        },
        raise_on_error=False,
    )
    assert not result.success
    assert mock_api_call.call_count == 2
