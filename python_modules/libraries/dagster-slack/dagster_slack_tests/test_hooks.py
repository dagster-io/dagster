from dagster import graph, op
from dagster_slack import slack_resource
from dagster_slack.hooks import slack_on_failure, slack_on_success
from mock import patch


class SomeUserException(Exception):
    pass


@patch("slack_sdk.WebClient.api_call")
def test_failure_hook_on_op_instance(mock_api_call):
    @op
    def passes():
        pass

    @op
    def fails():
        raise SomeUserException()

    @graph
    def call_ops():
        passes.with_hooks(hook_defs={slack_on_failure("#foo")})()
        passes.alias("op_with_hook").with_hooks(hook_defs={slack_on_failure("#foo")})()
        fails.alias("fails_without_hook")()
        fails.with_hooks(
            hook_defs={slack_on_failure(channel="#foo", dagit_base_url="localhost:3000")}
        )()

    result = call_ops.execute_in_process(
        resources={
            "slack": slack_resource.configured({"token": "xoxp-1234123412341234-12341234-1234"})
        },
        raise_on_error=False,
    )
    assert not result.success
    assert mock_api_call.call_count == 1


@patch("slack_sdk.WebClient.api_call")
def test_failure_hook_on_job(mock_api_call):
    @op
    def passes(_):
        pass

    @op
    def fails(_):
        raise SomeUserException()

    @graph
    def call_ops():
        passes()
        fails()
        fails.alias("another_failure")()

    call_ops_job = call_ops.to_job(
        hooks={slack_on_failure("#foo")},
        resource_defs={
            "slack": slack_resource.configured({"token": "xoxp-1234123412341234-12341234-1234"})
        },
    )

    result = call_ops_job.execute_in_process(raise_on_error=False)

    assert not result.success
    assert mock_api_call.call_count == 2


@patch("slack_sdk.WebClient.api_call")
def test_success_hook_on_op_instance(mock_api_call):
    def my_message_fn(_):
        return "Some custom text"

    @op
    def passes():
        pass

    @op
    def fails():
        raise SomeUserException()

    @graph
    def call_ops():
        passes.with_hooks(hook_defs={slack_on_success("#foo")})()
        passes.alias("op_with_hook").with_hooks(hook_defs={slack_on_success("#foo")})()
        passes.alias("op_without_hook")()
        fails.with_hooks(hook_defs={slack_on_success("#foo", message_fn=my_message_fn)})()

    result = call_ops.execute_in_process(
        resources={
            "slack": slack_resource.configured({"token": "xoxp-1234123412341234-12341234-1234"})
        },
        raise_on_error=False,
    )

    assert not result.success
    assert mock_api_call.call_count == 2


@patch("slack_sdk.WebClient.api_call")
def test_success_hook_on_job(mock_api_call):
    @op
    def passes(_):
        pass

    @op
    def fails(_):
        raise SomeUserException()

    @graph
    def call_ops():
        passes()
        passes.alias("another_passes")()
        fails()

    call_ops_job = call_ops.to_job(
        resource_defs={
            "slack": slack_resource.configured({"token": "xoxp-1234123412341234-12341234-1234"})
        },
        hooks={slack_on_success("#foo")},
    )
    result = call_ops_job.execute_in_process(raise_on_error=False)

    assert not result.success
    assert mock_api_call.call_count == 2
