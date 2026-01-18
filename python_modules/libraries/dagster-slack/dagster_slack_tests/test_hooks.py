from unittest.mock import patch

# Test-local hooks compatible with legacy slack_resource (WebClient)
from dagster import HookDefinition, op
from dagster._core.definitions.decorators.job_decorator import job


def legacy_slack_on_failure(channel, webserver_base_url=None):
    def _hook(context, _event_list):
        text = f"Failure! {context.op.name}"
        context.resources.slack.chat_postMessage(channel=channel, text=text)

    return HookDefinition(
        name="legacy_slack_on_failure",
        hook_fn=_hook,
        required_resource_keys={"slack"},
    )


def legacy_slack_on_success(channel, message_fn=None):
    def _hook(context, _event_list):
        text = message_fn(context) if message_fn else f"Success! {context.op.name}"
        context.resources.slack.chat_postMessage(channel=channel, text=text)

    return HookDefinition(
        name="legacy_slack_on_success",
        hook_fn=_hook,
        required_resource_keys={"slack"},
    )


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
        pass_op.with_hooks(hook_defs={legacy_slack_on_failure("#foo")})()
        fail_op.with_hooks(
            hook_defs={legacy_slack_on_failure(channel="#foo", webserver_base_url="localhost:3000")}
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

    job_with_hook = job_def.with_hooks({legacy_slack_on_failure("#foo")})
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
        pass_op.with_hooks(hook_defs={legacy_slack_on_success("#foo")})()
        fail_op.with_hooks(hook_defs={legacy_slack_on_success("#foo", message_fn=my_message_fn)})()

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

    job_with_hook = job_def.with_hooks({legacy_slack_on_success("#foo")})
    result = job_with_hook.execute_in_process(
        run_config={
            "resources": {"slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}}
        },
        raise_on_error=False,
    )
    assert not result.success
    assert mock_chat_postMessage.call_count == 1
