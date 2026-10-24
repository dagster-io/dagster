from unittest.mock import patch

from dagster import op
from dagster._core.definitions.decorators.job_decorator import job
from dagster_slack import SlackResource
from dagster_slack.hooks import slack_on_failure, slack_on_success


class SomeUserException(Exception):
    pass


@patch("slack_sdk.WebClient.api_call")
@patch("slack_sdk.WebClient.chat_postMessage")
def test_failure_hook_on_op_instance(mock_chat_postMessage, mock_api_call):
    @op(required_resource_keys={"slack"})
    def pass_op(_):
        pass

    @op(required_resource_keys={"slack"})
    def fail_op(_):
        raise SomeUserException()

    from dagster_slack.resources import slack_resource

    @job(resource_defs={"slack": slack_resource})
    def job_def():
        pass_op.with_hooks(hook_defs={slack_on_failure("#foo")})()
        fail_op.with_hooks(
            hook_defs={slack_on_failure(channel="#foo", webserver_base_url="localhost:3000")}
        )()

    result = job_def.execute_in_process(
        run_config={
            "resources": {"slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}}
        },
        raise_on_error=False,
    )
    assert not result.success
    assert mock_chat_postMessage.call_count == 1


@patch("slack_sdk.WebClient.api_call")
@patch("slack_sdk.WebClient.chat_postMessage")
def test_failure_hook_decorator(mock_chat_postMessage, mock_api_call):
    @op(required_resource_keys={"slack"})
    def pass_op(_):
        pass

    @op(required_resource_keys={"slack"})
    def fail_op(_):
        raise SomeUserException()

    from dagster_slack.resources import slack_resource

    @job(resource_defs={"slack": slack_resource})
    def job_def():
        pass_op()
        fail_op()

    job_with_hook = job_def.with_hooks({slack_on_failure("#foo")})
    result = job_with_hook.execute_in_process(
        run_config={
            "resources": {"slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}}
        },
        raise_on_error=False,
    )
    assert not result.success
    assert mock_chat_postMessage.call_count == 1


@patch("slack_sdk.WebClient.api_call")
@patch("slack_sdk.WebClient.chat_postMessage")
def test_success_hook_on_op_instance(mock_chat_postMessage, mock_api_call):
    def my_message_fn(_):
        return "Some custom text"

    @op(required_resource_keys={"slack"})
    def pass_op(_):
        pass

    @op(required_resource_keys={"slack"})
    def fail_op(_):
        raise SomeUserException()

    from dagster_slack.resources import slack_resource

    @job(resource_defs={"slack": slack_resource})
    def job_def():
        pass_op.with_hooks(hook_defs={slack_on_success("#foo")})()
        fail_op.with_hooks(hook_defs={slack_on_success("#foo", message_fn=my_message_fn)})()

    result = job_def.execute_in_process(
        run_config={
            "resources": {"slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}}
        },
        raise_on_error=False,
    )
    assert not result.success
    assert mock_chat_postMessage.call_count == 1


@patch("slack_sdk.WebClient.api_call")
@patch("slack_sdk.WebClient.chat_postMessage")
def test_success_hook_decorator(mock_chat_postMessage, mock_api_call):
    @op(required_resource_keys={"slack"})
    def pass_op(_):
        pass

    @op(required_resource_keys={"slack"})
    def another_pass_op(_):
        pass

    @op(required_resource_keys={"slack"})
    def fail_op(_):
        raise SomeUserException()

    from dagster_slack.resources import slack_resource

    @job(resource_defs={"slack": slack_resource})
    def job_def():
        pass_op()
        another_pass_op()
        fail_op()

    job_with_hook = job_def.with_hooks({slack_on_success("#foo")})
    result = job_with_hook.execute_in_process(
        run_config={
            "resources": {"slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}}
        },
        raise_on_error=False,
    )
    assert not result.success
    assert mock_chat_postMessage.call_count == 2


@patch("slack_sdk.WebClient.api_call")
@patch("slack_sdk.WebClient.chat_postMessage")
def test_hooks_with_slack_resource_class(mock_chat_postMessage, mock_api_call):
    @op
    def pass_op():
        pass

    @op
    def fail_op():
        raise SomeUserException()

    @job(resource_defs={"slack": SlackResource(token="xoxp-1234123412341234-12341234-1234")})
    def job_def():
        pass_op.with_hooks(hook_defs={slack_on_success("#foo")})()
        fail_op.with_hooks(hook_defs={slack_on_failure("#bar")})()

    result = job_def.execute_in_process(raise_on_error=False)
    assert not result.success
    assert sorted(call.kwargs["channel"] for call in mock_chat_postMessage.call_args_list) == [
        "#bar",
        "#foo",
    ]
