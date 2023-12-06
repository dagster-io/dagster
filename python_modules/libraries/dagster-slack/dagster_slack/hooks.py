from typing import Callable, Optional

from dagster._annotations import deprecated_param
from dagster._core.definitions import failure_hook, success_hook
from dagster._core.execution.context.hook import HookContext
from dagster._utils.warnings import normalize_renamed_param


def _default_status_message(context: HookContext, status: str) -> str:
    return f"Op {context.op.name} on job {context.job_name} {status}!\nRun ID: {context.run_id}"


def _default_failure_message(context: HookContext) -> str:
    return _default_status_message(context, status="failed")


def _default_success_message(context: HookContext) -> str:
    return _default_status_message(context, status="succeeded")


@deprecated_param(
    param="dagit_base_url",
    breaking_version="2.0",
    additional_warn_text="Use `webserver_base_url` instead.",
)
def slack_on_failure(
    channel: str,
    message_fn: Callable[[HookContext], str] = _default_failure_message,
    dagit_base_url: Optional[str] = None,
    webserver_base_url: Optional[str] = None,
):
    """Create a hook on step failure events that will message the given Slack channel.

    Args:
        channel (str): The channel to send the message to (e.g. "#my_channel")
        message_fn (Optional(Callable[[HookContext], str])): Function which takes in the HookContext
            outputs the message you want to send.
        dagit_base_url: (Optional[str]): The base url of your webserver instance. Specify this to allow
            messages to include deeplinks to the specific run that triggered the hook.
        webserver_base_url: (Optional[str]): The base url of your webserver instance. Specify this to allow
            messages to include deeplinks to the specific run that triggered the hook.

    Examples:
        .. code-block:: python

            @slack_on_failure("#foo", webserver_base_url="http://localhost:3000")
            @job(...)
            def my_job():
                pass

        .. code-block:: python

            def my_message_fn(context: HookContext) -> str:
                return f"Op {context.op} failed!"

            @op
            def an_op(context):
                pass

            @job(...)
            def my_job():
                an_op.with_hooks(hook_defs={slack_on_failure("#foo", my_message_fn)})

    """
    webserver_base_url = normalize_renamed_param(
        webserver_base_url, "webserver_base_url", dagit_base_url, "dagit_base_url"
    )

    @failure_hook(required_resource_keys={"slack"})
    def _hook(context: HookContext):
        text = message_fn(context)
        if webserver_base_url:
            text += f"\n<{webserver_base_url}/runs/{context.run_id}|View in Dagster UI>"

        context.resources.slack.chat_postMessage(channel=channel, text=text)

    return _hook


@deprecated_param(
    param="dagit_base_url",
    breaking_version="2.0",
    additional_warn_text="Use `webserver_base_url` instead.",
)
def slack_on_success(
    channel: str,
    message_fn: Callable[[HookContext], str] = _default_success_message,
    dagit_base_url: Optional[str] = None,
    webserver_base_url: Optional[str] = None,
):
    """Create a hook on step success events that will message the given Slack channel.

    Args:
        channel (str): The channel to send the message to (e.g. "#my_channel")
        message_fn (Optional(Callable[[HookContext], str])): Function which takes in the HookContext
            outputs the message you want to send.
        dagit_base_url: (Optional[str]): The base url of your webserver instance. Specify this to allow
            messages to include deeplinks to the specific run that triggered the hook.
        webserver_base_url: (Optional[str]): The base url of your webserver instance. Specify this to allow
            messages to include deeplinks to the specific run that triggered the hook.

    Examples:
        .. code-block:: python

            @slack_on_success("#foo", webserver_base_url="http://localhost:3000")
            @job(...)
            def my_job():
                pass

        .. code-block:: python

            def my_message_fn(context: HookContext) -> str:
                return f"Op {context.op} worked!"

            @op
            def an_op(context):
                pass

            @job(...)
            def my_job():
                an_op.with_hooks(hook_defs={slack_on_success("#foo", my_message_fn)})

    """
    webserver_base_url = normalize_renamed_param(
        webserver_base_url, "webserver_base_url", dagit_base_url, "dagit_base_url"
    )

    @success_hook(required_resource_keys={"slack"})
    def _hook(context: HookContext):
        text = message_fn(context)
        if webserver_base_url:
            text += f"\n<{webserver_base_url}/runs/{context.run_id}|View in Dagster UI>"

        context.resources.slack.chat_postMessage(channel=channel, text=text)

    return _hook
