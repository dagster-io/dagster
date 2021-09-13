from typing import Callable, Optional

from dagster.core.definitions import failure_hook, success_hook
from dagster.core.execution.context.hook import HookContext


def _default_status_message(context: HookContext, status: str) -> str:
    return "{described_node} on {described_target} {status}!\nRun ID: {run_id}".format(
        described_node=context.solid.describe_node(),
        described_target=context.describe_target(),
        run_id=context.run_id,
        status=status,
    )


def _default_failure_message(context: HookContext) -> str:
    return _default_status_message(context, status="failed")


def _default_success_message(context: HookContext) -> str:
    return _default_status_message(context, status="succeeded")


def slack_on_failure(
    channel: str,
    message_fn: Callable[[HookContext], str] = _default_failure_message,
    dagit_base_url: Optional[str] = None,
):
    """Create a hook on step failure events that will message the given Slack channel.

    Args:
        channel (str): The channel to send the message to (e.g. "#my_channel")
        message_fn (Optional(Callable[[HookContext], str])): Function which takes in the HookContext
            outputs the message you want to send.
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this to allow
            messages to include deeplinks to the specific run that triggered the hook.

    Examples:
        .. code-block:: python

            my_graph.to_job(hooks={slack_on_failure("#foo", dagit_base_url="http://localhost:3000")})

        .. code-block:: python

            def my_message_fn(context: HookContext) -> str:
                return "Op {op_name} failed!".format(
                    op_name=context.op.name
                )

            @op
            def a_op(context):
                pass

            @graph(...)
            def my_graph():
                a_op.with_hooks(hook_defs={slack_on_failure("#foo", my_message_fn)})

    Legacy Examples:
        .. code-block:: python

            @slack_on_failure("#foo", dagit_base_url="http://localhost:3000")
            @pipeline(...)
            def my_pipeline():
                pass

        .. code-block:: python

            def my_message_fn(context: HookContext) -> str:
                return "Solid {solid_name} failed!".format(
                    solid_name=context.solid
                )

            @solid
            def a_solid(context):
                pass

            @pipeline(...)
            def my_pipeline():
                a_solid.with_hooks(hook_defs={slack_on_failure("#foo", my_message_fn)})

    """

    @failure_hook(required_resource_keys={"slack"})
    def _hook(context: HookContext):
        text = message_fn(context)
        if dagit_base_url:
            text += "\n<{base_url}/instance/runs/{run_id}|View in Dagit>".format(
                base_url=dagit_base_url, run_id=context.run_id
            )

        context.resources.slack.chat_postMessage(channel=channel, text=text)

    return _hook


def slack_on_success(
    channel: str,
    message_fn: Callable[[HookContext], str] = _default_success_message,
    dagit_base_url: Optional[str] = None,
):
    """Create a hook on step success events that will message the given Slack channel.

    Args:
        channel (str): The channel to send the message to (e.g. "#my_channel")
        message_fn (Optional(Callable[[HookContext], str])): Function which takes in the HookContext
            outputs the message you want to send.
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this to allow
            messages to include deeplinks to the specific run that triggered the hook.

    Examples:
        .. code-block:: python

            my_graph.to_job(hooks={slack_on_success("#foo", dagit_base_url="http://localhost:3000")})

        .. code-block:: python

            def my_message_fn(context: HookContext) -> str:
                return "Op {op_name} worked!".format(
                    op_name=context.op.name
                )

            @op
            def a_op(context):
                pass

            @graph(...)
            def my_graph():
                a_op.with_hooks(hook_defs={slack_on_success("#foo", my_message_fn)})

    Legacy Examples:
        .. code-block:: python

            @slack_on_success("#foo", dagit_base_url="http://localhost:3000")
            @pipeline(...)
            def my_pipeline():
                pass

        .. code-block:: python

            def my_message_fn(context: HookContext) -> str:
                return "Solid {solid_name} worked!".format(
                    solid_name=context.solid
                )

            @solid
            def a_solid(context):
                pass

            @pipeline(...)
            def my_pipeline():
                a_solid.with_hooks(hook_defs={slack_on_success("#foo", my_message_fn)})

    """

    @success_hook(required_resource_keys={"slack"})
    def _hook(context: HookContext):
        text = message_fn(context)
        if dagit_base_url:
            text += "\n<{base_url}/instance/runs/{run_id}|View in Dagit>".format(
                base_url=dagit_base_url, run_id=context.run_id
            )

        context.resources.slack.chat_postMessage(channel=channel, text=text)

    return _hook
